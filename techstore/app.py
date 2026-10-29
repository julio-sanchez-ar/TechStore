from functools import wraps

import bcrypt
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, flash

from config import SECRET_KEY
from db import consultar, ejecutar

app = Flask(__name__)
app.secret_key = SECRET_KEY


# ---------------------------------------------------------------------
#  Protección de páginas
# ---------------------------------------------------------------------

def login_requerido(vista):
    """Solo deja entrar si el usuario inició sesión."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "id_empleado" not in session:
            return redirect(url_for("login"))
        return vista(*args, **kwargs)
    return envoltura


def solo_admin(vista):
    """Solo deja entrar al rol Admin."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if session.get("rol") != "Admin":
            flash("No tienes permiso para esa opción.", "danger")
            return redirect(url_for("inicio"))
        return vista(*args, **kwargs)
    return envoltura


# ---------------------------------------------------------------------
#  Login y logout
# ---------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        clave = request.form["clave"]
        emp = consultar("SELECT * FROM empleado WHERE usuario = %s", (usuario,), uno=True)

        try:
            clave_ok = emp and bcrypt.checkpw(clave.encode(), emp["clave_hash"].encode())
        except ValueError:          # clave_hash todavía no es un hash válido
            clave_ok = False

        if clave_ok:
            session["id_empleado"] = emp["id_empleado"]
            session["nombre"] = emp["nombre"]
            session["rol"] = emp["rol"]
            return redirect(url_for("inicio"))
        flash("Usuario o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
#  Inicio
# ---------------------------------------------------------------------

@app.route("/")
@login_requerido
def inicio():
    resumen = {
        "productos": consultar("SELECT COUNT(*) AS n FROM producto WHERE activo = 1", uno=True)["n"],
        "clientes": consultar("SELECT COUNT(*) AS n FROM cliente", uno=True)["n"],
        "pendientes": consultar("SELECT COUNT(*) AS n FROM cotizacion WHERE estado = 'Pendiente'", uno=True)["n"],
        "ventas": consultar("SELECT COALESCE(SUM(total), 0) AS n FROM venta", uno=True)["n"],
    }
    return render_template("inicio.html", resumen=resumen)


# ---------------------------------------------------------------------
#  Productos
# ---------------------------------------------------------------------

@app.route("/productos")
@login_requerido
def productos():
    lista = consultar("""
        SELECT p.*, c.nombre AS categoria
          FROM producto p
          JOIN categoria c ON c.id_categoria = p.id_categoria
         WHERE p.activo = 1
         ORDER BY p.nombre
    """)
    return render_template("productos.html", productos=lista)


@app.route("/productos/nuevo", methods=["GET", "POST"])
@login_requerido
@solo_admin
def producto_nuevo():
    if request.method == "POST":
        f = request.form
        try:
            ejecutar("""INSERT INTO producto (nombre, tipo, precio, stock, id_categoria)
                        VALUES (%s, %s, %s, %s, %s)""",
                     (f["nombre"], f["tipo"], f["precio"], f["stock"], f["id_categoria"]))
            flash("Producto creado.", "success")
            return redirect(url_for("productos"))
        except mysql.connector.Error as e:
            flash(f"No se pudo guardar: {e.msg}", "danger")
    categorias = consultar("SELECT * FROM categoria ORDER BY nombre")
    return render_template("producto_form.html", producto=None, categorias=categorias)


@app.route("/productos/<int:id>/editar", methods=["GET", "POST"])
@login_requerido
@solo_admin
def producto_editar(id):
    if request.method == "POST":
        f = request.form
        try:
            ejecutar("""UPDATE producto
                           SET nombre = %s, tipo = %s, precio = %s, stock = %s, id_categoria = %s
                         WHERE id_producto = %s""",
                     (f["nombre"], f["tipo"], f["precio"], f["stock"], f["id_categoria"], id))
            flash("Producto actualizado.", "success")
            return redirect(url_for("productos"))
        except mysql.connector.Error as e:
            flash(f"No se pudo guardar: {e.msg}", "danger")
    producto = consultar("SELECT * FROM producto WHERE id_producto = %s", (id,), uno=True)
    categorias = consultar("SELECT * FROM categoria ORDER BY nombre")
    return render_template("producto_form.html", producto=producto, categorias=categorias)


@app.route("/productos/<int:id>/desactivar", methods=["POST"])
@login_requerido
@solo_admin
def producto_desactivar(id):
    ejecutar("UPDATE producto SET activo = 0 WHERE id_producto = %s", (id,))
    flash("Producto desactivado.", "warning")
    return redirect(url_for("productos"))


if __name__ == "__main__":
    app.run(debug=True)
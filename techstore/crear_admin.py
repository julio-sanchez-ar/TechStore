# Asigna una contraseña cifrada (bcrypt) a un empleado existente.
# Uso: python crear_admin.py
import bcrypt
from db import ejecutar, consultar

usuario = input("Usuario (ej. admin o cruiz): ").strip()
clave = input("Nueva contraseña: ").strip()

if not consultar("SELECT id_empleado FROM empleado WHERE usuario = %s", (usuario,), uno=True):
    print("Ese usuario no existe en la tabla empleado.")
else:
    clave_hash = bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode()
    ejecutar("UPDATE empleado SET clave_hash = %s WHERE usuario = %s", (clave_hash, usuario))
    print(f"Contraseña asignada a '{usuario}'. Ya puedes iniciar sesión.")
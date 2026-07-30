from werkzeug.security import generate_password_hash

# Contraseña que quieres hashear
password = "admin"

hashed_password = generate_password_hash(password)
print(hashed_password)

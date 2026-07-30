# Importaciones de la biblioteca estándar
import json
from functools import wraps

# Importaciones de terceros
import pymysql
import pymysql.cursors
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

# Importaciones de aplicaciones locales
from config import config
from models.model_user import User

app = Flask(__name__)

# Cargar configuración desde config.py
app.config.from_object(config["development"])

# Configuración de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = User.get(conn, user_id)
    conn.close()
    return user


def get_db_connection():
    return pymysql.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )


def registrar_auditoria(
    accion, tabla, id_registro, datos_viejos=None, datos_nuevos=None
):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO audit_log (user_name, action, table_name, record_id, old_data, new_data)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(
                sql,
                (
                    current_user.username,
                    accion,
                    tabla,
                    id_registro,
                    json.dumps(datos_viejos) if datos_viejos else None,
                    json.dumps(datos_nuevos) if datos_nuevos else None,
                ),
            )
        conn.commit()
        conn.close()
    except pymysql.Error as e:
        print(f"Error registrando auditoría: {e}")


# --- RUTAS DE AUTENTICACIÓN ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Ahora también traemos el email y el rol
            sql = "SELECT id, username, password, fullname, email, role FROM user WHERE username = %s AND is_active = TRUE"
            cursor.execute(sql, (username,))
            user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data["password"], password):
            # Creamos el objeto User con todos los datos
            user = User(
                user_data["id"],
                user_data["username"],
                None,  # No es necesario pasar la contraseña al objeto de sesión
                user_data["fullname"],
                user_data["email"],
                user_data["role"],
            )
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Usuario o contraseña incorrectos.")
            return redirect(url_for("login"))
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# 1. RUTA PRINCIPAL
@app.route("/")
@login_required
def index():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Apuntamos a la nueva tabla 'user' y seleccionamos las columnas correctas
            cursor.execute(
                "SELECT id, username, fullname, email, role FROM user WHERE is_active = TRUE ORDER BY id ASC;"
            )
            users = cursor.fetchall()
        conn.close()
        return render_template("index.html", users=users)
    except pymysql.Error as e:
        return f"Error al cargar usuarios: {e}"  # Esto debería ser un flash message y un redirect.


# --- DECORADOR PARA RESTRINGIR ACCESO POR ROL ---
def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Si el rol del usuario actual no está en los roles permitidos
            if current_user.role not in roles:
                # Puedes mostrar un mensaje de error o simplemente redirigir
                flash("No tienes permiso para acceder a esta página.", "danger")
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# 2. CREAR (INSERT)
@app.route("/users/create", methods=["POST"])
@login_required
@roles_required("Administrador")
def create_user():
    # Recibimos los datos del formulario con los nuevos nombres
    username = request.form["username"]
    password = request.form["password"]
    fullname = request.form["fullname"]
    email = request.form["email"]
    role = request.form["role"]

    # Hasheamos la contraseña antes de guardarla
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    with conn.cursor() as cursor:
        sql = """
            INSERT INTO user (username, password, fullname, email, role) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (username, hashed_password, fullname, email, role))
        new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    new_data = {
        "username": username,
        "fullname": fullname,
        "email": email,
        "role": role,
    }
    registrar_auditoria(
        "INSERT",
        "user",  # Nombre de la tabla en inglés
        new_id,
        datos_viejos=None,
        datos_nuevos=new_data,
    )

    return redirect(url_for("index"))


# 3. EDITAR (UPDATE)
@app.route("/users/update/<int:user_id>", methods=["POST"])
@login_required
@roles_required("Administrador")
def update_user(user_id):
    # Recibimos los datos del formulario con los nuevos nombres
    new_fullname = request.form["fullname"]
    new_email = request.form["email"]
    new_role = request.form["role"]

    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Obtenemos los datos viejos para la auditoría
        cursor.execute(
            "SELECT fullname, email, role FROM user WHERE id = %s;",
            (user_id,),
        )
        old_data = cursor.fetchone()

        # Ejecutamos la actualización
        sql = """
            UPDATE user 
            SET fullname = %s, email = %s, role = %s 
            WHERE id = %s;
        """
        cursor.execute(sql, (new_fullname, new_email, new_role, user_id))
    conn.commit()
    conn.close()

    # Registramos la auditoría
    new_data = {
        "fullname": new_fullname,
        "email": new_email,
        "role": new_role,
    }
    registrar_auditoria(
        "UPDATE",
        "user",
        user_id,
        datos_viejos=old_data,
        datos_nuevos=new_data,
    )

    return redirect(url_for("index"))


# 4. ELIMINAR (DELETE)
@app.route("/users/delete/<int:user_id>")
@login_required
@roles_required("Administrador")
def delete_user(user_id):
    # Prevenir que un administrador se elimine a sí mismo
    if current_user.id == user_id:
        flash("No puedes eliminar tu propia cuenta de administrador.", "danger")
        return redirect(url_for("index"))

    conn = get_db_connection()
    with conn.cursor() as cursor:
        # Obtenemos los datos viejos para la auditoría
        cursor.execute(
            "SELECT id, username, fullname, email, role, is_active FROM user WHERE id = %s;",
            (user_id,),
        )
        old_data = cursor.fetchone()

        # En lugar de eliminar, desactivamos el usuario
        cursor.execute("UPDATE user SET is_active = FALSE WHERE id = %s;", (user_id,))
    conn.commit()
    conn.close()

    registrar_auditoria(
        "DEACTIVATE",  # Usamos una nueva acción para ser más claros
        "user",
        user_id,
        datos_viejos=old_data,
        datos_nuevos=None,
    )

    flash(f"El usuario '{old_data['username']}' ha sido desactivado.", "success")
    return redirect(url_for("index"))


# 5. VER AUDITORÍA
@app.route("/audit")
@login_required
def auditoria():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM audit_log ORDER BY created_at DESC;")
            registros = cursor.fetchall()
        conn.close()
        return render_template("audit.html", registros=registros)
    except pymysql.Error as e:
        return f"Error al cargar la auditoría: {e}"


# 6. DASHBOARD
@app.route("/dashboard")
@login_required
@roles_required("Administrador")
def dashboard():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Consulta para contar usuarios por rol
            cursor.execute("SELECT role, COUNT(id) as total FROM user GROUP BY role")
            users_by_role = cursor.fetchall()

        conn.close()

        # Preparamos los datos para Chart.js
        labels = [row["role"] for row in users_by_role]
        data = [row["total"] for row in users_by_role]

        return render_template("dashboard.html", chart_labels=labels, chart_data=data)

    except pymysql.Error as e:
        return f"Error al cargar el dashboard: {e}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

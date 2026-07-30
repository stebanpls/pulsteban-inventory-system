from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, password, fullname="", email="", role=""):
        self.id = id
        self.username = username
        self.password = password
        self.fullname = fullname
        self.email = email
        self.role = role

    @staticmethod
    def get(db_connection, user_id):
        with db_connection.cursor() as cursor:
            sql = "SELECT id, username, fullname, email, role FROM user WHERE id = %s"
            cursor.execute(sql, (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                return User(
                    id=user_data["id"],
                    username=user_data["username"],
                    password=None,  # No almacenamos el hash en la sesión
                    fullname=user_data["fullname"],
                    email=user_data["email"],
                    role=user_data["role"],
                )
            return None

class Config:
    SECRET_KEY = "c8a7b6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5"


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_HOST = "db"  # o 'localhost' si pruebas sin Docker
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "root"
    MYSQL_DB = "inventario_calzado"


config = {"development": DevelopmentConfig}

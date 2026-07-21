from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."
login_manager.login_message_category = "error"

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.admin.routes import admin_bp
    from app.lis.routes import lis_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(lis_bp, url_prefix="/lis")

    with app.app_context():
        from app import models
        db.create_all()
        from app.database_upgrade import upgrade_database
        changes = upgrade_database()
        if changes:
            app.logger.info("Database upgraded: %s", ", ".join(changes))

    from app.catalog_sync import start_scheduler
    start_scheduler(app)

    @app.template_filter("datetime_br")
    def datetime_br(value):
        if not value: return "-"
        try: return value.strftime("%d/%m/%Y às %H:%M")
        except Exception: return str(value)

    return app

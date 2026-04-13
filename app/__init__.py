from flask import Flask, render_template
import os

from app.student.myprojects import myprojects_bp
from app.student.registration import registration_bp
from app.student.thesis import thesis_bp
from app.login import login_bp
from app.lecturer.registrationsmanagement import registrationsmanagement_bp
from app.database import close_db
from app.lecturer.home.routes import lecturer_home_bp


def create_app():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )
    app.config['SECRET_KEY'] = 'dev-key-academic-prestige' # Should be in env in production

    # Đăng ký teardown để tự động đóng DB
    app.teardown_appcontext(close_db)

    app.register_blueprint(thesis_bp)
    app.register_blueprint(myprojects_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(registrationsmanagement_bp)

    app.register_blueprint(lecturer_home_bp)

    return app
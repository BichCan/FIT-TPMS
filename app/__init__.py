from flask import Flask
import os

from app.myprojects import myprojects_bp
from .myprojects import routes

def create_app():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )

    from .thesis import thesis_bp
    from .thesis import routes
    app.register_blueprint(thesis_bp)
    app.register_blueprint(myprojects_bp)

    return app
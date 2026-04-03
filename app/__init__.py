from flask import Flask
import os

def create_app():
    base_dir = os.path.dirname(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )

    from .thesis import thesis_bp
    app.register_blueprint(thesis_bp)

    from .registration import registration_bp
    app.register_blueprint(registration_bp)

    return app
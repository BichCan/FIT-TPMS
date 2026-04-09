from flask import Blueprint

login_bp = Blueprint(
    "login",
    __name__,
    template_folder=None,
    static_folder=None)
from . import routes

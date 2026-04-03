from flask import Blueprint

registration_bp = Blueprint(
    "registration",
    __name__,
    template_folder=None,
    static_folder=None)
from . import routes

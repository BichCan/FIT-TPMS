from flask import Blueprint

registrationsmanagement_bp = Blueprint(
    "registrationsmanagement",
    __name__,
    template_folder=None,
    static_folder=None)
from . import routes

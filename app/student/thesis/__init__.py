from flask import Blueprint

thesis_bp = Blueprint(
    "thesis",
    __name__,
    template_folder=None,
    static_folder=None)
from . import routes
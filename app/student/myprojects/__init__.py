from flask import Blueprint

myprojects_bp = Blueprint('myprojects', __name__,
                          template_folder=None,
                          static_folder=None)
from . import routes


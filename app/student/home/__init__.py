from flask import Blueprint

student_home_bp = Blueprint('student_home', __name__)

from . import routes

from flask import Blueprint

supervisor_bp = Blueprint('supervisor', __name__)

from app.supervisor import routes

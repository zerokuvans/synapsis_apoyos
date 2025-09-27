from flask import Blueprint

movil_bp = Blueprint('movil', __name__, template_folder='../../templates/movil')

from . import routes
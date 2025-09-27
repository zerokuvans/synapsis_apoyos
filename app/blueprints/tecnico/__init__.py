from flask import Blueprint

tecnico_bp = Blueprint('tecnico', __name__, template_folder='../../templates/tecnico')

from . import routes
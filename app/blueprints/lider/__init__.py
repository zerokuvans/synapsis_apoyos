from flask import Blueprint

lider_bp = Blueprint('lider', __name__, template_folder='../../templates/lider')

from . import routes
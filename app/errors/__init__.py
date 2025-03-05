from flask import Blueprint

# Configuração da blueprint
bp = Blueprint('errors', __name__)

# Importando os handlers
from app.errors import handlers
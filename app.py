# Importando o app
from app import app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Post



# Decorator para debug no shell
@app.shell_context_processor
def make_shell_context():
    # Dicionário para meu interpretador
    return {'sa':sa, 'so':so, 'db':db, 'User':User, 'Post':Post}

# Inicializando o Flask
if __name__ == '__main__':
    # Iniciando o app
    app.run(debug=True)
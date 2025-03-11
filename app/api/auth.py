import sqlalchemy as sa
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app import db
from app.models import User
from app.api.errors import resposta_erro

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verifica_senha(username, senha):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user and user.check_senha(senha):
        return user
    

@basic_auth.error_handler
def handle_auth_error(status):
    return resposta_erro(status)


@token_auth.verify_token
def verifica_token(token):
    return User.check_token(token) if token else None

@token_auth.error_handler
def token_auth_error(status):
    return resposta_erro(status)
from app.api import bp
from app.models import User
from app import db
from flask import request, url_for, abort
import sqlalchemy as sa
from app.api.errors import bad_request
from app.api.auth import token_auth



@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return db.get_or_404(User, id).to_dict()

@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_colection_dict(sa.select(User), page, per_page, 'api.get_users')

@bp.route('/users/<int:id>/seguidores', methods=['GET'])
@token_auth.login_required
def get_seguidores(id):
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_colection_dict(user.seguidores.select(), page, per_page, 'api.get_seguidores', id=id)


@bp.route('/users/<int:id>/seguindo', methods=['GET'])
@token_auth.login_required
def get_seguindo(id):
    user = db.get_or_404(User, id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    return User.to_colection_dict(user.seguindo.select(), page, per_page, 'api.get_seguindo', id=id)

@bp.route('/users', methods=['POST'])
def criar_user(id):
    data = request.get_json()
    if 'username' not in data or 'email' not in data or 'senha' not in data:
        return bad_request('Preencha os campos de usuário, email e senha')
    if db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        return bad_request('Por favor, user um nome de usuário diferente')
    if db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        return bad_request('Por favor, use um e-mail diferente')
    
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    return user.to_dict(), 201, {'location': url_for('api.get_user',
                                                     id=user.id)}

@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def atualizar_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    user = db.get_or_404(User, id)
    data = request.get_json()
    if 'username' in data and data['username'] != user.username and db.session.scalar(sa.select(User).where(
            User.username == data['username'])):
        return bad_request('Por favor, use um nome de usuário diferente')
    if 'email' in data and data['email'] != user.email and db.session.scalar(sa.select(User).where(
            User.email == data['email'])):
        return bad_request('Por favor, use um e-mail diferente')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return user.to_dict()
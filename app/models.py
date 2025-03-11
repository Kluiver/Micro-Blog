from app import db, login
from flask import current_app, url_for
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt
import json
import secrets

class PagimatedAPIMixin(object):
    @staticmethod
    def to_colection_dict(busca, page, per_page, endpoint, **kwargs):
        resources = db.paginate(busca, page=page, per_page=per_page,
                                error_out=False)
        
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total,
                '_links': {
                   'self': url_for(endpoint, page=page, per_page=per_page,
                                  **kwargs),
                    'next': url_for(endpoint, page=page + 1,
                                  per_page=per_page, **kwargs) if resources.has_next else None,
                    'prev': url_for(endpoint, page=page - 1,
                                  per_page=per_page, **kwargs) if resources.has_prev else None
                }
            }
        }
        return data


# Definindo a função que será chamada quando um usuário é carregado
@login.user_loader
def login(id):
    return db.session.get(User, int(id))

# tabela de associação para seguidores, precisa estar à cima do modelo user
seguidores = sa.Table(
    'seguidores',
    db.metadata,
    sa.Column('seguidor_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True),
    sa.Column('seguindo_id', sa.Integer, sa.ForeignKey('user.id'), primary_key=True)
)


# criando a classe de usuário
class User(PagimatedAPIMixin, UserMixin, db.Model):
    # Definindo os campos para a tabela USER do banco de dados
    id: so.Mapped[int] = so.mapped_column(primary_key=True) # ID será o campo primário de todas as tabelas
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True) # Defino que o usuário será idexável e é único
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index= True, unique=True) # email e senha também será único e indexável
    senha_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    # Relacionando a tabela usuário com a tabela posts
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='autor')
    sobre_mim: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    visto_ultimo: so.Mapped[Optional[datetime]] = so.mapped_column(default = lambda: datetime.now(timezone.utc))
    # Relacionando a tabeba usuário com a tabela mensagem
    tempo_ultima_mensagem_lida: so.Mapped[Optional[datetime]]
    mensagens_enviadas: so.WriteOnlyMapped['Mensagem'] = so.relationship(
        foreign_keys='Mensagem.remetente_id', back_populates='autor')
    mensagens_recebidas: so.WriteOnlyMapped['Mensagem'] = so.relationship(
        foreign_keys='Mensagem.destinatario_id', back_populates='destinatario')
    # Relacionando tabela usuário com a tabela de notificação
    notificacoes: so.WriteOnlyMapped['Notificacao'] = so.relationship(back_populates='user')
    token: so.Mapped[Optional[str]] = so.mapped_column(sa.String(32), index=True, unique=True)
    token_expiration: so.Mapped[Optional[datetime]]

    # Função para dar um token de autenticação para o usuário
    def get_token(self, expires_in=3600):
        now = datetime.now(timezone.utc)
        if self.token and self.token_expiration.replace(
                tzinfo=timezone.utc) > now + timedelta(seconds=60):
            return self.token
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token
    
    # Função para remover o o token de autentticação
    def revoke_token(self):
        self.token_expiration = datetime.now(timezone.utc) - timedelta(seconds=1)

    # Metodo statico para checar o token
    @staticmethod
    def check_token(token):
        user = db.session.scalar(sa.select(User).where(User.token == token))
        if user is None or user.token_expiration.replace(
                tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return user
    
    # Função que verifica quantidade de mensagens não lidas
    def qtd_msg_nao_lidas(self):
        tempo_ultima_lida = self.tempo_ultima_mensagem_lida or datetime(1900, 1, 1)
        busca = sa.select(Mensagem).where(Mensagem.destinatario == self,
                                          Mensagem.tempo > tempo_ultima_lida)
        return db.session.scalar(sa.select(sa.func.count()).select_from(busca.subquery()))


    # Relacionando a tabela de seguidores e seguindo
    seguindo: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=seguidores, primaryjoin=(seguidores.c.seguidor_id == id),
        secondaryjoin=(seguidores.c.seguindo_id == id),
        back_populates='seguidores'
    )

    seguidores: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=seguidores, primaryjoin=(seguidores.c.seguindo_id == id),
        secondaryjoin=(seguidores.c.seguidor_id == id),
        back_populates='seguindo'

    )


    # Definindo como o python mostra objetos dessa classe
    def __repr__(self):
        return f'<User: {self.username}>' 
    
    # Função para definir senha do usuário
    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    # Função para verificar se a senha do usuário é igual à do hash
    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    # Função para gerar um token JWT para resetar senha
    def get_token_recuperar_senha(self, expira_em=600):
        return jwt.encode(
            {'recuperar_senha': self.id, 'exp': time() + expira_em},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # Função para gerar um avatar
    def avatar(self, tamanho):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={tamanho}'
    
    # Função para seguir outro usuário
    def seguir(self, user):
        if not self.esta_seguindo(user):
            self.seguindo.add(user)

    # Função para deixar de seguir outro usuário
    def deixar_de_seguir(self, user):
        if self.esta_seguindo(user):
            self.seguindo.remove(user)

    # Função para verificar se o usuário está seguindo outro
    def esta_seguindo(self, user):
        busca = self.seguindo.select().where(User.id == user.id)
        return db.session.scalar(busca) is not None
    
    # Função para verificar a quantidade de seguidores
    def quantidade_seguidores(self):
        busca = sa.select(sa.func.count()).select_from(
            self.seguidores.select().subquery())
        return db.session.scalar(busca)
    
    # Função para verificar a quantidade de pessoas que sigo
    def quantidade_seguindo(self):
        busca = sa.select(sa.func.count()).select_from(
            self.seguindo.select().subquery())
        return db.session.scalar(busca)

    # Função que retorna os posts das pessoas que o usuário segue
    def posts_seguidos(self):
        Autor = so.aliased(User)
        Seguidor = so.aliased(User)

        return(
            sa.select(Post)
            .join(Post.autor.of_type(Autor))
            .join(Autor.seguidores.of_type(Seguidor), isouter=True)
            .where(sa.or_(
                Seguidor.id == self.id,
                Autor.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.tempo.desc())
        )
    
    # Função da classe para verificar o token de recurar senha
    @staticmethod
    def verificar_token_senha(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['recuperar_senha']
        except:
            return
        return db.session.get(User, id)
    
    # Função para adicionar notificação
    def add_notificacao(self, nome, data):
        db.session.execute(self.notificacoes.delete().where(
            Notificacao.nome == nome))
        
        n = Notificacao(nome=nome, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n
    
    # Função para verificar qnt de posts do usuário
    def qtd_posts(self):
        busca = sa.select(sa.func.count()).select_from(
            self.posts.select().subquery())
        return db.session.scalar(busca)
    
    # Função para converter os dados em um dicionario
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'visto_ultimo': self.visto_ultimo.replace(
                tzinfo=timezone.utc).isoformat() if self.visto_ultimo else None,
            'sobre_mim': self.sobre_mim,
            'qtd_posts': self.qtd_posts(),
            'quantidade_seguidores': self.quantidade_seguidores(),
            'quantidade_seguindo': self.quantidade_seguindo(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'seguidores': url_for('api.get_seguidores', id=self.id),
                'seguindo': url_for('api.get_seguindo', id=self.id),
                'avatar': self.avatar(128)
            }
        }

        # Se incluir email for TRUE, incluo o email em data
        if include_email:
            data['email'] = self.email

        # Retorno os dados
        return data
    
    # Fução para converter de dicionário para objeto
    def from_dict(self, data, new_user=False):
        # Para cada campo em username, email e sobre mim
        for field in ['username', 'email', 'sobre_mim']:
            # Se o campo estiver presente no dicionário
            if field in data:
                setattr(self, field, data[field])
        # Se o novo usuário estiver a ser criado
        if new_user and 'senha' in data:
            self.set_senha(data['senha'])

    

# Classe para posts
class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    corpo: so.Mapped[str] = so.mapped_column(sa.String(280))
    # Pegando o horário do post
    tempo: so.Mapped[datetime] = so.mapped_column(index=True, default= lambda : datetime.now(timezone.utc))
    # Vinculando o usuário com post
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    # definindo o usuário que postou
    autor: so.Mapped[User] = so.relationship(back_populates='posts')


    def __repr__(self):
        return f'<Post {self.corpo}>'
    
# Classe para mensagens diretas
class Mensagem(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    remetente_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    destinatario_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    corpo: so.Mapped[str] = so.mapped_column(sa.String(140))
    tempo: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda : datetime.now(timezone.utc))
    # Vinculando o usuário que enviou a mensagem
    autor: so.Mapped[User] = so.relationship(foreign_keys='Mensagem.remetente_id', back_populates='mensagens_enviadas')
    # Vinculando o usuário que recebeu a mensagem
    destinatario: so.Mapped[User] = so.relationship(foreign_keys='Mensagem.destinatario_id', back_populates='mensagens_recebidas')

    def __repr__(self):
        return f'<Mensagem {self.corpo}>'


# Classe de notificação
class Notificacao(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    nome: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    
    tempo: so.Mapped[float] = so.mapped_column(index=True, default=time)
    payload_json: so.Mapped[str] = so.mapped_column(sa.Text)

    user: so.Mapped[User] = so.relationship(back_populates='notificacoes')

    def get_data(self):
        return json.loads(str(self.payload_json))




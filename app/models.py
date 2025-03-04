from app import db, login, app
import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import Optional
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from time import time
import jwt



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
class User(UserMixin, db.Model):
    # Definindo os campos para a tabela USER do banco de dados
    id: so.Mapped[int] = so.mapped_column(primary_key=True) # ID será o campo primário de todas as tabelas
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True) # Defino que o usuário será idexável e é único
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index= True, unique=True) # email e senha também será único e indexável
    senha_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    # Relacionando a tabela usuário com a tabela posts
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='autor')
    sobre_mim: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    visto_ultimo: so.Mapped[Optional[datetime]] = so.mapped_column(default = lambda: datetime.now(timezone.utc))

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
            app.config['SECRET_KEY'], algorithm='HS256')
    
    # Função para gerar um avatar
    def avatar(self, tamanho):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?s={tamanho}&d=identicon'
    
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
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['recuperar_senha']
        except:
            return
        return db.session.get(User, id)
    

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
    
    



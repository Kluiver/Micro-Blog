from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
import sqlalchemy as sa
from app import db
from app.models import User

# Formulário de login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Campo obrigatório')])
    senha = PasswordField('Senha', validators=[DataRequired('Campo obrigatório')])
    manter_conectado = BooleanField('Manter conectado')
    btn_submit = SubmitField('Entrar')

# Formulário de cadastro
class CadastroForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Campo obrigatório')]) 
    email = StringField('Email', validators=[DataRequired('Campo obrigatório'), Email('E-mail inválido!')])
    senha = PasswordField('Senha', validators=[DataRequired('Campo obrigatório')])
    senha2 = PasswordField('Confirme a senha', validators=[DataRequired('Campo obrigatório'), EqualTo('senha', 'As senhas não são iguais!')])
    btn_submit = SubmitField('Cadastrar')

    # Função para validar o usuário
    def validate_username(self, username):
        # Verificando se tem outro usuário com o mesmo nome no banco de dados
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        # Se já tem alguém com esse usuário, mostro o aviso para o usuário
        if user is not None:
            raise ValidationError('Este nome de usuário já está em uso.')
        
    # Função para validar o email
    def validate_email(self, email):
        # Verificando se tem outro usuário como o mesmo e-mail no banco de dados
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        # Se já tem alguém com esse e-mail, mostro o aviso para o usuário
        if user is not None:
            raise ValidationError('Este e-mail já está em uso.')
        
# Formulário de edição de dados
class EditarPerfilForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired('Campo obrigatório')])
    sobre_mim = TextAreaField('Sobre mim', validators=[Length(min=0, max=140, message='Tamanho máximo excedido!')])
    btn_submit = SubmitField('Salvar')

    # Contrutor definindo meu username original
    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    # Validador de nome de usuário
    def validate_username(self, username):
        # Se o username for diferente do nome original
        if username.data != self.original_username:
            # Verificando se tem outro usuário com o mesmo nome no banco de dados
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            # Se já existe um usuário com esse nome, levanto um erro de validação
            if user is not None:
                raise ValidationError('Este nome de usuário já está em uso.')
        
# Formulário vazio para seguir e deixar de seguir um usuário
class VazioForm(FlaskForm):
    btn_submit = SubmitField('Enviar')

# Formulário para criação de posts
class PostForm(FlaskForm):
    post = TextAreaField('Diga alguma coisa', validators=[DataRequired('Campo obrigatório'), Length(min=1, max=140, message='Tamanho de texto inválido')])
    btn_submit = SubmitField('Postar')
    

# Formulário para SOLICITAR o resetar senha
class SolicitarRecuperarSenhaForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Campo obrigatório'), Email('Email inválido')])
    btn_submit = SubmitField('Recuperar senha')

# Formulário para resetar a senha
class ResetarSenhaForm(FlaskForm):
    senha = PasswordField('Senha', validators=[DataRequired('Campo obrigatório')])
    senha2 = PasswordField('Confirme a senha', validators=[DataRequired('Campo obrigatório'), EqualTo('senha', 'As senhas não são iguais!')])
    btn_submit = SubmitField('Resetar senha')
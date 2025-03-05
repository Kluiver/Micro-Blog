from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
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
        

# Formulário para SOLICITAR o resetar senha
class SolicitarRecuperarSenhaForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired('Campo obrigatório'), Email('Email inválido')])
    btn_submit = SubmitField('Recuperar senha')


# Formulário para resetar a senha
class ResetarSenhaForm(FlaskForm):
    senha = PasswordField('Senha', validators=[DataRequired('Campo obrigatório')])
    senha2 = PasswordField('Confirme a senha', validators=[DataRequired('Campo obrigatório'), EqualTo('senha', 'As senhas não são iguais!')])
    btn_submit = SubmitField('Resetar senha')
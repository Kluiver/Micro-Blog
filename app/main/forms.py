from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length
import sqlalchemy as sa
from app import db
from app.models import User

        
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
    
# Formulário para enviar mensagem
class MensagemForm(FlaskForm):
    mensagem = TextAreaField('Mensagem', validators=[DataRequired(), Length(min=0, max=140)])
    btn_submit = SubmitField('Enviar')
# Importando bibliotecas
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask_mail import Mail
from flask_moment import Moment

 

# criando o aplicativo e configurando
app = Flask(__name__)
# Configurando o aplicativo com a classe CONFIG do arquivo config
app.config.from_object(Config)
# Configurando app email
mail = Mail(app)

# Configurando banco de dados
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuração de Login
login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'Faça login para acessar essa página'

# Configuração do Moment
moment = Moment(app)


# SE o app não estiver em debug, configuro o envio de email de erros
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Erro no MicroBlog',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    # Se o diretório logs não existe, crio ele
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)

    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog inicializado')

from app import views, models, error


# Arquivo responsável por enviar emails para o usuário
from flask_mail import Message
from app import mail, app
from flask import render_template
from threading import Thread

# Deixando o envio de email mais leve para a aplicação
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# Função para enviar email
def enviar_email(assunto, remetente, destinatarios, corpo_texto, corpo_html):
    msg = Message(assunto, sender=remetente, recipients=destinatarios)
    msg.body = corpo_texto
    msg.html = corpo_html
    Thread(target=send_async_email, args=(app, msg)).start()

def enviar_recuperar_senha_email(user):
    token = user.get_token_recuperar_senha()
    enviar_email('[Microblog] Recupere sua senha', 
                 remetente=app.config['ADMINS'][0],
                 destinatarios=[user.email],
                 corpo_texto=render_template('email/recuperar_senha.txt',
                                             user=user, token=token),
                 corpo_html=render_template('email/recuperar_senha.html',
                                             user=user, token=token))
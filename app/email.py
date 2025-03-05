# Arquivo responsável por enviar emails para o usuário
from flask_mail import Message
from app import mail
from threading import Thread
from flask import current_app

# Deixando o envio de email mais leve para a aplicação
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

# Função para enviar email
def enviar_email(assunto, remetente, destinatarios, corpo_texto, corpo_html):
    msg = Message(assunto, sender=remetente, recipients=destinatarios)
    msg.body = corpo_texto
    msg.html = corpo_html
    Thread(target=send_async_email,
            args=(current_app._get_current_object(), msg)).start()


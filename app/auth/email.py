from flask import render_template, current_app
from app.email import enviar_email

def enviar_recuperar_senha_email(user):
    token = user.get_token_recuperar_senha()
    enviar_email('[Microblog] Recupere sua senha', 
                 remetente=current_app.config['ADMINS'][0],
                 destinatarios=[user.email],
                 corpo_texto=render_template('email/recuperar_senha.txt',
                                             user=user, token=token),
                 corpo_html=render_template('email/recuperar_senha.html',
                                             user=user, token=token))
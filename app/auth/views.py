from flask import render_template, url_for, redirect, flash, request
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
import sqlalchemy as sa
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, CadastroForm, ResetarSenhaForm, SolicitarRecuperarSenhaForm
from app.models import User
from app.auth.email import enviar_recuperar_senha_email


@bp.route('/login/', methods=['POST', 'GET'])
def login():
    # Se o usuário tá  autenticado
    if current_user.is_authenticated:
        return redirect(url_for('main.homepage'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Procurando o usuário no banco de dados
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        # Se o usuário não existir ou se a senha estiver incorreta
        if user is None or not user.check_senha(form.senha.data):
            # Mostro erro de usuário ou senha
            flash('Usuário ou senha inválidos!')
            return redirect(url_for('auth.login'))
        # se consegui logar, logo o usuário
        login_user(user, remember=form.manter_conectado.data)
        # Salvando a proxima página para o usuário
        proxima_pagina = request.args.get('next')
        # Se não tenho proxima pagina, o url fica vazio
        if not proxima_pagina or urlsplit(proxima_pagina).netloc != '':
            proxima_pagina = url_for('main.homepage')
        # redireciono para a home page
        return redirect(proxima_pagina)
    return render_template('auth/login.html', titulo='Login', form=form)


# Função para logout
@bp.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('main.homepage'))


# Rota para cadastro
@bp.route('/cadastro/', methods=['POST', 'GET'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('main.homepage'))
    
    form = CadastroForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_senha(form.senha.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('auth.login'))
    return render_template('auth/cadastro.html', titulo='cadastro', form=form)


@bp.route('/recuperar_senha/<token>', methods=['POST', 'GET'])
def recuperar_senha(token):
    # Se o usuário está logando, ele volta para a tela inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.homepage'))
    
    user= User.verificar_token_senha(token)

    if not user:
        return redirect(url_for('main.homepage'))
    
    form = ResetarSenhaForm()
    if form.validate_on_submit():
        # Procurando o usuário no banco de dados com base no email do formulário
        user.set_senha(form.senha.data)
        db.session.commit()
        flash('Sua senha foi resetada.')
        return redirect(url_for('auth.login'))
    return render_template('auth/resetar_senha.html', form=form)


@bp.route('/solicitar_recuperar_senha/', methods=['POST', 'GET'])
def solicitar_recuperar_senha():
    if current_user.is_authenticated:
        return redirect(url_for('main.homepage'))
    
    form = SolicitarRecuperarSenhaForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            enviar_recuperar_senha_email(user)
        flash('Um email foi enviado para você com instruções para recuperar a senha.')
        return redirect(url_for('auth.login'))
    return render_template('auth/solicitar_recuperar_senha.html', titulo = 'Resetar senha', form=form)
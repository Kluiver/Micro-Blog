from app import app, db
from flask import render_template, redirect, flash, url_for, request
from app.forms import LoginForm, CadastroForm, EditarPerfilForm, VazioForm, PostForm, SolicitarRecuperarSenhaForm, ResetarSenhaForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Post
import sqlalchemy as sa
from urllib.parse import urlsplit
from datetime import datetime, timezone
from app.email import enviar_recuperar_senha_email

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@login_required
def homepage():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(corpo = form.post.data, autor=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Seu post foi enviado!')
        return redirect(url_for('homepage'))
    
    # PAGINAÇÃO
    pagina = request.args.get('pagina', 1, type=int)
    posts = db.paginate(current_user.posts_seguidos(), page=pagina,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    # Proxima Página
    proxima_url = url_for('homepage', pagina=posts.next_num) \
         if posts.has_next else None
     # Página anterior
    anterior_url = url_for('homepage', pagina=posts.prev_num) \
         if posts.has_prev else None

    # next_url = url_for('homepage', pagina=posts.next_num) \
    #     if posts.has_next else None
    # prev_url = url_for('homepage', pagina=posts.prev_num) \
    #     if posts.has_prev else None
    
    return render_template('index.html', titulo='Home', posts=posts.items, form=form,
                           proxima_url=proxima_url, anterior_url=anterior_url)

@app.route('/login/', methods=['POST', 'GET'])
def login():
    # Se o usuário tá  autenticado
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Procurando o usuário no banco de dados
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        # Se o usuário não existir ou se a senha estiver incorreta
        if user is None or not user.check_senha(form.senha.data):
            # Mostro erro de usuário ou senha
            flash('Usuário ou senha inválidos!')
            return redirect(url_for('login'))
        # se consegui logar, logo o usuário
        login_user(user, remember=form.manter_conectado.data)
        # Salvando a proxima página para o usuário
        proxima_pagina = request.args.get('next')
        # Se não tenho proxima pagina, o url fica vazio
        if not proxima_pagina or urlsplit(proxima_pagina).netloc != '':
            proxima_pagina = url_for('homepage')
        # redireciono para a home page
        return redirect(proxima_pagina)
    return render_template('login.html', titulo='Login', form=form)

# Função para logout
@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('homepage'))

# Rota para cadastro
@app.route('/cadastro/', methods=['POST', 'GET'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = CadastroForm()

    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_senha(form.senha.data)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('login'))
    return render_template('cadastro.html', titulo='cadastro', form=form)

# Perfil do usuário
@app.route('/perfil/<username>')
@login_required
def perfil(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    
    pagina = request.args.get('pagina', 1, type=int)
    busca = user.posts.select().order_by(Post.tempo.desc())

    posts = db.paginate(busca, page=pagina,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    
    proxima_url = url_for('perfil', username=user.username, pagina=posts.next_num) \
        if posts.has_next else None
    anterior_url = url_for('perfil', username=user.username, pagina=posts.prev_num) \
        if posts.has_prev else None

    form = VazioForm()
    return render_template('perfil.html', user=user, posts=posts.items, form=form, proxima_url=proxima_url, anterior_url=anterior_url)

# Função para pegar a ultima vez que o usuário ficou online
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.visto_ultimo = datetime.now(timezone.utc)
        db.session.commit()
    
# Rota para editar o perfil do usuário

@app.route('/editar_perfil/', methods=['POST', 'GET'])
@login_required
def editar_perfil():
    form = EditarPerfilForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.sobre_mim = form.sobre_mim.data
        db.session.commit()
        flash('Perfil editado com sucesso!')
    # Se o request foi do tipo GET
    if request.method == 'GET':
        form.username.data = current_user.username
        form.sobre_mim.data = current_user.sobre_mim
    return render_template('editar_perfil.html', titulo='Editar Perfil', form=form)


# Rota para seguir e deixar de seguir usuário
@app.route('/seguir/<username>/', methods=['POST'])
@login_required
def seguir(username):
    form = VazioForm()

    if form.validate_on_submit():
        # Procuro o usuário no banco de dados
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        # Se não encontrar, falo que usuário não foi encontrado.
        if user is None:
            flash(f'Usuário {username} não encontrado.')
            return redirect(url_for('homepage'))
        # Se o usuário for o usuário atual, falo que não pode seguir ele mesmo
        if user == current_user:
            flash('Você não pode seguir a si mesmo!')
            return redirect(url_for('perfil', username=username))

        current_user.seguir(user)
        db.session.commit()
        flash(f'Você está seguindo {username}.')
        return redirect(url_for('perfil', username=username))
    else:
        return redirect(url_for('homepage'))
    
# Deixar de seguir
@app.route('/deixar_de_seguir/<username>/', methods=['POST'])
@login_required
def deixar_de_seguir(username):
    form = VazioForm()

    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'Usuário {username} não encontrado.')
            return redirect(url_for('homepage'))
        if user == current_user:
            flash('Você não pode deixar de seguir a si mesmo!')
            return redirect(url_for('homepage'))
        
        current_user.deixar_de_seguir(user)
        db.session.commit()
        flash(f'Você não está mais seguindo {username}.')
        return redirect(url_for('perfil', username=username))
    else:
        return redirect(url_for('homepage'))
    
# Rota com todos os posts do site
@app.route('/explorar')
@login_required
def explorar():
    # Paginação
    page = request.args.get('page', 1, type=int)
    busca = sa.select(Post).order_by(Post.tempo.desc())
    posts = db.paginate(busca, page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    
    proxima_url = url_for('explorar', page=posts.next_num) \
        if posts.has_next else None
    anterior_url = url_for('explorar', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('index.html', titulo='Explorar', posts=posts, anterior_url=anterior_url, proxima_url=proxima_url)

@app.route('/recuperar_senha/<token>', methods=['POST', 'GET'])
def recuperar_senha(token):
    # Se o usuário está logando, ele volta para a tela inicial
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    user= User.verificar_token_senha(token)

    if not user:
        return redirect(url_for('homepage'))
    
    form = ResetarSenhaForm()
    if form.validate_on_submit():
        # Procurando o usuário no banco de dados com base no email do formulário
        user.set_senha(form.senha.data)
        db.session.commit()
        flash('Sua senha foi resetada.')
        return redirect(url_for('login'))
    return render_template('resetar_senha.html', form=form)

@app.route('/solicitar_recuperar_senha/', methods=['POST', 'GET'])
def solicitar_recuperar_senha():
    if current_user.is_authenticated:
        return redirect(url_for('homepage'))
    
    form = SolicitarRecuperarSenhaForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            enviar_recuperar_senha_email(user)
        flash('Um email foi enviado para você com instruções para recuperar a senha.')
        return redirect(url_for('login'))
    return render_template('solicitar_recuperar_senha.html', titulo = 'Resetar senha', form=form)
        
        

        

@app.route('/cause_500')
def cause_error():
    1 / 0  # Isso causará um erro 500 de divisão por zero


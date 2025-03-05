from app import db
from flask import render_template, redirect, flash, url_for, request, current_app
from app.main.forms import EditarPerfilForm, VazioForm, PostForm
from flask_login import current_user, login_required
from app.models import User, Post
import sqlalchemy as sa
from datetime import datetime, timezone
from app.main import bp
from flask import current_app


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/home', methods=['GET', 'POST'])
@login_required
def homepage():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(corpo = form.post.data, autor=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Seu post foi enviado!')
        return redirect(url_for('main.homepage'))
    
    # PAGINAÇÃO
    pagina = request.args.get('pagina', 1, type=int)
    posts = db.paginate(current_user.posts_seguidos(), page=pagina,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    # Proxima Página
    proxima_url = url_for('main.homepage', pagina=posts.next_num) \
         if posts.has_next else None
     # Página anterior
    anterior_url = url_for('main.homepage', pagina=posts.prev_num) \
         if posts.has_prev else None

    # next_url = url_for('homepage', pagina=posts.next_num) \
    #     if posts.has_next else None
    # prev_url = url_for('homepage', pagina=posts.prev_num) \
    #     if posts.has_prev else None
    
    return render_template('index.html', titulo='Home', posts=posts.items, form=form,
                           proxima_url=proxima_url, anterior_url=anterior_url)



# Perfil do usuário
@bp.route('/perfil/<username>')
@login_required
def perfil(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    
    pagina = request.args.get('pagina', 1, type=int)
    busca = user.posts.select().order_by(Post.tempo.desc())

    posts = db.paginate(busca, page=pagina,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    
    proxima_url = url_for('main.perfil', username=user.username, pagina=posts.next_num) \
        if posts.has_next else None
    anterior_url = url_for('main.perfil', username=user.username, pagina=posts.prev_num) \
        if posts.has_prev else None

    form = VazioForm()
    return render_template('perfil.html', user=user, posts=posts.items, form=form, proxima_url=proxima_url, anterior_url=anterior_url)

# Função para pegar a ultima vez que o usuário ficou online
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.visto_ultimo = datetime.now(timezone.utc)
        db.session.commit()
    
# Rota para editar o perfil do usuário

@bp.route('/editar_perfil/', methods=['POST', 'GET'])
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
@bp.route('/seguir/<username>/', methods=['POST'])
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
            return redirect(url_for('main.homepage'))
        # Se o usuário for o usuário atual, falo que não pode seguir ele mesmo
        if user == current_user:
            flash('Você não pode seguir a si mesmo!')
            return redirect(url_for('main.perfil', username=username))

        current_user.seguir(user)
        db.session.commit()
        flash(f'Você está seguindo {username}.')
        return redirect(url_for('main.perfil', username=username))
    else:
        return redirect(url_for('main.homepage'))
    
# Deixar de seguir
@bp.route('/deixar_de_seguir/<username>/', methods=['POST'])
@login_required
def deixar_de_seguir(username):
    form = VazioForm()

    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'Usuário {username} não encontrado.')
            return redirect(url_for('main.homepage'))
        if user == current_user:
            flash('Você não pode deixar de seguir a si mesmo!')
            return redirect(url_for('main.homepage'))
        
        current_user.deixar_de_seguir(user)
        db.session.commit()
        flash(f'Você não está mais seguindo {username}.')
        return redirect(url_for('main.perfil', username=username))
    else:
        return redirect(url_for('main.homepage'))
    
# Rota com todos os posts do site
@bp.route('/explorar')
@login_required
def explorar():
    # Paginação
    page = request.args.get('page', 1, type=int)
    busca = sa.select(Post).order_by(Post.tempo.desc())
    posts = db.paginate(busca, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)
    
    proxima_url = url_for('main.explorar', page=posts.next_num) \
        if posts.has_next else None
    anterior_url = url_for('main.explorar', page=posts.prev_num) \
        if posts.has_prev else None
    
    return render_template('index.html', titulo='Explorar', posts=posts, anterior_url=anterior_url, proxima_url=proxima_url)

        
@bp.route('/cause_500')
def cause_error():
    1 / 0  # Isso causará um erro 500 de divisão por zero


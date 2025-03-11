from flask import render_template, request
from app import db
from app.errors import bp
from app.api.errors import resposta_erro as resposta_erro_api

def wants_json_response():
    return request.accept_mimetypes['aplication/json'] >= request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return resposta_erro_api(404)
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return resposta_erro_api(500)
    return render_template('errors/500.html'), 500


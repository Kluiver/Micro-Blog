from werkzeug.http import HTTP_STATUS_CODES
from app.api import bp
from werkzeug.exceptions import HTTPException

def resposta_erro(status_code, mensagem=None):
    payload = {'erro': HTTP_STATUS_CODES.get(status_code, 'unknown error')}
    if mensagem:
        payload['message'] = mensagem
    return payload, status_code


def bad_request():
    return resposta_erro(400, mensagem)

@bp.errorhandler(HTTPException)
def handle_exception(e):
    return error_response(e.code)
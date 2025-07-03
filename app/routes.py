from flask import Blueprint

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return 'Hello, World!111111'


@bp.route('/testaaa')
def test():
    return 'testaaa'
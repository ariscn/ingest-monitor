import logging
log = logging.getLogger(__name__)

from flask import Blueprint, render_template
#from peewee import fn

#from ..models import Channel


blueprint = Blueprint('dashboard', __name__, template_folder='templates', static_folder='../static')


@blueprint.route('/')
def home():
    log.warn('asdf')
    print('asdfasdfasdfasf')
    return render_template('layout.html')

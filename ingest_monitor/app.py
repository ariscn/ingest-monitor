import logging
from logging import StreamHandler

from flask import Flask, render_template

from .assets import assets
from .extensions import DB, debug_toolbar
from .settings import settings

from . import dashboard


def _render_error(error):
    error_code = getattr(error, 'code', 500)
    return render_template("{0}.html".format(error_code)), error_code


def create_app(config_name='prod'):
    app = Flask(__name__)
    app.config.from_object(settings[config_name])

    assets.init_app(app)
    DB.init_app(app)
    debug_toolbar.init_app(app)

    app.register_blueprint(dashboard.views.blueprint)

    for errcode in (401, 404, 500):
        app.errorhandler(errcode)(_render_error)

    console = StreamHandler()
    console.setLevel(logging.WARNING)
    console.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    app.logger.addHandler(console)

    return app

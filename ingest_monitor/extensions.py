from playhouse.flask_utils import FlaskDB
DB = FlaskDB()

from flask_debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()

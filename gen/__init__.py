from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

gen_app = Flask(__name__)
gen_app.config.from_object('config')
login_manager = LoginManager()
login_manager.init_app(gen_app)
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to view this page"
login_manager.login_message_category = "info"


db = SQLAlchemy(gen_app)


from gen import views, models

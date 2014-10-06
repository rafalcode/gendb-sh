from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

gen_app = Flask(__name__)
gen_app.config.from_object('config')
db = SQLAlchemy(gen_app)


from gen import views, models

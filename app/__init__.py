from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from elasticsearch import Elasticsearch
from flask_bootstrap import Bootstrap
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
#app.config now contains a dictionary with the config values, ex app.config['SECRET_KEY']

db = SQLAlchemy(app) #database
migrate = Migrate(app, db) #migration engine

login = LoginManager(app)
login.login_view = 'login'

moment = Moment(app)

bootstrap = Bootstrap(app)

app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None

from app import routes, models
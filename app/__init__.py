import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Flask,session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
db = SQLAlchemy()
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
basedir = os.path.join(basedir, 'app.db')
basedir = basedir.replace('\\','/')
basedir = basedir.replace('/app/','/')
basedir = 'sqlite:///' + basedir
app.config['SQLALCHEMY_DATABASE_URI'] = basedir
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session_files'  # cartella dove salvare i file di sessione
app.config['SESSION_PERMANENT'] = False  # oppure True, se vuoi sessioni persistenti
#app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
# Inizializza Flask-Session
Session(app)
#print(basedir)
db.init_app(app)
migrate = Migrate(app, db)

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/Server.log', maxBytes=1000000,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Server startup')

from app import routes,models



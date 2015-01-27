import os
import pbclient

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

import logging
from logging import FileHandler, Formatter

def create_app():
    app = Flask(__name__)
    __configure_app(app)
    __setup_logging(app)
    __setup_pbclient(app)
    return app

def __configure_app(app):
    # parent directory
    here = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(here), 'settings_local.py')
    if os.path.exists(config_path):
        app.config.from_pyfile(config_path)

    app.config['PYBOSSA_URL'] = "http%s://%s%s" % (
        's' if app.config['SSL_ACTIVATED'] else '',
        app.config['PYBOSSA_HOST'],
        app.config['PYBOSSA_ENDPOINT'])

    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://%s:%s@%s/%s" % (
        app.config['DB_USER'], app.config['DB_USER_PASSWD'],
        app.config['DB_HOST'], app.config['DB_NAME'])

    app.config['BROKER_URL'] = "amqp://%s:%s@%s:%d/%s" % (
        app.config['RABBIT_USER'],
        app.config['RABBIT_PASSWD'],
        app.config['RABBIT_HOST'],
        app.config['RABBIT_PORT'],
        app.config['RABBIT_VHOST'])

    app.config['CV_MODULES'] = os.path.join(
            os.path.dirname(here), 'cv-modules')
    
def __setup_pbclient(app):
    pbclient.set('endpoint', app.config['PYBOSSA_URL'])
    pbclient.set('api_key', app.config['API_KEY'])

def __setup_logging(app):
    log_file_path = ""
    log_dir_path = ""
    log_level = app.config.get('LOG_LEVEL', logging.INFO)
    
    if os.path.isabs(app.config['LOG_DIR']):
        log_dir_path = app.config['LOG_DIR']
        log_file_path = log_dir_path + app.config['LOG_FILE']
        
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        log_dir_path = os.path.join(
            os.path.dirname(here), app.config['LOG_DIR'])
        log_file_path = log_dir_path + app.config['LOG_FILE']
    
    if not os.path.isdir(log_dir_path):
        os.makedirs(log_dir_path, mode=app.config['LOG_FILE_MODE'])    
    
    if not os.path.isfile(log_file_path):
        open(log_file_path, 'a').close()
    
    log_file_handler = FileHandler(filename=log_file_path, encoding='utf-8')
    log_file_handler.setLevel(log_level)
    log_file_handler.setFormatter(Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s %(module)s:%(funcName)s:%(lineno)d'
    ))
    
    app.logger.addHandler(log_file_handler)
    app.logger.setLevel(log_level)
    
app = create_app()
logger = app.logger
logger.warn("------ STARTING MEB APP --------");

db = SQLAlchemy(app)

""" 
    Used to make migrations of database MBDB
"""
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('mbdb', MigrateCommand)

pbclient = pbclient

if __name__ == '__main__':
    manager.run()

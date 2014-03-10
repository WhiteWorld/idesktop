from flask import Flask, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.security import Security, SQLAlchemyUserDatastore
#from flask.ext.rq import RQ, get_worker, Worker, Connection
from redis import Redis
from rq import Queue, Connection, Worker
from rq_dashboard import RQDashboard


from config import HOST, PORT, DEBUG
from config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
#from helpers.my_celery import make_celery

app = Flask(__name__)
app.config.from_object('config')

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
low_q = Queue('low', connection=redis)

RQDashboard(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('runserver', Server(host=HOST, port=PORT, use_debugger=DEBUG, use_reloader=False))
manager.add_command('db', MigrateCommand)

from app.models import User, Role
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

from app import views

if __name__ == '__main__':
    manager.run()
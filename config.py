# -*- coding: utf8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))

APP_KEY = "vdisk key"
APP_SECRET = "APP_SECRET"

SECRET_KEY = 'you-will-never-guess'

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
#SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
SQLALCHEMY_DATABASE_URI = 'mysql://'
#SQLALCHEMY_DATABASE_URI = 'mysql://root:new-password@localhost/db'


# SECURITY_REGISTERABLE
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False

SECURITY_PASSWORD_HASH = 'bcrypt'
SECURITY_PASSWORD_SALT = 'salt'

#SECURITY_CONFIRMABLE = False
SECURITY_POST_REGISTER_VIEW = '/login'
SECURITY_POST_CONFIRM_VIEW = '/login'
SECURITY_RECOVERABLE = True

SECURITY_LOGIN_USER_TEMPLATE = 'security/login_user.html'
SECURITY_REGISTER_USER_TEMPLATE = 'security/register_user.html'
#SECURITY_REGISTER_USER_TEMPLATE = 'account/register_user.html'

ALLOWED_TYPE = set(['image/png', 'image/jpeg'])


# host 
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True

# UPYUN
# ------------------ CONFIG ---------------------
BUCKETNAME = 'idesktop'
USERNAME = ''
PASSWORD = ''
# -----------------------------------------------

SENTRY_DSN = ''


ONLINE_LAST_MINUTES = 1

#for rq rq-dashboard
REDIS_HOST='10.4.7.20'
REDIS_PORT=5070
REDIS_PASSWORD='redis password'
#flask-rq
RQ_DEFAULT_HOST='10.4.7.20'
RQ_DEFAULT_PORT=5070
RQ_DEFAULT_PASSWORD='redis password'

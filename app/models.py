# -*- coding: utf8 -*-
from flask.ext.security import UserMixin, RoleMixin

from app import db
from datetime import datetime

# Define models
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80))
    description = db.Column(db.String(255))

    def __repr__(self):
        return '<Role %r>' % self.name

follows = db.Table('follows',
                   db.Column('follows_id', db.Integer, db.ForeignKey('user.id')),
                   db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    user_name = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    uploads = db.relationship('Picture', backref='user', lazy='dynamic')

    followed = db.relationship('User', secondary=follows,
                               primaryjoin=(follows.c.follows_id == id),
                               secondaryjoin = (follows.c.followed_id == id),
                               backref = db.backref('follows', lazy='dynamic'),
                               lazy = 'dynamic')

    vdisk_token = db.Column(db.String(32))
    vdisk_refresh_token = db.Column(db.String(32))
    vdisk_expires = db.Column(db.DateTime())
    vdisk_connected = db.Column(db.Boolean())
    vdisk_hash = db.Column(db.String(32))
    vdisk_uid = db.Column(db.String(64))
    profile_image_url = db.Column(db.String(255))
    avatar_large = db.Column(db.String(255))

    def __repr__(self):
        return '<User %r>' % self.user_name


users = db.Table('users',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('picture_id', db.Integer, db.ForeignKey('picture.id')))

liked = db.Table('liked',
                 db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                 db.Column('picture_id', db.Integer, db.ForeignKey('picture.id')))



class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    users = db.relationship('User', secondary=users,
                            backref=db.backref('downloads', lazy='dynamic'),
                            lazy='dynamic')
    liked = db.relationship('User', secondary=liked,
                            backref=db.backref('likes', lazy='dynamic'),
                            lazy='dynamic')

    hash_id = db.Column(db.String(32))
    in_yun = db.Column(db.Boolean(), default=False)
    yun_filename = db.Column(db.String(255))
    added_at = db.Column(db.DateTime(), default=datetime.now())

    def __init__(self, filename, hash_id):
        self.filename = filename
        self.hash_id = hash_id
        self.yun_filename = hash_id+'.'+filename.split('.')[-1]

    def is_used(self, user):
        return self.users.filter(users.c.user_id == user.id).count() > 0

    def add_user(self, user):
        if not self.is_used(user):
            self.users.append(user)
            return self

    def remove_user(self, user):
        if self.is_used(user):
            self.users.remove(user)
            return self

    def __repr__(self):
        return '<Picture %r>' % self.filename





# -*- coding: utf8 -*-
from flask import url_for, render_template, redirect, request, g, jsonify, flash, abort
from flask.ext.security import login_required, current_user
from app import app, db
from config import APP_KEY, APP_SECRET, ONLINE_LAST_MINUTES
from helpers import vdisk
from rq import Queue, Connection, Worker


from models import Picture, User
from app import redis, low_q

import json
import ast
import datetime
import time
import urllib2
import upyun

#NAME = 'http://127.0.0.1:5000/'
NAME = 'http://idesktop.sturgeon.mopaas.com/'
ALLOWED_TYPE = set(['image/png', 'image/jpeg'])
oauth2 = vdisk.OAuth2(APP_KEY, APP_SECRET, NAME+"response/")
client = vdisk.Client(root='basic')
PER_PAGE = 20
up = upyun.UpYun('bucket', 'username', 'password', timeout=30, endpoint=upyun.ED_AUTO)


@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_active():
        mark_online(g.user.id)
    print 'current_user: %s, g.user: %s, leaving bef_req' % (current_user, g.user)# Views


def mark_online(user_id):
    now = int(time.time())
    expires = now + (ONLINE_LAST_MINUTES * 60) + 10
    all_users_key = 'online-users/%d' % (now // 60)
    user_key = 'user-activity/%s' % user_id
    p = redis.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()


def get_user_last_activity(user_id):
    last_active = redis.get('user-activity/%s' % user_id)
    if last_active is None:
        return None
    return datetime.datetime.utcfromtimestamp(int(last_active))


def get_online_users():
    current = int(time.time()) // 60
    minutes = xrange(ONLINE_LAST_MINUTES)
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])


@app.route('/')
@app.route('/page/')
@app.route('/page/<int:page>/')
def index(page=1):
    user = g.user
    if user.is_authenticated():
        if user.vdisk_connected:
            pictures = Picture.query.paginate(page, PER_PAGE, False)
            return render_template('metro/index.html', user=user, pictures=pictures)
        else:
            return render_template('metro/connect.html')
    else:
        return render_template('metro/welcome.html')


@app.route("/authorize/", methods=['GET', 'POST'])
def authorize():
    user = g.user
    if not user.is_authenticated():
        flash('please sign...', 'info')
        return redirect('/')
    else:
        url = oauth2.authorize()
        return redirect(url)


@app.route("/response/", methods=['GET', 'POST'])
@login_required
def response():
    code = request.args.get('code')
    if code == '':
        flash('get code failed!', 'error')
        return redirect(url_for('index'))
    result = ast.literal_eval(oauth2.access_token(code=code))
    print result
    if 'code' in result:
        flash('get token failed!', 'error')
        return redirect(url_for('index'))
    user = g.user
    user.vdisk_token = result['access_token']
    user.vdisk_refresh_token = result['refresh_token']
    user.vdisk_expires = datetime.datetime.fromtimestamp(int(result['expires_in']))
    user.vdisk_connected = True

    resp = client.account_info(g.user.vdisk_token)
    if isinstance(resp, str):
        flash('get account info failed!', 'error')
        return redirect(url_for('index'))
    result = json.loads(resp.read())
    user.user_name = result['user_name']
    user.profile_image_url = result['profile_image_url']
    user.avatar_large = result['avatar_large']
    user.vdisk_uid = result['uid']
    db.session.add(user)
    db.session.commit()

    # create folder in user's disk
    resp = client.fileops_create_folder(g.user.vdisk_token, '/idesktop')
    if isinstance(resp, str):
        flash('folder already exits!', 'info')
    else:
        flash('create /idesktop sucess', 'sucess')
    flash('set success!', 'success')
    return redirect(url_for('index'))


@app.route('/unlink_vdisk/')
@login_required
def unlink_vdisk():
    user = g.user
    user.vdisk_connected = False
    user.vdisk_token = ''
    user.vdisk_uid = ''
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('setting'))


@app.route('/info/')
@login_required
def info():
    resp = client.account_info(g.user.vdisk_token)
    if isinstance(resp, str):
        flash('get account info failed!', 'error')
        return 'get account info failed!'
    result = json.loads(resp.read())
    print result
    user = g.user
    user.user_name = result['user_name']
    user.vdisk_uid = result['uid']
    db.session.add(user)
    db.session.commit()
    return "success"


def is_good(content):
    if content['is_dir']:
        return False
    if content['mime_type'] not in ALLOWED_TYPE:
        return False
    return True


def get_exif(filename):  # filename hash
    rootpath = '/idesktop/'
    resp_dict = json.loads(up.get(rootpath+filename+'!exif'))
    return resp_dict


def down_upload(url, filename):  # down from  vdisk, upload to upyun
    print url+'#'+filename
    rootpath = '/idesktop/'
    f = urllib2.urlopen(url)
    up.put(rootpath + filename, f.read(), checksum=False)


# pull from upyun, upload to vdisk, url: filename
def pull_upload(upyun_filename, vdisk_filename, vdisk_token):
    rootpath = '/idesktop/'
    with open('tmp.file', 'wb') as f:
        up.get(rootpath+upyun_filename, f)
    with open('tmp.file', 'rb') as f:
        client.files_put(vdisk_token, rootpath+vdisk_filename, f.read())


#@sched.interval_schedule(minutes=20)
@app.route('/update_pic_exif/')
def update_pic_exif():
    print "start update_pic_exif..."
    with app.test_request_context():
        pictures = Picture.query.all()
        pics = [p for p in pictures if not p.width]
        for p in pics:
            print p.yun_filename
            exif = get_exif(p.yun_filename)
            p.width = exif['width']
            p.height = exif['height']
            db.session.add(p)
        db.session.commit()
    print "stop update_pic_exif..."
    ret={'result':'ok'}
    return jsonify(**ret)


#@sched.interval_schedule(hours=12)
@app.route('/cron_refresh_token/')
def cron_refresh_token():
    print 'start cron_refresh_token...'
    with app.test_request_context():
        users = User.query.all()
        for user in users:
            result = ast.literal_eval(oauth2.access_token(grant_type='refresh_token', refresh_token=user.vdisk_refresh_token))
            print result
            if 'code' in result:
                continue
            user.vdisk_refresh_token = result['refresh_token']
            user.vdisk_token = result['access_token']
            user.vdisk_expires = datetime.datetime.fromtimestamp(int(result['expires_in']))
            db.session.add(user)
            db.session.commit()
    print 'stop cron_refresh_token...'
    ret={'result':'ok'}
    return jsonify(**ret)

@app.route('/cron_test/')
def cron_test():
    #lock.acquire()
    print 'Print every 10s!'
    #lock.release()
    ret={'result':'ok'}
    return jsonify(**ret)

@app.route('/cron_sync/')
def cron_sync():
    print 'start cron_sync ...'
    with app.test_request_context():
        users = User.query.all()
        for user in users:
            print user
            # make sure not conflict
            if get_user_last_activity(user.id) is not None:
                continue
            resp = client.metadata(user.vdisk_token, '/idesktop')
            if isinstance(resp, str):
                print 'error in metadata'
                continue
            result = json.loads(resp.read())
            if result['hash'] == user.vdisk_hash:
                print 'same hash'
                continue
            user.vdisk_hash = result['hash']
            db.session.add(user)
            db.session.commit()

            contents = [content for content in result['contents'] if is_good(content)]
            for content in contents:
                #print content['md5']
                pic = Picture.query.filter_by(hash_id=content['md5']).first()
                if not pic:  # need to upload
                    #upload to upyun
                    ret = client.media(user.vdisk_token, content['path'])
                    if isinstance(ret, str):
                        continue
                    url = json.loads(ret.read())['url']
                    filename = content['md5']
                    filename += '.' + content['path'].split('.')[-1]
                    low_q.enqueue(down_upload, url, filename)

                    # add to db
                    filename = content['path'].split('/')[-1]
                    picture = Picture(filename, content['md5'])
                    picture.in_yun = True
                    picture.user = user
                    picture.users.append(user)
                    db.session.add(picture)
                    db.session.commit()
                    #print filename + '#' + url
                elif user not in pic.users:
                    pic.users.append(user)
                    db.session.add(pic)
                    db.session.commit()
            #handle self delete in local folder
            hashs = [content['md5'] for content in contents]
            for pic in user.downloads.all():
                if pic.hash_id not in hashs:
                    #need delete
                    pic.users.remove(user)
                    db.session.add(pic)
                    db.session.commit()
    print 'stop cron_sync ...'
    ret = {'result':'ok'}
    return jsonify(**ret)


@app.route('/sync/')
@login_required
def sync():
    resp = client.metadata(g.user.vdisk_token, '/idesktop')
    if isinstance(resp, str):
        flash('get metadata failed!', 'error')
        return redirect(url_for('setting'))
    result = json.loads(resp.read())
    user = g.user
    user.vdisk_hash = result['hash']
    db.session.add(user)
    db.session.commit()
    #handle self add file in local folder
    contents = [content for content in result['contents'] if is_good(content)]
    for content in contents:
        #print content['md5']
        pic = Picture.query.filter_by(hash_id=content['md5']).first()
        if not pic:  # need to upload
            #upload to upyun
            ret = client.media(g.user.vdisk_token, content['path'])
            if isinstance(ret, str):
                continue
            url = json.loads(ret.read())['url']
            filename = content['md5']
            filename += '.' + content['path'].split('.')[-1]
            #get_queue('default').enqueue(down_upload, url, filename)
            low_q.enqueue(down_upload, url, filename)
            #down_upload(url, filename)
            # add to db
            filename = content['path'].split('/')[-1]
            picture = Picture(filename, content['md5'])
            picture.in_yun = True
            picture.user = g.user
            picture.users.append(g.user)
            db.session.add(picture)
            db.session.commit()
            #print filename + '#' + url
        elif g.user not in pic.users:
            pic.users.append(g.user)
            db.session.add(pic)
            db.session.commit()
    #handle self delete in local folder
    hashs = [content['md5'] for content in contents]
    for pic in g.user.downloads.all():
        if pic.hash_id not in hashs:
            #need delete
            pic.users.remove(g.user)
            db.session.add(pic)
            db.session.commit()
    flash('sync completed!', 'success')
    return redirect(url_for('setting'))


@app.route('/mine/')
@login_required
def mine():
    return render_template('metro/mine.html')


@app.route('/mine/upload/', defaults={'page': 1})
@app.route('/mine/upload/<int:page>/')
@login_required
def my_upload(page):
    #pictures = Picture.query.filter_by(owner=g.user).paginate(page, 9, False)
    pictures = g.user.uploads.paginate(page, 9, False)
    print g.user.uploads.all()
    return render_template('metro/upload.html', pictures=pictures)


@app.route('/mine/download/', defaults={'page': 1})
@app.route('/mine/download/<int:page>/')
@login_required
def my_download(page):
    pictures = g.user.downloads.paginate(page, 9, False)
    return render_template('metro/download.html', pictures=pictures)


@app.route('/mine/setting/')
@login_required
def setting():
    return render_template('metro/setting.html')


def picture_yun_to_user(picture, vdisk_token):
    pull_upload(picture.yun_filename, picture.filename, vdisk_token)


def picture_delete(picture, vdisk_token):
    client.fileops_delete(vdisk_token, '/idesktop/'+picture.filename)


@app.route('/download/<int:picture_id>/<int:types>/')
@login_required
def download(picture_id, types):
    picture = Picture.query.filter_by(id=picture_id).first()
    if types == 1:  # add
        low_q.enqueue(picture_yun_to_user, picture, g.user.vdisk_token)
        picture.users.append(g.user)
    elif types == 2:
        low_q.enqueue(picture_delete, picture, g.user.vdisk_token)
        picture.users.remove(g.user)
    db.session.add(picture)
    db.session.commit()
    ret = {'ok': 'add or remove success'}
    return jsonify(**ret)


@app.route('/like/<int:picture_id>/<int:types>/')
@login_required
def like(picture_id, types):
    picture = Picture.query.filter_by(id=picture_id).first()
    if types == 1:  # like
        picture.liked.append(g.user)
    elif types == 2:  # dislike
        picture.liked.remove(g.user)
    db.session.add(picture)
    db.session.commit()
    ret = {'ok': 'add or remove like success'}
    return jsonify(**ret)


@app.route('/follow/<int:user_id>/<int:types>/')
@login_required
def follow(user_id, types):
    user = User.query.filter_by(id=user_id).first()
    me = g.user
    if types == 1:  # follow
        me.follows.append(user)
    elif types == 2:  # unfillow
        me.follows.remove(user)
    db.session.add(me)
    db.session.commit()
    ret = {'ok': 'add or remove follow success'}
    return jsonify(**ret)


@app.route('/<vdisk_uid>/', defaults={'page': 1})
@app.route('/<vdisk_uid>/<int:page>')
@login_required
def user_page(vdisk_uid, page):
    user = User.query.filter_by(vdisk_uid=vdisk_uid).first()
    if user is None:
        flash('no such user!', 'error')
        abort(404)
    pictures = user.downloads.paginate(page, 9, False)
    return render_template('metro/user_page.html', pictures=pictures, user=user)


@app.route('/<vdisk_uid>/upload/', defaults={'page': 1})
@app.route('/<vdisk_uid>/upload/<int:page>')
@login_required
def user_upload_page(vdisk_uid, page):
    user = User.query.filter_by(vdisk_uid=vdisk_uid).first()
    if user is None:
        flash('no such user!', 'error')
        abort(404)
    pictures = user.uploads.paginate(page, 9, False)
    return render_template('metro/user_upload_page.html', pictures=pictures, user=user)


@app.route('/<vdisk_uid>/following/', defaults={'page': 1})
@app.route('/<vdisk_uid>/following/<int:page>')
@login_required
def user_following_page(vdisk_uid, page):
    user = User.query.filter_by(vdisk_uid=vdisk_uid).first()
    if user is None:
        flash('no such user!', 'error')
        abort(404)
    following = user.follows.paginate(page, 12, False)
    return render_template('metro/user_following_page.html', following=following, user=user)

@app.route('/<vdisk_uid>/followers/', defaults={'page': 1})
@app.route('/<vdisk_uid>/followers/<int:page>')
@login_required
def user_follower_page(vdisk_uid, page):
    user = User.query.filter_by(vdisk_uid=vdisk_uid).first()
    if user is None:
        flash('no such user!', 'error')
        abort(404)
    followers = user.followed.paginate(page, 12, False)
    return render_template('metro/user_follower_page.html', followers=followers, user=user)


@app.route('/faq/')
def faq():
    return render_template('metro/faq.html')

def testrq(a, b):
    return a+b

@app.route('/test/')
@login_required
def test():
    low_q.enqueue(testrq,1,2)
    return jsonify(**{'a':'b'})


@app.route('/worker/')
def worker():
    with Connection(redis):
        Worker(low_q).work(True)
    return jsonify(**{'worker':'worker'})

@app.route('/delete_pic/<int:picture_id>/')
@login_required
def delete_pic(picture_id):
    if g.user.email != 'ljq258@gmail.com':
        return jsonify(**{'result':'not me!'})
    delete_picture(picture_id)
    return jsonify(**{'result':'Delete OK!'})

def delete_picture(picture_id):
    users = User.query.all()
    picture = Picture.query.filter_by(id=picture_id).first()
    for user in users:
        if picture in user.uploads:
            user.uploads.remove(picture)
        if picture in user.downloads:
            user.downloads.remove(picture)
        if picture in user.likes:
            user.likes.remove(picture)
    db.session.delete(picture)
    db.session.commit()

@app.route('/delete_user/<int:user_id>/')
@login_required
def delete_user(user_id):
    if g.user.email != 'ljq258@gmail.com':
        return jsonify(**{'result':'not me!'})
    user = User.query.filter_by(id=user_id).first()
    for pic in user.uploads:
        delete_pic(pic.id)
    for pic in user.downloads:
        user.downloads.remove(pic.id)
    for pic in user.likes:
        user.likes.remove(pic.id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(**{'result':'Delete user OK!'})
from flask import Flask, request, jsonify, abort
from pymongo import MongoClient
from bson import ObjectId
from os import getenv
import json
import sys
from flask_cors import CORS, cross_origin
import smtplib, ssl
from email.message import EmailMessage
from numpy.random import randint, seed
import time
import datetime

seed(int(time.time()))

client = MongoClient(host=getenv('DB_HOST', 'localhost'), port=27017)
db = client.notesdb

app = Flask(__name__)

COOKIE_DOMAIN = getenv('COOKIE_DOMAIN', '127.0.0.1:5000')
# CORS_ORIGIN = getenv('CORS_ORIGIN', 'http://127.1.0.1:8888/')
#
# CORS(app, origins=CORS_ORIGIN, supports_credentials=True, allow_headers=['Content-Type', 'Cookie'])
# app.config['CORS_HEADERS'] = 'Content-Type, Cookie'

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@app.route('/point/create')
@cross_origin()
def create_point():
    if '_id' not in request.cookies:
        print('ERR: no _id cookie in create_point', file=sys.stderr)
        return abort(403)

    x = request.args.get('x', '0')
    y = request.args.get('y', '0')
    if x == 0 or y == 0:
        print('ERR: zero x or y point', file=sys.stderr)
        return abort(400)

    note = {
        'x': int(x),
        'y': int(y),
        'text': request.args.get('text', 'null'),
        'user_id': ObjectId(request.cookies['_id']),
    }
    result = db.points.insert_one(note)
    note['_id'] = str(result.inserted_id)
    note['user_id'] = str(note['user_id'])
    return jsonify(note)

@app.route('/point')
@cross_origin()
def get_points():
    if '_id' not in request.cookies:
        print('ERR: no _id cookie in get_points', file=sys.stderr)
        return jsonify([])

    user_id_filter = {
        'user_id': ObjectId(request.cookies['_id']),
    }

    limit = int(request.args.get('limit', '100'))
    offset = int(request.args.get('offset', '0'))
    total = db.points.count(user_id_filter)

    points = list({
        'x': p['x'],
        'y': p['y'],
        'text': p['text'],
        '_id': str(p.get('_id')),
    } for p in db.points.find(user_id_filter).limit(limit).skip(offset))

    return jsonify({
        'points': points,
        'more': offset + len(points) < total,
        'result': True,
    })

@app.route('/point/delete')
@cross_origin()
def delete_point():
    if '_id' not in request.cookies:
        print('ERR: no _id cookie in get_points', file=sys.stderr)
        return jsonify([])

    filters = {
        'user_id': ObjectId(request.cookies['_id']),
        '_id': ObjectId(request.args.get('id', '0')),
    }

    d = db.points.delete_one(filters)

    return jsonify({
        'result': d.deleted_count > 0
    })

@app.route('/auth_check')
@cross_origin()
def auth_check():
    print('INFO: auth_check', file=sys.stderr)
    res = {"result": False}
    if  '_auth' in request.cookies and '_email' in request.cookies and '_id' in request.cookies:
        res["result"] = True

    return jsonify(res)

@app.route('/auth_start')
@cross_origin()
def auth_start():
    print('INFO: auth_start', file=sys.stderr)

    res = {"result": False}
    email = request.args.get('email', '')

    email = email.lower().strip()
    if not email or not '@' in email:
        print('ERR: invalid email', email, '.', file=sys.stderr)
        return jsonify(res)

    user = db.users.find_one({'email': email})
    code = str(randint(1000, 9999))

    if user:
        print('Update user _id %s with code %s' % (user['_id'], code), file=sys.stderr)
        result = db.users.update({'_id': user['_id']}, {'$set': {'code': code}}, upsert=False)
        print(result, file=sys.stderr)
    else:
        user = {"email": email, "code": code}
        result = db.users.insert_one(user)
        user["_id"] = result.inserted_id

    print('Sending email to', email, file=sys.stderr)
    send_email(email, "Your auth code: %s" % code)

    res['result'] = True

    resp = jsonify(res)
    set_cookie(resp, '_email', user['email'], domain=COOKIE_DOMAIN)
    set_cookie(resp, '_id', str(user['_id']), domain=COOKIE_DOMAIN)
    return resp

@app.route('/auth_finish')
@cross_origin()
def auth_finish():
    print('INFO: auth_finish', file=sys.stderr)

    res = {"result": False}
    code = request.args.get('code', '')

    if not '_email' in request.cookies:
        print('ERR: no cookie _email set', file=sys.stderr)

    if not code:
        print('ERR: code is empty', file=sys.stderr)

    code = code.lower().strip()
    if not code:
        print('ERR: NO code', file=sys.stderr)
        return jsonify(res)

    email = request.cookies.get('_email', 'err')
    user = db.users.find_one({'email': email})
    if not user:
        print('ERR: auth: user not found with email: %s' % email, file=sys.stderr)
        return jsonify(res)

    if user['code'] != code:
        print('ERR: code mistmatch: expected %s, not %s' % (user['code'], code), file=sys.stderr)
        return jsonify(res)

    print('AUTH SUCCESS for ID %s email %s code %s' % (str(user['_id']), email, code), file=sys.stderr)

    res['result'] = True
    resp = jsonify(res)
    set_cookie(resp, '_auth', 'ok', domain=COOKIE_DOMAIN)
    return resp

def set_cookie(resp, *args, **kwargs):
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=7)
    resp.set_cookie(*args, **kwargs, expires=expire_date)

def send_email(email, text):
    try:
        gmail_user = getenv('GMAIL_USER', '')
        gmail_password = getenv('GMAIL_PASSWORD', '')

        if not gmail_user or not gmail_password:
            raise Exception("no GMAIL_USER or GMAUL_PASSWORD from getenv")

        msg = EmailMessage()
        msg.set_content(text)
        msg["Subject"] = "Auth code"
        msg["From"] = gmail_user
        msg["To"] = email

        context=ssl.create_default_context()

        with smtplib.SMTP("smtp.gmail.com", port=587) as smtp:
            smtp.starttls(context=context)
            smtp.login(gmail_user, gmail_password)
            smtp.send_message(msg)

        print('Email sent to', email, text, file=sys.stderr)

    except BaseException as e:
        print("an error has occurred in send_email: %s" % e, file=sys.stderr)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=int(getenv('PORT', 5000)))

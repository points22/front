from flask import Flask, request, make_response
from pymongo import MongoClient
from os import getenv
import json
import sys
from flask_cors import CORS, cross_origin
import smtplib, ssl
from email.message import EmailMessage
from numpy.random import randint, seed
from datetime import datetime

seed(int(datetime.now().timestamp()))

client = MongoClient(host=getenv('DB_HOST', 'localhost'), port=27017)
db = client.notesdb

app = Flask(__name__)

API_DOMAIN = getenv('API_DOMAIN', None)
CORS_ORIGIN = getenv('CORS_ORIGIN', '*')

cors = CORS(app, origins=CORS_ORIGIN, supports_credentials=True)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/point/create')
@cross_origin()
def create_point():
    note = {
        'x': int(request.args.get('x', '0')),
        'y': int(request.args.get('y', '0')),
        'text': request.args.get('text', 'null'),
    }
    result = db.points.insert_one(note)
    note['_id'] = str(result.inserted_id)
    return json.dumps(note)

@app.route('/point')
@cross_origin()
def get_points():
    res = list({
        'x': p['x'],
        'y': p['y'],
        'text': p['text'],
        '_id': str(p.get('_id')),
    } for p in db.points.find())
    return json.dumps(res)

@app.route('/auth_check')
@cross_origin()
def auth_check():
    print('INFO: auth_check', file=sys.stderr)
    res = {"result": False}
    if  '_auth' in request.cookies and '_email' in request.cookies and '_id' in request.cookies:
        res["result"] = True
    return json.dumps(res)

@app.route('/auth_start')
@cross_origin()
def auth_start():
    print('INFO: auth_start', file=sys.stderr)

    res = {"result": False}
    email = request.args.get('email', '')

    email = email.lower().strip()
    if not email or not '@' in email:
        print('ERR: invalid email', email, '.', file=sys.stderr)
        return json.dumps(res)

    user = db.users.find_one({'email': email})

    if not user:
        user = {"email": email, "code": str(randint(111, 999))}
        result = db.users.insert_one(user)
        user["_id"] = result.inserted_id
    elif not user['code']:
        user['code'] = str(randint(111, 999))
        db.ProductData.update_one({
          '_id': user['_id']
        },{
          '$set': {
            'code': user['code']
          }
        }, upsert=False)

    print('Sending email to', email, file=sys.stderr)
    send_email(email, "Your auth code: %s" % user['code'])

    res['result'] = True
    resp = make_response(json.dumps(res))
    resp.set_cookie('_email', user['email'], domain=API_DOMAIN)
    resp.set_cookie('_id', str(user['_id']), domain=API_DOMAIN)

    return resp

@app.route('/auth_finish')
@cross_origin()
def auth_finish():
    print('INFO: auth_finish', file=sys.stderr)

    res = {"result": False}
    code = request.args.get('code', '')

    if not '_email' in request.cookies:
        print('ERR: no cookie _email set', file=sys.stderr)

    code = code.lower().strip()
    if not code:
        print('ERR: NO code', file=sys.stderr)
        return json.dumps(res)

    email = request.cookies.get('_email', 'err')
    code = request.args.get('code', 'err')
    user = db.users.find_one({'email': email, 'code': code})
    if not user:
        print('ERR: auth: user not found with email/code: %s/%s' % (email, code), file=sys.stderr)
        return json.dumps(res)

    res['result'] = True
    resp = make_response(json.dumps(res))
    resp.set_cookie('_auth', 'ok', domain=API_DOMAIN)
    return resp

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

        print('Email sent to', email, file=sys.stderr)

    except BaseException as e:
        print("an error has occurred in send_email: %s" % e, file=sys.stderr)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=int(getenv('PORT', 5000)))

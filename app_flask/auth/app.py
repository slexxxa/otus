import random

from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3
import json as jsons

global dbname, user, password, host, port, data, token

envdbname = os.environ.get("PGDBNAME", "auth")
envuser = os.environ.get("PGUSER", "postgres")
envpassword = os.environ.get("PGPASSWORD", "12345678")
envhost = os.environ.get("PGHOST", "10.169.44.141")
envport = os.environ.get("PGPORT", "5432")
envbilling = os.environ.get("billing_url", "127.0.0.1:8001")


def get_profile(username):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute("""
                        SELECT password, email, phone from users WHERE username = %s;""", (username,)
                )
    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    if row is None:
        return 199
    else:
        return row


def psql(method, uid=0, username=0, password=0, firstname=0, lastname=0, email=0, phone=0):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    # conn.autocommit = True
    if method == "GET":
        cur.execute("""
                SELECT username, firstname, lastname, email, phone FROM users WHERE username = %s;""", (username,)
                    )
        row = cur.fetchone()
        output = json.jsonify(
            id=uid,
            username=row[0],
            firstName=row[1],
            lastName=row[2],
            email=row[3],
            phone=row[4]
        )

    if method == "DELETE":
        cur.execute("""
                DELETE FROM users WHERE username = %s;""", (username,)
                    )
        output = ''

    if method == "PUT":
        cur.execute("""
                UPDATE users SET 
                firstname = %s, 
                lastname = %s,
                email = %s,
                phone = %s
                WHERE username = %s;""", (firstname, lastname, email, phone, username)
                    )
        output = ''

    if method == "POST":
        cur.execute("""
            INSERT INTO users (username, password, firstname, lastname, email, phone) 
            VALUES (%s, %s, %s, %s, %s, %s);""", (username, password, firstname, lastname, email, phone)
                    )
        output = ''
    conn.commit()

    cur.close()
    conn.close()

    return output


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jndsifhvusdkhbfjdsfbgljdbgfvljdsgvjld' #'''.join(random.choices(string.ascii_letters, k=20))

PrometheusMetrics(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        global token
        token = request.args.get('token')

        if not token:
            return Response('token is missing', 403)
        global data
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return Response('token is invalid', 403)

        return f(*args, **kwargs)
    return decorated


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/api/v1/user', methods=['GET'])
@token_required
def get_user():
    global data
    return psql("GET", 0, data['user'])


@app.route('/api/v1/user/<username_from_arg>', methods=['DELETE'])
@token_required
def delete_user(username_from_arg):
    global data
    if data['user'] == 'admin':
      return psql("DELETE", 0, username_from_arg), 204
    else:
        return Response('token is invalid', 403)

@app.route('/api/v1/user', methods=['PUT'])
@token_required
def update_user():
    global data
    request_data = request.get_json()
    firstname = request_data['firstName']
    lastname = request_data['lastName']
    email = request_data['email']
    phone = request_data['phone']
    return psql("PUT", 0, data['user'], 0, firstname, lastname, email, phone)



@app.route('/api/v1/user', methods=['POST'])
@token_required
def post_user():
    global data
    global token
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']
    firstname = request_data['firstName']
    lastname = request_data['lastName']
    email = request_data['email']
    phone = request_data['phone']
    if data['user'] == 'admin':
        psql("POST", 0, username, password, firstname, lastname, email, phone)
        payload = jsons.dumps({'username': username})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envbilling + "/api/v1/user"
        r = requests.post(connstring, data=payload, params=param, headers=json_headers)
        print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        return Response(username, 201)
    else:
        return Response('token is invalid', 403)


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/login')
def login():
    auth = request.authorization
    if not auth:
        return Response('you need be authorised', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    username_from_auth = auth.username
    profile_from_db = get_profile(username_from_auth)
    if profile_from_db == 199:
        return Response('you are not authorised', 401)
    password_from_auth = auth.password.rstrip()
    if profile_from_db[0] == password_from_auth:
        token = jwt.encode(
            {'user': username_from_auth,'email': profile_from_db[1], 'phone': profile_from_db[2], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=50)},
            app.config['SECRET_KEY'], algorithm='HS256')
        return json.jsonify({'token': token})
    else:
        return Response('you are not authorised', 401)


app.run(debug=False, host='0.0.0.0', port=8000)


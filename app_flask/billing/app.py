from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3

global dbname, user, password, host, port, data

envdbname = os.environ.get("PGDBNAME", "billing")
envuser = os.environ.get("PGUSER", "postgres")
envpassword = os.environ.get("PGPASSWORD", "12345678")
envhost = os.environ.get("PGHOST", "10.169.44.141")
envport = os.environ.get("PGPORT", "5432")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
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


def user_create(username):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    money = 0
    cur.execute("""
                        INSERT INTO billing (username, money) VALUES (%s, %s);""", (username, money)
                )
    conn.commit()

    cur.close()
    conn.close()
    return 0


def money_get(username):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute("""
                        SELECT money FROM billing WHERE username = %s;""", (username, )
                )
    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    return row[0]


def money_add(username, money):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute("""
                        UPDATE billing SET money = money + %s WHERE username = %s;""", (money, username)
                )
    conn.commit()

    cur.close()
    conn.close()
    return 0


def money_delete(username, money):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    try:
        cur.execute("""
                            UPDATE billing SET money = money - %s WHERE username = %s;""", (money, username)
                    )
        conn.commit()
        cur.close()
        conn.close()
        return 0
    except Exception as err:
        if err.pgcode == "23514":
            cur.close()
            conn.close()
            return 199
        exit(1)





app = Flask(__name__)
app.config['SECRET_KEY'] = 'jndsifhvusdkhbfjdsfbgljdbgfvljdsgvjld' #'''.join(random.choices(string.ascii_letters, k=20))


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/api/v1/user', methods=['POST'])
@token_required
def post_user():
    global data
    request_data = request.get_json()
    username = request_data['username']
    if data['user'] == 'admin':
        user_create(username)
        return Response('user created', 201)
    else:
        return Response('token is invalid', 403)


@app.route('/api/v1/money', methods=['GET'])
@token_required
def get_money():
    global data
    request_data = request.get_json()
    username = request_data['username']
    if data['user'] == 'admin':
        money = money_get(request_data['username'])
        return Response(str(money), 200)
    else:
        return Response('token is invalid', 403)


@app.route('/api/v1/money', methods=['PUT'])
@token_required
def put_money():
    global data
    request_data = request.get_json()
    username = request_data['username']
    if data['user'] == 'admin':
        money_add(request_data['username'], request_data['money'])
        return Response('money added', 200)
    else:
        return Response('token is invalid', 403)


@app.route('/api/v1/money', methods=['DELETE'])
@token_required
def delete_money():
    global data
    request_data = request.get_json()
    username = request_data['username']
    if data['user'] == 'admin':
        c = money_delete(request_data['username'], request_data['money'])
        if c == 199:
            return Response('you not have money', 210)
        return Response('money deleted', 200)
    else:
        return Response('token is invalid', 403)


app.run(debug=False, host='0.0.0.0', port=8000)

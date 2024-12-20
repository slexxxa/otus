from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3

global dbname, user, password, host, port, data

envdbname = os.environ.get("PGDBNAME", "notify")
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


def get_notify_from_db(email):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute("""
                        SELECT message FROM email WHERE email = %s ORDER BY id DESC LIMIT 1;""", (email, )
                )
    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    return row[0]


def create_notify(email, message):
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
                        INSERT INTO email (email, message) VALUES (%s, %s);""", (email, message)
                )
    conn.commit()

    cur.close()
    conn.close()
    return 0


app = Flask(__name__)
app.config['SECRET_KEY'] = 'jndsifhvusdkhbfjdsfbgljdbgfvljdsgvjld' #'''.join(random.choices(string.ascii_letters, k=20))


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/api/v1/notify', methods=['POST'])
@token_required
def post_notify():
    global data
    request_data = request.get_json()
    message = request_data['message']
    email = request_data['email']
    if data['user'] == 'admin':
        create_notify(email, message)
        return Response('message sended', 201)
    else:
        return Response('token is invalid', 403)



@app.route('/api/v1/notify', methods=['GET'])
@token_required
def get_notify():
    global data
    request_data = request.get_json()
    email = request_data['email']
    if data['user'] == 'admin':
        out = get_notify_from_db(email)
        return Response(str(out), 200)
    else:
        return Response('token is invalid', 403)


app.run(debug=False, host='0.0.0.0', port=8000)

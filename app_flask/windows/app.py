from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3
import json as jsons

global dbname, user, password, host, port, data

envdbname = os.environ.get("PGDBNAME", "windows")
envuser = os.environ.get("PGUSER", "postgres")
envpassword = os.environ.get("PGPASSWORD", "12345678")
envhost = os.environ.get("PGHOST", "10.169.44.141")
envport = os.environ.get("PGPORT", "5432")
envbilling = os.environ.get("billing_url", "127.0.0.1:8001")
envnotify = os.environ.get("notify_url", "127.0.0.1:8003")


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJleHAiOjQ3MzQ0NDg4NjV9.VGqNY8WXYsgLutlgvjG8C5tdktfPw5WrNB17QsvBGmc"

def get_prise(window_name):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute("""
                        SELECT cost from windows WHERE th = %s;""", (window_name,)
                )
    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    if row is None:
        return 199
    else:
        return row[0]




class order:
    money_write_off = False
    def __init__(self, window, user):
        self.window = window
        self.user = user





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



app = Flask(__name__)
app.config['SECRET_KEY'] = 'jndsifhvusdkhbfjdsfbgljdbgfvljdsgvjld' #'''.join(random.choices(string.ascii_letters, k=20))


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/api/v1/order', methods=['POST'])
@token_required
def post_order():
    global data
    request_data = request.get_json()
    order_t = order(request_data['window'], data['user'])
    window_prise = get_prise(order_t.window)

    payload = jsons.dumps({'username': data['user'], 'money': window_prise})
    param = {'token': token}
    json_headers = {"Content-type": "application/json"}
    connstring = "http://" + envbilling + "/api/v1/money"
    r = requests.delete(connstring, data=payload, params=param, headers=json_headers)
    print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
    if r.status_code == 210:
        try:
            message = "order is not created, you have not money :" + order_t.window + ", cost: " + str(window_prise)
            payload = jsons.dumps({'username': data['user'], 'email': data['email'], 'phone': data['phone'], 'message': message})
            param = {'token': token}
            json_headers = {"Content-type": "application/json"}
            connstring = "http://" + envnotify + "/api/v1/notify"
            r2 = requests.post(connstring, data=payload, params=param, headers=json_headers)
            print(f"urlr2: {r2.url} \n\ntextr2: \n {r2.text}\n\ncoder2:{r2.status_code}")
        except:
            print("An exception occurred")
        return Response('you have no money', 210)
    elif r.status_code == 200:
        try:
            message = "order have been created :" + order_t.window + ", cost: " + str(window_prise)
            payload = jsons.dumps({'username': data['user'], 'email': data['email'], 'phone': data['phone'], 'message': message})
            param = {'token': token}
            json_headers = {"Content-type": "application/json"}
            connstring = "http://" + envnotify + "/api/v1/notify"
            r2 = requests.post(connstring, data=payload, params=param, headers=json_headers)
            print(f"urlr2: {r2.url} \n\ntextr2: \n {r2.text}\n\ncoder2:{r2.status_code}")
        except:
            print("An exception occurred")
        return Response('your order is created', 201)
    else:
        return Response('some problem', 590)


app.run(debug=False, host='0.0.0.0', port=8000)

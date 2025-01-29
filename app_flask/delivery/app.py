from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3

global dbname, user, password, host, port, data

envdbname = os.environ.get("PGDBNAME", "delivery")
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


def do_request_to_DB_nr(request):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    try:
        cur.execute(request)

        conn.commit()
        cur.close()
        conn.close()
        return 0
    except Exception as err:
        if err.pgcode == "23505":
            cur.close()
            conn.close()
            return 199
        elif err.pgcode == "23514":
            cur.close()
            conn.close()
            return 197
        else:
            return 198
    return


def do_request_to_DB_r(request):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute(request)
    row = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return row



app = Flask(__name__)
app.config['SECRET_KEY'] = 'jndsifhvusdkhbfjdsfbgljdbgfvljdsgvjld' #'''.join(random.choices(string.ascii_letters, k=20))


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/api/v1/delivery', methods=['POST'])
@token_required
def delivery():
    global data
    request_data = request.get_json()
    order_id = request_data['order_id']
    th = request_data['th']
    quantity = request_data['quantity']
    username = request_data['username']
    phone = request_data['phone']

    if data['user'] == 'admin':
        request_to_db = f"INSERT INTO delivery (order_id, th, quantity, username, phone) VALUES ('{order_id}', '{th}', {quantity}, '{username}', '{phone}') ;"
        r = do_request_to_DB_nr(request_to_db)
        if r == 199 or r == 198:
            raise TypeError("order is not created, some problem with DB: delivery table: delivery")
        return Response(f'courier is assigned,order_id is {order_id}', 201)
    else:
        return Response('token is invalid', 403)



@app.route('/api/v1/delivery', methods=['DELETE'])
@token_required
def delete_delivery():
    global data
    request_data = request.get_json()
    order_id = request_data['order_id']
    th = request_data['th']
    quantity = request_data['quantity']
    username = request_data['username']
    phone = request_data['phone']

    if data['user'] == 'admin':
        request_to_db = f"DELETE FROM delivery WHERE order_id = {order_id} ;"
        r = do_request_to_DB_nr(request_to_db)
        if r == 199 or r == 198:
            raise TypeError("rollback is failed, some problem with DB: delivery table: delivery")
        return Response(f'courier is canselled,order_id is {order_id}', 201)
    else:
        return Response('token is invalid', 403)


app.run(debug=False, host='0.0.0.0', port=8000)

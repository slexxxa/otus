from flask import Flask, request, json
import psycopg2


def psql(method, uid=0,  username=0, firstname=0, lastname=0, email=0, phone=0):
    global output
    conn = psycopg2.connect(
        dbname="otus",
        user="postgres",
        password="12345678",
        host="10.169.44.141",
        port="30490"
    )

    cur = conn.cursor()

    # conn.autocommit = True
    if method == "GET":
        cur.execute("""
                SELECT username, firstname, lastname, email, phone FROM users WHERE id = %s;""", (uid, )
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

    if method == "POST":
        cur.execute("""
            INSERT INTO users (username, firstname, lastname, email, phone) 
            VALUES (%s, %s, %s, %s, %s);""", (username, firstname, lastname, email, phone)
                    )
        output = ''
    conn.commit()

    cur.close()
    conn.close()

    return output

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/api/v1/user/<uid>', methods=['GET'])
def show_user_profile(uid):
    # uid = int(uid)
    return psql("GET", uid)


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/api/v1/user', methods=['POST'])
def user():
    request_data = request.get_json()

    username = request_data['username']
    firstname = request_data['firstName']
    lastname = request_data['lastName']
    email = request_data['email']
    phone = request_data['phone']
    return psql("POST", 0, username, firstname, lastname, email, phone)


app.run(debug=True, host='0.0.0.0', port=8000)


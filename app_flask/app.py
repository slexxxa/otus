from flask import Flask, request
import psycopg2


def psql(method, username, firstname, lastname, email, phone):
    conn = psycopg2.connect(
        dbname="otus",
        user="postgres",
        password="12345678",
        host="10.169.44.141",
        port="30490"
    )

    cur = conn.cursor()

    # conn.autocommit = True

    cur.execute("""
        INSERT INTO users (username, firstname, lastname, email, phone) 
        VALUES (%s, %s, %s, %s, %s);""", (username, firstname, lastname, email, phone)
                )
    conn.commit()

    cur.close()
    conn.close()


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


# @app.route('/user/<username>')
# def show_user_profile(username):
#     return f'User {username}'


@app.route('/health')
def health():
    return '{"status": "OK"}'


@app.route('/user', methods=['POST'])
def user():
    request_data = request.get_json()

    username = request_data['username']
    firstname = request_data['firstname']
    lastname = request_data['lastname']
    email = request_data['email']
    phone = request_data['phone']
    psql("insert", username, firstname, lastname, email, phone)
    return f'Username {username}, firstname {firstname}'


app.run(debug=True, host='0.0.0.0', port=8000)

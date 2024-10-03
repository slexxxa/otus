from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'Hello, World!'

@app.route('/user/<username>')
def show_user_profile(username):
  return f'User {username}'

@app.route('/health')
def health():
    return '{"status": "OK"}'

app.run(debug=True, host='0.0.0.0', port=8000)

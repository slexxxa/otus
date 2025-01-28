from flask import Flask, request, json, Response
from prometheus_flask_exporter import PrometheusMetrics
from functools import wraps
import psycopg2, os, time
import jwt, datetime, string  # pyjwt
import requests #requests 2.32.3
import json as jsons
from multiprocessing import Process #

global dbname, user, password, host, port, data

envdbname = os.environ.get("PGDBNAME", "windows")
envuser = os.environ.get("PGUSER", "postgres")
envpassword = os.environ.get("PGPASSWORD", "12345678")
envhost = os.environ.get("PGHOST", "10.169.44.141")
envport = os.environ.get("PGPORT", "5432")
envbilling = os.environ.get("billing_url", "127.0.0.1:8001")
envnotify = os.environ.get("notify_url", "127.0.0.1:8003")


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJleHAiOjQ3MzQ0NDg4NjV9.VGqNY8WXYsgLutlgvjG8C5tdktfPw5WrNB17QsvBGmc"

class OrderService:
    def create_order(self, order_data):
        # Здесь реализация создания заказа
        pass

    def cancel_order(self, order_id):
        # Здесь реализация отмены заказа и компенсирующих действий
        pass

class PaymentService:
    def process_payment(self, order_id, payment_data):
        # Здесь реализация обработки платежа
        pass

    def rollback_payment(self, order_id):
        # Здесь реализация отмены платежа и компенсирующих действий
        pass

class StoreService:
    def reserve_product(self, order_id, reserve_data):
        # Здесь реализация резервирования товара
        pass

    def rollback_reserve(self, order_id):
        # Здесь реализация отмены резервирования и компенсирующих действий
        pass

class DeliveryService:
    def reserve_courier(self, order_id, reserve_data):
        # Здесь реализация резервирования курьера
        pass

    def rollback_courier(self, order_id):
        # Здесь реализация отмены резервирования и компенсирующих действий
        pass

class NotificationService:
    def send_notification(self, order_id, notification_data):
        # Здесь реализация отправки уведомления
        pass

    def rollback_notification(self, order_id):
        # Здесь реализация отмены уведомления и компенсирующих действий
        pass

class SagaCoordinator:
    def execute_saga(self, order_t, window_prise):
        order_service = OrderService()
        payment_service = PaymentService()
        store_service = StoreService()
        delivery_service = DeliveryService()
        notification_service = NotificationService()

        try:
            # Шаг 1: Создание заказа
            order_id = order_service.create_order(order_t, window_prise)

            # Шаг 2: Выполнение платежа
            payment_service.process_payment(order_id, payment_data)

            # Шаг 3: резервирование товара
            store_service.reserve_product(order_id, reservation_data)

            # Шаг 4: резервирование курьера
            delivery_service.reserve_courier(order_id, reservation_data)

            # Шаг 5: Отправка уведомления
            notification_service.send_notification(order_id, notification_data)

            # Все успешно выполнено, завершаем сагу
            print("Сага успешно завершена!")
        except Exception as e:
            # Обработка ошибки и выполнение компенсирующих действий
            print(f"Произошла ошибка: {e}")
            self.rollback_saga(order_id)

    def rollback_saga(self, order_id):
        # Вызываем компенсирующие действия для отмены всех предыдущих операций
        order_service = OrderService()
        payment_service = PaymentService()
        store_service = StoreService()
        delivery_service = DeliveryService()
        notification_service = NotificationService()

        try:
            # Шаг 1: Отмена платежа
            payment_service.rollback_payment(order_id)

            # Шаг 2: Отмена уведомления
            notification_service.rollback_notification(order_id)

            # Шаг 3: отмена резервирование товара
            store_service.rollback_reserve(order_id, reservation_data)

            # Шаг 4: отмена резервирование курьера
            delivery_service.rollback_courier(order_id, reservation_data)

            # Шаг 5: Отмена создания заказа
            order_service.cancel_order(order_id)

            print("Сага успешно отменена!")
        except Exception as e:
            # Обработка ошибки во время отката
            print(f"Ошибка при откате саги: {e}")


def process_for_idenpotentoncy():
    request_to_db = "DELETE FROM for_idenpotentoncy WHERE date < NOW() - INTERVAL '1 minute';"
    while True:
      print("start")
      do_request_to_DB_nr(request_to_db)
      time.sleep(30)
      print("after sleep")
    return


def do_request_to_DB_nr(request):
    conn = psycopg2.connect(
        dbname=envdbname,
        user=envuser,
        password=envpassword,
        host=envhost,
        port=envport
    )
    cur = conn.cursor()
    cur.execute(request)

    conn.commit()

    cur.close()
    conn.close()

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
    def __init__(self, window, user, email, phone):
        self.window = window
        self.user = user
        self.email = email
        self.phone = phone





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
    order_t = order(request_data['window'], data['user'], data['email'], data['phone'])
    window_prise = get_prise(order_t.window)

    saga_coordinator = SagaCoordinator()
    saga_coordinator.execute_saga(order_t, window_prise)

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

if __name__ == '__main__':

  p = Process(target=process_for_idenpotentoncy)
  p.start()
  p.join()

app.run(debug=False, host='0.0.0.0', port=8000)


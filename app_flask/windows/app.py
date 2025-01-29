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
envstore = os.environ.get("store_url", "127.0.0.1:8004")
envdelivery = os.environ.get("delivery_url", "127.0.0.1:8005")


token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJleHAiOjQ3MzQ0NDg4NjV9.VGqNY8WXYsgLutlgvjG8C5tdktfPw5WrNB17QsvBGmc"

class OrderService:
    def create_order(self, order_t, window_prise):
        # Здесь реализация создания заказа
        request_to_db = f"INSERT INTO order_table " \
                        f"(th, cost, username, email, phone) " \
                        f"VALUES " \
                        f"('{order_t.window}', {window_prise}, '{order_t.user}', '{order_t.email}', {order_t.phone}) " \
                        f"RETURNING id;"
        r = do_request_to_DB_r(request_to_db)
        return r[0]

    def cancel_order(self, order_id, order_t, window_prise):
        # Здесь реализация отмены заказа и компенсирующих действий
        request_to_db = f"DELETE FROM order_table WHERE id = {order_id} ;"
        r = do_request_to_DB_nr(request_to_db)
        if r == 199 or r == 198:
            raise TypeError("rollback is failed, some proble with DB: windows table: order_table")
        return


class PaymentService:
    def process_payment(self, order_id, order_t, window_prise):
        #Здесь реализация обработки платежа
        payload = jsons.dumps({'username': order_t.user, 'money': window_prise})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envbilling + "/api/v1/money"
        r = requests.delete(connstring, data=payload, params=param, headers=json_headers)
        #print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        if r.status_code == 210:
            raise TypeError("order is not created, you have not money :" + order_t.window + ", cost: " + str(window_prise))
        elif r.status_code == 200:
            request_to_db = f"UPDATE order_table SET is_payed = true WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("order is not created, some proble with DB: windows table: oeder_table")
            return
        else:
            raise TypeError("some problem")

    def rollback_payment(self, order_id, order_t, window_prise):
        # Здесь реализация отмены платежа и компенсирующих действий
        request_to_db = f"SELECT is_payed FROM order_table WHERE id = {order_id};"
        o = do_request_to_DB_r(request_to_db)
        if o[0] == False:
            return
        payload = jsons.dumps({'username': order_t.user, 'money': window_prise})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envbilling + "/api/v1/money"
        r = requests.put(connstring, data=payload, params=param, headers=json_headers)
        # print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        print(r)
        if r.status_code == 200:
            request_to_db = f"UPDATE order_table SET is_payed = false WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("rollback is failed, some proble with DB: windows table: oeder_table")
            return
        else:
            raise TypeError("some problem")

class StoreService:
    def reserve_product(self, order_id, order_t, window_prise):
        # Здесь реализация резервирования товара
        payload = jsons.dumps({'order_id': order_id, 'th': order_t.window, 'quantity': 1})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envstore + "/api/v1/item"
        r = requests.post(connstring, data=payload, params=param, headers=json_headers)
        # print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        if r.status_code == 210:
            raise TypeError(
                "order is not created, store has not :" + order_t.window + ", quantity: 1")
        elif r.status_code == 201:
            request_to_db = f"UPDATE order_table SET is_booked = true WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("order is not created, some proble with DB: windows table: oeder_table")
            return
        else:
            raise TypeError("some problem")


    def rollback_reserve(self, order_id, order_t, window_prise):
        # Здесь реализация отмены резервирования и компенсирующих действий
        request_to_db = f"SELECT is_booked FROM order_table WHERE id = {order_id};"
        o = do_request_to_DB_r(request_to_db)
        if o[0] == False:
            return
        payload = jsons.dumps({'order_id': order_id, 'th': order_t.window, 'quantity': 1})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envstore + "/api/v1/item"
        r = requests.post(connstring, data=payload, params=param, headers=json_headers)
        # print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        if r.status_code == 201:
            request_to_db = f"UPDATE order_table SET is_booked = false WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("rollback is failed, some proble with DB: windows table: oeder_table")
            return
        else:
            raise TypeError("some problem")

class DeliveryService:
    def reserve_courier(self, order_id, order_t, window_prise):
        # Здесь реализация резервирования курьера
        payload = jsons.dumps({'order_id': order_id, 'th': order_t.window, 'quantity': 1, 'username': order_t.user, 'phone': order_t.phone})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envdelivery + "/api/v1/delivery"
        r = requests.post(connstring, data=payload, params=param, headers=json_headers)
        # print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        if r.status_code == 210:
            raise TypeError(
                "order is not created, delivery service has not couriers")
        elif r.status_code == 201:
            request_to_db = f"UPDATE order_table SET is_delivered = true WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("order is not created, some proble with DB: windows table: oeder_table")
            return

        else:
            raise TypeError("some problem")

    def rollback_courier(self, order_id, order_t, window_prise):
        # Здесь реализация отмены резервирования и компенсирующих действий
        request_to_db = f"SELECT is_delivered FROM order_table WHERE id = {order_id};"
        o = do_request_to_DB_r(request_to_db)
        if o[0] == False:
            return
        payload = jsons.dumps({'order_id': order_id, 'th': order_t.window, 'quantity': 1, 'username': order_t.user,
                               'phone': order_t.phone})
        param = {'token': token}
        json_headers = {"Content-type": "application/json"}
        connstring = "http://" + envdelivery + "/api/v1/delivery"
        r = requests.delete(connstring, data=payload, params=param, headers=json_headers)
        # print(f"url: {r.url} \n\ntext: \n {r.text}\n\ncode:{r.status_code}")
        if r.status_code == 201:
            request_to_db = f"UPDATE order_table SET is_delivered = false WHERE id = {order_id}"
            r2 = do_request_to_DB_nr(request_to_db)
            if r2 == 199 or r2 == 198:
                raise TypeError("rollback is failed, some proble with DB: windows table: oeder_table")
            return

        else:
            raise TypeError("some problem")


class NotificationService:
    def send_notification(self, order_id, order_t, window_prise):
        # Здесь реализация отправки уведомления
        try:
            message = "order have been created :" + order_t.window + ", cost: " + str(window_prise)
            payload = jsons.dumps(
                {'username': data['user'], 'email': data['email'], 'phone': data['phone'], 'message': message})
            param = {'token': token}
            json_headers = {"Content-type": "application/json"}
            connstring = "http://" + envnotify + "/api/v1/notify"
            r2 = requests.post(connstring, data=payload, params=param, headers=json_headers)
            #print(f"urlr2: {r2.url} \n\ntextr2: \n {r2.text}\n\ncoder2:{r2.status_code}")
        except:
            print("An exception occurred")
        return

    def rollback_notification(self, order_id, order_t, window_prise):
        # Здесь реализация отмены уведомления и компенсирующих действий
        try:
            message = "failed to create your order :" + order_t.window + ", cost: " + str(window_prise)
            payload = jsons.dumps(
                {'username': data['user'], 'email': data['email'], 'phone': data['phone'], 'message': message})
            param = {'token': token}
            json_headers = {"Content-type": "application/json"}
            connstring = "http://" + envnotify + "/api/v1/notify"
            r2 = requests.post(connstring, data=payload, params=param, headers=json_headers)
            # print(f"urlr2: {r2.url} \n\ntextr2: \n {r2.text}\n\ncoder2:{r2.status_code}")
        except:
            print("An exception occurred")
        return

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
            print("order service done")

            # Шаг 2: Выполнение платежа
            payment_service.process_payment(order_id, order_t, window_prise)
            print("payment service done")

            # Шаг 3: резервирование товара
            store_service.reserve_product(order_id, order_t, window_prise)
            print("store service done")

            # Шаг 4: резервирование курьера
            delivery_service.reserve_courier(order_id, order_t, window_prise)
            print("delivery service done")

            # Шаг 5: Отправка уведомления
            notification_service.send_notification(order_id, order_t, window_prise)
            print("notification service done")

            # Все успешно выполнено, завершаем сагу
            print("Сага успешно завершена!")

        except Exception as e:
            # Обработка ошибки и выполнение компенсирующих действий
            print(f"Произошла ошибка: {e}")
            time.sleep(5)
            self.rollback_saga(order_id, order_t, window_prise)
            return 210

        return 201

    def rollback_saga(self, order_id, order_t, window_prise):
        # Вызываем компенсирующие действия для отмены всех предыдущих операций
        order_service = OrderService()
        payment_service = PaymentService()
        store_service = StoreService()
        delivery_service = DeliveryService()
        notification_service = NotificationService()
        try:
            # Шаг 1: Отмена платежа
            payment_service.rollback_payment(order_id, order_t, window_prise)
            print("rollback payment service done")

            # Шаг 2: отмена резервирование товара
            store_service.rollback_reserve(order_id, order_t, window_prise)
            print("rollback store service done")

            # Шаг 3: отмена резервирование курьера
            delivery_service.rollback_courier(order_id, order_t, window_prise)
            print("rollback delivery service done")

            # Шаг 4: Отмена создания заказа
            order_service.cancel_order(order_id, order_t, window_prise)
            print("rollback order service done")

            # Шаг 5: Отмена уведомления
            notification_service.rollback_notification(order_id, order_t, window_prise)
            print("rollback notification service done")

            print("Сага успешно отменена!")
        except Exception as e:
            # Обработка ошибки во время отката
            print(f"Ошибка при откате саги: {e}")

        return


def process_for_idenpotentoncy():
    request_to_db = "DELETE FROM for_idenpotentoncy WHERE date < NOW() - INTERVAL '1 minute';"
    while True:
      do_request_to_DB_nr(request_to_db)
      time.sleep(30)
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
    def __init__(self, window,x_request_id, user, email, phone):
        self.window = window
        self.x_request_id = x_request_id
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
    order_t = order(request_data['window'],request_data['x_request_id'], data['user'], data['email'], data['phone'])
    window_prise = get_prise(order_t.window)

    request_to_db = f"INSERT INTO for_idenpotentoncy (x_request_id) VALUES ({order_t.x_request_id});"
    o = do_request_to_DB_nr(request_to_db)
    if o == 199:
        return Response('your request already exists', 210)

    saga_coordinator = SagaCoordinator()
    o = saga_coordinator.execute_saga(order_t, window_prise)
    if o == 210:
        return Response('your order can not be created, failure', 210)


    return Response('your order has been created', 201)


def flask():
    app.run(debug=False, host='0.0.0.0', port=8000)


if __name__ == '__main__':

  p = Process(target=process_for_idenpotentoncy)
  p2 = Process(target=flask)
  p2.start()
  p.start()
  p.join()
  p2.join()


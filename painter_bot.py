import json
import random
import time
import uuid
from flask import Flask, request, render_template
from config import *
from medsenger_api import *
from paint import Text2ImageAPI
from celery import Celery, Task
import redis
from helper import *


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url="redis://localhost",
            result_backend="redis://localhost",
            task_ignore_result=True,
        ),
    )
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app


flask_app = create_app()
celery_app = flask_app.extensions["celery"]
medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, debug=True)


@celery_app.task
def generate_image(data, message_text):
    r = redis.Redis(host='localhost', port=6379, db=0)
    start_time = round(time.time())
    if r.get('gen_sec') == None:
        r.set('gen_sec', 50)
    prev_time = int(r.get('gen_sec').decode('UTF-8'))
    prev_time = random.randint(prev_time - 10, prev_time + 10)

    prepare_sec = plural_seconds(int(prev_time))
    medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, debug=True)
    medsenger_api.send_message(
        text=f'Приступаю к созданию иллюстрации, это может занять примерно ~ {prepare_sec}',
        contract_id=data['contract_id'],
    )
    print("приступаю к рисованию")

    api = Text2ImageAPI(
        URL,
        API_KEY,
        SECRET_KEY
    )

    model_id = api.get_model()
    u = api.generate(message_text, model_id)
    images = api.check_generation(u)
    uniq_id = str(uuid.uuid4())
    image_path = f"static/{uniq_id}.png"
    with open(image_path, "wb") as fh:
        fh.write(base64.b64decode(images[0]))
    end_time = round(time.time())
    gen_sec = end_time - start_time
    r.set('gen_sec', gen_sec)

    all_sec = plural_seconds(int(gen_sec))
    medsenger_api.send_message(
        text=f'Иллюстрация была создана за {all_sec}',
        contract_id=data['contract_id'],
        attachments=[prepare_file(image_path)]
    )
    print("иллюстрация готова")
    return 'ok'


@flask_app.route('/status', methods=['POST'])
def status():
    data = request.json

    if data['api_key'] != APP_KEY:
        return 'invalid key'

    answer = {
        "is_tracking_data": False,
        "supported_scenarios": [],
        "tracked_contracts": []
    }

    return json.dumps(answer)


@flask_app.route('/init', methods=['POST'])
def init():
    data = request.json
    medsenger_api.add_record(data.get('contract_id'), 'doctor_action', f'Подключен прибор "{data.get("agent_name")}".')
    return 'ok'


@flask_app.route('/remove', methods=['POST'])
def remove():
    data = request.json
    medsenger_api.add_record(data.get('contract_id'), 'doctor_action', f'Отключен прибор "{data.get("agent_name")}".')
    return 'ok'


@flask_app.route('/settings', methods=['GET'])
def settings():
    return render_template('settings.html')


@flask_app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


@flask_app.route('/message', methods=['POST'])
def save_message():
    data = request.json
    message_info = data['message']
    message_text = message_info['text']
    first = message_text.split()[0]
    if first.lower() == "нарисуй":
        medsenger_api.send_message(
            text=f'Запрос принят, иллюстрация в очереди',
            contract_id=data['contract_id'],
        )
        print("Запрос принят, иллюстрация в очереди")
        generate_image.delay(data, message_text)
    return "ok"


if __name__ == "__main__":
    flask_app.run(port=PORT, host=HOST)

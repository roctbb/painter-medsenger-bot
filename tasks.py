from medsenger_api import AgentApiClient, prepare_file
from infrastructure import celery
from helper import plural_seconds
from paint import Text2ImageAPI
from config import *
import random
import base64
import redis
import time


@celery.task
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
    import uuid
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
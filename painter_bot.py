from flask import Flask, request, render_template
from config import *
from medsenger_api import *
import json
from tasks import generate_image

app = Flask(__name__)
medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, debug=True)


@app.route('/status', methods=['POST'])
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


@app.route('/init', methods=['POST'])
def init():
    data = request.json
    medsenger_api.add_record(data.get('contract_id'), 'doctor_action', f'Подключен прибор "{data.get("agent_name")}".')
    return 'ok'


@app.route('/remove', methods=['POST'])
def remove():
    data = request.json
    medsenger_api.add_record(data.get('contract_id'), 'doctor_action', f'Отключен прибор "{data.get("agent_name")}".')
    return 'ok'


@app.route('/settings', methods=['GET'])
def settings():
    return render_template('settings.html')


@app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


@app.route('/message', methods=['POST'])
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
    app.run(port=PORT, host=HOST)

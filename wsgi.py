from painter_bot import flask_app
from config import *

if __name__ == "__main__":
    flask_app.run(port=PORT, host=HOST)
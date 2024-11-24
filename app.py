# +
from flask import Flask, request, jsonify
from flask_restx import Resource, Api
from werkzeug.middleware.proxy_fix import ProxyFix
import torch.multiprocessing as mp

import re
import torch
import pandas as pd
# -


from flask_socketio import SocketIO, join_room
from socketio_instance import socketio

from evaluation import EV
#from revision import RV
from repo import init_db
from etc import etc
from okr import okr

app = Flask(__name__, static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://####:####@localhost/eqsdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
init_db(app)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'xlsx','csv'}

api = Api(app, version='1.0', title='Sanhak EqualSum API', description='equalsum 산학협력 팀의 API입니다. ', doc='/docs')

api.add_namespace(EV, '/okrEV')
api.add_namespace(okr, '/okr')
#api.add_namespace(RV, '/okrRV')

api.add_namespace(etc, '')
socketio.init_app(app)

@app.route('/task_completed', methods=['POST'])
def task_completed():
    data = request.json
    result = data['result']
    # SocketIO를 통해 클라이언트에 알림 전송
    print(data)
    socketio.emit('task_completed', jsonify({'result': result}))
    socketio.sleep(0)
    return 'Notification sent', 200

if __name__=="__main__":
    mp.set_start_method('spawn', force=True) 
    socketio.run(app, debug=False, host='0.0.0.0', port=13000)

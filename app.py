import datetime
from datetime import datetime, timedelta, time
from flask_cors import CORS
from flask import Flask, url_for
from flask import request, render_template, redirect, Response, session, jsonify
import requests
import redis
from redis.exceptions import ConnectionError
import json
import uuid
import logging
import threading
import time
from flask import Flask, send_file
import redis


app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

redis_s = redis.StrictRedis(host='redis-1', port=6379, db=0)


class MyClass:
    def __init__(self):
        self.message = "Hello, Flask!"

    def get_message(self):
        return self.message


# check redis connection
def redis_connection():
    try:
        if redis_s.ping():
             return True
        else:
            return "Failed to connect to Redis"
    except redis_s.ConnectionError:
        return "Failed to connect to Redis"


@app.route('/')
def hello():
    return "Hello from flask ---"


@app.route('/index', methods=['GET'])
def index_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def user_login():
    data = request.json
    username = data['username']
    password = data['password']
    # stored_password = redis_client.get(username)
    return jsonify({'username': username,'Password': password}), 200


@app.route('/1/api/add/', methods=["POST"])
def add():
    try:
        if redis_connection():
            keys_ = []
            json_response = request.json
            # uuid
            json_response['id'] = _id = str(uuid.uuid1())
            redis_s.set("site_config_" + _id, json.dumps([json_response]), 86400)
            keys_.append(json_response)
            existing_list_json = redis_s.get('site_config_all')
            if existing_list_json:
                # Parse the existing list from a JSON string to a Python list object
                existing_list = json.loads(existing_list_json.decode('utf-8'))
                # Append the new object to the existing list
                existing_list.append(json_response)
                # Convert the updated list back to a JSON string
                updated_list_json = json.dumps(existing_list)
                # Store the updated list in Redis
                redis_s.set("site_config_all", updated_list_json, 86400)
                return json.dumps(existing_list), 200
            else:
                redis_s.set("site_config_all", json.dumps([json_response]), 86400)
            return ''
        else:
            response = {"message": "connection error"}
            return jsonify(response)
    except Exception as e:
        return str(e)


@app.route('/1/api/', methods=["GET"])
def get_():
    try:
        if redis_connection():
            json_response = redis_s.get("site_config_all")
            if json_response:
                return json_response, 200
            else:
                response = {"message": "record not found"}
                return response, 404
        else:
            response = {"message": "connection error"}
            return jsonify(response)
    except Exception as e:
        return str(e)


@app.route('/api/<_id>', methods=["GET"])
def get(_id):
    try:
        if redis_connection():
            json_response = redis_s.get("site_config_" + _id)
            if json_response:
                return json_response
            else:
                response = {"message": "record not found"}
                return response, 404
            # return json.loads(json_response)
            # if request.authorization and request.authorization.username == "admin" and\
            #         request.authorization.password == "admin":
            #     json_response = redis_s.get("site_config_"+config_name)
            #     return json.loads(json_response)
            # else:
            #     return {"message": "unauthorized"}, 401
        else:
            response = {"message": "connection error"}
            return jsonify(response)
    except Exception as e:
        return str(e)


@app.route('/clear/<existing_record>/<test>')
def clear(existing_record):
    v = existing_record
    existing_list_json = redis_s.get('site_config_all')
    existing_list = json.loads(existing_list_json.decode('utf-8'))
    if existing_list:
        for element in existing_list:
            element["config_type"] = v["config_type"]
            element["config_value"] = v["config_value"]
            break
        redis_s.set("site_config_all", json.dumps(existing_list), 86400)
        return existing_list


@app.route('/api/update/<_id>', methods=["POST", "PATCH"])
def update(_id):
    try:
        if redis_connection():
            json_response = redis_s.get("site_config_"+_id)
            if json_response:
                existing_record = json.loads(json_response.decode('utf-8'))
                input_params = request.json
                for element in existing_record:
                    if element["id"] == _id:
                        element["config_type"] = input_params["config_type"]
                        element["config_value"] = input_params["config_value"]
                        redis_s.set("site_config_" + _id, json.dumps([existing_record][0]), 86400)
                        return existing_record
            else:
                response = {"message": "record not found"}
                return response, 404
        else:
            response = {"message": "connection error"}
            return jsonify(response)
    except Exception as e:
        return str(e)


def validation_check(data):
    required_fields = ['config_label', 'config_name', 'config_type', 'config_value']
    for field in required_fields:
        if field not in data or not data[field]:
            return False
    else:
        return True


# for template form post
@app.route('/template', methods=['GET', 'POST'])
def form_post():
    try:
        if request.method == 'POST':
            config_label = request.form.get("config_label")
            config_name = request.form.get("config_name")
            config_type = request.form.get("config_type")
            config_value = request.form.get("config_value")
            data = {
                            "config_name": config_name,
                            "config_label": config_label,
                            "config_type": config_type,
                            "config_value": config_value
                        }
            if validation_check(data):
                response = requests.post('http://localhost:5000/1/api/add/', json=data)
                if response.status_code == 200:
                    return redirect('/template')
            else:
                error_msg = 'one or more fields missing'
                return render_template('template.html', data=None, msg=error_msg)

        if request.method == 'GET':
            response = requests.get('http://localhost:5000/1/api/')
            if response.status_code == 200:
                data = response.json()
                #time.sleep(10)
                return render_template('/template.html', data=data)
            else:
                return render_template('/template.html')
    except Exception as e:
        return str(e)


# for template edit form post
@app.route('/edit_template/<string:_id>', methods=['GET'])
def form_edit(_id):
    if request.method == 'GET':
        response = requests.get(f'http://localhost:5000/api/{_id}')
        return render_template('/edit_template.html', response=response.json())


# for template edit form post
@app.route('/edit_template/<string:_id>', methods=['POST'])
def form_edit_post(_id):
    if request.method == 'POST':
        response = requests.post(f'http://localhost:5000/api/update/{_id}', json=request.form)
        return redirect('/template')


@app.route('/1/api/register/', methods=["POST"])
def register():
    try:
        if redis_connection():
            keys_ = []
            json_response = request.json
            # uuid
            json_response['id'] = _id = str(uuid.uuid1())
            redis_s.set("user_id_" + _id, json.dumps([json_response]), 86400)
            keys_.append(json_response)
            existing_list_json = redis_s.get('user_ids')
            if existing_list_json:
                # Parse the existing list from a JSON string to a Python list object
                existing_list = json.loads(existing_list_json.decode('utf-8'))
                # Append the new object to the existing list
                existing_list.append(json_response)
                # Convert the updated list back to a JSON string
                updated_list_json = json.dumps(existing_list)
                # Store the updated list in Redis
                redis_s.set("user_ids", updated_list_json, 86400)
                return existing_list, 200
            else:
                redis_s.set("user_ids", json.dumps([json_response]), 86400)
            return ''
        else:
            response = {"message": "connection error"}
            return jsonify(response)
    except Exception as e:
        return str(e)


@app.route('/post_name', methods=['POST'])
def name_set():
    try:
        name = request.form.get("name")
        name = f"Hello!!!! {name}"
        return render_template('/Add_name.html', name=name)
    except Exception as e:
        return str(e)


# @app.route('/get_session')
# def get_session_1():
#     try:
#         print("Saket")
#         username = session.get('username')
#         print(username)
#         if username:
#             return f"session variable is {username}"
#     except Exception as e:
#         return str(e)



if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=True)



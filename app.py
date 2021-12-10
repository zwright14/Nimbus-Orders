import json
import logging
import os

from datetime import datetime

from flask import Flask, Response, redirect, url_for, request, render_template, jsonify
from flask_cors import CORS
from flask_dance.contrib.google import make_google_blueprint, google

from middleware.notification import Notification
from middleware.security import Security
from middleware.service_helper import _get_service_by_name, _generate_order_links, _generate_pages

import utils.rest_utils as rest_utils

from pprint import pprint

app = Flask(__name__)
CORS(app)

blueprint = make_google_blueprint(
    client_id=os.environ.get("OAUTH_ID", None),
    client_secret=os.environ.get("OAUTH_SECRET", None),
    scope=["profile", "email"],
    reprompt_consent=True
)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersekrit")
app.register_blueprint(blueprint, url_prefix="/userlogin")


@app.before_request
def checkSecurity():
    return Security.checkLogin(request.path)

@app.after_request
def sendSnsNotification(response):
    Notification.triggerNotification(request.path)
    return response

@app.route("/")
def index():
    return "Logged In!"

@app.route("/helloworld")
def hello():
    return '<u>Hello World!</u>'

@app.route('/orders', methods=["GET", "POST"])
def get_orders():
    try:
        inputs = rest_utils.RESTContext(request)
        service = _get_service_by_name("order_service")
        if service is not None:
            if inputs.method == 'GET':
                res, total_count = service.find_by_template(inputs.args, inputs.fields, inputs.limit, inputs.offset)
                if res is not None:
                    res = _generate_order_links(res)
                    res = _generate_pages(res, inputs, total_count)
                    res = json.dumps(res, default=str)
                    rsp = Response(res, status=200, content_type='application/JSON')
                else:
                    rsp = Response("NOT FOUND", status=404, content_type='text/plain')

            elif inputs.method == 'POST':
                res = service.create(inputs.data)
                if res is not None:
                    values = list(map(str, res.values()))
                    key = "_".join(values)
                    headers = {"location": f"/orders/{key}"}
                    rsp = Response("CREATED", status=201, content_type='text/plain', headers=headers)
                else:
                    rsp = Response("UNPROCESSABLE ENTITY", status=422, content_type='text/plain')

            else:
                rsp = Response("NOT IMPLEMENTED", status=501)
        else:
            rsp = Response("NOT FOUND", status=404, content_type='text/plain')

    except Exception as e:
        print(f"Path: /orders\nException: {e}")
        rsp = Response("INTERNAL ERROR", status=500, content_type='text/plain')

    return rsp


@app.route('/orders/<orderid>', methods=["GET", "PUT", "DELETE"])
def get_orders_by_orderid(orderid):
    try:
        inputs= rest_utils.RESTContext(request)
        service = _get_service_by_name("order_service")
        if service is not None:
            if inputs.method == 'GET':
                args = {}
                if inputs.args:
                    args = inputs.args
                args['orderID'] = orderid

                res, total_count = service.find_by_template(args, inputs.fields) # single product (no limits/offset)
                if res is not None:
                    res = _generate_order_links(res)
                    res = _generate_pages(res, inputs, total_count) # single product
                    res = json.dumps(res, default = str)
                    rsp = Response(res, status=200, content_type='application/JSON')
                else:
                    rsp = Response("NOT FOUND", status=404, content_type='text/plain')

            elif inputs.method == 'PUT':
                res = service.update(orderid, inputs.data)
                if res is not None:
                    rsp = Response("OK", status=200, content_type='text/plain')
                else:
                    rsp = Response("NOT FOUND", status=404, content_type='text/plain')

            elif inputs.method == 'DELETE':
                res = service.delete({"orderID": orderid})
                if res is not None:
                    rsp = Response(f"Rows Deleted: {res['no_of_rows_deleted']}", status=204, content_type='text/plain')
                else:
                    rsp = Response("NOT FOUND", status=404, content_type='text/plain')

            else:
                rsp = Response("NOT IMPLEMENTED", status=501)

        else:
            rsp = Response("NOT FOUND", status=404, content_type='text/plain')

    except Exception as e:
        print(f"Path: /orders/<orderid>\nException: {e}")
        rsp = Response("INTERNAL ERROR", status=500, content_type='text/plain')

    return rsp


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002)
from flask import Flask, Response
import database_services.RDBService as d_service
from flask_cors import CORS
import json

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from application_services.Orders.orders_service import Orders


app = Flask(__name__)
CORS(app)




@app.route('/')
def hello_world():
    return '<u>Hello World!</u>'

@app.route('/orders')
def get_orders():
    res = Orders.get_by_template(None)
    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp

@app.route('/orders/<orderid>')
def get_orders_by_id(orderid):
    res = Orders.get_by_order_id(orderid)
    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp

@app.route('/<db_schema>/<table_name>/<column_name>/<prefix>')
def get_by_prefix(db_schema, table_name, column_name, prefix):
    res = d_service.get_by_prefix(db_schema, table_name, column_name, prefix)
    rsp = Response(json.dumps(res, default=str), status=200, content_type="application/json")
    return rsp


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

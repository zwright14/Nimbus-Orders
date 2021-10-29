from application_services.BaseApplicationResource import BaseApplicationResource
import database_services.RDBService as d_service


class Orders(BaseApplicationResource):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_by_template(cls, template):
        res = d_service.find_by_template("OrderDB", "orders",
                                       template, None)
        return res

    @classmethod
    def get_by_order_id(cls, orderid):
        res = d_service.get_by_id("OrderDB", "orders",
                                       "orderID", orderid)
        return res
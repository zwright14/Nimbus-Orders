import os
import pymysql

# from Services.AddressService.address_service import AddressService as AddressService
# from Services.UserService.user_service import UserService as UserService

context = {
    "MAX_TABLE_ROWS_TO_PRINT": 10
}


def get_context_value(c_name=None):

    if c_name is None:
        result = context
    else:
        result = context.get(c_name)

    return result


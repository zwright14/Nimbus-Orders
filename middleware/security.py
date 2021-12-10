from flask import Flask, Response, redirect, url_for
from flask_dance.contrib.google import  google

import re

class Security:

    def checkLogin(path):
        # Create a whitelist of paths that don't need login access
        loginWhitelist = ['/helloworld', '/userlogin/google','/userlogin/google/authorized','/orders']
        if path not in loginWhitelist and not re.match('\/orders\/\d+', path):
            if not google.authorized:
                return redirect(url_for("google.login"))

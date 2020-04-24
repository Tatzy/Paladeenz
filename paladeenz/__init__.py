#Python 3.7
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
import requests
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from flask_login import login_user, logout_user, current_user, login_required
from flask_session import Session
import os
from flask_wtf import FlaskForm
from flask_session import Session
from datetime import timedelta
from paladeenz.api import api
from livereload import Server
from flask_wtf import FlaskForm
import arrow
import paladeenz.odd_functions as of
import paladeenz.read_credentials as r
from flask_login import LoginManager
from datetime import timedelta



DEVELOPMENT_MODE = True

basedir = os.path.abspath(os.path.dirname(__file__))
# Time Delay
# from datetime import datetime, timedelta
# new_time = datetime.now() + timedelta(minutes = 2)
# then look at datetime.now() > new_time


creds = r.read_credentials()
dev_id = creds['hirez']['id']
dev_key = creds['hirez']['key']
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SECRET_KEY'] = creds['db']['secret_key']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import paladeenz.models






LIVEMATCH_RATE_LIMIT = "15/hr"
RECENTMATCHES_RATE_LIMIT = "5/hr"
MATCHFEED_LIMIT = "10/hr"



s = api.PaladinsSession(dev_id,dev_key)
s2 = api.PaladinsSession(dev_id,dev_key)

session_time = arrow.utcnow()
session2_time = arrow.utcnow()

def check_session():
    global s
    global session_time

    if (arrow.utcnow()-session_time).seconds/60 >= 15:
        s = api.PaladinsSession(dev_id,dev_key) 
        session_time = arrow.utcnow()
    
def check_session2():
    global s2
    global session2_time

    if (arrow.utcnow()-session_time).seconds/60 >= 15:
        s2 = api.PaladinsSession(dev_id,dev_key) 
        session2_time = arrow.utcnow()

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=4)





login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
COOKIE_DURATION = timedelta(hours = 4)
app.config["DEBUG"] = True

limiter = Limiter(
    app,
    key_func=get_ipaddr,
    default_limits=["200 per day", "50 per hour"]
)

import paladeenz.views


    
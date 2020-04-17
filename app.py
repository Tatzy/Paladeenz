#Python 3.7
from flask import Flask, render_template, request, redirect, flash, url_for, session, app, jsonify
import odd_functions as of
import read_credentials as r
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import arrow
import json
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from flask_migrate import Migrate
from werkzeug.urls import url_parse
import pandas as pd
from flask_session import Session
from datetime import timedelta
import api.api


class LoginForm(FlaskForm):
    username = StringField('username')
    password = PasswordField('password')
    submit = SubmitField('Submit')

basedir = os.path.abspath(os.path.dirname(__file__))
# Time Delay
# from datetime import datetime, timedelta
# new_time = datetime.now() + timedelta(minutes = 2)
# then look at datetime.now() > new_time


creds = r.read_credentials()
dev_id = creds['hirez']['id']
dev_key = creds['hirez']['key']
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'login.db')
app.config['SECRET_KEY'] = creds['db']['secret_key']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)
COOKIE_DURATION = timedelta(days=365)

LIVEMATCH_RATE_LIMIT = "15/hr"
RECENTMATCHES_RATE_LIMIT = "5/hr"

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(hours=4)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@login_manager.user_loader
def load_user(id): 
    return User.query.get(int(id))

@app.route('/logs')
@login_required
@limiter.exempt
def logs():
    table = pd.read_csv("searches.log")
    return render_template("logs.html", data=table.to_html(classes="greyGridTable"))

@app.route('/admin')
@login_required
@limiter.exempt
def admin():
    return render_template('admin.html')

@app.route('/roadmap')
def roadmap():
    return render_template('roadmap.html')


@app.route('/login', methods=['GET', 'POST'])
@limiter.exempt
def login():
    if current_user.is_authenticated:
        return redirect(url_for('search'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('search')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)
#@login_required

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password_hash = db.Column(db.String(128))
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



SERVER_IP = requests.get("https://api.ipify.org?format=json").json()['ip']
@app.route("/", methods=['GET'])
#@limiter.limit("15/hour")
@limiter.exempt
def search():
    return render_template('index.html')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('search'))
# have html do a status check first and then if the error message is good do a livematch


@app.route("/statistics")
@limiter.exempt
def redir():
    return redirect("https://docs.google.com/spreadsheets/d/1YgshfIDPZikBA7-1L5dIA2pm0ouXsNJ54dgEUp0a7KM/edit?usp=sharing")

@app.route("/player", methods=['GET'])
#@limiter.limit("5/hour")
@limiter.exempt
def recent_matches():
    if 'recentmatches' in request.args:
        player_name = request.args['recentmatches']
        s = api.api.PaladinsSession(dev_id,dev_key)
        player_id_json = s._make_request("getplayeridbyname", [player_name])
        if player_id_json == []:
            return jsonify({"error_msg" : "Player not found", "status":0})
        else:
            player_id = player_id_json[0]['player_id']
            utc = arrow.utcnow()
            local = utc.to('US/Eastern')
            dt_string = local.format('MM/DD/YYYY HH:mm')
            f = open("searches.log", 'a')
            f.write("HISTORY," + dt_string + "," + player_name+"\n")
            final_matches = of.get_recent_matches(s, player_id)
            return jsonify(final_matches)


@app.route("/about", methods = ['GET'])
@limiter.exempt
def about():
    f = open("static/suggestions.txt", 'r')
    lines = f.readlines()
    data = {"LIVEMATCH_RATE_LIMIT":LIVEMATCH_RATE_LIMIT, "RECENTMATCHES_RATE_LIMIT" : LIVEMATCH_RATE_LIMIT, "SUGGESTIONS":lines}
    return render_template("about.html", data=data)

@app.route("/live", methods=['GET'])
@limiter.limit("15/hour")
@limiter.exempt
def livematch():
    if 'livematch' in request.args:
        player_name = request.args['livematch']
        utc = arrow.utcnow()
        local = utc.to('US/Eastern')
        dt_string = local.format('MM/DD/YYYY HH:mm')
        f = open("searches.log", 'a')
        f.write("LIVEMATCH," + dt_string + "," + player_name+"\n")
        f.close()

        if player_name == "":
            return jsonify(status = 0, error_msg="Blank username, please try a different username.")
        # elif request.remote_addr in iplist.keys():
        #     if datetime.now() < iplist[request.remote_addr]:
        #         return jsonify(status = 0, error_msg="Too many searches, please wait 90 seconds before searching again.")
        #     else:
        #         iplist.pop(request.remote_addr)
        else:
            s = api.api.PaladinsSession(dev_id,dev_key)
            player_status = of.get_player_status(player_name,s)
            if player_status == False or player_status == 5: #this is if the username does not exist
                return jsonify(status = 5, error_msg="Player not found.")
            elif player_status == 2:
                return jsonify(status = player_status, error_msg="Player is currently in champion selection, please try again later.")
            elif player_status in [0,1,4]:
                return jsonify(status = player_status, error_msg="Player is not currently in a game.")
            else:
                game_info = of.player_live_lookup(player_status,s)
                return jsonify(game_info)


@app.route("/test", methods=['GET'])
@limiter.exempt
def test():
    s = api.api.PaladinsSession(dev_id,dev_key)
    player_name = request.args['player']
    player_id_json = s._make_request("getplayeridbyname", [player_name])
    if player_id_json == []:
        pass
    else:
        player_id = player_id_json[0]['player_id']
        #return jsonify(s._make_request('getqueuestats', [player_id,'486']))
        #return jsonify(s._make_request('getchampions', ['1']))
        return jsonify(s._make_request('getchampionleaderboard', ['2314','486']))

@app.route("/analysis", methods=['GET'])
@limiter.exempt
def analysis():
    s = api.api.PaladinsSession(dev_id,dev_key)
    champ_names = []
    all_champions = s._make_request('getchampions', ['1'])
    #print(all_champions)
    for item in all_champions:
        champ_names.append(item['Name'])
    return render_template("analysis.html", c_names=champ_names)


if __name__ == "__main__":
    app.run(debug=True)
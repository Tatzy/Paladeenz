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
COOKIE_DURATION = timedelta(hours = 4)

LIVEMATCH_RATE_LIMIT = "15/hr"
RECENTMATCHES_RATE_LIMIT = "5/hr"
MATCHFEED_LIMIT = "10/hr"



s = api.api.PaladinsSession(dev_id,dev_key)
s2 = api.api.PaladinsSession(dev_id,dev_key)
session_time = arrow.utcnow()
session2_time = arrow.utcnow()

def check_session():
    global s
    global session_time

    if (arrow.utcnow()-session_time).seconds/60 >= 15:
        s = api.api.PaladinsSession(dev_id,dev_key) 
    
def check_session2():
    global s2
    global session2_time

    if (arrow.utcnow()-session_time).seconds/60 >= 15:
        s2 = api.api.PaladinsSession(dev_id,dev_key) 

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
        utc = arrow.utcnow()
        local = utc.to('US/Eastern')
        dt_string = local.format('MM/DD/YYYY HH:mm')
        f = open("searches.log", 'a')
        f.write("LOGIN," + dt_string + "," + user.username +"\n")
        f.close()
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
@limiter.exempt
def search():
    return render_template('index.html')

@app.route("/logout")
@limiter.exempt
def logout():
    logout_user()
    return redirect(url_for('search'))
# have html do a status check first and then if the error message is good do a livematch


@app.route("/statistics")
@limiter.exempt
def redir():
    return redirect("https://docs.google.com/spreadsheets/d/1YgshfIDPZikBA7-1L5dIA2pm0ouXsNJ54dgEUp0a7KM/edit?usp=sharing")

@app.route("/player", methods=['GET'])
@limiter.limit(RECENTMATCHES_RATE_LIMIT)
def recent_matches():

    if 'recentmatches' in request.args:
        t = request.args.get('time')
        if t == None:
            t = int(0)
        print(t)
        player_name = request.args['recentmatches']
        utc = arrow.utcnow()
        player_id_json = s._make_request("getplayeridbyname", [player_name])
        if player_id_json == []:
            return jsonify({"error_msg" : "Player not found", "status":0})
        else:
            player_id = player_id_json[0]['player_id']
            local = utc.to('US/Eastern')
            dt_string = local.format('MM/DD/YYYY HH:mm')
            f = open("searches.log", 'a')
            f.write("HISTORY," + dt_string + "," + player_name+"\n")
            check_session()
            final_matches = of.get_recent_matches(s, player_id, t)
            return jsonify(final_matches)

@app.route("/about", methods = ['GET'])
@limiter.exempt
def about():
    f = open("static/suggestions.txt", 'r')
    lines = f.readlines()
    data = {"LIVEMATCH_RATE_LIMIT":LIVEMATCH_RATE_LIMIT, "RECENTMATCHES_RATE_LIMIT" : LIVEMATCH_RATE_LIMIT, "SUGGESTIONS":lines}
    return render_template("about.html", data=data)

@app.route("/live", methods=['GET'])
@limiter.limit(LIVEMATCH_RATE_LIMIT)
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
            #s = api.api.PaladinsSession(dev_id,dev_key)
            check_session()
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



@app.route("/matchfeed", methods=['GET'])
@limiter.limit(MATCHFEED_LIMIT)
def matchfeed():
    return render_template("matchfeed.html")

@app.route("/test", methods=['GET'])
@limiter.exempt
@login_required
def test():
    check_session()
    #print(s)
    a = s._make_request("getdataused", [])
    #print(a)
    return jsonify(a)

@app.route("/updatefeed", methods = ['GET'])
@limiter.limit(MATCHFEED_LIMIT)
def send_new_data():
    check_session2()
    utc = arrow.utcnow()
    date = utc.format('YYYYMMDD')
    match_return_list = []
    time = utc
    time = time.format('H,mm')
    #print(time.split(",")[1])
    #print(str((int(time.split(",")[1]) - (int(time.split(",")[1])%10))%60))
    b = str((int(time.split(",")[1]) - (int(time.split(",")[1])%10))%60)
    a = time.split(",")[0]
    if int(b) == 0:
        b = "00"
        a = str((int(a))%24)
    else:
        b = str(b)
    if int(a) == 0:
        a = "0"
    else:
        a = str(a)
    time = str(a) + "," + str(b)

    all_matches = s2._make_request("getmatchidsbyqueue", ["486",str(date),"-1"])

     
    if all_matches != []:
        all_matches = all_matches[::-1]
        matches_length = min(len(all_matches),30)
        id_string = ""
        match_details = {}
        for i in range(0, matches_length):
            if i % 10 == 9:
                id_string += all_matches[i]['Match']
                #print(id_string)
                batch_results = s2._make_request("getmatchdetailsbatch", [id_string])
                for item in batch_results:
                    if item['Match'] not in match_details.keys():
                        match_details[item['Match']] = []
                    match_details[item['Match']].append(item)
                id_string=""
            else:
                id_string += all_matches[i]['Match'] + ","
        match_return_list = []
        for match in match_details:
            avg_rank = 0
            for i in range(0,len(match_details[match])):
                avg_rank += match_details[match][i]['League_Tier']
                entry_time = match_details[match][i]['Entry_Datetime']
                region = match_details[match][i]['Region']
            avg_rank = int(avg_rank/10)
            arrowtime = arrow.get(str(entry_time), 'M/DD/YYYY h:mm:ss A')
            k = utc - arrowtime
            if region == "Latin America North":
                region = "LAN"
            match_return_list.append({"region":region ,"average_rank_img" : of.parse_rank(avg_rank), "average_rank" : of.parse_rank_name(avg_rank), "time":str((k.seconds//60)%60)+ " minutes ago...", "avg_rank" : avg_rank})

    utc = arrow.utcnow()
    local = utc.to('US/Eastern')
    dt_string = local.format('MM/DD/YYYY HH:mm')
    f = open("searches.log", 'a')
    f.write("MATCHFEED," + dt_string + "," + "ALL" +"\n")
    #print(match_return_list)
    return json.dumps(match_return_list)


@app.route("/analysis", methods=['GET'])
@limiter.exempt
def analysis():
    s = api.api.PaladinsSession(dev_id,dev_key)
    champ_names = []
    all_champions = s._make_request('getchampions', ['1'])
    for item in all_champions:
        champ_names.append(item['Name'])
    return render_template("analysis.html", c_names=champ_names)


if __name__ == "__main__":
    app.run(debug=False)
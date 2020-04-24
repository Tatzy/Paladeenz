from flask import Flask, render_template

emergency = Flask(__name__)
@emergency.route("/", methods = ["GET"])
def index():
    return "<html><body><center><h1>Site Outage. Will be back soon, check <a href=\"https://discord.gg/WutJ7d\">https://discord.gg/WutJ7d</a> for details</h1></center></body></html>"

if __name__ == "__main__":
    emergency.run(debug=False)
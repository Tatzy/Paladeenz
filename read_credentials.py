import json

with open('credentials.json') as json_file:
    data = json.load(json_file)

def read_credentials():
    return data
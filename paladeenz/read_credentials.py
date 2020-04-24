import json

with open('paladeenz/files/credentials.json') as json_file:
    data = json.load(json_file)

def read_credentials():
    return data
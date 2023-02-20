from flask import Flask
from dbctl import apeksdbctl

def main():
    apeksdbctl.DbInit()
    app_ = Flask(__name__)
    #Start Ping and Send Challenge Request to Arduino
    print('Sending Challenge Request...')
    #PingMe()
    #a = Thread(target=miscale2.mainS, daemon=True)
    #a.start()
    print('[OK] Challenge Received')
    return app_

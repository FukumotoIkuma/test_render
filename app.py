from os import PathLike
from flask import Flask, request,jsonify,make_response
from pprint import pformat
from system import create_hmac_sha256
import os

app = Flask(__name__)
show_text = "no webhook"


#環境変数の読み込み
try:#ローカル
    import secret_key
except:#鯖
    SECRET_KEY =  os.getenv('SECRET_KEY')

@app.route("/",methods = ['GET'])
def home():
    return "Hello World!"

@app.route("/webhook",methods = ["POST"])
def webhook():
    # TO DO zoomからのリクエストかを判断する
    # https://developers.zoom.us/docs/api/rest/webhook-reference/#verify-webhook-events

    # クエリパラメータを取得
    data = request.get_json()
    global show_text
    show_text = pformat(data, indent=4)

    if data["event"] == "endpoint.url_validation":
        plainToken = data["payload"]["plainToken"]
        res_json = {
            "plainToken": plainToken,
            "encryptedToken": create_hmac_sha256(SECRET_KEY,plainToken)
        }
        res =jsonify(res_json)
        res.status_code = 200
        return res

    return make_response("",200)

@app.route("/newest")
def newest_webhook():
    global show_text
    return show_text

if __name__ == '__main__':
    app.run(port=3000)
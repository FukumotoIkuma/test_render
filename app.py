from flask import Flask, request,jsonify,make_response
from pprint import pformat
from system import create_hmac_sha256
import os

from send_sms import ZoomAPI,send_sms

#.envを読み込み（ローカル用）
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
show_text = ["no webhook"]
zoom_api = ZoomAPI()


#環境変数の読み込み
ZOOM_SECRET_TOKEN =  os.getenv('ZOOM_SECRET_TOKEN')

@app.route("/",methods = ['GET'])
def home():
    return "hello world!"

@app.route("/webhook",methods = ["POST"])
def webhook():
    # TO DO zoomからのリクエストかを判断する
    # https://developers.zoom.us/docs/api/rest/webhook-reference/#verify-webhook-events

    # クエリパラメータを取得
    data = request.get_json()
    global show_text
    show_text.append(data)

    event = data["event"]
    payload = data["payload"]
    if event == "endpoint.url_validation":
        plainToken = payload["plainToken"]
        res_json = {
            "plainToken": plainToken,
            "encryptedToken": create_hmac_sha256(ZOOM_SECRET_TOKEN,plainToken)
        }
        res =jsonify(res_json)
        res.status_code = 200
        return res

    elif event == "phone.callee_ended":
        call_id = payload["object"]["call_id"]
        phone_number,extension_numbers = zoom_api.extract_SMS_info(call_id)
        print(f"extension_numbers: {extension_numbers}")

        #TODO 本番環境で可変にすべき
        if "210" in extension_numbers:
            try:
                send_sms(phone_number=phone_number,message="test")
                print("completely sended msg")
            except Exception as e:
                print(e)

    return make_response("",200)

@app.route("/newest")
def newest_webhook():
    global show_text
    return show_text

@app.route("/clear")
def clear():
    global show_text
    show_text = []
    return "completely finished"
    
if __name__ == '__main__':
    app.run(port=5000)
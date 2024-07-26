from os import PathLike
from flask import Flask, request,jsonify,make_response
from pprint import pformat
import hmac
import hashlib
import os

app = Flask(__name__)
show_text = "no webhook"

#環境変数の読み込み
try:#ローカル
    import secret_key
except:#鯖
    SECRET_KEY =  os.getenv('SECRET_KEY')

def create_hmac_sha256(secret, plainToken):
    """
    HMAC SHA-256 ハッシュを作成する関数。
    
    :param secret: Webhook のシークレットトークン（ソルトとして使用）
    :param plainToken: ハッシュする文字列
    :return: HMAC SHA-256 ハッシュの 16 進数表現
    """
    # シークレットとプレーンテキストをバイト型に変換
    secret_bytes = secret.encode('utf-8')
    plainToken_bytes = plainToken.encode('utf-8')
    
    # HMAC SHA-256 ハッシュを計算
    hmac_hash = hmac.new(secret_bytes, plainToken_bytes, hashlib.sha256)
    
    # ハッシュを 16 進数表現で返す
    return hmac_hash.hexdigest()


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
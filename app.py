from flask import Flask, request
import requests
import json
from pprint import pformat

app = Flask(__name__)
show_text = "no webhook"
@app.route("/",methods = ['GET'])
def main():
    return "Hello World!"

@app.route("/webhook",methods = ["GET","POST"])
def webhook_get():
    if request.method == "GET":
        # クエリパラメータを取得
        response = request.args.to_dict()
    elif request.method == "POST":
        # JSONペイロードを取得
        response = request.get_json()

    # pprintで整形した文字列を作成
    formatted_response = pformat(response, indent=4)
    global show_text
    show_text = formatted_response
    print(formatted_response)

    return f"<pre>{formatted_response}</pre>"

@app.route("/newest")
def newest_webhook():
    global show_text
    return show_text

if __name__ == '__main__':
    
    app.run(port=3000)
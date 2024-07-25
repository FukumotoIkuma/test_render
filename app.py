from flask import Flask, request
import requests
import json
from pprint import pformat


def webhook(event,url,body=None):#bodyを少し変えたい場合body変数を使う
    method = event.method
    #url = event.url
    print(f"headersType:{type(event.headers)}")
    headers = {key: value for key, value in dict(event.headers).items() if key != 'Host'} 
    if(not body):#bodyを指定されなければeventのbodyを利用（本来の挙動）
        body = event.json

    print(f"Method: {method}Type:{type(method)}")
    print(f"URL : {url}Type:{type(url)}")
    print(f"Headers: {headers}Type:{type(headers)}")
    print(f"Body: {body}Type:{type(body)}")

    try:
        # Reconstruct headers and forward the request
        headers["Content-Type"] = "application/json;charset=utf-8"
        response = requests.request(
            method=method,
            url=url,
            headers=json.loads(json.dumps(headers)),
            json=json.loads(json.dumps(body)),
        )

        print('Forwarded Data:', response)
        print('HTTP Status Code:', response.status_code)

        return 'Data forwarded successfully', 200
    except Exception as e:
        print('Error:', e)
        return 'Failed to forward data', 500
    


app = Flask(__name__)

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

    print(formatted_response)

    return f"<pre>{formatted_response}</pre>"
if __name__ == '__main__':
    
    app.run(port=3000)
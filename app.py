from os import PathLike
from flask import Flask, request,jsonify,make_response
from pprint import pformat
from system import create_hmac_sha256
import os
import pandas as pd
import schedule#require
import time
from datetime import datetime, timedelta
import threading

class CallManager:
    """call_idと電話番号を管理するクラス
    """
    def __init__(self):
        self.CALL_ID = "call_id"
        self.PHONE_NUMBER = "phone_number"
        self.CREATED_AT = "created_at"
        self.df = pd.DataFrame(columns=[self.CALL_ID, self.PHONE_NUMBER, self.CREATED_AT])

    def add_record(self, call_id:str, phone_number:str):
        """レコードを追加する

        Args:
            call_id (str): webhookに含まれるcall_id
            phone_number (str): call_idに対応するphone_number
        """

        created_at = datetime.now()
        new_record = pd.DataFrame({'call_id': [call_id], 'phone_number': [phone_number], 'created_at': [created_at]})
        self.df = pd.concat([self.df, new_record], ignore_index=True)
        print(f"Added record: {new_record.iloc[0].to_dict()}")


    def get_phone_number(self, call_id:str):
        """call_idからphone_numberを取得する

        Args:
            call_id (str): webhookに含まれるcall_id

        Returns:
            str: 電話番号
            None: call_idが存在しない
        """
        record = self.df[self.df[self.CALL_ID] == call_id]
        if not record.empty:
            return record.iloc[0][self.PHONE_NUMBER]
        else:
            return None

    def start_cleanup_schedule(self, interval_minutes=30):
        self.interval_minutes = interval_minutes
        cleanup_thread = threading.Thread(target=self._start_cleanup_schedule)
        cleanup_thread.daemon = True
        cleanup_thread.start()

    def _start_cleanup_schedule(self):
        schedule.every(self.interval_minutes).minutes.do(self._delete_old_records)
        while True:
            schedule.run_pending()
            time.sleep(60*10)

    def _delete_old_records(self):
        current_time = datetime.now()
        threshold_time = current_time - timedelta(minutes=30)
        self.df = self.df[self.df[self.CREATED_AT] > threshold_time]
        print("Old records deleted")

# インスタンスの作成
call_manager = CallManager()

# 定期的に古いレコードを削除するスケジュールを開始（バックグラウンドで実行）
call_manager.start_cleanup_schedule()


app = Flask(__name__)
show_text = ["no webhook"]


#環境変数の読み込み
try:#ローカル
    local = True
    from secret_key import SECRET_KEY
except:#鯖
    local = False
    SECRET_KEY =  os.getenv('SECRET_KEY')

@app.route("/",methods = ['GET'])
def home():
    return call_manager.get_phone_number(1)

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
            "encryptedToken": create_hmac_sha256(SECRET_KEY,plainToken)
        }
        res =jsonify(res_json)
        res.status_code = 200
        return res
    
    elif event == "phone.caller_connected":
        obj = payload["object"]
        call_id = obj["call_id"]
        phone_number = obj["callee"]["phone_number"]
        call_manager.add_record(call_id,phone_number)

    elif event == "phone.callee_ended":
        call_id = payload["object"]["call_id"]
        phone_number = call_manager.get_phone_number(call_id=call_id)
        # TODO SMS送信処理

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
    if local:
        app.run()
    else:
        app.run(port=6000)
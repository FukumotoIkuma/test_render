import base64
import requests

from pprint import pprint
import time
from datetime import datetime, timedelta
import boto3#requirement
import os


class ZoomTokenMaker:
    def __init__(self):
        self._token = None
        self.token_creation_time = None
        self.ZOOM_CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')
        self.ZOOM_CLIENT_SECRET  = os.getenv('ZOOM_CLIENT_SECRET')
        self.ZOOM_ACCOUNT_ID = os.getenv('ZOOM_ACCOUNT_ID')

    def generate_token(self):
        # クライアントIDとクライアントシークレットをbase64形式でエンコード
        client_credentials = f"{self.ZOOM_CLIENT_ID}:{self.ZOOM_CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(client_credentials.encode()).decode()

        # ヘッダーの設定
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        # ボディの設定
        body = {
            "grant_type": "account_credentials",
            "account_id": self.ZOOM_ACCOUNT_ID
        }

        # トークンAPIのエンドポイント
        token_url = "https://zoom.us/oauth/token"

        # POSTリクエストの送信
        response = requests.post(token_url, headers=headers, data=body)

        # レスポンスの確認
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            return access_token
        else:
            raise Exception("Coldn't get access token")
        
    @property
    def token(self):
        """有効なTokenを返す

        Returns:
            _type_: _description_
        """
        if self._is_token_expired():
            self._token = self.generate_token()
        return self._token

    def _is_token_expired(self):
        if self.token_creation_time is None:
            return True
        return datetime.now() - self.token_creation_time > timedelta(minutes=50)

class ZoomAPI(object):
    def __init__(self) -> None:
        self.token_mng = ZoomTokenMaker()
        self.base_url ="https://api.zoom.us/v2"
        self.call_history_url = self.base_url+"/phone/call_history/{callLogId}"

    def extract_keys_from_segments(self,segments, *args):
        """
        特定のキーを抽出したセグメントの新しいリストを作成する関数。

        Parameters:
            segments (list): 元のセグメントのリスト。
            *args: 抽出したいキー。

        Returns:
            list: 抽出されたキーに基づく新しいセグメントのリスト。
        """
        extracted_segments = [{key: segment.get(key) for key in args}for segment in  segments]

        
        return extracted_segments

    def remove_duplicate_segments(self,segments):
        """
        重複したセグメントを取り除く関数。

        Parameters:
            segments (list): 元のセグメントのリスト。

        Returns:
            list: 重複が取り除かれたセグメントのリスト。
        """
        unique_segments = []
        seen = set()

        for segment in segments:
            # セグメントの各項目をタプルにして一意性を確保
            segment_tuple = tuple(sorted(segment.items()))
            
            if segment_tuple not in seen:
                seen.add(segment_tuple)
                unique_segments.append(segment)

        return unique_segments

    def extract_SMS_info(self,call_id:str):
        """APIによりcall_idからSMS送信が必要か判断するための取得する

        Args:
            call_id (str): webhookで得られるcall_id

        Returns:
            str: 電話番号(+813012341234/国際電話形式)
            set: 経由した内線番号のリスト
        """
        
        # ヘッダーの設定
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Bearer {self.token_mng.token}"
        }

        

        # call historyからcallLogIdを取得する
        # webhookレスポンスにコールログのIDが存在するが、そのIDと現在取得しているIDは
        # 別物らしい（スクリプト作成時点）。そのうち統合されるかも？
        # https://developers.zoom.us/docs/zoom-phone/understanding-call-history/
        
        # キーワードにcall_idを指定することで確実に絞り込み
        # TODO HEAVYなので、40 リクエスト/秒、60000/dayまでである。少し数を減らす工夫が必要そう
        params ={
            "keyword":call_id
        }
        history_response = requests.get(
            self.call_history_url.format(callLogId=""),
            headers=headers,params=params
        )
        if history_response.status_code!=200:
            return#TODO errorハンドリング
        history = history_response.json()["call_logs"]
        # keywordがマッチする値はcall_idで絞り込んでるとは言え不確定なので、手動で絞り込みも行う
        call_log_id = [his for his in history if his["call_id"]==call_id][0]["id"]

        # call_log_idからcall_logを取得し、整形する
        # LIGHTなので、制限は80 リクエスト/秒。気にせずアクセスして良い。
        callLog_response = requests.get(self.call_history_url.format(callLogId = call_log_id),headers=headers)
        phone_number = callLog_response.json()["callee_did_number"]
        segments = callLog_response.json()["call_path"]
        
        # ログ変換にはこれらの処理を利用できそう。メモとして残す
        # segments = extract_keys_from_segments(segments,"event","result","operator_ext_number","callee_ext_number","operator_ext_Type","callee_ext_type","operator_name","caller_name","callee_name","press_key")
        # segments = remove_duplicate_segments(segments)

        segments = self.extract_keys_from_segments(segments,"operator_ext_number")
        extension_numbers = set([dic.get("operator_ext_number") for dic in segments])
        return phone_number,extension_numbers

def send_sms(phone_number:str, message:str,sender_name:str="send-Test"):
    """SMSメッセージを送信する

    Args:
        phone_number (str): 国際電話番号(+00 11 2222 3333)
        message (str): 本文
        sender_name (str, optional): 送信者の名前.英数字と-のみ使用可能. Defaults to "send-Test".

    Returns:
        bool: メッセージ送信完了
    
    Raises:
        Exception:何らかのエラーが発生した場合
    
    Examples:
        send_sms("+811122223333,"message","sender")
    """
    message_attributes = {
    'AWS.SNS.SMS.SenderID': {
    'DataType': 'String',
    'StringValue': sender_name # 通知者表示に使用される送信者ID
    }
    }
    AWS_ACCESS_KEY      =  os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY      =  os.getenv('AWS_SECRET_KEY')
    

    sns = boto3.client(
        'sns', 
        aws_access_key_id=AWS_ACCESS_KEY, 
        aws_secret_access_key=AWS_SECRET_KEY, 
        region_name='ap-northeast-1'
    )
    response = sns.publish(
        PhoneNumber = phone_number,
        Message = message,
        MessageAttributes = message_attributes
    )
    return True

import base64
import requests

from pprint import pprint
# 変数に格納された値
from API_INFO import ACCOUNT_ID,CLIENT_ID,CLIENT_SECRET
import time
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self):
        self._token = None
        self.token_creation_time = None

    def generate_token(self):
        # クライアントIDとクライアントシークレットをbase64形式でエンコード
        client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded_credentials = base64.b64encode(client_credentials.encode()).decode()
        print(encoded_credentials)

        # ヘッダーの設定
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }

        # ボディの設定
        body = {
            "grant_type": "account_credentials",
            "account_id": ACCOUNT_ID
        }

        # トークンAPIのエンドポイント
        token_url = "https://zoom.us/oauth/token"

        # POSTリクエストの送信
        response = requests.post(token_url, headers=headers, data=body)

        # レスポンスの確認
        if response.status_code == 200:
            access_token = response.json().get("access_token")
            print(f"ACCESS_TOKEN: {access_token}")
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
    
def extract_SMS_info(call_id:str):
    """call_idからSMS送信が必要か判断するための取得する

    Args:
        call_id (str): webhookで得られるcall_id

    Returns:
        str: 電話番号(+813012341234/国際電話形式)
        set: 経由した内線番号のリスト
    """
    # token_mng= TokenManager()
    # token = token_mng.token
    token = 'eyJzdiI6IjAwMDAwMSIsImFsZyI6IkhTNTEyIiwidiI6IjIuMCIsImtpZCI6IjU5ODVjNDcwLTMxNDQtNDZhOS04Y2Q3LWMwZjI4N2RmYzEzOSJ9.eyJhdWQiOiJodHRwczovL29hdXRoLnpvb20udXMiLCJ1aWQiOiJKVzRqODZmelF2aWtSbTA4MGVPZGNBIiwidmVyIjo5LCJhdWlkIjoiOTViOWZhZWFiYjk3MDBhMGFkMTQ4M2JhN2ZmYjVjN2QiLCJuYmYiOjE3MjMxNzAzNzEsImNvZGUiOiJWZ3dRc21mSFN5aS02UUlxQjk1TndnYnNrUXM2WHJDTUEiLCJpc3MiOiJ6bTpjaWQ6bkRvM3RDeFRKZUhNc0Q3R3ZQVjh3IiwiZ25vIjowLCJleHAiOjE3MjMxNzM5NzEsInR5cGUiOjMsImlhdCI6MTcyMzE3MDM3MSwiYWlkIjoiU0FEeTNJUlJRdW02QnlPM0Z3WG1uQSJ9.khZiPR94YZwqZH7P9EPIlqXjL1wKGStim3yK4MFSQnsiaMVGYF98230G5F7nzDq1UE7WIMpWZ6ZvG6uXdBJNtA'
    # ヘッダーの設定
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Bearer {token}"
    }

    url ="https://api.zoom.us/v2/phone/call_history/{callLogId}"

    # call historyからcallLogIdを取得する
    # webhookレスポンスにコールログのIDが存在するが、そのIDと現在取得しているIDは
    # 別物らしい（スクリプト作成時点）。そのうち統合されるかも？
    # https://developers.zoom.us/docs/zoom-phone/understanding-call-history/
    
    # キーワードにcall_idを指定することで確実に絞り込み
    params ={
        "keyword":call_id
    }
    history_response = requests.get(url.format(callLogId=""),headers=headers,params=params)
    if history_response.status_code!=200:
        return#TODO errorハンドリング
    history = history_response.json()["call_logs"]
    # keywordがマッチする値はcall_idで絞り込んでるとは言え不確定なので、手動で絞り込みも行う
    call_log_id = [his for his in history if his["call_id"]==call_id][0]["id"]

    # call_log_idからcall_logを取得し、整形する
    callLog_response = requests.get(url.format(callLogId = call_log_id),headers=headers)
    phone_number = callLog_response.json()["callee_did_number"]
    segments = callLog_response.json()["call_path"]
    
    # ログ変換にはこれらの処理を利用できそう。メモとして残す
    # segments = extract_keys_from_segments(segments,"event","result","operator_ext_number","callee_ext_number","operator_ext_Type","callee_ext_type","operator_name","caller_name","callee_name","press_key")
    # segments = remove_duplicate_segments(segments)

    # 特定の内線番号に転送されたことをトリガーとしてSMSを送信する
    segments = extract_keys_from_segments(segments,"operator_ext_number")
    extension_numbers = set([dic.get("operator_ext_number") for dic in segments])
    return phone_number,extension_numbers



def extract_keys_from_segments(segments, *args):
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

def remove_duplicate_segments(segments):
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

if __name__=="__main__":
    phone_number,extension_numbers = extract_SMS_info("7400958907136918608")
    print(phone_number,extension_numbers)

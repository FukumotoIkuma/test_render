import hmac
import hashlib
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
import _thread as thread
import base64
import hashlib
import hmac
import json
from urllib.parse import urlparse, urlencode
import ssl
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
import websocket

answer = ""
callback_func = None
accumulated_text = ""
processing_status = "ready"

def set_callback(callback):
    """设置回调函数"""
    global callback_func, answer, accumulated_text
    callback_func = callback
    answer = ""
    accumulated_text = ""

class Ws_Param:
    def __init__(self, APPID, APIKey, APISecret, Spark_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Spark_url).netloc
        self.path = urlparse(Spark_url).path
        self.Spark_url = Spark_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))
        
        signature_origin = f"host: {self.host}\ndate: {date}\nGET {self.path} HTTP/1.1"
        signature_sha = hmac.new(
            self.APISecret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
        
        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        
        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        
        url = f"{self.Spark_url}?{urlencode(v)}"
        return url

def on_error(ws, error):
    global processing_status
    print("### error:", error)
    processing_status = "error"
    if callback_func:
        callback_func(f"\nError: {error}\n")

def on_close(ws, *args):
    global processing_status
    print("\n### WebSocket Closed ###\n")
    # 只有在正常处理状态下才显示完成消息
    if processing_status != "error" and callback_func:
        callback_func("\n分析完成.\n")
    processing_status = "closed"

def on_open(ws):
    global processing_status
    processing_status = "processing"
    thread.start_new_thread(run, (ws,))

def on_message(ws, message):
    global answer, accumulated_text, processing_status
    try:
        data = json.loads(message)
        code = data['header']['code']
        if code != 0:
            error_msg = f'请求错误: {code}, {data}'
            print(error_msg)
            processing_status = "error"
            if callback_func:
                callback_func(f"\n{error_msg}\n")
            ws.close()
        else:
            choices = data["payload"]["choices"]
            status = choices["status"]
            content = choices["text"][0]["content"]
            
            accumulated_text += content
            answer += content

            # 当累积的文本达到一定长度或包含特定字符时触发回调
            if len(accumulated_text) >= 50 or \
               any(char in accumulated_text for char in ['.', '。', '!', '?', '\n']):
                if callback_func:
                    callback_func(accumulated_text)
                accumulated_text = ""  # 重置累积的文本
           
            print(content, end="", flush=True)
            
            # 如果是最后一条消息
            if status == 2:
                # 确保发送剩余的累积文本
                if accumulated_text and callback_func:
                    callback_func(accumulated_text)
                processing_status = "completed"
                ws.close()
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        processing_status = "error"
        if callback_func:
            callback_func(f"\nError processing message: {str(e)}\n")
        ws.close()

def run(ws, *args):
    data = json.dumps(gen_params(appid=ws.appid, domain=ws.domain, question=ws.question))
    ws.send(data)

def gen_params(appid, domain, question):
    return {
        "header": {
            "app_id": "0340274e",
            "uid": "1234"
        },
        "parameter": {
            "chat": {
                "domain": "4.0Ultra",
                "temperature": 0.5,
                "max_tokens": 8192
            }
        },
        "payload": {
            "message": {
                "text": question
            }
        }
    }

def main(appid, api_key, api_secret, Spark_url, domain, question):
    global answer, accumulated_text, processing_status
    # 重置状态
    answer = ""
    accumulated_text = ""
    processing_status = "ready"
    
    wsParam = Ws_Param(appid, api_key, api_secret, Spark_url)
    websocket.enableTrace(False)
    wsUrl = wsParam.create_url()
    ws = websocket.WebSocketApp(wsUrl, 
                              on_message=on_message, 
                              on_error=on_error, 
                              on_close=on_close, 
                              on_open=on_open)
    ws.appid = appid
    ws.question = question
    ws.domain = domain
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
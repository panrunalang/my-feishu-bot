# app.py (修正版)

import os
import json
import threading
from flask import Flask, request, jsonify
from feishu import FeishuClient

# ... (初始化部分代码无改动) ...
app = Flask(__name__)
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("TABLE_ID")
if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID]):
    raise ValueError("错误：一个或多个环境变量没有设置。")
client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID)


def process_text_message(chat_id, record_text):
    # ... (此函数无改动) ...
    pass

def process_image_message(chat_id, message_id, image_key):
    """在后台线程中处理图片消息"""
    print(f"后台开始处理图片消息, message_id: {message_id}, image_key: {image_key}")
    image_bytes = client.download_image(message_id, image_key) # 传入两个ID
    if image_bytes:
        description = client.get_image_description(image_bytes)
        if description:
            if client.write_bitable(description):
                if chat_id:
                    reply_content = f"✅ 图片记账成功: {description}"
                    client.send_reply(chat_id, reply_content)
            else:
                client.send_reply(chat_id, "❌ 写入表格失败，请检查后台日志。")
        else:
            client.send_reply(chat_id, "❌ 图片识别失败，请稍后再试。")
    else:
        # 如果下载失败，现在会由download_image函数打印详细错误
        client.send_reply(chat_id, "❌ 图片处理失败，请查看后台日志了解详情。")


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
        
    event = data.get("event", {})
    message = event.get("message", {})
    msg_type = message.get("message_type")
    chat_id = message.get("chat_id")
    message_id = message.get("message_id")
    
    thread = None
    if msg_type == "text":
        content = json.loads(message.get("content", "{}"))
        record_text = content.get("text", "")
        if record_text:
            thread = threading.Thread(target=process_text_message, args=(chat_id, record_text))
    elif msg_type == "image":
        # 解析出 image_key
        content = json.loads(message.get("content", "{}"))
        image_key = content.get("image_key")
        if image_key:
            # 将 image_key 传递给后台函数
            thread = threading.Thread(target=process_image_message, args=(chat_id, message_id, image_key))
    
    if thread:
        thread.start()

    return jsonify({"code": 0})


if __name__ == "__main__":
    app.run(port=5000, debug=True)

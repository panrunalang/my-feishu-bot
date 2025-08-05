# app.py (最终版)

import os
import json
import threading
from flask import Flask, request, jsonify
from feishu import FeishuClient

# 初始化 Flask 应用 和 飞书客户端
app = Flask(__name__)
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("TABLE_ID")

if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID]):
    raise ValueError("错误：一个或多个环境变量没有设置。")
client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID)


def process_text_message(chat_id, record_text):
    """在后台线程中处理文本消息"""
    print(f"后台开始处理文本: {record_text}")
    if client.write_bitable(record_text):
        if chat_id:
            reply_content = f"✅ 记账成功: {record_text}"
            client.send_reply(chat_id, reply_content)

def process_image_message(chat_id, message_id):
    """在后台线程中处理图片消息"""
    print(f"后台开始处理图片消息, message_id: {message_id}")
    image_bytes = client.download_image(message_id)
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
        client.send_reply(chat_id, "❌ 图片下载失败，请稍后再试。")


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
    
    # 根据消息类型分发到不同的处理函数
    thread = None
    if msg_type == "text":
        content = json.loads(message.get("content", "{}"))
        record_text = content.get("text", "")
        if record_text:
            thread = threading.Thread(target=process_text_message, args=(chat_id, record_text))
    elif msg_type == "image":
        thread = threading.Thread(target=process_image_message, args=(chat_id, message_id))
    
    if thread:
        thread.start()

    return jsonify({"code": 0})

if __name__ == "__main__":
    app.run(port=5000, debug=True)

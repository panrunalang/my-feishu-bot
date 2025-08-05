# app.py

import os
import json
import threading # 引入线程模块
from flask import Flask, request, jsonify
from feishu import FeishuClient

# 初始化 Flask 应用
app = Flask(__name__)

# --- 从环境变量安全地读取配置 ---
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("TABLE_ID")

# 检查环境变量是否都已设置
if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID]):
    raise ValueError("错误：一个或多个环境变量没有设置，请检查 Render.com 上的配置。")

# 初始化飞书客户端
client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID)

def process_message(chat_id, record_text):
    """
    在后台线程中处理耗时操作
    """
    print(f"后台开始处理: {record_text}")
    # 检查写入是否成功
    if client.write_bitable(record_text):
        # 如果成功，并且我们拿到了 chat_id，就发送回复
        if chat_id:
            # 使用 f-string 来格式化回复内容
            reply_content = f"✅ 记账成功: {record_text}"
            client.send_reply(chat_id, reply_content)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        
        # 1. 处理飞书的 URL 验证请求
        if data.get("type") == "url_verification":
            print("收到 URL 验证请求，已正确响应。")
            return jsonify({"challenge": data.get("challenge")})
            
        # 2. 处理事件回调
        event = data.get("event")
        if not event:
            return jsonify({"code": 1, "msg": "Invalid event"})

        message = event.get("message", {})
        msg_type = message.get("message_type")
        chat_id = message.get("chat_id")
        
        if msg_type == "text":
            content_str = message.get("content", "{}")
            content = json.loads(content_str)
            record_text = content.get("text", "")
            
            if record_text:
                print(f"收到文本消息，准备后台处理: {record_text}")
                # 创建并启动一个新线程来处理消息，主线程可以立刻返回
                thread = threading.Thread(target=process_message, args=(chat_id, record_text))
                thread.start()

    except Exception as e:
        print(f"发生未知错误: {e}")

    # 无论如何，都立刻向飞书返回成功响应，防止重试
    return jsonify({"code": 0})

# 这个部分仅用于本地测试
if __name__ == "__main__":
    app.run(port=5000, debug=True)

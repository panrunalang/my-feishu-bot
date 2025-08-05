# app.py

import os
import json
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
            print("收到的请求不是一个有效的事件。")
            return jsonify({"code": 1, "msg": "Invalid event"})

        message = event.get("message", {})
        msg_type = message.get("message_type")
        # 新增：获取 chat_id
        chat_id = message.get("chat_id")
        
        # --- 核心逻辑：只处理文本消息 ---
        if msg_type == "text":
            content_str = message.get("content", "{}")
            content = json.loads(content_str)
            record_text = content.get("text", "")
            
            print(f"解析到文本内容: {record_text}")

            if record_text:
                # 检查写入是否成功
                if client.write_bitable(record_text):
                    # 如果成功，并且我们拿到了 chat_id，就发送回复
                    if chat_id:
                        client.send_reply(chat_id, "✅ 记账成功")
            else:
                print("文本内容为空，已忽略。")
        else:
            print(f"收到非文本消息 (类型: {msg_type})，已忽略，不作处理。")

    except Exception as e:
        print(f"发生未知错误: {e}")

    # 始终向飞书返回成功响应
    return jsonify({"code": 0})

# 这个部分仅用于本地测试
if __name__ == "__main__":
    app.run(port=5000, debug=True)

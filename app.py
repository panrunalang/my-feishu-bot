# app.py (已更新，更健壮的版本)

import os
import json
import threading
from flask import Flask, request, jsonify
from feishu import FeishuClient

# 初始化 Flask 应用
app = Flask(__name__)

# --- 环境变量 (保持不变) ---
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("TABLE_ID")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID, GCP_PROJECT_ID]):
    raise ValueError("错误：一个或多个环境变量没有设置。请检查 APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID, 和 GCP_PROJECT_ID。")

# --- 客户端初始化 (保持不变) ---
try:
    client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID)
except Exception as e:
    # 如果客户端初始化失败，在日志中记录并阻止应用启动
    print(f"CRITICAL: FeishuClient 初始化失败，应用无法启动: {e}")
    raise e

# --- 消息处理函数 (保持不变) ---
def process_text_message(chat_id, record_text):
    """在后台线程中处理文本消息"""
    print(f"后台开始处理文本: {record_text}")
    if client.write_bitable(record_text):
        if chat_id:
            reply_content = f"✅ 记账成功: {record_text}"
            client.send_reply(chat_id, reply_content)

def process_image_message(chat_id, message_id, image_key):
    """在后台线程中处理图片消息"""
    print(f"后台开始处理图片消息, message_id: {message_id}, image_key: {image_key}")
    image_bytes = client.download_image(message_id, image_key)
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

# --- Webhook 路由 (核心修改点) ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    
    # 打印接收到的原始请求体，这是最重要的诊断信息
    print(f"收到的原始请求: {json.dumps(data, indent=2)}")
    
    # 1. 处理飞书的 Challenge 验证
    if data.get("type") == "url_verification":
        print("收到 URL Verification 请求，正在返回 challenge...")
        return jsonify({"challenge": data.get("challenge")})
        
    # 2. 使用 try...except 包裹整个事件处理逻辑，防止因意外错误而崩溃
    try:
        event = data.get("event", {})
        message = event.get("message", {})
        msg_type = message.get("message_type")
        chat_id = message.get("chat_id")
        message_id = message.get("message_id")
        
        thread = None
        
        # 确认我们收到了一个有效消息事件
        if not all([msg_type, chat_id, message_id]):
            print("收到的事件不是一个有效的消息，已忽略。")
            return jsonify({"code": 0})
            
        print(f"正在处理消息，类型: {msg_type}, 消息ID: {message_id}")

        if msg_type == "text":
            # 使用 .get() 安全地获取 content，避免 KeyError
            content_str = message.get("content", "{}")
            content = json.loads(content_str)
            record_text = content.get("text", "")
            if record_text:
                print(f"已解析出文本内容，准备启动后台线程。")
                thread = threading.Thread(target=process_text_message, args=(chat_id, record_text))
            
        elif msg_type == "image":
            content_str = message.get("content", "{}")
            print(f"图片消息的 Content 字段 (字符串): {content_str}")
            
            # 同样用 try...except 包裹 JSON 解析，这是最容易出错的地方
            try:
                content_json = json.loads(content_str)
                image_key = content_json.get("image_key")

                if image_key:
                    print(f"已成功解析出 image_key: {image_key}，准备启动后台线程。")
                    thread = threading.Thread(target=process_image_message, args=(chat_id, message_id, image_key))
                else:
                    print(f"错误：未能从消息中解析出 image_key。解析后的 JSON: {content_json}")
            except json.JSONDecodeError as e:
                print(f"错误：解析图片消息的 content 字段失败，它不是一个有效的 JSON 字符串。错误信息: {e}")

        if thread:
            thread.start()
        
    except Exception as e:
        # 如果任何地方发生未知错误，打印它，这样我们就不会再“一无所知”
        print(f"处理 Webhook 时发生未知错误: {e}")

    # 始终返回成功的响应给飞书，防止飞书因超时而重试
    return jsonify({"code": 0})


# --- 本地调试启动 (保持不变) ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

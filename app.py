import os
import json
import threading
from flask import Flask, request, jsonify
from feishu import FeishuClient
# 导入 vertexai
import vertexai

# 初始化 Flask 应用
app = Flask(__name__)

# --- 环境变量配置 ---
# 飞书相关
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
TABLE_ID = os.getenv("TABLE_ID")
# Google Cloud 相关
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_REGION", "us-central1") # 提供一个默认值

# 完善环境变量检查，确保所有需要的变量都被设置了
if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID, GCP_PROJECT_ID]):
    raise ValueError("错误：一个或多个环境变量没有设置。请检查 APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID, GCP_PROJECT_ID。")

# --- 初始化服务 ---
# 1. 初始化 Vertex AI (这是关键一步)
# 在 Render 上，它会自动寻找 GOOGLE_APPLICATION_CREDENTIALS 凭证文件
try:
    print(f"正在初始化 Vertex AI, 项目: {GCP_PROJECT_ID}, 区域: {GCP_REGION}")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    print("Vertex AI 初始化成功。")
except Exception as e:
    # 抛出异常，这样在Render启动失败时能从日志中看到明确错误
    raise RuntimeError(f"Vertex AI 初始化失败: {e}")

# 2. 初始化飞书客户端 (不再需要传递API Key)
client = FeishuClient(APP_ID, APP_SECRET, BITABLE_APP_TOKEN, TABLE_ID)


def process_text_message(chat_id, record_text):
    # ... (此函数无需修改) ...
    """在后台线程中处理文本消息"""
    print(f"后台开始处理文本: {record_text}")
    if client.write_bitable(record_text):
        if chat_id:
            reply_content = f"✅ 记账成功: {record_text}"
            client.send_reply(chat_id, reply_content)

def process_image_message(chat_id, message_id, image_key):
    # ... (此函数无需修改) ...
    """在后台线程中处理图片消息"""
    print(f"后台开始处理图片消息, message_id: {message_id}, image_key: {image_key}")
    image_bytes = client.download_image(message_id, image_key)
    if image_bytes:
        # get_image_description 现在调用的是 Vertex AI
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
    # ... (此函数无需修改) ...
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
        content_str = message.get("content", "{}")
        content_json = json.loads(content_str)
        image_key = content_json.get("image_key")

        if image_key:
            thread = threading.Thread(target=process_image_message, args=(chat_id, message_id, image_key))
        else:
            print(f"错误：未能从消息中解析出 image_key。Content: {content_str}")

    if thread:
        thread.start()

    return jsonify({"code": 0})

if __name__ == "__main__":
    # Gunicorn会忽略这里的设置，但为了本地调试方便，保留此部分
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

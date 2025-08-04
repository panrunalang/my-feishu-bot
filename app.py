import os
import json
from flask import Flask, request, jsonify
from feishu import FeishuClient

# 初始化 Flask 应用
app = Flask(__name__)

# --- 从环境变量安全地读取配置 ---
# 请确保在 Render.com 的后台设置了这些环境变量
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
        # 解析请求体
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
        message_id = message.get("message_id")
        content_str = message.get("content", "{}")
        
        # 飞书发来的 content 是一个 JSON 字符串，需要二次解析
        content = json.loads(content_str)
        record_text = ""

        print(f"收到消息，类型: {msg_type}, ID: {message_id}")

        if msg_type == "text":
            record_text = content.get("text", "")
            print(f"解析到文本内容: {record_text}")
            
        elif msg_type == "image":
            print("正在处理图片消息...")
            image_key = content.get("image_key")
            # 注意：新版API中，图片的file_key就是message_id
            image_bytes = client.download_image(message_id)
            if image_bytes:
                record_text = client.do_ocr(image_bytes)
                print(f"图片OCR识别结果: {record_text}")
            else:
                print("图片下载失败，跳过处理。")

        # 写入多维表格 (只有在有内容时才写入)
        if record_text:
            client.write_bitable(record_text)
        else:
            print("无有效内容可写入表格，已忽略。")

    except Exception as e:
        # 如果发生任何预料之外的错误，打印日志，但仍然返回成功，防止飞书重试
        print(f"发生未知错误: {e}")

    # 向飞书返回成功响应
    return jsonify({"code": 0})

# 这个部分仅用于本地测试，在Render上会使用gunicorn启动
if __name__ == "__main__":
    app.run(port=5000, debug=True)
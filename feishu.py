# feishu.py (修正版)

import lark_oapi as lark
import json
import os
import base64
from openai import OpenAI

from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody, GetMessageResourceRequest

class FeishuClient:
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        # ... (此部分无改动) ...
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        self.feishu_client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    def write_bitable(self, text):
        # ... (此方法无改动) ...
        pass

    def send_reply(self, chat_id, text):
        # ... (此方法无改动) ...
        pass
    
    def download_image(self, message_id, image_key):
        """根据消息ID和文件Key下载图片"""
        request = GetMessageResourceRequest.builder() \
            .message_id(message_id) \
            .file_key(image_key) \
            .type("image") \
            .build()
        
        resp = self.feishu_client.im.v1.message_resource.get(request)

        if resp is None or resp.code != 0:
            print(f"下载图片失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            return None
        
        print("图片下载成功。")
        return resp.file

    def get_image_description(self, image_bytes):
        # ... (此方法无改动) ...
        pass

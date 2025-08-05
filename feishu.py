# feishu.py

import lark_oapi as lark
import json
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody, GetMessageResourceRequest

class FeishuClient:
    # 移除了 openrouter_api_key 参数
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        
        # 飞书客户端 (保持不变)
        self.feishu_client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()
        
        # 初始化 Vertex AI
        # 它会自动从环境变量中获取项目ID、区域和凭证
        try:
            PROJECT_ID = os.getenv("GCP_PROJECT_ID")
            REGION = os.getenv("GCP_REGION", "us-central1") # 默认为 us-central1
            if not PROJECT_ID:
                raise ValueError("错误：GCP_PROJECT_ID 环境变量未设置，无法初始化 Vertex AI。")
            vertexai.init(project=PROJECT_ID, location=REGION)
            print("Vertex AI 客户端初始化成功。")
        except Exception as e:
            # 在实际部署中，如果初始化失败，应用应该无法启动
            # 这个打印是为了在日志中看到明确的错误
            print(f"Vertex AI 客户端初始化失败: {e}")
            raise e

    # write_bitable 和 send_reply 方法保持不变，这里省略...
    def write_bitable(self, text):
        """向多维表格写入一行记录，并返回是否成功"""
        try:
            fields = {"原始文本": text}
            record = AppTableRecord.builder().fields(fields).build()
            
            request = CreateAppTableRecordRequest.builder() \
                .app_token(self.bitable_app_token) \
                .table_id(self.table_id) \
                .request_body(record) \
                .build()

            resp = self.feishu_client.bitable.v1.app_table_record.create(request)
            
            if resp is None or resp.code != 0:
                print(f"写入表格失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
                return False
            else:
                print(f"成功写入表格: '{text}'")
                return True
        except Exception as e:
            print(f"调用 write_bitable 时发生异常: {e}")
            return False

    def send_reply(self, chat_id, text):
        """向指定聊天发送回复消息"""
        try:
            content = {"text": text}
            body = CreateMessageRequestBody.builder() \
                .receive_id(chat_id) \
                .msg_type("text") \
                .content(json.dumps(content)) \
                .build()

            request = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(body) \
                .build()

            resp = self.feishu_client.im.v1.message.create(request)

            if resp is None or resp.code != 0:
                print(f"发送回复失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
        except Exception as e:
            print(f"调用 send_reply 时发生异常: {e}")
            
    def download_image(self, message_id, file_key):
        """根据消息ID和文件Key下载图片 (保持不变)"""
        print(f"正在准备下载图片，message_id: {message_id}, file_key: {file_key}")
        request = GetMessageResourceRequest.builder() \
            .message_id(message_id) \
            .file_key(file_key) \
            .type("image") \
            .build()
        
        resp = self.feishu_client.im.v1.message_resource.get(request)

        if resp is None or resp.code != 0:
            print(f"下载图片失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            return None
        
        return resp.file

    def get_image_description(self, image_bytes):
        """【已更新】调用 Vertex AI 获取图片描述"""
        print("正在调用 Vertex AI API...")
        try:
            # 准备请求内容
            # 注意：这里我们直接使用 image_bytes，SDK会处理它
            # 我们假设所有图片都是 png，如果可能有 jpeg，需要更复杂的逻辑判断 mime_type
            image_part = Part.from_data(data=image_bytes.read(), mime_type="image/png")
            
            prompt_text = "请详细描述这张图片里的内容，用于记账。如果包含收据或发票，请提取关键信息：总金额、日期、项目名称，生成简短描述。要求：1. 除了信息之外，不要添加任何额外的文字或者符号包括：`，`,`。`,`.`，`*`等；2. 只用一句简短的中文描述即可，比如`10月1日购买办公用品花费10刀`、`中午吃饭花了15人民币`，**不能超过20字**；3. 注意货币的种类，比如美元(刀，美元，$，bucks)、人民币(元，人民币，¥，块钱)等。"

            # 初始化模型并发送请求
            model = GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content(
                [image_part, prompt_text],
            )
            
            description = response.text
            print(f"Vertex AI 返回描述: {description}")
            return description
        except Exception as e:
            print(f"调用 Vertex AI API 失败: {e}")
            return None

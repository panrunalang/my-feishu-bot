# feishu.py

import lark_oapi as lark
import json
from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest
# 新增：导入发送消息相关的模块
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

class FeishuClient:
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()

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

            resp = self.client.bitable.v1.app_table_record.create(request)
            
            if resp is None or resp.code != 0:
                print(f"写入表格失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
                return False # 失败时返回 False
            else:
                print(f"成功写入表格: '{text}'")
                return True # 成功时返回 True
        except Exception as e:
            print(f"调用 write_bitable 时发生异常: {e}")
            return False

    def send_reply(self, chat_id, text):
        """向指定聊天发送回复消息"""
        try:
            # 构建消息内容，注意 content 是一个 JSON 格式的字符串
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

            resp = self.client.im.v1.message.create(request)

            if resp is None or resp.code != 0:
                print(f"发送回复失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            else:
                print(f"成功向 Chat ID {chat_id} 发送回复: '{text}'")
        except Exception as e:
            print(f"调用 send_reply 时发生异常: {e}")

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest

class FeishuClient:
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()

    def write_bitable(self, text):
        """向多维表格写入一行记录"""
        try:
            fields = {"原始文本": text}  # 假设你的表格第一列字段名为“原始文本”
            record = AppTableRecord.builder().fields(fields).build()
            
            request = CreateAppTableRecordRequest.builder() \
                .app_token(self.bitable_app_token) \
                .table_id(self.table_id) \
                .request_body(record) \
                .build()

            resp = self.client.bitable.v1.app_table_record.create(request)
            
            if resp is None or resp.code != 0:
                print(f"写入表格失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            else:
                print(f"成功写入表格: '{text}'")
        except Exception as e:
            print(f"调用 write_bitable 时发生异常: {e}")

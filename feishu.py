import os
import requests
import lark_oapi as lark
from lark_oapi.api.im.v1 import GetMessageResourceRequest
from lark_oapi.api.ocr.v1 import RecognizeBasicImageRequest
from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

class FeishuClient:
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .build()

    def download_image(self, message_id):
        """根据消息ID下载图片"""
        request = GetMessageResourceRequest.builder() \
            .message_id(message_id) \
            .file_key(message_id) \
            .type("image") \
            .build()
        
        resp = self.client.im.v1.message_resource.get(request)

        if not resp.success():
            print(f"下载图片失败: Code {resp.code}, Msg {resp.msg}")
            return None
        
        return resp.file

    def do_ocr(self, image_bytes):
        """对图片进行文字识别"""
        request = RecognizeBasicImageRequest.builder() \
            .request_body(lark.RecognizeBasicImageRequestBody.builder()
                          .image(image_bytes)
                          .build()) \
            .build()

        resp = self.client.ocr.v1.image.recognize_basic(request)

        if not resp.success():
            print(f"OCR识别失败: Code {resp.code}, Msg {resp.msg}")
            return ""
        
        return resp.data.text

    def write_bitable(self, text):
        """向多维表格写入一行记录"""
        fields = {"原始文本": text}  # 请确保您的表格里有一列的列名就叫“原始文本”
        record = AppTableRecord.builder().fields(fields).build()
        request = CreateAppTableRecordRequest.builder() \
            .app_token(self.bitable_app_token) \
            .table_id(self.table_id) \
            .request_body(record) \
            .build()

        resp = self.client.bitable.v1.app_table_record.create(request)
        
        if not resp.success():
            print(f"写入表格失败: Code {resp.code}, Msg {resp.msg}")
        else:
            print(f"成功写入表格: {text}")
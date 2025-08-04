import lark_oapi as lark
# 由于安装了 [all] 版本，这些路径现在都是有效的
from lark_oapi.api.im.v1 import GetMessageResourceRequest, GetMessageResourceResponse
from lark_oapi.api.ocr.v1 import RecognizeBasicImageRequest, RecognizeBasicImageRequestBody
from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest

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
            .path_params({
                "message_id": message_id,
                "file_key": message_id,
                "type": "image"
            }) \
            .build()
        
        resp: GetMessageResourceResponse = self.client.im.v1.message_resource.get(request)

        if resp is None or resp.code != 0:
            print(f"下载图片失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            return None
        
        return resp.file

    def do_ocr(self, image_bytes):
        """对图片进行文字识别"""
        body = RecognizeBasicImageRequestBody.builder().image(image_bytes).build()
        request = RecognizeBasicImageRequest.builder().request_body(body).build()

        resp = self.client.ocr.v1.image.recognize_basic(request)

        if resp is None or resp.code != 0:
            print(f"OCR识别失败: Code {getattr(resp, 'code', 'N/A')}, Msg {getattr(resp, 'msg', 'Unknown error')}")
            return ""
        
        return resp.data.text if resp.data and resp.data.text else ""


    def write_bitable(self, text):
        """向多维表格写入一行记录"""
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
        else:
            print(f"成功写入表格: '{text}'")

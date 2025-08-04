import lark_oapi as lark
# 核心SDK的导入
from lark_oapi.api.im.v1 import GetMessageResourceRequest, GetMessageResourceResponse
from lark_oapi.api.bitable.v1 import AppTableRecord, CreateAppTableRecordRequest
# 导入独立的OCR SDK
from lark_oapi.adapter.pysdk_ocr import OcrSdk

class FeishuClient:
    def __init__(self, app_id, app_secret, bitable_app_token, table_id):
        self.bitable_app_token = bitable_app_token
        self.table_id = table_id
        # 保存凭证，供两个SDK使用
        self.app_id = app_id
        self.app_secret = app_secret
        
        # 这个client用于处理“多维表格”和“消息”相关的API
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
        """对图片进行文字识别 (使用独立的 OCR SDK)"""
        try:
            # 每次调用时，实例化独立的OcrSdk客户端
            ocr_client = OcrSdk(
                app_id=self.app_id,
                app_secret=self.app_secret,
                domain=lark.DOMAIN_FEISHU # 指定使用飞书域名
            )
            # 直接调用 recognize 方法
            resp = ocr_client.recognize(image_bytes)

            if resp.code != 0:
                 print(f"OCR识别失败: Code {resp.code}, Msg {resp.msg}")
                 return ""
            
            # 返回识别出的文本
            return resp.data.text if resp.data and resp.data.text else ""

        except Exception as e:
            print(f"OCR SDK 调用时发生异常: {e}")
            return ""


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

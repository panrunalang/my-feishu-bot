当然，一个好的 README 是吸引贡献者和用户的第一步。根据我们整个调试过程和你项目的功能，我为你精心准备了一份 README 文件。

你只需要将下面的所有内容复制到一个名为 `README.md` 的文件里，然后把它放到你的 GitHub 项目根目录即可。

-----

# 飞书 AI 记账机器人 (Feishu AI Bookkeeping Bot)

这是一个部署在 [Render](https://render.com/) 上的飞书机器人，它能帮你轻松记账。你只需要向机器人发送文本消息或账单截图，它就能自动识别关键信息，并将结构化的数据存入飞书多维表格 (Bitable) 中。

告别手动输入，让 AI 成为你的私人记账助理！

## ✨ Demo

记账机器人会自动将聊天内容和图片票据解析并存入你指定的飞书多维表格中，最终效果如下：
\*\*

## 🚀 主要功能

  * **文本记账**: 直接发送文本消息（如“打车花了25块钱”），机器人会自动记录。
  * **图片识别 (AI核心)**: 发送包含账单、收据或发票的图片，机器人会：
      * 调用 **Google Cloud Vertex AI** 的 `Gemini` 多模态模型进行智能分析。
      * 自动提取**总金额、货币种类、消费项目**等关键信息。
      * 生成标准化的记账描述（例如：“中午吃饭花了15人民币”）。
  * **自动化入库**: 所有记账信息都会被自动添加为飞书多维表格中的一条新记录。
  * **即时反馈**: 记账成功或失败，机器人都会在聊天中给你发送一条即时消息。

## 🛠️ 工作流程

```mermaid
graph TD
    A[用户在飞书中发送消息] --> B{飞书机器人};
    B -->|Webhook| C[Render服务器 (Flask App)];
    subgraph C [Render服务器 (Flask App)]
        direction LR
        C1[接收事件] --> C2{判断消息类型};
        C2 -->|文本消息| C3[直接处理];
        C2 -->|图片消息| C4[调用Vertex AI];
    end
    C4 --> D[Google Vertex AI];
    D --> C4;
    C3 --> E[写入飞书多维表格];
    C4 --> E;
    E --> F[发送回复消息至飞书];
    F --> B;
```

## 部署指南

你可以通过以下步骤，轻松部署属于你自己的记账机器人。

### 前提条件

1.  一个**飞书**账号，并拥有创建企业应用的权限。
2.  一个**Google Cloud**账号（新用户有免费赠金，本项目消耗极低）。
3.  一个**GitHub**账号。
4.  一个**Render**账号。

### 步骤一：创建并配置飞书应用

1.  **创建应用**: 访问 [飞书开放平台](https://open.feishu.cn/app) 创建一个企业自建应用。
2.  **开通权限**:
      * 在“权限管理”页面，搜索并开通以下权限：
          * `im:message`
          * `im:message.group_at_msg`
          * `im:message.p2p_msg`
          * `im:message:send_as_bot`
          * `im:resource`
          * `bitable:app:readonly`
          * `bitable:app_table:readonly`
          * `bitable:app_table_record:readwrite`
3.  **创建多维表格**: 创建一个用于记账的[多维表格](https://www.google.com/search?q=https://www.feishu.cn/base)，并至少包含一个名为“原始文本”的文本列。
4.  **获取凭证和ID**:
      * 在“凭证与基础信息”页面，记下你的 **App ID** 和 **App Secret**。
      * 在你的多维表格中，根据[飞书官方文档](https://www.google.com/search?q=https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/get)指引，获取 **Bitable App Token** 和 **Table ID**。
5.  **发布应用**: 将应用发布到你的企业中。

### 步骤二：配置 Google Cloud (Vertex AI)

1.  **创建项目**: 访问 [Google Cloud Console](https://console.cloud.google.com/) 创建一个新项目。记下你的 **Project ID**。
2.  **启用API**: 在你的项目中，搜索并**启用 "Vertex AI API"**。
3.  **创建服务账号 (Service Account)**:
      * 在 "IAM & Admin" -\> "Service Accounts" 中创建一个新的服务账号。
      * 授予它 **"Vertex AI User"** 的角色。
      * 创建并下载该服务账号的 **JSON 密钥文件**。这个文件包含了你的程序访问GCP的凭证。

### 步骤三：部署到 Render

1.  **Fork 本项目**: 将此 GitHub 项目 Fork 到你自己的仓库中。

2.  **创建Web服务**: 在 Render 上，点击 "New" -\> "Web Service"，并连接到你刚刚 Fork 的仓库。

3.  **配置环境变量**: 在 "Environment" 标签页下，添加以下环境变量：
    | Key (键) | Value (值) | 说明 |
    | :--- | :--- | :--- |
    | `APP_ID` | (你的飞书App ID) | 来自步骤一 |
    | `APP_SECRET` | (你的飞书App Secret) | 来自步骤一 |
    | `BITABLE_APP_TOKEN` | (你的多维表格App Token) | 来自步骤一 |
    | `TABLE_ID` | (你的多维表格Table ID) | 来自步骤一 |
    | `GCP_PROJECT_ID` | (你的GCP项目ID) | 来自步骤二 |
    | `GCP_REGION` | `us-central1` | 建议使用此区域，因为模型可用性最好 |
    | `PYTHON_VERSION` | `3.11` | (或你希望使用的Python版本) |

4.  **配置机密文件 (Secret File)**:

      * 向下滚动到 "Secret Files" 部分，点击 "Add Secret File"。
      * **Filename/Path**: 填写 `google_credentials.json`。
      * **Contents**: 将步骤二中下载的 **JSON 密钥文件的全部内容**粘贴进去。

5.  **关联机密文件**: **非常重要！** 额外添加一个环境变量来告诉程序密钥文件的位置：
    | Key (键) | Value (值) |
    | :--- | :--- |
    | `GOOGLE_APPLICATION_CREDENTIALS` | `/etc/secrets/google_credentials.json` |

6.  **保存并部署**: 点击 "Save, rebuild, and deploy"。

### 步骤四：完成飞书配置

1.  部署成功后，复制你的 Render 服务的 URL (例如 `https://your-bot-name.onrender.com`)。
2.  回到飞书开放平台的应用配置页面，进入“事件订阅”。
3.  在“请求地址配置”中，填入你的 Webhook URL：`https://your-bot-name.onrender.com/webhook`。
4.  将机器人拉入你需要记账的群聊中，或者直接私聊它，开始使用！

## 🔧 项目结构

```
.
├── app.py          # Flask Web应用入口，处理飞书的Webhook事件
├── feishu.py       # 封装了所有与飞书和Vertex AI交互的逻辑
├── requirements.txt# 项目依赖库
└── docs/
    └── demo.png    # README中使用的示例图片
```

## 🤝 贡献

欢迎提出 Issue 或提交 Pull Request 来让这个项目变得更好！

## 📄 License

本项目采用 [MIT License](https://www.google.com/search?q=LICENSE) 开源。

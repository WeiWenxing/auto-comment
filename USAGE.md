# 使用教程

## 详细使用步骤

### 1. 安装库
使用 `pip` 安装本库：pip install auto_comment
### 2. 初始化 OpenAI 接口
在 Python 脚本中导入库并初始化 OpenAI 接口：import auto_comment

baseurl = "https://api.openai.com"
apikey = "your_openai_api_key"
model = "gpt - 3.5 - turbo"
auto_comment.your_library_name_init(baseurl, apikey, model)
### 3. 准备个人信息和目标网址
定义评论者的姓名、邮箱、网站和目标网址：name = "John Doe"
email = "johndoe@example.com"
website = "https://example.com"
url = "https://targetwebsite.com"
### 4. 调用 `send_comment` 函数
调用 `send_comment` 函数发送评论：result = auto_comment.send_comment(name, email, website, url)
if result:
    print("评论发送成功！")
else:
    print("评论发送失败，请检查相关信息。")
## 常见问题解答

### OpenAI 调用出错
- **原因**：可能是 API 密钥无效、模型不支持或网络问题。
- **解决方法**：检查 API 密钥是否正确，确保使用的模型是 OpenAI 支持的，检查网络连接。

### 评论发送失败
- **原因**：可能是目标网址无法访问、请求参数错误或服务器端问题。
- **解决方法**：检查目标网址是否有效，确保提供的姓名、邮箱、网站和评论内容符合目标网站的要求，联系目标网站管理员。

### 模型不支持
- **原因**：可能是使用了不支持的 OpenAI 模型。
- **解决方法**：查阅 OpenAI 文档，选择支持的模型。
    
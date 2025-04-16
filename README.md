# 自动评论 Python 库

## 项目简介
本库是一个可通过 `pip` 安装的 Python 库，用于自动生成并发送评论。用户在初始化库时需提供 OpenAI 接口的 `baseurl`、`apikey` 以及 `model`，之后可指定姓名、邮箱、网站和目标网址，库会根据目标网址内容利用 OpenAI 自动生成评论并发送到该网址。

## 安装方法
使用以下命令安装本库：pip install auto_comment
## 使用示例import auto_comment

# 初始化 OpenAI 接口
baseurl = "https://api.openai.com"
apikey = "your_openai_api_key"
model = "gpt - 3.5 - turbo"
auto_comment.your_library_name_init(baseurl, apikey, model)

# 填写个人信息和目标网址
name = "John Doe"
email = "johndoe@example.com"
website = "https://example.com"
url = "https://targetwebsite.com"

# 调用库的接口发送评论
result = auto_comment.send_comment(name, email, website, url)
if result:
    print("评论发送成功！")
else:
    print("评论发送失败，请检查相关信息。")
## 依赖说明
本库依赖以下库：
- `requests`：用于网页请求和评论发送。
- `beautifulsoup4`：用于网页内容解析。
- `openai`：用于调用 OpenAI 接口生成评论。

## 注意事项
- 请妥善保管你的 OpenAI API 密钥，避免泄露。
- 使用本库时请遵守 OpenAI 的使用条款。
- 选择合适的 OpenAI 模型，不同模型可能有不同的性能和成本。
    
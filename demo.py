import auto_comment

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
    
"""
Auto Comment Library
~~~~~~~~~~~~~~~~~~~
A library for auto-generating and posting comments using OpenAI.
"""

from .config import init_openai
from .comment import send_comment
from .playwright_comment import PlaywrightCommentSender

__version__ = '0.1.0'
# 添加新的发送评论方法
send_comment_playwright = PlaywrightCommentSender.send_comment
__all__ = ['init_openai', 'send_comment', 'send_comment_playwright']


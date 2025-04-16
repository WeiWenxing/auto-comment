"""
Auto Comment Library
~~~~~~~~~~~~~~~~~~~
A library for auto-generating and posting comments using OpenAI.
"""

from .config import init_openai
from .comment import send_comment

__version__ = '0.1.0'
__all__ = ['init_openai', 'send_comment']

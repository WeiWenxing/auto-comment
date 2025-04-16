from openai import OpenAI
from typing import Optional
from .config import OpenAIConfig
from .exceptions import CommentGenerationError

class CommentGenerator:
    @staticmethod
    def generate(content: str) -> str:
        """Generate comment using OpenAI API."""
        config = OpenAIConfig.get_instance()
        if not config.is_initialized():
            raise CommentGenerationError("OpenAI not initialized")

        try:
            client = OpenAI(
                base_url=config.baseurl,
                api_key=config.apikey
            )

            prompt = f"Please generate a comment based on the following content: {content}"
            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": "You are a professional commenter."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise CommentGenerationError(f"OpenAI API error: {e}")

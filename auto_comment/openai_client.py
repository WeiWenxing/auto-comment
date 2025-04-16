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

            system_prompt = """You are a regular internet user leaving comments on blogs or articles.
Please follow these guidelines:
- Write in the same language as the content you're commenting on
- Use a natural, down-to-earth tone
- Avoid exaggerated or marketing-style language
- Base your comment on specific points from the content
- Keep comments very brief (maximum 60 words)
- Share personal experiences when relevant, but keep it genuine
- Match the writing style and terminology of the original content
- Use only periods, commas and question marks for punctuation
- Do not use parentheses, brackets, or any other special characters
- Avoid emojis, special characters, or unusual symbols
- Write simple, direct sentences without any annotations"""

            user_prompt = f"""Please write a comment based on the following content.
Use the same language as the original content. Write naturally using only basic punctuation.
Do not use any parentheses, brackets, emojis or special characters.

Content:
{content}"""

            response = client.chat.completions.create(
                model=config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise CommentGenerationError(f"OpenAI API error: {e}")

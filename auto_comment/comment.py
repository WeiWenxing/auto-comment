import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .content import ContentExtractor
from .openai_client import CommentGenerator
from .exceptions import CommentError

class CommentSender:
    COMMON_COMMENT_SELECTORS = {
        'name_input': [
            'input[name="author"]',
            'input[name="name"]',
            'input[id*="name"]',
            'input[class*="name"]'
        ],
        'email_input': [
            'input[name="email"]',
            'input[type="email"]',
            'input[id*="email"]'
        ],
        'website_input': [
            'input[name="url"]',
            'input[name="website"]',
            'input[id*="website"]',
            'input[id*="url"]'
        ],
        'comment_input': [
            'textarea[name="comment"]',
            'textarea[id*="comment"]',
            'div[role="textbox"]'
        ],
        'submit_button': [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[id*="submit"]',
            'button[class*="submit"]',
            'input[value*="Submit"]',
            'button:contains("Submit")',
            'button:contains("Post")'
        ]
    }

    @staticmethod
    def find_element(driver, selectors):
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element.is_displayed():
                    return element
            except (TimeoutException, NoSuchElementException):
                continue
        return None

    @staticmethod
    def send_comment(name: str, email: str, website: str, url: str, content: Optional[str] = None) -> bool:
        """
        Send comment to the target URL using browser automation.

        Args:
            name: Commenter's name
            email: Commenter's email
            website: Commenter's website
            url: Target URL to post comment
            content: Optional comment content. If not provided, content will be auto-generated

        Returns:
            bool: True if comment was sent successfully, False otherwise
        """
        if not all([name, email, website, url]):
            logging.error("Incomplete information provided")
            return False

        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)

            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # 如果没有提供评论内容，则自动生成
                if content is None:
                    page_content = ContentExtractor.extract(url)
                    comment = CommentGenerator.generate(page_content)
                else:
                    comment = content

                # 查找并填写评论表单
                name_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['name_input'])
                email_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['email_input'])
                website_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['website_input'])
                comment_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['comment_input'])
                submit_button = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['submit_button'])

                if not all([name_field, email_field, comment_field, submit_button]):
                    raise CommentError("Could not find all required comment form fields")

                # 填写表单
                name_field.send_keys(name)
                email_field.send_keys(email)
                if website_field:
                    website_field.send_keys(website)
                comment_field.send_keys(comment)

                # 添加随机延迟，模拟人类行为
                import random
                import time
                time.sleep(random.uniform(1, 3))

                # 提交评论
                submit_button.click()

                # 等待提交完成
                time.sleep(2)

                logging.info("Comment sent successfully")
                return True

            finally:
                driver.quit()

        except Exception as e:
            logging.error(f"Failed to send comment: {e}")
            return False

# 模块级别的公共接口
def send_comment(name: str, email: str, website: str, url: str, content: Optional[str] = None) -> bool:
    """
    Public interface for sending comments.

    Args:
        name: Commenter's name
        email: Commenter's email
        website: Commenter's website
        url: Target URL to post comment
        content: Optional comment content. If not provided, content will be auto-generated

    Returns:
        bool: True if comment was sent successfully, False otherwise
    """
    return CommentSender.send_comment(name, email, website, url, content)



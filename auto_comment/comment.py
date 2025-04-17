import os
import asyncio
import logging
import random
import time
import tempfile
import uuid
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .content import ContentExtractor
from .openai_client import CommentGenerator
from .exceptions import CommentError
from tenacity import retry, stop_after_attempt, wait_exponential

class CommentSender:
    COMMON_COMMENT_SELECTORS = {
        'name': [
            'input[name="author"]',
            'input[name="name"]',
            'input[id*="name"]',
            'input[class*="name"]'
        ],
        'email': [
            'input[name="email"]',
            'input[type="email"]',
            'input[id*="email"]'
        ],
        'website': [
            'input[name="url"]',
            'input[name="website"]',
            'input[id*="website"]',
            'input[id*="url"]'
        ],
        'comment': [
            'textarea[name="comment"]',
            'textarea[id*="comment"]',
            'div[role="textbox"]'
        ],
        'submit_button': [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[id*="submit"]',
            'button[class*="submit"]',
            'input[name="submit"]',
            'input[id*="submit"]',
            'input[class*="submit"]',
            'button[name="submit"]',
            '#submit',
            '.submit',
            'input[value*="Post"]',
            'button:contains("Post")',
            'input[value*="Submit"]',
            'button:contains("Submit")',
            'input[value*="Comment"]',
            'button:contains("Comment")'
        ]
    }

    @staticmethod
    def find_element(driver, selectors):
        """Try multiple selectors to find an element."""
        for selector in selectors:
            try:
                logging.debug(f"Trying to find element with selector: {selector}")
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if element.is_displayed():
                    logging.info(f"Found visible element with selector: {selector}")
                    return element
            except (TimeoutException, NoSuchElementException) as e:
                logging.debug(f"Selector {selector} failed: {str(e)}")
                continue
        logging.warning("No matching element found after trying all selectors")
        return None

    @staticmethod
    @retry(stop=stop_after_attempt(1), wait=wait_exponential(multiplier=1, min=4, max=10))
    def submit_comment_form(driver, form_elements: dict, name: str, email: str, website: str, content: str) -> bool:
        """单独处理表单提交逻辑，包含重试机制"""
        try:
            # 清空之前的输入
            for field in ['name_field', 'email_field', 'website_field', 'comment_field']:
                if form_elements[field]:
                    form_elements[field].clear()

            # 重新填写表单
            form_elements['name_field'].send_keys(name)
            form_elements['email_field'].send_keys(email)
            if form_elements['website_field']:
                form_elements['website_field'].send_keys(website)
            form_elements['comment_field'].send_keys(content)

            # 添加随机延迟
            time.sleep(random.uniform(1, 3))

            # 尝试不同的提交方法
            submit_methods = [
                lambda: form_elements['submit_button'].click(),
                lambda: driver.execute_script("arguments[0].click();", form_elements['submit_button']),
                lambda: ActionChains(driver).move_to_element(form_elements['submit_button']).click().perform()
            ]

            for submit_method in submit_methods:
                try:
                    submit_method()
                    time.sleep(5)  # 等待提交完成
                    return True
                except Exception as e:
                    logging.warning(f"Submit method failed: {str(e)}")
                    continue

            return False

        except Exception as e:
            logging.error(f"Form submission failed: {str(e)}")
            raise  # 重新抛出异常以触发重试

    @staticmethod
    def send_comment(name: str, email: str, website: str, url: str, content: Optional[str] = None) -> bool:
        """Send comment to the target URL using browser automation."""
        if not all([name, email, website, url]):
            logging.error(f"Incomplete information provided: name={name}, email={email}, website={website}, url={url}")
            return False

        driver = None
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix=f'chrome_user_data_{uuid.uuid4().hex}_')

            options = webdriver.ChromeOptions()

            # 基础配置
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            # 添加稳定性配置
            options.add_argument('--disable-gpu')
            options.add_argument('--remote-debugging-port=9222')  # 添加调试端口
            options.add_argument(f'--user-data-dir={temp_dir}')  # 指定用户数据目录

            # 减少配置项，提高稳定性
            options.add_argument('--window-size=1024,768')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            # 简化性能配置
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'profile.managed_default_content_settings.javascript': 1,
            }
            options.add_experimental_option('prefs', prefs)

            # 添加服务配置
            service = webdriver.ChromeService()

            logging.info("Creating Chrome WebDriver instance...")
            driver = webdriver.Chrome(
                options=options,
                service=service
            )

            # 移除快速检查，直接访问目标URL
            logging.info(f"Navigating to target URL: {url}")
            driver.get(url)

            # 生成评论内容
            if content is None:
                logging.info("Generating comment...")
                page_content = ContentExtractor.extract(url)
                content = CommentGenerator.generate(page_content)

            # 查找表单元素
            form_elements = {
                'name_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['name']),
                'email_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['email']),
                'website_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['website']),
                'comment_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['comment']),
                'submit_button': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['submit_button'])
            }

            # 记录找到的元素状态
            for field_name, element in form_elements.items():
                logging.debug(f"Form element '{field_name}' found: {element is not None}")

            if not all([form_elements['name_field'], form_elements['email_field'],
                       form_elements['comment_field'], form_elements['submit_button']]):
                missing_fields = [k for k, v in form_elements.items() if not v]
                raise CommentError(f"Could not find required comment form fields: {', '.join(missing_fields)}")

            # 调用带重试机制的提交方法
            return CommentSender.submit_comment_form(driver, form_elements, name, email, website, content)

        except Exception as e:
            logging.error(f"Error in comment submission process: {str(e)}", exc_info=True)
            return False

        finally:
            # 确保资源清理的顺序：先关闭driver，再删除临时目录
            if driver:
                try:
                    driver.quit()
                    logging.info("Browser closed successfully")
                except Exception as e:
                    logging.error(f"Error while closing browser: {str(e)}")

            if temp_dir and os.path.exists(temp_dir):
                try:
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=False)  # 改为False以便看到具体错误
                    logging.info(f"Temporary directory cleaned up: {temp_dir}")
                except Exception as e:
                    logging.error(f"Error cleaning up temporary directory {temp_dir}: {str(e)}")
                    # 如果常规删除失败，尝试强制删除
                    try:
                        os.system(f'rm -rf "{temp_dir}"')
                        logging.info(f"Temporary directory force cleaned up: {temp_dir}")
                    except Exception as e2:
                        logging.error(f"Force cleanup also failed for {temp_dir}: {str(e2)}")

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














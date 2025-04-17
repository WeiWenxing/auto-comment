import logging
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

# 设置更详细的日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s'
)

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
    def send_comment(name: str, email: str, website: str, url: str, content: Optional[str] = None) -> bool:
        """Send comment to the target URL using browser automation."""
        if not all([name, email, website, url]):
            logging.error("Incomplete information provided")
            return False

        driver = None
        try:
            # 1. 初始化浏览器（只执行一次）
            logging.info("Initializing Chrome WebDriver...")
            options = webdriver.ChromeOptions()
            # ... (保持原有的options设置) ...
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)
            driver.implicitly_wait(20)

            # 2. 获取页面内容（只执行一次）
            logging.info("Navigating to target URL...")
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # 3. 生成评论内容（只执行一次）
            if content is None:
                logging.info("Generating comment...")
                page_content = ContentExtractor.extract(url)
                content = CommentGenerator.generate(page_content)

            # 4. 查找表单元素（只执行一次）
            form_elements = {
                'name_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['name']),
                'email_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['email']),
                'website_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['website']),
                'comment_field': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['comment']),
                'submit_button': CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['submit_button'])
            }

            if not all([form_elements['name_field'], form_elements['email_field'],
                       form_elements['comment_field'], form_elements['submit_button']]):
                raise CommentError("Could not find all required comment form fields")

            # 5. 填写表单并提交（这部分需要重试机制）
            max_submit_retries = 3
            for attempt in range(max_submit_retries):
                try:
                    logging.info(f"Submission attempt {attempt + 1} of {max_submit_retries}")

                    # 清空之前的输入（如果是重试）
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
                            # 检查提交是否成功（可以添加具体的成功判断逻辑）
                            return True
                        except Exception as e:
                            logging.warning(f"Submit method failed: {str(e)}")
                            continue

                    # 如果所有提交方法都失败，等待后重试
                    if attempt < max_submit_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logging.info(f"Waiting {wait_time} seconds before next attempt...")
                        time.sleep(wait_time)

                except Exception as e:
                    logging.error(f"Form submission attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_submit_retries - 1:
                        return False

            return False

        except Exception as e:
            logging.error(f"Error in comment submission process: {str(e)}")
            return False

        finally:
            if driver:
                try:
                    driver.quit()
                    logging.info("Browser closed successfully")
                except Exception as e:
                    logging.error(f"Error while closing browser: {str(e)}")

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

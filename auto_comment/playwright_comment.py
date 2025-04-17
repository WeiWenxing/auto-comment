import logging
from typing import Optional, Dict
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential

from .content import ContentExtractor
from .openai_client import CommentGenerator
from .exceptions import CommentError

class PlaywrightCommentSender:
    """使用 Playwright 实现的评论发送器"""

    COMMON_SELECTORS = {
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
        'submit': [
            'input[type="submit"]',
            'button[type="submit"]',
            'button[id*="submit"]',
            'button:has-text("Submit")',
            'button:has-text("Post")',
            'button:has-text("Comment")'
        ]
    }

    @staticmethod
    def _find_element(page: Page, selectors: list) -> Optional[str]:
        """尝试多个选择器找到元素"""
        for selector in selectors:
            try:
                # 等待元素可见
                if page.wait_for_selector(selector, state='visible', timeout=5000):
                    return selector
            except PlaywrightTimeoutError:
                continue
        return None

    @staticmethod
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _fill_form(page: Page, form_selectors: Dict[str, str], data: Dict[str, str]) -> bool:
        """填写并提交表单"""
        try:
            # 填写表单字段
            for field, selector in form_selectors.items():
                if selector and field in data:
                    # 确保元素在视图中
                    page.locator(selector).scroll_into_view_if_needed()
                    # 清除并填写
                    page.fill(selector, data[field])
                    logging.debug(f"Filled {field} with {data[field]}")

            # 提交表单
            submit_selector = form_selectors['submit']
            logging.info(f"Attempting to submit form with selector: {submit_selector}")

            if submit_selector:
                # 等待提交按钮可点击
                logging.debug("Waiting for submit button to be visible...")
                submit_button = page.wait_for_selector(submit_selector, state='visible')

                if submit_button:
                    logging.info("Submit button found, attempting to click...")
                    # 尝试不同的点击方法
                    try:
                        # 方法1: 直接点击
                        logging.debug("Attempting direct click...")
                        submit_button.click()
                        logging.info("Direct click successful")
                    except Exception as e:
                        logging.warning(f"Direct click failed: {str(e)}")
                        try:
                            # 方法2: JavaScript点击
                            logging.debug("Attempting JavaScript click...")
                            page.evaluate('(element) => element.click()', submit_button)
                            logging.info("JavaScript click successful")
                        except Exception as e:
                            logging.warning(f"JavaScript click failed: {str(e)}")
                            # 方法3: dispatch事件
                            logging.debug("Attempting event dispatch...")
                            page.evaluate('''(element) => {
                                element.dispatchEvent(new MouseEvent('click', {
                                    bubbles: true,
                                    cancelable: true,
                                    view: window
                                }));
                            }''', submit_button)
                            logging.info("Event dispatch completed")

                    logging.debug("Waiting for page load state...")
                    # 等待网络请求完成
                    page.wait_for_load_state('networkidle')
                    logging.info("Page load completed after form submission")
                    return True
                else:
                    logging.error("Submit button not visible after wait")
            else:
                logging.error("No submit selector found")
            return False

        except Exception as e:
            logging.error(f"Form submission failed: {str(e)}")
            raise

    @staticmethod
    def send_comment(name: str, email: str, website: str, url: str, content: Optional[str] = None) -> bool:
        """发送评论的主方法"""
        if not all([name, email, website, url]):
            logging.error("Missing required fields")
            return False

        with sync_playwright() as p:
            try:
                # 启动浏览器时添加更多真实的参数
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-automation',
                        '--disable-infobars',
                    ]
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    color_scheme='light',
                    has_touch=True,
                    is_mobile=False,
                    device_scale_factor=1,
                )
                page = context.new_page()

                # 访问页面
                page.goto(url, wait_until='load')

                # 如果没有提供评论内容，则生成
                if content is None:
                    page_content = ContentExtractor.extract(url)
                    content = CommentGenerator.generate(page_content)

                # 查找表单元素
                form_selectors = {
                    'name': PlaywrightCommentSender._find_element(page, PlaywrightCommentSender.COMMON_SELECTORS['name']),
                    'email': PlaywrightCommentSender._find_element(page, PlaywrightCommentSender.COMMON_SELECTORS['email']),
                    'website': PlaywrightCommentSender._find_element(page, PlaywrightCommentSender.COMMON_SELECTORS['website']),
                    'comment': PlaywrightCommentSender._find_element(page, PlaywrightCommentSender.COMMON_SELECTORS['comment']),
                    'submit': PlaywrightCommentSender._find_element(page, PlaywrightCommentSender.COMMON_SELECTORS['submit'])
                }

                # 检查必要字段
                if not all([form_selectors['name'], form_selectors['email'],
                          form_selectors['comment'], form_selectors['submit']]):
                    raise CommentError("Could not find all required form fields")

                # 填写并提交表单
                return PlaywrightCommentSender._fill_form(page, form_selectors, {
                    'name': name,
                    'email': email,
                    'website': website,
                    'comment': content
                })

            except Exception as e:
                logging.error(f"Comment submission failed: {str(e)}")
                return False

            finally:
                if 'browser' in locals():
                    browser.close()




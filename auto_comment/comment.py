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

        driver = None
        try:
            logging.info("Starting comment submission process...")
            logging.info(f"Target URL: {url}")
            
            logging.info("Initializing Chrome options...")
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            
            logging.info("Creating Chrome WebDriver instance...")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(30)
            
            logging.info("Navigating to target URL...")
            driver.get(url)
            
            logging.info("Waiting for page body to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logging.info("Page body loaded successfully")

            if content is None:
                logging.info("No content provided, generating comment...")
                page_content = ContentExtractor.extract(url)
                logging.info("Content extracted, generating comment using OpenAI...")
                comment = CommentGenerator.generate(page_content)
                logging.info("Comment generated successfully")
            else:
                logging.info("Using provided comment content")
                comment = content

            logging.info("Looking for comment form fields...")
            
            logging.info("Searching for name input field...")
            name_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['name_input'])
            
            logging.info("Searching for email input field...")
            email_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['email_input'])
            
            logging.info("Searching for website input field...")
            website_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['website_input'])
            
            logging.info("Searching for comment input field...")
            comment_field = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['comment_input'])
            
            logging.info("Searching for submit button...")
            submit_button = CommentSender.find_element(driver, CommentSender.COMMON_COMMENT_SELECTORS['submit_button'])

            if not all([name_field, email_field, comment_field, submit_button]):
                missing_fields = []
                if not name_field: missing_fields.append("name field")
                if not email_field: missing_fields.append("email field")
                if not comment_field: missing_fields.append("comment field")
                if not submit_button: missing_fields.append("submit button")
                logging.error(f"Missing required form fields: {', '.join(missing_fields)}")
                raise CommentError("Could not find all required comment form fields")

            logging.info("All required form fields found, filling form...")
            
            logging.info("Entering name...")
            name_field.send_keys(name)
            
            logging.info("Entering email...")
            email_field.send_keys(email)
            
            if website_field:
                logging.info("Entering website...")
                website_field.send_keys(website)
            
            logging.info("Entering comment...")
            comment_field.send_keys(comment)

            logging.info("Adding random delay to simulate human behavior...")
            import random
            import time
            delay = random.uniform(1, 3)
            logging.info(f"Waiting for {delay:.2f} seconds...")
            time.sleep(delay)

            logging.info("Preparing to click submit button...")
            
            # 尝试多种方法点击提交按钮
            try:
                # 方法1：使用JavaScript点击
                logging.info("Attempting to click submit button using JavaScript...")
                driver.execute_script("arguments[0].click();", submit_button)
            except Exception as e:
                logging.warning(f"JavaScript click failed: {str(e)}")
                try:
                    # 方法2：滚动到元素可见
                    logging.info("Scrolling to make submit button visible...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(1)  # 等待滚动完成
                    
                    # 方法3：移除可能的遮挡元素
                    logging.info("Attempting to remove potential overlays...")
                    driver.execute_script("""
                        var elements = document.querySelectorAll('[data-type="_mgwidget"], .overlay, .modal, .popup');
                        for(var i=0; i<elements.length; i++){
                            elements[i].remove();
                        }
                    """)
                    
                    # 方法4：等待元素可点击
                    logging.info("Waiting for submit button to be clickable...")
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, submit_button.get_attribute("css")))
                    )
                    
                    # 方法5：使用ActionChains点击
                    logging.info("Attempting to click submit button using ActionChains...")
                    ActionChains(driver).move_to_element(submit_button).click().perform()
                except Exception as e:
                    logging.error(f"All click attempts failed: {str(e)}")
                    raise

            logging.info("Submit button clicked successfully")
            logging.info("Waiting for submission to complete...")
            time.sleep(5)

            logging.info("Comment submitted successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to send comment: {str(e)}", exc_info=True)
            return False
        
        finally:
            if driver:
                logging.info("Cleaning up: closing browser...")
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






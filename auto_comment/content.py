import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging
from .exceptions import ContentExtractionError

class ContentExtractor:
    @staticmethod
    def extract(url: str) -> str:
        """Extract content from the given URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',  # 移除 br 编码，只使用 gzip 和 deflate
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Cookie': ''
            }

            logging.info(f"Attempting to fetch URL: {url}")
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                verify=True,
                allow_redirects=True
            )

            logging.info(f"Response status code: {response.status_code}")
            logging.info(f"Response headers: {dict(response.headers)}")

            response.raise_for_status()

            # 确保响应内容使用正确的编码
            if response.encoding is None:
                response.encoding = response.apparent_encoding

            # 记录使用的编码
            logging.info(f"Response encoding: {response.encoding}")

            # 解码响应内容
            try:
                content_text = response.text
                logging.info(f"Response content preview: {content_text[:200]}")
            except UnicodeDecodeError as e:
                logging.warning(f"Unicode decode error: {e}, trying with different encodings")
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252', 'gbk', 'gb2312']
                for encoding in encodings:
                    try:
                        content_text = response.content.decode(encoding)
                        logging.info(f"Successfully decoded content using {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ContentExtractionError("Failed to decode response content with any known encoding")

            soup = BeautifulSoup(content_text, 'html.parser')

            # 首先尝试提取标题
            title = None
            title_selectors = [
                ('h1', {'class_': ['entry-title', 'post-title', 'article-title', 'title']}),
                ('h1', {}),
                ('h2', {'class_': ['entry-title', 'post-title']}),
                ('title', {}),
                ('.post-title', {}),
                ('.entry-title', {})
            ]

            for tag, attrs in title_selectors:
                element = soup.find(tag, attrs)
                if element and element.text.strip():
                    title = element.text.strip()
                    logging.info(f"Found title using selector: {tag} {attrs}")
                    break

            # 移除不需要的元素
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()

            # 尝试找到主要内容区域
            main_content = None

            content_selectors = [
                ('article', {}),
                ('div', {'class_': ['post-content', 'entry-content', 'article-content', 'content', 'single-content']}),
                ('main', {}),
                ('div', {'id': ['content', 'main-content', 'post-content']}),
                ('div', {'class_': ['post', 'article', 'blog-post']}),
                ('div', {'itemprop': 'articleBody'}),
                ('.post-content', {}),
                ('.entry-content', {}),
                ('.article-content', {})
            ]

            for tag, attrs in content_selectors:
                elements = soup.find_all(tag, attrs)
                for element in elements:
                    if element and element.text.strip():
                        logging.info(f"Found content using selector: {tag} {attrs}")
                        main_content = element
                        break
                if main_content:
                    break

            if not main_content:
                logging.warning("No specific content container found, using body")
                main_content = soup.find('body')

            if not main_content:
                logging.error("No content found in the page")
                return "Failed to extract content"

            # 组合标题和内容
            content_parts = []
            if title:
                content_parts.append(f"Title: {title}")
                logging.info(f"Found title: {title}")

            main_text = main_content.get_text(separator='\n', strip=True)
            if main_text:
                content_parts.append(main_text)

            # 合并内容并清理
            content = '\n\n'.join(content_parts)

            # 清理多余的空行
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            content = '\n'.join(lines)

            logging.info(f"Extracted content length: {len(content)} characters")

            if len(content) < 100:
                logging.warning("Extracted content seems too short")
                logging.debug(f"Full extracted content: {content}")

            return content

        except requests.RequestException as e:
            error_msg = f"Failed to access URL {url}: {str(e)}"
            logging.error(error_msg)
            raise ContentExtractionError(error_msg)
        except Exception as e:
            error_msg = f"Error extracting content: {str(e)}"
            logging.error(error_msg)
            raise ContentExtractionError(error_msg)

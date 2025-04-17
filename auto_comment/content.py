import requests
from bs4 import BeautifulSoup
from typing import Optional
from .exceptions import ContentExtractionError

class ContentExtractor:
    @staticmethod
    def extract(url: str) -> str:
        """Extract content from the given URL."""
        try:
            # 添加更完整的请求头，模拟真实浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                verify=True,  # SSL验证
                allow_redirects=True  # 允许重定向
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 移除不需要的元素
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()

            # 尝试找到主要内容区域
            main_content = None

            # 常见的内容容器
            content_candidates = [
                soup.find('article'),
                soup.find(class_='post-content'),
                soup.find(class_='entry-content'),
                soup.find('main'),
                soup.find(id='content'),
                soup.find(class_='content')
            ]

            # 使用第一个找到的有效容器
            for candidate in content_candidates:
                if candidate and candidate.text.strip():
                    main_content = candidate
                    break

            # 如果没找到特定容器，使用body
            if not main_content:
                main_content = soup.find('body')

            if not main_content:
                return "Failed to extract content"

            # 获取文本并清理
            content = main_content.get_text(separator='\n', strip=True)

            # 清理多余的空行
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            content = '\n'.join(lines)

            return content

        except requests.RequestException as e:
            raise ContentExtractionError(f"Failed to access URL {url}: {e}")
        except Exception as e:
            raise ContentExtractionError(f"Error extracting content: {e}")

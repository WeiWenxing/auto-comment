import os
import asyncio
from asyncio import Semaphore
from typing import List, Dict
import json
from datetime import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv
from auto_comment import init_openai, send_comment_playwright
from auto_comment.content import ContentExtractor
from auto_comment.openai_client import CommentGenerator
from tenacity import retry, stop_after_attempt, wait_exponential

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(f'playwright_comments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def process_url(url: str, name: str, email: str, website: str, semaphore: Semaphore) -> Dict:
    """异步处理单个URL的评论发送"""
    async with semaphore:
        result = {
            'url': url,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'success': False,
            'error': None
        }

        try:
            logging.info(f"Processing URL: {url}")

            if not all([name, email, website]):
                result['error'] = "Missing required commenter information"
                return result

            # 提取内容并生成评论
            page_content = ContentExtractor.extract(url)
            comment_content = CommentGenerator.generate(page_content)
            result['comment'] = comment_content

            # 记录生成的评论内容
            logging.info(f"Generated comment for {url}:")
            logging.info("-" * 50)
            logging.info(comment_content)
            logging.info("-" * 50)

            # 在新的进程中运行Playwright
            loop = asyncio.get_event_loop()
            comment_result = await loop.run_in_executor(
                None,
                send_comment_playwright,
                name, email, website, url, comment_content
            )

            if not comment_result:
                result['error'] = "Comment submission failed"
                logging.error(f"Failed to comment on {url}: Comment submission failed")
                return result

            result['success'] = True
            return result

        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            logging.error(f"Failed to comment on {url}: {error_msg}")
            return result

async def batch_comment(urls: List[str], name: str, email: str, website: str) -> List[Dict]:
    """异步处理所有URL，使用合理的并发数"""
    # 设置合理的并发数，避免资源耗尽
    max_concurrent = min(os.cpu_count() or 1, 4)  # 最多4个并发
    semaphore = Semaphore(max_concurrent)

    # 创建一个锁用于同步 Playwright 操作
    playwright_lock = asyncio.Lock()

    async def process_url_with_lock(url: str) -> Dict:
        # 并发进行内容提取和评论生成
        async with semaphore:
            result = {
                'url': url,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': False,
                'error': None
            }

            try:
                # 提取内容并生成评论
                page_content = ContentExtractor.extract(url)
                comment_content = CommentGenerator.generate(page_content)
                result['comment'] = comment_content

                # 串行执行 Playwright 操作
                async with playwright_lock:
                    loop = asyncio.get_event_loop()
                    comment_result = await loop.run_in_executor(
                        None,
                        send_comment_playwright,
                        name, email, website, url, comment_content
                    )

                    if not comment_result:
                        result['error'] = "Comment submission failed"
                        logging.error(f"Failed to comment on {url}: Comment submission failed")
                        return result

                result['success'] = True
                return result

            except Exception as e:
                error_msg = str(e)
                result['error'] = error_msg
                logging.error(f"Failed to comment on {url}: {error_msg}")
                return result

    logging.info(f"Starting batch processing with {max_concurrent} concurrent tasks")
    tasks = [process_url_with_lock(url) for url in urls]
    return await asyncio.gather(*tasks)

def load_urls(filepath: str) -> List[str]:
    """从文件加载URL列表并随机排序"""
    import random
    with open(filepath, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    random.shuffle(urls)  # 随机打乱顺序
    return urls

def save_results(results: List[Dict], filepath: str):
    """保存处理结果到CSV文件"""
    import csv
    
    # 分离成功和失败的结果
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    # 保存成功结果
    success_path = f'{filepath}_success.csv'
    with open(success_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', '时间戳', '评论内容'])
        for r in successful:
            writer.writerow([r['url'], r['timestamp'], r.get('comment', '')])

    # 保存失败结果
    fail_path = f'{filepath}_failed.csv'
    with open(fail_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['URL', '时间戳', '错误信息'])
        for r in failed:
            writer.writerow([r['url'], r['timestamp'], r.get('error', '')])

    # 保存失败的URL到单独文件
    with open('failed_urls.txt', 'w', encoding='utf-8') as f:
        for r in failed:
            f.write(f"{r['url']}\n")

async def main():
    # 加载环境变量
    load_dotenv()

    # 获取必要的配置
    baseurl = os.getenv('OPENAI_API_BASE')
    apikey = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    name = os.getenv('COMMENTER_NAME')
    email = os.getenv('COMMENTER_EMAIL')
    website = os.getenv('COMMENTER_WEBSITE')

    # 检查必要的环境变量
    required_vars = {
        'OPENAI_API_BASE': baseurl,
        'OPENAI_API_KEY': apikey,
        'COMMENTER_NAME': name,
        'COMMENTER_EMAIL': email,
        'COMMENTER_WEBSITE': website
    }

    missing_vars = [var for var, val in required_vars.items() if not val]
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    # 初始化OpenAI
    init_openai(baseurl, apikey, model)

    # 获取输入文件路径
    urls_file = input("Enter the path to the URLs file (default: urls.txt): ").strip() or "urls.txt"
    if not os.path.exists(urls_file):
        logging.error(f"File not found: {urls_file}")
        return

    # 加载URL列表
    urls = load_urls(urls_file)
    if not urls:
        logging.error("No URLs found in the input file")
        return

    logging.info(f"Found {len(urls)} URLs to process")

    # 批量处理URL
    results = await batch_comment(urls, name, email, website)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_results(results, f'playwright_results_{timestamp}')

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    logging.info(f"\nProcessing completed:")
    logging.info(f"Total URLs: {len(urls)}")
    logging.info(f"Successful: {success_count}")
    logging.info(f"Failed: {len(urls) - success_count}")

if __name__ == "__main__":
    asyncio.run(main())
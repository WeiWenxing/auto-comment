import os
import asyncio
from asyncio import Semaphore
import aiohttp
from dotenv import load_dotenv
from typing import List, Dict
import json
from datetime import datetime
import logging
import random
from pathlib import Path
from auto_comment import init_openai, send_comment
from auto_comment.content import ContentExtractor
from auto_comment.openai_client import CommentGenerator
from tenacity import retry, stop_after_attempt, wait_exponential

# 定义名字和邮箱域名列表
NAMES = [
    'Alex', 'Amy', 'Ben', 'Eva', 'Finn',
    'Gray', 'Hope', 'Jack', 'Kate', 'Luke',
    'Max', 'Mia', 'Nick', 'Noah', 'Ryan',
    'Sam', 'Sky', 'Tia', 'Viva', 'Zara'
]

EMAIL_DOMAINS = [
    '@gmail.com',
    '@yahoo.com',
    '@hotmail.com',
    '@outlook.com',
    '@aol.com'
]

def get_random_commenter_info() -> tuple:
    """生成随机的评论者名字和邮箱"""
    name = random.choice(NAMES)
    email = name.lower() + random.choice(EMAIL_DOMAINS)
    return name, email

# 加载环境变量
load_dotenv()

# 获取评论者信息
COMMENTER_NAME = os.getenv('COMMENTER_NAME')
COMMENTER_EMAIL = os.getenv('COMMENTER_EMAIL')
COMMENTER_WEBSITE = os.getenv('COMMENTER_WEBSITE')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(f'comments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def batch_comment(urls: List[str], website: str) -> List[Dict]:
    """异步处理所有URL，使用合理的并发数"""
    # 设置合理的并发数，避免资源耗尽
    max_concurrent = min(os.cpu_count() or 1, 4)  # 最多4个并发
    semaphore = Semaphore(max_concurrent)

    # 创建一个锁用于同步 Selenium 操作
    selenium_lock = asyncio.Lock()

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

                # 串行执行 Selenium 操作
                async with selenium_lock:
                    name, email = get_random_commenter_info()
                    loop = asyncio.get_event_loop()
                    comment_result = await loop.run_in_executor(
                        None,
                        send_comment,
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
    """保存处理结果到CSV文件，分别保存成功和失败的结果"""
    import csv
    from datetime import datetime

    # 分离成功和失败的结果
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    # 添加时间戳
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for result in results:
        result['timestamp'] = current_time

    # 从原始文件路径中获取基础部分
    base_path = Path(filepath).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 生成成功和失败结果的文件路径
    successful_path = f'{base_path}_successful_{timestamp}.csv'
    failed_path = f'{base_path}_failed_{timestamp}.csv'

    # 保存成功的结果
    if successful_results:
        with open(successful_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['URL', '时间戳', '评论内容', '详情'])
            # 写入数据
            for result in successful_results:
                writer.writerow([
                    result['url'],
                    result['timestamp'],
                    result.get('comment', ''),
                    json.dumps(result.get('details', ''), ensure_ascii=False)
                ])
        logging.info(f"Successful results saved to: {successful_path}")

    # 保存失败的结果
    if failed_results:
        with open(failed_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['URL', '时间戳', '评论内容', '错误信息'])
            # 写入数据
            for result in failed_results:
                writer.writerow([
                    result['url'],
                    result['timestamp'],
                    result.get('comment', ''),
                    result.get('error', '')
                ])
        logging.info(f"Failed results saved to: {failed_path}")

        # 保存失败的URL到txt文件
        fail_urls_path = 'fail-urls.txt'
        with open(fail_urls_path, 'w', encoding='utf-8') as f:
            f.write("# 失败的URL列表\n")
            for result in failed_results:
                f.write(f"{result['url']}\n")
        logging.info(f"Failed URLs saved to: {fail_urls_path}")

async def main():
    # 加载环境变量
    load_dotenv()

    # 获取必要的配置
    baseurl = os.getenv('OPENAI_API_BASE')
    apikey = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

    website = os.getenv('COMMENTER_WEBSITE')

    # 检查必要的环境变量
    required_vars = {
        'OPENAI_API_BASE': baseurl,
        'OPENAI_API_KEY': apikey,
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
    results = await batch_comment(urls, website)

    # 保存结果
    output_file = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    save_results(results, output_file)

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    logging.info(f"\nProcessing completed:")
    logging.info(f"Total URLs: {len(urls)}")
    logging.info(f"Successful: {success_count}")
    logging.info(f"Failed: {len(urls) - success_count}")
    logging.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())








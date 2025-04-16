import argparse
import sys
from auto_comment import init_openai
from auto_comment.content import ContentExtractor
from auto_comment.openai_client import CommentGenerator

def main():
    parser = argparse.ArgumentParser(description='Test content extraction and OpenAI comment generation')
    
    # OpenAI 配置参数
    parser.add_argument('--baseurl', default='https://api.openai.com',
                      help='OpenAI API base URL')
    parser.add_argument('--apikey', required=True,
                      help='OpenAI API key')
    parser.add_argument('--model', default='gpt-3.5-turbo',
                      help='OpenAI model name')
    
    # 目标URL
    parser.add_argument('--url', required=True,
                      help='Target URL to generate comment for')
    
    # 可选参数
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')

    args = parser.parse_args()

    try:
        # 初始化 OpenAI
        print("Initializing OpenAI...")
        init_openai(args.baseurl, args.apikey, args.model)
        
        # 提取内容
        print(f"\nExtracting content from {args.url}...")
        content = ContentExtractor.extract(args.url)
        content_length = len(content)
        print(f"\nExtracted content length: {content_length} characters")
        print("\nExtracted content preview (first 500 chars):")
        print("-" * 50)
        print(content[:500])
        if content_length > 500:
            print("...")
        print("-" * 50)

        # 如果内容太少，给出警告
        if content_length < 100:
            print("\nWarning: Extracted content seems too short!")
            if args.debug:
                print("\nFull extracted content:")
                print("-" * 50)
                print(content)
                print("-" * 50)
        
        # 生成评论
        print("\nGenerating comment using OpenAI...")
        comment = CommentGenerator.generate(content)
        print("\nGenerated comment:")
        print("-" * 50)
        print(comment)
        print("-" * 50)
        
        sys.exit(0)
            
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

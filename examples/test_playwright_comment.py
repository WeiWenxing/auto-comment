import argparse
import sys
from auto_comment import init_openai, send_comment_playwright
from auto_comment.content import ContentExtractor
from auto_comment.openai_client import CommentGenerator

def main():
    parser = argparse.ArgumentParser(description='Test Playwright-based comment submission')
    
    # OpenAI 配置参数
    parser.add_argument('--baseurl', default='https://api.openai.com',
                      help='OpenAI API base URL')
    parser.add_argument('--apikey',
                      help='OpenAI API key (required if content is not provided)')
    parser.add_argument('--model', default='gpt-3.5-turbo',
                      help='OpenAI model name')
    
    # 评论必要参数
    parser.add_argument('--name', required=True,
                      help='Commenter name')
    parser.add_argument('--email', required=True,
                      help='Commenter email')
    parser.add_argument('--website', required=True,
                      help='Commenter website')
    parser.add_argument('--url', required=True,
                      help='Target URL to post comment')
    
    # 可选参数
    parser.add_argument('--content',
                      help='Comment content (if not provided, will be generated)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')

    args = parser.parse_args()

    try:
        comment_content = args.content

        # 如果没有提供评论内容，则生成评论
        if not comment_content:
            if not args.apikey:
                print("Error: OpenAI API key is required when content is not provided")
                sys.exit(1)
            
            print("\nInitializing OpenAI...")
            init_openai(args.baseurl, args.apikey, args.model)

            print("\nExtracting content from URL...")
            page_content = ContentExtractor.extract(args.url)

            print("\nGenerating comment...")
            comment_content = CommentGenerator.generate(page_content)

            # 检查生成的评论是否为空
            if not comment_content or not comment_content.strip():
                print("\nError: Generated comment is empty")
                sys.exit(1)

        # 发送评论
        print("\nSending comment using Playwright to:", args.url)
        print("\nComment content:")
        print("-" * 50)
        print(comment_content)
        print("-" * 50)

        result = send_comment_playwright(
            name=args.name,
            email=args.email,
            website=args.website,
            url=args.url,
            content=comment_content
        )

        if result:
            print("\nSuccess: Comment submitted successfully!")
            sys.exit(0)
        else:
            print("\nError: Failed to submit comment")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
import argparse
import sys
import os
from auto_comment import init_openai, send_comment

def main():
    parser = argparse.ArgumentParser(description='Test auto_comment functionality')
    
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
                      help='Custom comment content (optional)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode')

    args = parser.parse_args()

    try:
        # 只有在没有提供 content 时才需要初始化 OpenAI
        if not args.content:
            if not args.apikey:
                print("Error: OpenAI API key is required when content is not provided")
                sys.exit(1)
            init_openai(args.baseurl, args.apikey, args.model)
        
        # 发送评论
        result = send_comment(
            name=args.name,
            email=args.email,
            website=args.website,
            url=args.url,
            content=args.content
        )
        
        if result:
            print("Comment sent successfully!")
            sys.exit(0)
        else:
            print("Failed to send comment.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

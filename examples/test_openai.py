import argparse
import time
from openai import OpenAI

def test_openai(baseurl: str, apikey: str, model: str, prompt: str, timeout: int = 30):
    """Test OpenAI API connection and response"""
    print(f"\nTesting OpenAI API...")
    print(f"Base URL: {baseurl}")
    print(f"Model: {model}")
    print(f"Timeout: {timeout} seconds")
    
    try:
        # 初始化客户端
        print("\nInitializing OpenAI client...")
        client = OpenAI(
            base_url=baseurl,
            api_key=apikey
        )
        
        # 开始计时
        start_time = time.time()
        
        print("\nSending request...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=timeout
        )
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        
        print(f"\nResponse received in {elapsed_time:.2f} seconds:")
        print("-" * 50)
        print(response.choices[0].message.content)
        print("-" * 50)
        
    except Exception as e:
        print(f"\nError: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test OpenAI API')
    parser.add_argument('--baseurl', default='https://api.openai.com/v1',
                      help='OpenAI API base URL')
    parser.add_argument('--apikey', required=True,
                      help='OpenAI API key')
    parser.add_argument('--model', default='gpt-3.5-turbo',
                      help='OpenAI model name')
    parser.add_argument('--prompt', default='Say hello!',
                      help='Test prompt')
    parser.add_argument('--timeout', type=int, default=30,
                      help='Timeout in seconds')
    
    args = parser.parse_args()
    test_openai(args.baseurl, args.apikey, args.model, args.prompt, args.timeout)

if __name__ == '__main__':
    main()
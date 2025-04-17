from setuptools import setup, find_packages

setup(
    name='auto_comment',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
        'beautifulsoup4>=4.9.0',
        'aiohttp>=3.8.0',
        'lxml>=4.9.0',
        'openai>=1.0.0',
        'selenium>=4.0.0',
        'webdriver_manager>=3.8.0',
        'undetected-chromedriver>=3.5.0',
        'python-dotenv>=0.19.0',
        'asyncio>=3.4.3',
        'tenacity>=8.0.0'
    ],
    author='Your Name',
    author_email='your.email@example.com',
    description='A Python library for auto-generating and posting comments',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/auto_comment',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    python_requires='>=3.9',
)

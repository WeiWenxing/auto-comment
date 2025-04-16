import unittest
from unittest.mock import patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from auto_comment.comment import CommentSender, send_comment
from auto_comment.exceptions import CommentError

class TestCommentSender(unittest.TestCase):
    def setUp(self):
        self.test_name = "Test User"
        self.test_email = "test@example.com"
        self.test_website = "http://example.com"
        self.test_url = "http://target.com"
        self.test_content = "This is a test comment"

    @patch('selenium.webdriver.Chrome')
    @patch('auto_comment.content.ContentExtractor.extract')
    @patch('auto_comment.openai_client.CommentGenerator.generate')
    def test_send_comment_success(self, mock_generate, mock_extract, mock_chrome):
        # 设置模拟对象
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_element = MagicMock()
        mock_element.is_displayed.return_value = True
        mock_generate.return_value = "Auto generated comment"
        
        # 模拟find_element返回成功
        def mock_find_element(*args):
            return mock_element
        
        with patch.object(CommentSender, 'find_element', side_effect=mock_find_element):
            # 测试自动生成评论内容的情况
            result = send_comment(
                self.test_name,
                self.test_email,
                self.test_website,
                self.test_url
            )
            self.assertTrue(result)
            mock_generate.assert_called_once()
            
            # 测试指定评论内容的情况
            result = send_comment(
                self.test_name,
                self.test_email,
                self.test_website,
                self.test_url,
                self.test_content
            )
            self.assertTrue(result)
            mock_element.send_keys.assert_any_call(self.test_content)

    @patch('selenium.webdriver.Chrome')
    def test_send_comment_missing_fields(self, mock_chrome):
        # 测试缺少必要字段的情况
        result = send_comment("", self.test_email, self.test_website, self.test_url)
        self.assertFalse(result)

    @patch('selenium.webdriver.Chrome')
    def test_send_comment_form_not_found(self, mock_chrome):
        # 设置模拟对象
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # 模拟找不到表单元素
        with patch.object(CommentSender, 'find_element', return_value=None):
            result = send_comment(
                self.test_name,
                self.test_email,
                self.test_website,
                self.test_url
            )
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

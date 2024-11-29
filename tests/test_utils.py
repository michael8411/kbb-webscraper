# test_utils.py

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import requests


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import (
    load_config,
    get_proxy,
    create_session,
    get_user_agent,
    get_cached_or_request,
    setup_logging,
    config
)

class TestUtils(unittest.TestCase):

    def test_load_config_success(self):
        config = load_config('config.ini')
        self.assertIn('BaseURL', config)
        self.assertIn('DataFilePath', config)

    def test_get_proxy_with_credentials(self):
        with patch.dict(os.environ, {
            'PROXY_USERNAME': 'user',
            'PROXY_PASSWORD': 'pass',
            'PROXY_HOST': 'host',
            'PROXY_PORT': '8080'
        }):
            proxy = get_proxy()
            self.assertEqual(proxy, 'http://user:pass@host:8080')

    def test_get_proxy_without_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            proxy = get_proxy()
            self.assertIsNone(proxy)

    def test_create_session(self):
        session = create_session()
        self.assertIsInstance(session, requests.Session)

    def test_get_user_agent(self):
        user_agent = get_user_agent()
        self.assertIsInstance(user_agent, str)
        self.assertTrue(len(user_agent) > 0)

    @patch('utils.cache')
    @patch('utils.requests.Session.get')
    def test_get_cached_or_request_with_cache(self, mock_get, mock_cache):
        url = 'http://example.com'
        mock_cache.__contains__.return_value = True
        mock_cache.__getitem__.return_value = 'Cached Content'
        session = MagicMock()
        headers = {}
        proxies = {}
        content = get_cached_or_request(url, session, headers, proxies)
        self.assertEqual(content, 'Cached Content')
        mock_get.assert_not_called()

    @patch('utils.cache')
    @patch('utils.requests.Session.get')
    def test_get_cached_or_request_without_cache(self, mock_get, mock_cache):
        url = 'http://example.com'
        mock_cache.__contains__.return_value = False
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'New Content'
        session = requests.Session()
        headers = {}
        proxies = {}
        content = get_cached_or_request(url, session, headers, proxies)
        self.assertEqual(content, 'New Content')
        mock_get.assert_called_once_with(url, headers=headers, proxies=proxies, timeout=30)
        mock_cache.__setitem__.assert_called_once()

if __name__ == '__main__':
    unittest.main()

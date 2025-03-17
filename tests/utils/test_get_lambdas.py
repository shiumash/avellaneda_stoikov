import unittest
from unittest.mock import patch, MagicMock
import os
import time
import json
import sys
from utils.get_lambda import get_lambdas_from_order_book, get_default_lambdas, get_lambdas

"""
Unit tests for get_lambda.py
"""

# Import the functions from the module using absolute import

class TestGetLambda(unittest.TestCase):
    """Tests for the get_lambda module functions."""
    
    @patch('v1.utils.get_lambda.requests.get')
    def test_get_lambdas_from_order_book_success(self, mock_get):
        """Test successful lambda estimation from order book."""
        # Mock response for the first API call
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            'result': {
                'XBTCZUSD': {
                    'bids': [['40000', '2.5', '1618207500'], ['39900', '1.5', '1618207400']],
                    'asks': [['40100', '1.8', '1618207500'], ['40200', '2.2', '1618207490']]
                }
            }
        }
        
        # Mock response for the second API call
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            'result': {
                'XBTCZUSD': {
                    'bids': [['40100', '3.0', '1618207600'], ['39800', '2.0', '1618207550']],
                    'asks': [['40200', '2.0', '1618207600'], ['40300', '2.5', '1618207580']]
                }
            }
        }
        
        # Mock response for the third API call
        mock_response3 = MagicMock()
        mock_response3.json.return_value = {
            'result': {
                'XBTCZUSD': {
                    'bids': [['40050', '2.8', '1618207700'], ['39850', '1.8', '1618207650']],
                    'asks': [['40150', '2.2', '1618207700'], ['40250', '2.4', '1618207680']]
                }
            }
        }
        
        # Set up the mock to return the responses in sequence
        mock_get.side_effect = [mock_response1, mock_response2, mock_response3]
        
        # Mock time.time() to return controlled timestamps
        with patch('v1.utils.get_lambda.time.time', side_effect=[1000.0, 1005.0, 1010.0]):
            with patch('v1.utils.get_lambda.time.sleep') as mock_sleep:
                # Call the function with minimal interval for faster test
                lambda_b, lambda_a = get_lambdas_from_order_book('BTC/USD', num_samples=3, interval=0.1)
        
        # Verify results are reasonable
        self.assertGreaterEqual(lambda_b, 5.0)
        self.assertGreaterEqual(lambda_a, 5.0)
        
        # Verify the API was called with correct parameters
        mock_get.assert_called_with(
            'https://api.kraken.com/0/public/Depth', 
            params={'pair': 'XBTCZUSD', 'count': 100}, 
            timeout=10
        )
        self.assertEqual(mock_get.call_count, 3)
    
    @patch('v1.utils.get_lambda.requests.get')
    def test_get_lambdas_from_order_book_api_error(self, mock_get):
        """Test handling of API errors in lambda estimation."""
        # Mock an API error response
        mock_response = MagicMock()
        mock_response.json.return_value = {'error': ['Invalid pair']}
        mock_get.return_value = mock_response
        
        # Mock get_default_lambdas for this test
        with patch('v1.utils.get_lambda.get_default_lambdas') as mock_defaults:
            mock_defaults.return_value = (10.0, 10.0)
            
            # Call function with minimal samples for faster test
            lambda_b, lambda_a = get_lambdas_from_order_book('BTC/USD', num_samples=1)
            
        # Should fall back to default lambdas
        self.assertEqual((lambda_b, lambda_a), (10.0, 10.0))
        mock_defaults.assert_called_once_with('BTC/USD')
    
    @patch('v1.utils.get_lambda.requests.get')
    def test_get_lambdas_from_order_book_exception(self, mock_get):
        """Test handling of exceptions in order book fetching."""
        # Mock a request that raises an exception
        mock_get.side_effect = Exception("Connection error")
        
        # Mock get_default_lambdas for this test
        with patch('v1.utils.get_lambda.get_default_lambdas') as mock_defaults:
            mock_defaults.return_value = (10.0, 10.0)
            
            # Call function with minimal samples for faster test
            lambda_b, lambda_a = get_lambdas_from_order_book('BTC/USD', num_samples=1)
            
        # Should fall back to default lambdas
        self.assertEqual((lambda_b, lambda_a), (10.0, 10.0))
        mock_defaults.assert_called_once_with('BTC/USD')
    
    def test_symbol_formatting(self):
        """Test the symbol formatting for different trading pairs."""
        # Use inspect to directly test the formatting logic
        with patch('v1.utils.get_lambda.requests.get') as mock_get:
            # Mock to avoid actual API calls
            mock_get.side_effect = Exception("Test exception")
            with patch('v1.utils.get_lambda.get_default_lambdas') as mock_defaults:
                mock_defaults.return_value = (1.0, 1.0)
                
                # Test USDT/USD formatting
                get_lambdas_from_order_book('USDT/USD', num_samples=1)
                mock_get.assert_called_with(
                    'https://api.kraken.com/0/public/Depth', 
                    params={'pair': 'USDTZUSD', 'count': 100}, 
                    timeout=10
                )
                
                # Test BTC/USD formatting
                get_lambdas_from_order_book('BTC/USD', num_samples=1)
                mock_get.assert_called_with(
                    'https://api.kraken.com/0/public/Depth', 
                    params={'pair': 'XBTCZUSD', 'count': 100}, 
                    timeout=10
                )
                
                # Test other pair formatting
                get_lambdas_from_order_book('LTC/EUR', num_samples=1)
                mock_get.assert_called_with(
                    'https://api.kraken.com/0/public/Depth', 
                    params={'pair': 'LTCEUR', 'count': 100}, 
                    timeout=10
                )
    
    @patch.dict(os.environ, {
        'AS_LAMBDA_B_STABLE': '100.0',
        'AS_LAMBDA_A_STABLE': '110.0',
        'AS_LAMBDA_B_MAJOR': '20.0',
        'AS_LAMBDA_A_MAJOR': '25.0'
    })
    def test_get_default_lambdas_env_vars(self):
        """Test that environment variables override default lambda values."""
        # Test stable pair with env vars
        lambda_b, lambda_a = get_default_lambdas('USDT/USD')
        self.assertEqual(lambda_b, 100.0)
        self.assertEqual(lambda_a, 110.0)
        
        # Test major crypto with env vars
        lambda_b, lambda_a = get_default_lambdas('BTC/USD')
        self.assertEqual(lambda_b, 20.0)
        self.assertEqual(lambda_a, 25.0)
    
    def test_get_default_lambdas_categories(self):
        """Test default lambda values for different trading pair categories."""
        # Ensure env vars don't interfere with the test
        with patch.dict(os.environ, {}, clear=True):
            # Test stable pair
            lambda_b, lambda_a = get_default_lambdas('USDT/USD')
            self.assertEqual(lambda_b, 50.0)
            self.assertEqual(lambda_a, 50.0)
            
            # Test major crypto
            lambda_b, lambda_a = get_default_lambdas('ETH/USD')
            self.assertEqual(lambda_b, 15.0)
            self.assertEqual(lambda_a, 15.0)
            
            # Test mid crypto
            lambda_b, lambda_a = get_default_lambdas('SOL/USD')
            self.assertEqual(lambda_b, 7.5)
            self.assertEqual(lambda_a, 7.5)
            
            # Test other/unknown pair
            lambda_b, lambda_a = get_default_lambdas('XYZ/USD')
            self.assertEqual(lambda_b, 5.0)
            self.assertEqual(lambda_a, 5.0)
    
    def test_get_lambdas_use_order_book_false(self):
        """Test get_lambdas with use_order_book=False."""
        with patch('v1.utils.get_lambda.get_default_lambdas') as mock_defaults:
            mock_defaults.return_value = (15.0, 15.0)
            
            # Call with use_order_book=False
            lambda_b, lambda_a = get_lambdas('BTC/USD', use_order_book=False)
            
            # Should use default lambdas
            self.assertEqual((lambda_b, lambda_a), (15.0, 15.0))
            mock_defaults.assert_called_once_with('BTC/USD')
    
    def test_get_lambdas_order_book_exception(self):
        """Test get_lambdas falls back to defaults when order book fails."""
        with patch('v1.utils.get_lambda.get_lambdas_from_order_book') as mock_ob:
            mock_ob.side_effect = Exception("Test exception")
            
            with patch('v1.utils.get_lambda.get_default_lambdas') as mock_defaults:
                mock_defaults.return_value = (15.0, 15.0)
                
                # Call with use_order_book=True, but it will fail
                lambda_b, lambda_a = get_lambdas('BTC/USD', use_order_book=True)
                
                # Should fall back to default lambdas
                self.assertEqual((lambda_b, lambda_a), (15.0, 15.0))
                mock_defaults.assert_called_once_with('BTC/USD')
    
    def test_get_lambdas_order_book_success(self):
        """Test get_lambdas uses order book estimates when successful."""
        with patch('v1.utils.get_lambda.get_lambdas_from_order_book') as mock_ob:
            mock_ob.return_value = (25.0, 30.0)
            
            # Call with use_order_book=True
            lambda_b, lambda_a = get_lambdas('BTC/USD', use_order_book=True)
            
            # Should use order book lambdas
            self.assertEqual((lambda_b, lambda_a), (25.0, 30.0))
            mock_ob.assert_called_once_with('BTC/USD')

if __name__ == '__main__':
    unittest.main()
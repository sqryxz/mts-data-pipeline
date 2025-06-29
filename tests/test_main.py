"""Tests for the main command-line interface."""

import sys
import pytest
import subprocess
import os
import logging
import json
import threading
import time
import requests
from unittest.mock import patch, Mock, MagicMock
from io import StringIO
from http.server import HTTPServer

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from src.services.collector import DataCollector
from src.services.monitor import HealthChecker


class TestMainCommandLine:
    """Test the main command-line interface functionality."""
    
    def test_main_no_arguments_shows_help(self, capsys):
        """Test that running with no arguments shows help."""
        with patch('sys.argv', ['main.py']):
            exit_code = main.main()
            
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "MTS Crypto Data Pipeline" in captured.out
        assert "--collect" in captured.out
    
    def test_main_version_flag(self, capsys):
        """Test the --version flag."""
        with patch('sys.argv', ['main.py', '--version']):
            exit_code = main.main()
            
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "MTS Crypto Data Pipeline v1.0.0" in captured.out
        assert "Collects OHLCV data" in captured.out
    
    def test_main_invalid_days_negative(self, capsys):
        """Test validation of negative days parameter."""
        with patch('sys.argv', ['main.py', '--collect', '--days', '-1']):
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "must be a positive integer" in captured.err
    
    def test_main_invalid_days_too_large(self, capsys):
        """Test validation of days parameter exceeding limit."""
        with patch('sys.argv', ['main.py', '--collect', '--days', '400']):
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "cannot exceed 365" in captured.err
    
    def test_main_keyboard_interrupt(self, capsys):
        """Test handling of keyboard interrupt."""
        with patch('sys.argv', ['main.py', '--collect']), \
             patch('main.setup_application') as mock_setup:
            
            mock_setup.side_effect = KeyboardInterrupt()
            exit_code = main.main()
            
        assert exit_code == 130
        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.err
    
    def test_main_unexpected_exception(self, capsys):
        """Test handling of unexpected exceptions."""
        with patch('sys.argv', ['main.py', '--collect']), \
             patch('main.setup_application') as mock_setup:
            
            mock_setup.side_effect = RuntimeError("Unexpected error")
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Fatal error: Unexpected error" in captured.err


class TestSetupApplication:
    """Test the application setup functionality."""
    
    @patch('main.setup_logging')
    @patch('main.Config')
    @patch('main.DataCollector')
    def test_setup_application_success(self, mock_collector_class, mock_config_class, mock_setup_logging):
        """Test successful application setup."""
        # Setup mocks
        mock_config = Mock()
        mock_config.COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
        mock_config_class.return_value = mock_config
        
        mock_collector = Mock(spec=DataCollector)
        mock_collector_class.return_value = mock_collector
        
        # Execute
        collector, logger = main.setup_application()
        
        # Verify
        mock_setup_logging.assert_called_once()
        mock_config_class.assert_called_once()
        mock_collector_class.assert_called_once()
        
        assert collector is mock_collector
        assert logger is not None
    
    @patch('main.setup_logging')
    @patch('main.Config')
    def test_setup_application_config_failure(self, mock_config_class, mock_setup_logging):
        """Test application setup when configuration fails."""
        mock_config_class.side_effect = RuntimeError("Config error")
        
        with pytest.raises(RuntimeError):
            main.setup_application()
    
    @patch('main.setup_logging')
    @patch('main.Config')
    @patch('main.DataCollector')
    def test_setup_application_collector_failure(self, mock_collector_class, mock_config_class, mock_setup_logging):
        """Test application setup when collector initialization fails."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        mock_collector_class.side_effect = RuntimeError("Collector error")
        
        with pytest.raises(RuntimeError):
            main.setup_application()


class TestRunCollection:
    """Test the collection execution functionality."""
    
    def test_run_collection_success(self):
        """Test successful collection run."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 3,
            'failed': 0,
            'retries_used': 0,
            'duration_seconds': 2.5,
            'successful_cryptos': ['bitcoin', 'ethereum', 'tether'],
            'failed_cryptos': [],
            'error_categories': {}
        }
        
        mock_logger = Mock()
        
        # Execute
        result = main.run_collection(mock_collector, mock_logger, days=1)
        
        # Verify
        assert result is True
        mock_collector.collect_all_data.assert_called_once_with(days=1)
        
        # Check that success logging was called
        success_calls = [call for call in mock_logger.info.call_args_list 
                        if "✅ Data collection completed successfully" in str(call)]
        assert len(success_calls) > 0
    
    def test_run_collection_partial_success(self):
        """Test collection with some failures but overall success."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 2,
            'failed': 1,
            'retries_used': 1,
            'duration_seconds': 3.2,
            'successful_cryptos': ['bitcoin', 'ethereum'],
            'failed_cryptos': ['tether'],
            'error_categories': {'network': 1}
        }
        
        mock_logger = Mock()
        
        # Execute
        result = main.run_collection(mock_collector, mock_logger, days=7)
        
        # Verify
        assert result is True
        mock_collector.collect_all_data.assert_called_once_with(days=7)
        
        # Check that warning about failures was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if "Failed to collect data for: tether" in str(call)]
        assert len(warning_calls) > 0
    
    def test_run_collection_total_failure(self):
        """Test collection when all cryptos fail."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.return_value = {
            'total_attempted': 3,
            'successful': 0,
            'failed': 3,
            'retries_used': 6,
            'duration_seconds': 15.7,
            'successful_cryptos': [],
            'failed_cryptos': ['bitcoin', 'ethereum', 'tether'],
            'error_categories': {'network': 2, 'server_error': 1}
        }
        
        mock_logger = Mock()
        
        # Execute
        result = main.run_collection(mock_collector, mock_logger)
        
        # Verify
        assert result is False
        
        # Check that failure logging was called
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if "❌ Data collection failed" in str(call)]
        assert len(error_calls) > 0
    
    def test_run_collection_exception_handling(self):
        """Test collection exception handling."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.side_effect = RuntimeError("Collection error")
        
        mock_logger = Mock()
        
        # Execute
        result = main.run_collection(mock_collector, mock_logger)
        
        # Verify
        assert result is False
        
        # Check that error was logged
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if "Unexpected error during collection" in str(call)]
        assert len(error_calls) > 0
    
    def test_run_collection_pipeline_exception(self):
        """Test collection with pipeline-specific exception."""
        from src.utils.exceptions import APIError
        
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_collector.collect_all_data.side_effect = APIError("API failed")
        
        mock_logger = Mock()
        
        # Execute
        result = main.run_collection(mock_collector, mock_logger)
        
        # Verify
        assert result is False
        
        # Check that pipeline error was logged
        error_calls = [call for call in mock_logger.error.call_args_list 
                      if "Pipeline error during collection" in str(call)]
        assert len(error_calls) > 0


class TestMainIntegration:
    """Integration tests for the main functionality."""
    
    @patch('main.setup_application')
    @patch('main.run_collection')
    def test_main_collect_success_integration(self, mock_run_collection, mock_setup_application):
        """Test successful end-to-end collection."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_logger = Mock()
        mock_setup_application.return_value = (mock_collector, mock_logger)
        mock_run_collection.return_value = True
        
        # Execute
        with patch('sys.argv', ['main.py', '--collect']):
            exit_code = main.main()
        
        # Verify
        assert exit_code == 0
        mock_setup_application.assert_called_once()
        mock_run_collection.assert_called_once_with(mock_collector, mock_logger, days=1)
    
    @patch('main.setup_application')
    @patch('main.run_collection')
    def test_main_collect_failure_integration(self, mock_run_collection, mock_setup_application):
        """Test collection failure end-to-end."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_logger = Mock()
        mock_setup_application.return_value = (mock_collector, mock_logger)
        mock_run_collection.return_value = False
        
        # Execute
        with patch('sys.argv', ['main.py', '--collect']):
            exit_code = main.main()
        
        # Verify
        assert exit_code == 1
    
    @patch('main.setup_application')
    @patch('main.run_collection')
    def test_main_collect_with_custom_days(self, mock_run_collection, mock_setup_application):
        """Test collection with custom days parameter."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_logger = Mock()
        mock_setup_application.return_value = (mock_collector, mock_logger)
        mock_run_collection.return_value = True
        
        # Execute
        with patch('sys.argv', ['main.py', '--collect', '--days', '7']):
            exit_code = main.main()
        
        # Verify
        assert exit_code == 0
        mock_run_collection.assert_called_once_with(mock_collector, mock_logger, days=7)
    
    @patch('main.setup_application')
    @patch('main.run_collection')
    def test_main_verbose_logging(self, mock_run_collection, mock_setup_application):
        """Test verbose logging flag."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_logger = Mock()
        mock_setup_application.return_value = (mock_collector, mock_logger)
        mock_run_collection.return_value = True
        
        # Execute
        with patch('sys.argv', ['main.py', '--collect', '--verbose']), \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_root_logger = Mock()
            mock_get_logger.return_value = mock_root_logger
            
            exit_code = main.main()
        
        # Verify verbose logging was enabled
        mock_root_logger.setLevel.assert_called_with(logging.DEBUG)
        assert exit_code == 0


class TestCommandLineExecution:
    """Test actual command line execution."""
    
    def test_help_command_execution(self):
        """Test that help command works when executed."""
        result = subprocess.run([
            sys.executable, 'main.py', '--help'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 0
        assert "MTS Crypto Data Pipeline" in result.stdout
        assert "--collect" in result.stdout
    
    def test_version_command_execution(self):
        """Test that version command works when executed."""
        result = subprocess.run([
            sys.executable, 'main.py', '--version'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 0
        assert "MTS Crypto Data Pipeline v1.0.0" in result.stdout
    
    def test_invalid_days_execution(self):
        """Test that invalid days parameter fails correctly."""
        result = subprocess.run([
            sys.executable, 'main.py', '--collect', '--days', '-1'
        ], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(__file__)))
        
        assert result.returncode == 1
        assert "must be a positive integer" in result.stderr


class TestHealthRequestHandler:
    """Test the HTTP health request handler."""
    
    def test_health_endpoint_success(self):
        """Test successful health check endpoint."""
        # Setup mock health checker
        mock_health_checker = Mock()
        mock_health_checker.get_system_health_status.return_value = {
            'status': 'healthy',
            'healthy': True,
            'message': 'All components healthy',
            'checked_at': '2025-06-29T02:00:00.000000',
            'components': {
                'data_freshness': {
                    'overall_status': 'healthy',
                    'is_healthy': True,
                    'fresh_count': 3,
                    'total_count': 3
                }
            }
        }
        
        # Create a minimal handler object without calling parent __init__
        handler = object.__new__(main.HealthRequestHandler)
        handler.health_checker = mock_health_checker
        handler.path = '/health'
        
        # Mock the response methods
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        
        # Execute
        handler._handle_health_check()
        
        # Verify
        mock_health_checker.get_system_health_status.assert_called_once()
        handler.send_response.assert_called_once_with(200)
        
        # Check JSON response content
        write_calls = handler.wfile.write.call_args_list
        assert len(write_calls) == 1
        response_data = write_calls[0][0][0].decode('utf-8')
        response_json = json.loads(response_data)
        
        assert response_json['status'] == 'healthy'
        assert response_json['healthy'] is True
        assert 'timestamp' in response_json
        assert 'components' in response_json
    
    @patch('main.HealthChecker')
    def test_health_endpoint_error(self, mock_health_checker_class):
        """Test health check endpoint when health checker fails."""
        # Setup mock health checker to raise exception
        mock_health_checker = Mock()
        mock_health_checker.get_system_health_status.side_effect = RuntimeError("Health check failed")
        
        # Create a minimal handler object without calling parent __init__
        handler = object.__new__(main.HealthRequestHandler)
        handler.health_checker = mock_health_checker
        handler.path = '/health'
        
        # Mock the response methods
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        
        # Mock the fallback HealthChecker call for timestamp
        mock_fallback_health_checker = Mock()
        mock_fallback_health_checker.get_system_health_status.return_value = {
            'checked_at': '2025-06-29T02:00:00.000000'
        }
        mock_health_checker_class.return_value = mock_fallback_health_checker
        
        # Execute
        handler._handle_health_check()
        
        # Verify error response
        handler.send_response.assert_called_once_with(500)
        
        # Check error JSON response
        write_calls = handler.wfile.write.call_args_list
        assert len(write_calls) == 1
        response_data = write_calls[0][0][0].decode('utf-8')
        response_json = json.loads(response_data)
        
        assert response_json['status'] == 'error'
        assert response_json['healthy'] is False
        assert 'Health check failed' in response_json['message']
    
    def test_not_found_endpoint(self):
        """Test 404 handling for unknown endpoints."""
        # Create a minimal handler object without calling parent __init__
        handler = object.__new__(main.HealthRequestHandler)
        handler.path = '/unknown'
        
        # Mock the response methods
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        
        # Execute
        handler._handle_not_found()
        
        # Verify 404 response
        handler.send_response.assert_called_once_with(404)
        
        # Check 404 JSON response
        write_calls = handler.wfile.write.call_args_list
        assert len(write_calls) == 1
        response_data = write_calls[0][0][0].decode('utf-8')
        response_json = json.loads(response_data)
        
        assert response_json['status'] == 'error'
        assert 'Endpoint not found' in response_json['message']
        assert response_json['path'] == '/unknown'


class TestHttpServerIntegration:
    """Test HTTP server command line integration."""
    
    def test_server_argument_validation(self, capsys):
        """Test server argument validation."""
        # Test invalid port range
        with patch('sys.argv', ['main.py', '--server', '--port', '0']):
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "must be between 1 and 65535" in captured.err
        
        # Test port too high
        with patch('sys.argv', ['main.py', '--server', '--port', '70000']):
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "must be between 1 and 65535" in captured.err
    
    def test_conflicting_arguments(self, capsys):
        """Test that --collect and --server cannot be used together."""
        with patch('sys.argv', ['main.py', '--collect', '--server']):
            exit_code = main.main()
            
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Cannot specify both --collect and --server" in captured.err
    
    @patch('main.run_server')
    @patch('main.setup_application')
    def test_server_command_execution(self, mock_setup_application, mock_run_server):
        """Test server command execution."""
        # Setup mocks
        mock_collector = Mock(spec=DataCollector)
        mock_logger = Mock()
        mock_setup_application.return_value = (mock_collector, mock_logger)
        
        # Execute
        with patch('sys.argv', ['main.py', '--server', '--port', '9090']):
            exit_code = main.main()
        
        # Verify
        assert exit_code == 0
        mock_setup_application.assert_called_once()
        mock_run_server.assert_called_once_with(mock_logger, port=9090)
    
    @patch('main.HTTPServer')
    @patch('main.HealthChecker')
    def test_run_server_function(self, mock_health_checker_class, mock_http_server_class):
        """Test the run_server function."""
        # Setup mocks
        mock_logger = Mock()
        mock_health_checker = Mock()
        mock_health_checker_class.return_value = mock_health_checker
        
        mock_server = Mock()
        mock_http_server_class.return_value = mock_server
        
        # Execute (should not block since we're mocking serve_forever)
        main.run_server(mock_logger, port=8080)
        
        # Verify
        mock_health_checker_class.assert_called_once()
        mock_http_server_class.assert_called_once_with(('0.0.0.0', 8080), main.HealthRequestHandler)
        mock_server.serve_forever.assert_called_once()
        
        # Verify health checker was set on handler class
        assert main.HealthRequestHandler.health_checker is mock_health_checker 
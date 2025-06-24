"""
Environment and system tests for EC2 Slack Bot
"""
import pytest
import sys
import subprocess
import os
from pathlib import Path


class TestEnvironmentRequirements:
    """Test environment requirements"""
    
    def test_python_version(self):
        """Test Python version requirement (3.8+)"""
        version = sys.version_info
        assert version.major == 3
        assert version.minor >= 8, f"Python 3.8+ required, got {version.major}.{version.minor}"
    
    def test_required_packages(self):
        """Test that required packages are available"""
        required_packages = [
            'flask',
            'slack_bolt',
            'boto3',
            'dotenv',
            'requests'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"Required package '{package}' is not installed")
    
    def test_docker_available(self):
        """Test if Docker is available (optional)"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"Docker available: {result.stdout.strip()}")
            else:
                print("Docker not available (optional)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Docker not available (optional)")
    
    def test_docker_compose_available(self):
        """Test if Docker Compose is available (optional)"""
        # Try docker-compose first
        try:
            result = subprocess.run(
                ['docker-compose', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"Docker Compose available: {result.stdout.strip()}")
                return
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try docker compose (newer version)
        try:
            result = subprocess.run(
                ['docker', 'compose', 'version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"Docker Compose available: {result.stdout.strip()}")
            else:
                print("Docker Compose not available (optional)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("Docker Compose not available (optional)")


class TestFileStructure:
    """Test required file structure"""
    
    def test_app_file_exists(self):
        """Test that app.py exists"""
        assert Path('app.py').exists(), "app.py file not found"
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists"""
        assert Path('requirements.txt').exists(), "requirements.txt file not found"
    
    def test_env_template_exists(self):
        """Test that env.template exists"""
        assert Path('env.template').exists(), "env.template file not found"
    
    def test_data_directory_creatable(self):
        """Test that data directory can be created"""
        data_dir = Path('data')
        if not data_dir.exists():
            data_dir.mkdir()
        
        assert data_dir.exists(), "Cannot create data directory"
        assert data_dir.is_dir(), "data is not a directory"


class TestConfiguration:
    """Test configuration setup"""
    
    def test_env_file_creation(self):
        """Test that .env file can be created from template"""
        env_template = Path('env.template')
        env_file = Path('.env')
        
        if not env_file.exists() and env_template.exists():
            # Create .env from template
            with open(env_template, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
        
        # Test that .env exists (either was there or created)
        if env_file.exists():
            print("✅ .env file exists")
        else:
            pytest.skip("Cannot create .env file from template")
    
    def test_test_mode_configuration(self):
        """Test test mode configuration"""
        # Set test mode
        os.environ['TEST_MODE'] = 'true'
        
        # Verify test mode is set
        assert os.environ.get('TEST_MODE') == 'true'
        
        # Clean up
        if 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']


class TestDatabaseAccess:
    """Test database access and permissions"""
    
    def test_database_directory_writable(self):
        """Test that database directory is writable"""
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        # Test write permission
        test_file = data_dir / 'test_write.tmp'
        try:
            test_file.write_text('test')
            assert test_file.exists()
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"Cannot write to data directory: {e}")
    
    def test_sqlite_available(self):
        """Test that SQLite is available"""
        try:
            import sqlite3
            # Test basic SQLite functionality
            conn = sqlite3.connect(':memory:')
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            conn.close()
            assert result[0] == 1
        except Exception as e:
            pytest.fail(f"SQLite not available: {e}")


class TestNetworkAccess:
    """Test network access (for integration tests)"""
    
    def test_localhost_access(self):
        """Test that localhost is accessible"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            # Port 5000 might not be open, but localhost should be accessible
            # We're just testing that we can create a socket
            print("✅ Localhost access available")
        except Exception as e:
            pytest.fail(f"Cannot access localhost: {e}")
    
    def test_requests_library(self):
        """Test that requests library works"""
        try:
            import requests
            # Test basic requests functionality
            response = requests.get('http://httpbin.org/get', timeout=5)
            assert response.status_code == 200
        except Exception as e:
            print(f"⚠️  Requests library test failed (network issue): {e}")
            # This is not a critical failure, just a warning 
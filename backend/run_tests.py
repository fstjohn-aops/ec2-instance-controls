#!/usr/bin/env python3
"""
Simple test runner for EC2 Slack Bot
Replaces complex shell scripts with clean Python-based testing
"""
import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def check_environment():
    """Check basic environment requirements"""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if we're in the right directory
    if not Path('app.py').exists():
        print("❌ app.py not found. Run from backend directory.")
        return False
    
    print("✅ In correct directory")
    return True


def setup_environment():
    """Set up test environment"""
    print("\n🔧 Setting up environment...")
    
    # Create .env if it doesn't exist
    if not Path('.env').exists():
        if Path('env.template').exists():
            run_command("cp env.template .env", "Creating .env from template")
        else:
            print("⚠️  No env.template found, creating basic .env")
            with open('.env', 'w') as f:
                f.write("""# Test Configuration
TEST_MODE=true
FLASK_ENV=testing
FLASK_DEBUG=false
SLACK_BOT_TOKEN=xoxb-test-token
SLACK_SIGNING_SECRET=test-secret
AWS_ACCESS_KEY_ID=test-key
AWS_SECRET_ACCESS_KEY=test-secret
AWS_REGION=us-east-1
""")
    
    # Create virtual environment if needed
    if not Path('venv').exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    
    # Install dependencies
    if not run_command("venv/bin/pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    return True


def run_pytest_tests():
    """Run pytest test suite"""
    print("\n🧪 Running pytest tests...")
    
    # Run tests with verbose output
    cmd = "venv/bin/python -m pytest tests/ -v --tb=short"
    return run_command(cmd, "Running pytest test suite")


def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running integration tests...")
    
    # Start app in background
    print("🚀 Starting Flask app for integration tests...")
    app_process = subprocess.Popen(
        ["venv/bin/python", "app.py"],
        env={**os.environ, 'TEST_MODE': 'true'},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    try:
        # Wait for app to start
        import time
        time.sleep(3)
        
        # Run integration tests
        success = run_command(
            "venv/bin/python -m pytest tests/test_integration.py -v",
            "Running integration tests"
        )
        
        return success
    finally:
        # Clean up
        app_process.terminate()
        app_process.wait()


def run_docker_tests():
    """Run Docker tests (optional)"""
    print("\n🐳 Running Docker tests...")
    
    # Check if Docker is available
    if not run_command("docker --version", "Checking Docker availability"):
        print("⚠️  Docker not available, skipping Docker tests")
        return True
    
    # Check if Docker Compose is available
    docker_compose_cmd = None
    if run_command("docker-compose --version", "Checking docker-compose"):
        docker_compose_cmd = "docker-compose"
    elif run_command("docker compose version", "Checking docker compose"):
        docker_compose_cmd = "docker compose"
    else:
        print("⚠️  Docker Compose not available, skipping Docker tests")
        return True
    
    # Run Docker tests
    print(f"🐳 Using {docker_compose_cmd}")
    
    # Stop any existing containers
    run_command(f"{docker_compose_cmd} down", "Stopping existing containers")
    
    # Build and start
    if not run_command(f"{docker_compose_cmd} up -d --build", "Building and starting container"):
        return False
    
    # Wait for container to be ready
    import time
    time.sleep(10)
    
    # Test health endpoint
    if not run_command("curl -f http://localhost:5000/health", "Testing health endpoint"):
        run_command(f"{docker_compose_cmd} down", "Cleaning up containers")
        return False
    
    # Clean up
    run_command(f"{docker_compose_cmd} down", "Cleaning up containers")
    return True


def main():
    """Main test runner"""
    print("🚀 EC2 Slack Bot - Test Runner")
    print("=" * 40)
    
    # Track overall success
    success = True
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        success = False
    
    # Run pytest tests
    if not run_pytest_tests():
        success = False
    
    # Run integration tests
    if not run_integration_tests():
        success = False
    
    # Run Docker tests (optional)
    if not run_docker_tests():
        print("⚠️  Docker tests failed (optional)")
    
    # Final results
    print("\n📊 Test Results Summary")
    print("=" * 30)
    
    if success:
        print("🎉 All critical tests passed!")
        print("\n✅ Your EC2 Slack Bot is ready for:")
        print("   1. Environment setup")
        print("   2. API functionality")
        print("   3. Database operations")
        print("   4. Integration flows")
        print("\n📝 Next steps:")
        print("   1. Configure real credentials in .env")
        print("   2. Deploy to production")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print("📝 Check the output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test runner script for the Mattermost MCP Python client.

This script provides a convenient way to run different categories of tests
with appropriate configurations and environment setup.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description="", check=True):
    """Run a command and handle output."""
    if description:
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print('='*60)
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        if check:
            sys.exit(1)
        return e


def check_dependencies():
    """Check if test dependencies are installed."""
    try:
        import pytest
        import httpx_mock
        import mcp_mattermost
        return True
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install test dependencies with: pip install -e '.[test]'")
        return False


def run_unit_tests(verbose=True, coverage=True):
    """Run unit tests."""
    cmd = ["python", "-m", "pytest"]
    
    # Add test files (exclude integration tests)
    test_files = [
        "tests/test_api_exceptions.py",
        "tests/test_http_client.py",
        "tests/test_services.py",
        "tests/test_server.py",
    ]
    cmd.extend(test_files)
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=mcp_mattermost",
            "--cov-report=term-missing",
            "--cov-report=html:coverage_html"
        ])
    
    return run_command(cmd, "Running Unit Tests")


def run_mock_integration_tests(verbose=True):
    """Run mocked integration tests."""
    cmd = [
        "python", "-m", "pytest", 
        "tests/test_integration.py::TestMockIntegration",
    ]
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    return run_command(cmd, "Running Mocked Integration Tests")


def run_live_integration_tests(verbose=True):
    """Run live integration tests."""
    # Check if integration tests are configured
    required_env = ["MATTERMOST_URL", "MATTERMOST_TOKEN", "MATTERMOST_TEAM_ID"]
    missing_env = [var for var in required_env if not os.getenv(var)]
    
    if os.getenv("MATTERMOST_INTEGRATION_TESTS", "false").lower() != "true":
        print("⚠️  Live integration tests are disabled")
        print("💡 To enable: export MATTERMOST_INTEGRATION_TESTS=true")
        return None
    
    if missing_env:
        print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
        print("💡 Set these variables to run live integration tests:")
        for var in missing_env:
            print(f"   export {var}=your-value")
        return None
    
    print("⚠️  WARNING: Live tests will make real API calls to your Mattermost instance!")
    print(f"🌐 Target: {os.getenv('MATTERMOST_URL')}")
    print(f"👥 Team: {os.getenv('MATTERMOST_TEAM_ID')}")
    if os.getenv('MATTERMOST_TEST_CHANNEL_ID'):
        print(f"💬 Test Channel: {os.getenv('MATTERMOST_TEST_CHANNEL_ID')}")
    else:
        print("💬 No test channel configured - some tests will be skipped")
    
    # Ask for confirmation
    response = input("\n🤔 Continue with live tests? (y/N): ").lower()
    if response not in ['y', 'yes']:
        print("🚫 Live integration tests skipped")
        return None
    
    cmd = [
        "python", "-m", "pytest",
        "tests/test_integration.py::TestLiveIntegration",
    ]
    
    if verbose:
        cmd.extend(["-v", "-s"])
    
    return run_command(cmd, "Running Live Integration Tests", check=False)


def run_all_tests(verbose=True, coverage=True, include_live=False):
    """Run all test categories."""
    results = []
    
    # Unit tests
    result = run_unit_tests(verbose=verbose, coverage=coverage)
    results.append(("Unit Tests", result.returncode if result else 1))
    
    # Mocked integration tests
    result = run_mock_integration_tests(verbose=verbose)
    results.append(("Mock Integration Tests", result.returncode if result else 1))
    
    # Live integration tests (if requested and configured)
    if include_live:
        result = run_live_integration_tests(verbose=verbose)
        if result:
            results.append(("Live Integration Tests", result.returncode))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    all_passed = True
    for test_category, returncode in results:
        status = "✅ PASSED" if returncode == 0 else "❌ FAILED"
        print(f"{test_category:25} {status}")
        if returncode != 0:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n💥 Some tests failed!")
        return 1


def generate_test_report():
    """Generate a comprehensive test report."""
    print("📝 Generating comprehensive test report...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=mcp_mattermost",
        "--cov-report=html:test_report/coverage",
        "--cov-report=json:test_report/coverage.json",
        "--cov-report=term",
        "--junitxml=test_report/junit.xml",
        "-v",
        "--tb=short",
    ]
    
    # Create report directory
    os.makedirs("test_report", exist_ok=True)
    
    result = run_command(cmd, "Generating Test Report", check=False)
    
    if result.returncode == 0:
        print("\n📋 Test report generated in 'test_report/' directory")
        print("   - coverage/index.html: HTML coverage report")
        print("   - coverage.json: JSON coverage data")
        print("   - junit.xml: JUnit test results")
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for Mattermost MCP Python client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py unit                    # Run unit tests only
  python run_tests.py mock                    # Run mocked integration tests
  python run_tests.py live                    # Run live integration tests (if configured)
  python run_tests.py all                     # Run all tests except live
  python run_tests.py all --include-live     # Run all tests including live
  python run_tests.py report                 # Generate comprehensive test report
  
Environment Variables for Live Tests:
  MATTERMOST_INTEGRATION_TESTS=true          # Enable live tests
  MATTERMOST_URL=https://your-instance.com   # Mattermost server URL
  MATTERMOST_TOKEN=your-token                 # Bot access token
  MATTERMOST_TEAM_ID=your-team-id            # Team ID for testing
  MATTERMOST_TEST_CHANNEL_ID=channel-id      # Optional test channel
        """
    )
    
    parser.add_argument(
        "test_type",
        choices=["unit", "mock", "live", "all", "report"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--no-verbose", "-q",
        action="store_true",
        help="Reduce test output verbosity"
    )
    
    parser.add_argument(
        "--no-coverage", 
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--include-live",
        action="store_true",
        help="Include live integration tests (only with 'all')"
    )
    
    args = parser.parse_args()
    
    print("🧪 Mattermost MCP Python Client - Test Runner")
    print(f"📁 Working directory: {Path.cwd()}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    verbose = not args.no_verbose
    coverage = not args.no_coverage
    
    if args.test_type == "unit":
        result = run_unit_tests(verbose=verbose, coverage=coverage)
        sys.exit(result.returncode if result else 1)
    
    elif args.test_type == "mock":
        result = run_mock_integration_tests(verbose=verbose)
        sys.exit(result.returncode if result else 1)
    
    elif args.test_type == "live":
        result = run_live_integration_tests(verbose=verbose)
        sys.exit(result.returncode if result else 1)
    
    elif args.test_type == "all":
        exit_code = run_all_tests(
            verbose=verbose, 
            coverage=coverage, 
            include_live=args.include_live
        )
        sys.exit(exit_code)
    
    elif args.test_type == "report":
        exit_code = generate_test_report()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

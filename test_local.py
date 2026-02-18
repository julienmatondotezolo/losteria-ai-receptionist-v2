#!/usr/bin/env python3
"""
Local testing script for L'Osteria AI Receptionist v2
Tests the core components without requiring full deployment
"""

import asyncio
import json
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv()

class TestRunner:
    """Test runner for local validation"""
    
    def __init__(self):
        self.base_url = "http://localhost:5010"
        self.results = []
    
    async def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/health", timeout=5.0)
                success = response.status_code == 200
                data = response.json() if success else None
                
                self.results.append({
                    "test": "Health Check",
                    "status": "✅ PASS" if success else "❌ FAIL",
                    "details": data if success else f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            self.results.append({
                "test": "Health Check", 
                "status": "❌ FAIL",
                "details": f"Connection error: {e}"
            })
    
    async def test_status_endpoint(self):
        """Test status endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/status", timeout=5.0)
                success = response.status_code == 200
                data = response.json() if success else None
                
                self.results.append({
                    "test": "Status Endpoint",
                    "status": "✅ PASS" if success else "❌ FAIL", 
                    "details": data if success else f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            self.results.append({
                "test": "Status Endpoint",
                "status": "❌ FAIL",
                "details": f"Connection error: {e}"
            })
    
    async def test_environment_variables(self):
        """Test that required environment variables are set"""
        required_vars = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN", 
            "TWILIO_PHONE_NUMBER"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        success = len(missing_vars) == 0
        
        self.results.append({
            "test": "Environment Variables",
            "status": "✅ PASS" if success else "⚠️ PARTIAL",
            "details": {
                "required": required_vars,
                "missing": missing_vars,
                "optional_missing": [
                    var for var in ["GROQ_API_KEY", "CARTESIA_API_KEY"] 
                    if not os.getenv(var)
                ]
            }
        })
    
    def test_dependencies(self):
        """Test that required Python packages are installed"""
        required_packages = [
            "fastapi", "uvicorn", "websockets", "twilio", 
            "groq", "httpx", "python-dotenv"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        success = len(missing_packages) == 0
        
        self.results.append({
            "test": "Python Dependencies",
            "status": "✅ PASS" if success else "❌ FAIL",
            "details": {
                "required": required_packages,
                "missing": missing_packages
            }
        })
    
    async def run_all_tests(self):
        """Run all tests and display results"""
        print("🧪 Running L'Osteria AI Receptionist v2 Tests...\n")
        
        # Test dependencies first (synchronous)
        self.test_dependencies()
        self.test_environment_variables()
        
        # Test API endpoints (asynchronous)  
        await self.test_health_check()
        await self.test_status_endpoint()
        
        # Display results
        print("📊 Test Results:")
        print("=" * 60)
        
        for result in self.results:
            print(f"🔸 {result['test']}: {result['status']}")
            if isinstance(result['details'], dict):
                for key, value in result['details'].items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {result['details']}")
            print()
        
        # Summary
        passed = sum(1 for r in self.results if "PASS" in r['status'])
        total = len(self.results)
        
        print("=" * 60)
        print(f"📈 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Ready for deployment.")
        else:
            print("⚠️  Some tests failed. Check configuration before deploying.")
        
        return passed == total

async def main():
    """Main test runner"""
    print("L'Osteria AI Receptionist v2 - Local Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing against: http://localhost:5010")
    print()
    
    # Check if server is supposed to be running
    print("💡 Make sure the server is running:")
    print("   python main.py")
    print()
    
    runner = TestRunner()
    success = await runner.run_all_tests()
    
    if success:
        print("\n🚀 Next steps:")
        print("1. Get API keys for Groq and Cartesia")
        print("2. Update .env file with real API keys")
        print("3. Run ./deploy.sh to deploy to VPS")
        print("4. Configure nginx and SSL")
        print("5. Update Twilio webhook URL")
    else:
        print("\n🔧 Fix the failed tests before proceeding.")

if __name__ == "__main__":
    asyncio.run(main())
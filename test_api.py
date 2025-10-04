#!/usr/bin/env python3
"""
Quick test script to verify the personal finance API endpoints.
Tests the core functionality without requiring the LLM server.
"""

import requests
import json
import sys
from datetime import date, datetime

# Test configuration
API_BASE = "http://127.0.0.1:8000"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on port 8000.")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_narrative_templates():
    """Test narrative templates endpoint."""
    print("\n🔍 Testing narrative templates endpoint...")
    try:
        response = requests.get(f"{API_BASE}/narrate/templates")
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', {})
            print(f"✅ Found {len(templates)} narrative templates:")
            for name in templates.keys():
                print(f"   - {name}")
            return True
        else:
            print(f"❌ Templates endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Templates test error: {e}")
        return False

def test_narrate_endpoint():
    """Test narrate endpoint (will fail if Hermes not running)."""
    print("\n🔍 Testing narrate endpoint...")
    try:
        # Simple test data
        test_request = {
            "template": "Generate a brief summary of these facts: {facts}",
            "facts": {
                "total_spent": "$1,234.56",
                "top_category": "Food & Dining",
                "transactions": 45
            }
        }
        
        response = requests.post(
            f"{API_BASE}/narrate",
            json=test_request,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Narrate endpoint working!")
            print(f"   Generated text: {data.get('text', '')[:100]}...")
            return True
        elif response.status_code == 503:
            print("⚠️  Narrate endpoint reachable but LLM server not available")
            print("   This is expected if Hermes is not running")
            return True  # Endpoint works, just no LLM
        else:
            print(f"❌ Narrate endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Narrate test error: {e}")
        return False

def test_available_forms():
    """Test forms endpoint."""
    print("\n🔍 Testing available forms endpoint...")
    try:
        response = requests.get(f"{API_BASE}/forms/available")
        if response.status_code == 200:
            data = response.json()
            forms = data.get('forms', [])
            print(f"✅ Forms endpoint working. Available forms: {len(forms)}")
            return True
        else:
            print(f"❌ Forms endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Forms test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Personal Finance API")
    print("=" * 50)
    
    tests = [
        test_health,
        test_narrative_templates,
        test_narrate_endpoint,
        test_available_forms
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Syntherion AI Backend API Testing Suite
Tests all backend endpoints including health, authentication, chat, and user management
"""

import requests
import json
import uuid
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "https://9cb6fa81-a1c2-4384-8647-fb04d744403a.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test data
TEST_EMAIL = "testuser@syntherion.ai"
TEST_PASSWORD = "TestPassword123!"
TEST_MESSAGES = [
    {"role": "user", "content": "Hello, can you help me with a simple question?"}
]

class SyntherionAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.session_id = str(uuid.uuid4())
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {test_name}")
        print(f"   {message}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        return success
    
    def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy' and 'timestamp' in data:
                    return self.log_test("Health Check", True, 
                                       f"Health endpoint returned healthy status with timestamp: {data.get('timestamp')}")
                else:
                    return self.log_test("Health Check", False, 
                                       "Health endpoint returned 200 but invalid response format", data)
            else:
                return self.log_test("Health Check", False, 
                                   f"Health endpoint returned status {response.status_code}", 
                                   response.text)
                
        except Exception as e:
            return self.log_test("Health Check", False, f"Exception occurred: {str(e)}")
    
    def test_cors_headers(self):
        """Test CORS headers on OPTIONS request"""
        try:
            response = self.session.options(f"{API_BASE}/health", timeout=10)
            
            headers = response.headers
            cors_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
            
            missing_headers = []
            for header, expected_value in cors_headers.items():
                if header not in headers:
                    missing_headers.append(header)
                elif headers[header] != expected_value:
                    missing_headers.append(f"{header} (expected: {expected_value}, got: {headers[header]})")
            
            if not missing_headers and response.status_code == 200:
                return self.log_test("CORS Headers", True, "All CORS headers are properly configured")
            else:
                return self.log_test("CORS Headers", False, 
                                   f"CORS headers issues: {missing_headers}, Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("CORS Headers", False, f"Exception occurred: {str(e)}")
    
    def test_signup(self):
        """Test POST /api/auth/signup endpoint"""
        try:
            # Use unique email for each test run
            unique_email = f"test_{int(time.time())}@syntherion.ai"
            
            payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/signup", 
                                       json=payload, 
                                       timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'user' in data:
                    self.user_data = data['user']
                    return self.log_test("Authentication Signup", True, 
                                       f"User signup successful for {unique_email}")
                else:
                    return self.log_test("Authentication Signup", False, 
                                       "Signup returned 200 but invalid response format", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Authentication Signup", False, 
                                   f"Signup failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Authentication Signup", False, f"Exception occurred: {str(e)}")
    
    def test_signin(self):
        """Test POST /api/auth/signin endpoint"""
        try:
            # First create a user to sign in with
            unique_email = f"signin_test_{int(time.time())}@syntherion.ai"
            
            # Create user
            signup_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signup_response = self.session.post(f"{API_BASE}/auth/signup", 
                                              json=signup_payload, 
                                              timeout=15)
            
            if signup_response.status_code != 200:
                return self.log_test("Authentication Signin", False, 
                                   "Failed to create test user for signin test")
            
            # Wait a moment for user creation to complete
            time.sleep(2)
            
            # Now test signin
            signin_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/signin", 
                                       json=signin_payload, 
                                       timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'user' in data:
                    self.user_data = data['user']
                    return self.log_test("Authentication Signin", True, 
                                       f"User signin successful for {unique_email}")
                else:
                    return self.log_test("Authentication Signin", False, 
                                       "Signin returned 200 but invalid response format", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Authentication Signin", False, 
                                   f"Signin failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Authentication Signin", False, f"Exception occurred: {str(e)}")
    
    def test_user_info_unauthorized(self):
        """Test GET /api/auth/user endpoint without authentication"""
        try:
            # Test without authentication
            response = self.session.get(f"{API_BASE}/auth/user", timeout=10)
            
            if response.status_code == 401:
                data = response.json()
                if data.get('error') == 'Unauthorized':
                    return self.log_test("User Info (Unauthorized)", True, 
                                       "Correctly returned 401 for unauthenticated request")
                else:
                    return self.log_test("User Info (Unauthorized)", False, 
                                       "Returned 401 but wrong error message", data)
            else:
                return self.log_test("User Info (Unauthorized)", False, 
                                   f"Expected 401 but got {response.status_code}")
                
        except Exception as e:
            return self.log_test("User Info (Unauthorized)", False, f"Exception occurred: {str(e)}")
    
    def test_user_info_authorized(self):
        """Test GET /api/auth/user endpoint with authentication"""
        try:
            # First create and sign in a user
            unique_email = f"userinfo_test_{int(time.time())}@syntherion.ai"
            
            # Create user
            signup_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signup_response = self.session.post(f"{API_BASE}/auth/signup", 
                                              json=signup_payload, 
                                              timeout=15)
            
            if signup_response.status_code != 200:
                return self.log_test("User Info (Authorized)", False, 
                                   "Failed to create test user for user info test")
            
            # Sign in to get authentication
            signin_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signin_response = self.session.post(f"{API_BASE}/auth/signin", 
                                              json=signin_payload, 
                                              timeout=15)
            
            if signin_response.status_code != 200:
                return self.log_test("User Info (Authorized)", False, 
                                   "Failed to sign in test user for user info test")
            
            # Wait for authentication to be processed
            time.sleep(2)
            
            # Now test user info endpoint
            response = self.session.get(f"{API_BASE}/auth/user", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'user' in data and data['user'].get('email') == unique_email:
                    return self.log_test("User Info (Authorized)", True, 
                                       f"Successfully retrieved user info for {unique_email}")
                else:
                    return self.log_test("User Info (Authorized)", False, 
                                       "User info returned but invalid format or wrong user", data)
            elif response.status_code == 401:
                return self.log_test("User Info (Authorized)", False, 
                                   "Authentication failed - Supabase session may not be properly maintained")
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("User Info (Authorized)", False, 
                                   f"User info failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("User Info (Authorized)", False, f"Exception occurred: {str(e)}")
    
    def test_chat_unauthorized(self):
        """Test POST /api/chat endpoint without authentication"""
        try:
            payload = {
                "messages": TEST_MESSAGES,
                "sessionId": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat", 
                                       json=payload, 
                                       timeout=30)
            
            if response.status_code == 401:
                data = response.json()
                if data.get('error') == 'Unauthorized':
                    return self.log_test("Chat (Unauthorized)", True, 
                                       "Correctly returned 401 for unauthenticated chat request")
                else:
                    return self.log_test("Chat (Unauthorized)", False, 
                                       "Returned 401 but wrong error message", data)
            else:
                return self.log_test("Chat (Unauthorized)", False, 
                                   f"Expected 401 but got {response.status_code}")
                
        except Exception as e:
            return self.log_test("Chat (Unauthorized)", False, f"Exception occurred: {str(e)}")
    
    def test_chat_authorized(self):
        """Test POST /api/chat endpoint with authentication"""
        try:
            # First create and sign in a user
            unique_email = f"chat_test_{int(time.time())}@syntherion.ai"
            
            # Create user
            signup_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signup_response = self.session.post(f"{API_BASE}/auth/signup", 
                                              json=signup_payload, 
                                              timeout=15)
            
            if signup_response.status_code != 200:
                return self.log_test("Chat (Authorized)", False, 
                                   "Failed to create test user for chat test")
            
            # Sign in to get authentication
            signin_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signin_response = self.session.post(f"{API_BASE}/auth/signin", 
                                              json=signin_payload, 
                                              timeout=15)
            
            if signin_response.status_code != 200:
                return self.log_test("Chat (Authorized)", False, 
                                   "Failed to sign in test user for chat test")
            
            # Wait for authentication to be processed
            time.sleep(2)
            
            # Now test chat endpoint
            payload = {
                "messages": TEST_MESSAGES,
                "sessionId": self.session_id
            }
            
            response = self.session.post(f"{API_BASE}/chat", 
                                       json=payload, 
                                       timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'sessionId' in data and 'chatId' in data:
                    return self.log_test("Chat (Authorized)", True, 
                                       f"Chat successful - AI responded with: {data['message'][:100]}...")
                else:
                    return self.log_test("Chat (Authorized)", False, 
                                       "Chat returned 200 but invalid response format", data)
            elif response.status_code == 401:
                return self.log_test("Chat (Authorized)", False, 
                                   "Authentication failed - Supabase session may not be properly maintained")
            elif response.status_code == 500:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Chat (Authorized)", False, 
                                   "Chat failed with 500 error - likely OpenRouter API issue", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Chat (Authorized)", False, 
                                   f"Chat failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Chat (Authorized)", False, f"Exception occurred: {str(e)}")
    
    def test_chat_history_unauthorized(self):
        """Test GET /api/chats endpoint without authentication"""
        try:
            response = self.session.get(f"{API_BASE}/chats", timeout=10)
            
            if response.status_code == 401:
                data = response.json()
                if data.get('error') == 'Unauthorized':
                    return self.log_test("Chat History (Unauthorized)", True, 
                                       "Correctly returned 401 for unauthenticated chat history request")
                else:
                    return self.log_test("Chat History (Unauthorized)", False, 
                                       "Returned 401 but wrong error message", data)
            else:
                return self.log_test("Chat History (Unauthorized)", False, 
                                   f"Expected 401 but got {response.status_code}")
                
        except Exception as e:
            return self.log_test("Chat History (Unauthorized)", False, f"Exception occurred: {str(e)}")
    
    def test_chat_history_authorized(self):
        """Test GET /api/chats endpoint with authentication"""
        try:
            # First create and sign in a user
            unique_email = f"history_test_{int(time.time())}@syntherion.ai"
            
            # Create user
            signup_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signup_response = self.session.post(f"{API_BASE}/auth/signup", 
                                              json=signup_payload, 
                                              timeout=15)
            
            if signup_response.status_code != 200:
                return self.log_test("Chat History (Authorized)", False, 
                                   "Failed to create test user for chat history test")
            
            # Sign in to get authentication
            signin_payload = {
                "email": unique_email,
                "password": TEST_PASSWORD
            }
            
            signin_response = self.session.post(f"{API_BASE}/auth/signin", 
                                              json=signin_payload, 
                                              timeout=15)
            
            if signin_response.status_code != 200:
                return self.log_test("Chat History (Authorized)", False, 
                                   "Failed to sign in test user for chat history test")
            
            # Wait for authentication to be processed
            time.sleep(2)
            
            # Now test chat history endpoint
            response = self.session.get(f"{API_BASE}/chats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chats' in data and isinstance(data['chats'], list):
                    return self.log_test("Chat History (Authorized)", True, 
                                       f"Successfully retrieved chat history with {len(data['chats'])} chats")
                else:
                    return self.log_test("Chat History (Authorized)", False, 
                                       "Chat history returned but invalid format", data)
            elif response.status_code == 401:
                return self.log_test("Chat History (Authorized)", False, 
                                   "Authentication failed - Supabase session may not be properly maintained")
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Chat History (Authorized)", False, 
                                   f"Chat history failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Chat History (Authorized)", False, f"Exception occurred: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 80)
        print("SYNTHERION AI BACKEND API TESTING SUITE")
        print("=" * 80)
        print(f"Testing against: {API_BASE}")
        print(f"Test started at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        results = []
        
        # Basic functionality tests
        results.append(self.test_health_check())
        results.append(self.test_cors_headers())
        
        # Authentication tests
        results.append(self.test_signup())
        results.append(self.test_signin())
        
        # User info tests
        results.append(self.test_user_info_unauthorized())
        results.append(self.test_user_info_authorized())
        
        # Chat functionality tests
        results.append(self.test_chat_unauthorized())
        results.append(self.test_chat_authorized())
        
        # Chat history tests
        results.append(self.test_chat_history_unauthorized())
        results.append(self.test_chat_history_authorized())
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Backend API is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        
        print("=" * 80)
        
        return passed == total

if __name__ == "__main__":
    tester = SyntherionAPITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
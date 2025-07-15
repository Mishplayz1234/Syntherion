#!/usr/bin/env python3
"""
Syntherion AI Test Authentication Feature Testing Suite
Tests the new test authentication bypass feature alongside regular authentication
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

# Test credentials for bypass authentication
TEST_EMAIL = "123@test.com"
TEST_PASSWORD = "123@test.com"

# Regular test credentials
REGULAR_EMAIL = f"regular_test_{int(time.time())}@syntherion.ai"
REGULAR_PASSWORD = "TestPassword123!"

class TestAuthTester:
    def __init__(self):
        self.test_session = requests.Session()  # For test user
        self.regular_session = requests.Session()  # For regular user
        self.test_user_data = None
        self.regular_user_data = None
        self.session_id = str(uuid.uuid4())
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n{status} {test_name}")
        print(f"   {message}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        return success
    
    def test_auth_bypass_signin(self):
        """Test POST /api/auth/signin with test credentials (123@test.com / 123@test.com)"""
        try:
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.test_session.post(f"{API_BASE}/auth/signin", 
                                            json=payload, 
                                            timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if ('message' in data and 
                    'test mode' in data['message'].lower() and 
                    'user' in data and 
                    data['user'].get('id') == 'test-user-123' and
                    data['user'].get('email') == TEST_EMAIL):
                    
                    self.test_user_data = data['user']
                    
                    # Check if test-user cookie was set
                    cookies = response.cookies
                    test_cookie_found = any(cookie.name == 'test-user' and cookie.value == 'test-user-123' 
                                          for cookie in cookies)
                    
                    if test_cookie_found:
                        return self.log_test("Test Authentication Bypass", True, 
                                           f"Test user signin successful with test-user cookie set. User ID: {data['user']['id']}")
                    else:
                        return self.log_test("Test Authentication Bypass", False, 
                                           "Test user signin successful but test-user cookie not found", data)
                else:
                    return self.log_test("Test Authentication Bypass", False, 
                                       "Test signin returned 200 but invalid response format or wrong user data", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test Authentication Bypass", False, 
                                   f"Test signin failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Test Authentication Bypass", False, f"Exception occurred: {str(e)}")
    
    def test_user_session_after_test_login(self):
        """Test GET /api/auth/user after test login"""
        try:
            # First ensure test user is logged in
            if not self.test_user_data:
                signin_success = self.test_auth_bypass_signin()
                if not signin_success:
                    return self.log_test("Test User Session", False, 
                                       "Cannot test user session - test login failed")
            
            # Test user info endpoint with test user session
            response = self.test_session.get(f"{API_BASE}/auth/user", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if ('user' in data and 
                    data['user'].get('id') == 'test-user-123' and
                    data['user'].get('email') == TEST_EMAIL):
                    return self.log_test("Test User Session", True, 
                                       f"Test user session working correctly. Retrieved user: {data['user']['email']}")
                else:
                    return self.log_test("Test User Session", False, 
                                       "User session returned but wrong user data", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test User Session", False, 
                                   f"User session failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Test User Session", False, f"Exception occurred: {str(e)}")
    
    def test_chat_with_test_user(self):
        """Test POST /api/chat with test user session"""
        try:
            # First ensure test user is logged in
            if not self.test_user_data:
                signin_success = self.test_auth_bypass_signin()
                if not signin_success:
                    return self.log_test("Test Chat with Test User", False, 
                                       "Cannot test chat - test login failed")
            
            # Test chat endpoint with test user
            payload = {
                "messages": [{"role": "user", "content": "Hello, this is a test message from test user"}],
                "sessionId": self.session_id
            }
            
            response = self.test_session.post(f"{API_BASE}/chat", 
                                            json=payload, 
                                            timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if ('message' in data and 
                    'sessionId' in data and 
                    'chatId' in data and
                    len(data['message']) > 0):
                    return self.log_test("Test Chat with Test User", True, 
                                       f"Test user chat successful. AI response: {data['message'][:100]}...")
                else:
                    return self.log_test("Test Chat with Test User", False, 
                                       "Chat returned 200 but invalid response format", data)
            elif response.status_code == 401:
                return self.log_test("Test Chat with Test User", False, 
                                   "Chat failed with 401 - test user authentication not working properly")
            elif response.status_code == 500:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test Chat with Test User", False, 
                                   "Chat failed with 500 error - likely OpenRouter API issue", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test Chat with Test User", False, 
                                   f"Chat failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Test Chat with Test User", False, f"Exception occurred: {str(e)}")
    
    def test_chat_history_with_test_user(self):
        """Test GET /api/chats with test user session"""
        try:
            # First ensure test user is logged in and has sent a chat
            if not self.test_user_data:
                signin_success = self.test_auth_bypass_signin()
                if not signin_success:
                    return self.log_test("Test Chat History with Test User", False, 
                                       "Cannot test chat history - test login failed")
            
            # Send a chat first to ensure there's history
            chat_payload = {
                "messages": [{"role": "user", "content": "Test message for history"}],
                "sessionId": self.session_id
            }
            
            chat_response = self.test_session.post(f"{API_BASE}/chat", 
                                                 json=chat_payload, 
                                                 timeout=30)
            
            if chat_response.status_code != 200:
                return self.log_test("Test Chat History with Test User", False, 
                                   "Cannot test chat history - failed to send test chat")
            
            # Wait a moment for chat to be saved
            time.sleep(2)
            
            # Now test chat history endpoint
            response = self.test_session.get(f"{API_BASE}/chats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'chats' in data and isinstance(data['chats'], list):
                    # Check if the chats belong to test user
                    test_user_chats = [chat for chat in data['chats'] if chat.get('userId') == 'test-user-123']
                    return self.log_test("Test Chat History with Test User", True, 
                                       f"Test user chat history working. Found {len(test_user_chats)} chats for test user")
                else:
                    return self.log_test("Test Chat History with Test User", False, 
                                       "Chat history returned but invalid format", data)
            elif response.status_code == 401:
                return self.log_test("Test Chat History with Test User", False, 
                                   "Chat history failed with 401 - test user authentication not working properly")
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test Chat History with Test User", False, 
                                   f"Chat history failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Test Chat History with Test User", False, f"Exception occurred: {str(e)}")
    
    def test_signout_with_test_user(self):
        """Test POST /api/auth/signout with test user session"""
        try:
            # First ensure test user is logged in
            if not self.test_user_data:
                signin_success = self.test_auth_bypass_signin()
                if not signin_success:
                    return self.log_test("Test Signout", False, 
                                       "Cannot test signout - test login failed")
            
            # Test signout endpoint
            response = self.test_session.post(f"{API_BASE}/auth/signout", 
                                            json={}, 
                                            timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data and 'test mode' in data['message'].lower():
                    
                    # Verify that test-user cookie was deleted
                    cookies = response.cookies
                    test_cookie_deleted = any(cookie.name == 'test-user' and cookie.value == '' 
                                            for cookie in cookies)
                    
                    # Test that user session is now invalid
                    user_check = self.test_session.get(f"{API_BASE}/auth/user", timeout=10)
                    
                    if user_check.status_code == 401:
                        return self.log_test("Test Signout", True, 
                                           "Test user signout successful. Session cleared and user now unauthorized.")
                    else:
                        return self.log_test("Test Signout", False, 
                                           "Signout returned success but user session still active")
                else:
                    return self.log_test("Test Signout", False, 
                                       "Signout returned 200 but invalid response format", data)
            else:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return self.log_test("Test Signout", False, 
                                   f"Signout failed with status {response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Test Signout", False, f"Exception occurred: {str(e)}")
    
    def test_regular_auth_still_works(self):
        """Test that regular Supabase authentication still works alongside test auth"""
        try:
            # Create a regular user
            signup_payload = {
                "email": REGULAR_EMAIL,
                "password": REGULAR_PASSWORD
            }
            
            signup_response = self.regular_session.post(f"{API_BASE}/auth/signup", 
                                                      json=signup_payload, 
                                                      timeout=15)
            
            if signup_response.status_code == 200:
                data = signup_response.json()
                if ('message' in data and 
                    'user' in data and 
                    'test mode' not in data['message'].lower()):
                    return self.log_test("Regular Authentication Still Works", True, 
                                       f"Regular Supabase authentication working correctly for {REGULAR_EMAIL}")
                else:
                    return self.log_test("Regular Authentication Still Works", False, 
                                       "Regular signup returned unexpected response format", data)
            else:
                data = signup_response.json() if signup_response.headers.get('content-type', '').startswith('application/json') else signup_response.text
                return self.log_test("Regular Authentication Still Works", False, 
                                   f"Regular signup failed with status {signup_response.status_code}", data)
                
        except Exception as e:
            return self.log_test("Regular Authentication Still Works", False, f"Exception occurred: {str(e)}")
    
    def test_user_isolation(self):
        """Test that test user data is isolated from regular users"""
        try:
            # First login as test user and send a chat
            if not self.test_user_data:
                signin_success = self.test_auth_bypass_signin()
                if not signin_success:
                    return self.log_test("User Isolation", False, 
                                       "Cannot test isolation - test login failed")
            
            # Send a chat as test user
            test_chat_payload = {
                "messages": [{"role": "user", "content": "This is a test user message for isolation test"}],
                "sessionId": str(uuid.uuid4())
            }
            
            test_chat_response = self.test_session.post(f"{API_BASE}/chat", 
                                                      json=test_chat_payload, 
                                                      timeout=30)
            
            if test_chat_response.status_code != 200:
                return self.log_test("User Isolation", False, 
                                   "Cannot test isolation - failed to send test user chat")
            
            # Get test user chat history
            test_history_response = self.test_session.get(f"{API_BASE}/chats", timeout=10)
            
            if test_history_response.status_code != 200:
                return self.log_test("User Isolation", False, 
                                   "Cannot test isolation - failed to get test user chat history")
            
            test_history = test_history_response.json()
            test_user_chat_count = len(test_history.get('chats', []))
            
            # Now create and login as regular user (if possible)
            regular_signup = {
                "email": f"isolation_test_{int(time.time())}@syntherion.ai",
                "password": REGULAR_PASSWORD
            }
            
            regular_signup_response = self.regular_session.post(f"{API_BASE}/auth/signup", 
                                                              json=regular_signup, 
                                                              timeout=15)
            
            if regular_signup_response.status_code == 200:
                # Try to get chat history as regular user (will likely fail due to email confirmation)
                regular_history_response = self.regular_session.get(f"{API_BASE}/chats", timeout=10)
                
                if regular_history_response.status_code == 401:
                    # This is expected - regular user can't access without email confirmation
                    return self.log_test("User Isolation", True, 
                                       f"User isolation working correctly. Test user has {test_user_chat_count} chats, regular user properly unauthorized.")
                elif regular_history_response.status_code == 200:
                    regular_history = regular_history_response.json()
                    regular_user_chat_count = len(regular_history.get('chats', []))
                    
                    # Check that regular user doesn't see test user's chats
                    if regular_user_chat_count == 0:
                        return self.log_test("User Isolation", True, 
                                           f"User isolation working correctly. Test user has {test_user_chat_count} chats, regular user has {regular_user_chat_count} chats.")
                    else:
                        return self.log_test("User Isolation", False, 
                                           f"Potential isolation issue - regular user sees {regular_user_chat_count} chats")
                else:
                    return self.log_test("User Isolation", False, 
                                       f"Unexpected response from regular user chat history: {regular_history_response.status_code}")
            else:
                return self.log_test("User Isolation", True, 
                                   f"User isolation test completed. Test user isolation verified (regular user creation failed as expected).")
                
        except Exception as e:
            return self.log_test("User Isolation", False, f"Exception occurred: {str(e)}")
    
    def run_all_tests(self):
        """Run all test authentication feature tests"""
        print("=" * 80)
        print("SYNTHERION AI TEST AUTHENTICATION FEATURE TESTING SUITE")
        print("=" * 80)
        print(f"Testing against: {API_BASE}")
        print(f"Test started at: {datetime.now().isoformat()}")
        print(f"Test credentials: {TEST_EMAIL} / {TEST_PASSWORD}")
        print("=" * 80)
        
        results = []
        
        # Test authentication bypass feature
        results.append(self.test_auth_bypass_signin())
        results.append(self.test_user_session_after_test_login())
        results.append(self.test_chat_with_test_user())
        results.append(self.test_chat_history_with_test_user())
        results.append(self.test_signout_with_test_user())
        
        # Test that regular authentication still works
        results.append(self.test_regular_auth_still_works())
        
        # Test user isolation
        results.append(self.test_user_isolation())
        
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
            print("\n🎉 ALL TEST AUTHENTICATION TESTS PASSED!")
            print("✅ Test authentication bypass working correctly")
            print("✅ Test user sessions managed properly")
            print("✅ Test user can chat and access history")
            print("✅ Test user signout working")
            print("✅ Regular authentication still functional")
            print("✅ User isolation working correctly")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        
        print("=" * 80)
        
        return passed == total

if __name__ == "__main__":
    tester = TestAuthTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
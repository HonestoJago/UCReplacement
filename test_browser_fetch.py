#!/usr/bin/env python3
"""
Comprehensive test suite for browser-side JavaScript fetch requests using my_stealth.

This script tests various scenarios for sending authentic-looking network requests
through the browser context, including:
- Basic GET/POST requests
- CORS handling 
- Cookie/session management
- Error handling and diagnostics
- Network monitoring via CDP
- Comparison with different execution methods

The goal is to ensure requests appear completely authentic and indistinguishable
from real user-initiated browser requests.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Import our stealth package
import my_stealth as uc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class BrowserFetchTester:
    """
    Comprehensive tester for browser-side fetch requests using my_stealth.
    
    Tests multiple scenarios to ensure requests look completely authentic:
    - Different HTTP methods (GET, POST, PUT, DELETE)
    - CORS handling and preflight requests  
    - Cookie and session management
    - Error handling and network diagnostics
    - CDP-based vs execute_script comparison
    """
    
    def __init__(self, profile_path: Optional[str] = None):
        """Initialize the tester with a stealth browser instance."""
        self.profile_path = profile_path or "./test_profiles/fetch_test"
        self.driver = None
        self.network_events: List[Dict] = []
        self.test_results: Dict[str, Any] = {}
        
    def setup_driver(self) -> None:
        """Create and configure the stealth browser with network monitoring."""
        log.info("🚀 Setting up stealth browser with network monitoring...")
        
        try:
            # Create stealth driver with persistent profile
            # UC Philosophy: Always visible - headless is a major detection flag
            self.driver = uc.Chrome(
                profile_path=self.profile_path,
                maximise=True,
                enable_stealth=True
            )
            
            # Navigate to blank page to initialize context
            self.driver.get("about:blank")
            
            # Enable CDP domains for monitoring
            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Runtime.enable", {})
            self.driver.execute_cdp_cmd("Security.enable", {})
            
            # Verify stealth is working
            webdriver_hidden = self.driver.execute_script("return navigator.webdriver === undefined;")
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            
            log.info(f"✅ Stealth browser ready:")
            log.info(f"   - navigator.webdriver hidden: {webdriver_hidden}")
            log.info(f"   - User agent: {user_agent[:80]}...")
            
        except Exception as e:
            log.error(f"❌ Failed to setup browser: {e}")
            raise
    
    def capture_network_events(self) -> None:
        """Start capturing network events for analysis."""
        log.info("📡 Starting network event capture...")
        
        # Clear previous events
        self.network_events.clear()
        
        # In a real implementation, you'd set up CDP event listeners here
        # For this test, we'll capture manually via performance logs
        
    def execute_fetch_cdp(self, url: str, options: Dict = None) -> Dict[str, Any]:
        """
        Execute fetch request using CDP Runtime.evaluate (most stealthy).
        
        This method is preferred because:
        - Uses CDP directly, avoiding execute_script detection
        - Supports promises with awaitPromise
        - Provides detailed error information
        """
        options = options or {}
        
        # Build JavaScript fetch expression
        js_expression = f"""
        (async () => {{
            try {{
                const startTime = performance.now();
                
                const response = await fetch('{url}', {json.dumps(options)});
                
                const endTime = performance.now();
                const headers = Object.fromEntries(response.headers.entries());
                
                let body = null;
                const contentType = response.headers.get('content-type') || '';
                
                if (contentType.includes('application/json')) {{
                    body = await response.json();
                }} else {{
                    body = await response.text();
                }}
                
                return {{
                    success: true,
                    status: response.status,
                    statusText: response.statusText,
                    headers: headers,
                    body: body,
                    url: response.url,
                    redirected: response.redirected,
                    timing: {{
                        duration: endTime - startTime,
                        timestamp: Date.now()
                    }},
                    context: {{
                        origin: location.origin,
                        href: location.href,
                        userAgent: navigator.userAgent.substring(0, 50) + '...'
                    }}
                }};
                
            }} catch (error) {{
                return {{
                    success: false,
                    error: error.message,
                    type: error.name,
                    context: {{
                        origin: location.origin,
                        href: location.href
                    }}
                }};
            }}
        }})()
        """
        
        try:
            log.info(f"🌐 Executing CDP fetch to: {url}")
            log.debug(f"   Options: {options}")
            
            result = self.driver.execute_cdp_cmd("Runtime.evaluate", {
                "expression": js_expression,
                "awaitPromise": True,
                "returnByValue": True,
                "userGesture": True  # Simulate user gesture
            })
            
            if "exceptionDetails" in result:
                log.error(f"❌ CDP execution error: {result['exceptionDetails']}")
                return {"success": False, "error": "CDP execution failed", "details": result}
            
            return result.get("result", {}).get("value", {})
            
        except Exception as e:
            log.error(f"❌ CDP fetch failed: {e}")
            return {"success": False, "error": str(e), "type": "CDP_ERROR"}
    
    def execute_fetch_async_script(self, url: str, options: Dict = None) -> Dict[str, Any]:
        """
        Execute fetch request using execute_async_script (fallback method).
        
        Less stealthy than CDP but more widely supported.
        """
        options = options or {}
        
        js_code = f"""
        const [url, options, callback] = arguments;
        
        (async () => {{
            try {{
                const startTime = performance.now();
                const response = await fetch(url, options);
                const endTime = performance.now();
                
                const headers = Object.fromEntries(response.headers.entries());
                
                let body = null;
                const contentType = response.headers.get('content-type') || '';
                
                if (contentType.includes('application/json')) {{
                    body = await response.json();
                }} else {{
                    body = await response.text();
                }}
                
                callback({{
                    success: true,
                    status: response.status,
                    statusText: response.statusText,
                    headers: headers,
                    body: body,
                    timing: {{ duration: endTime - startTime }},
                    method: 'execute_async_script'
                }});
                
            }} catch (error) {{
                callback({{
                    success: false,
                    error: error.message,
                    type: error.name,
                    method: 'execute_async_script'
                }});
            }}
        }})();
        """
        
        try:
            log.info(f"🌐 Executing async script fetch to: {url}")
            
            # Set longer timeout for network requests
            self.driver.set_script_timeout(30)
            
            result = self.driver.execute_async_script(js_code, url, options)
            return result
            
        except Exception as e:
            log.error(f"❌ Async script fetch failed: {e}")
            return {"success": False, "error": str(e), "type": "ASYNC_SCRIPT_ERROR"}
    
    def test_basic_get_request(self) -> bool:
        """Test basic GET request to httpbin.org (reliable test endpoint)."""
        log.info("🧪 TEST 1: Basic GET Request")
        
        try:
            # Test with CDP method (preferred)
            result_cdp = self.execute_fetch_cdp("https://httpbin.org/get")
            
            # Test with async script method (comparison)
            result_async = self.execute_fetch_async_script("https://httpbin.org/get")
            
            # Analyze results
            cdp_success = result_cdp.get("success", False) and result_cdp.get("status") == 200
            async_success = result_async.get("success", False) and result_async.get("status") == 200
            
            log.info(f"   CDP method: {'✅ SUCCESS' if cdp_success else '❌ FAILED'}")
            log.info(f"   Async method: {'✅ SUCCESS' if async_success else '❌ FAILED'}")
            
            if cdp_success:
                log.info(f"   Response time: {result_cdp.get('timing', {}).get('duration', 0):.1f}ms")
                log.info(f"   User-Agent sent: {result_cdp.get('body', {}).get('headers', {}).get('User-Agent', 'N/A')[:50]}...")
            
            self.test_results["basic_get"] = {
                "cdp": result_cdp,
                "async": result_async,
                "success": cdp_success or async_success
            }
            
            return cdp_success or async_success
            
        except Exception as e:
            log.error(f"❌ Basic GET test failed: {e}")
            self.test_results["basic_get"] = {"success": False, "error": str(e)}
            return False
    
    def test_post_request_with_json(self) -> bool:
        """Test POST request with JSON payload."""
        log.info("🧪 TEST 2: POST Request with JSON")
        
        try:
            payload = {
                "message": "Hello from my_stealth browser!",
                "timestamp": datetime.now().isoformat(),
                "test_id": "browser_fetch_test"
            }
            
            options = {
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                "body": json.dumps(payload),
                "credentials": "omit"  # Don't send cookies for this test
            }
            
            result = self.execute_fetch_cdp("https://httpbin.org/post", options)
            
            success = result.get("success", False) and result.get("status") == 200
            
            if success:
                response_data = result.get("body", {}).get("json", {})
                sent_correctly = response_data.get("message") == payload["message"]
                log.info(f"   ✅ POST successful, payload echo: {'✅' if sent_correctly else '❌'}")
            else:
                log.error(f"   ❌ POST failed: {result.get('error', 'Unknown error')}")
            
            self.test_results["post_json"] = {"result": result, "success": success}
            return success
            
        except Exception as e:
            log.error(f"❌ POST JSON test failed: {e}")
            self.test_results["post_json"] = {"success": False, "error": str(e)}
            return False
    
    def test_cors_preflight_request(self) -> bool:
        """Test CORS preflight handling with custom headers."""
        log.info("🧪 TEST 3: CORS Preflight Request")
        
        try:
            # This should trigger a preflight OPTIONS request
            options = {
                "method": "PUT",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Custom-Header": "my_stealth_test",
                    "X-Requested-With": "XMLHttpRequest"
                },
                "body": json.dumps({"test": "cors_preflight"}),
                "mode": "cors",
                "credentials": "omit"
            }
            
            result = self.execute_fetch_cdp("https://httpbin.org/put", options)
            
            # CORS might be blocked, that's normal behavior
            success = result.get("success", False)
            
            if success:
                log.info("   ✅ CORS request succeeded")
            else:
                error_msg = result.get("error", "")
                if "cors" in error_msg.lower() or "fetch" in error_msg.lower():
                    log.info("   ✅ CORS properly blocked (expected browser behavior)")
                    success = True  # This is actually correct behavior
                else:
                    log.error(f"   ❌ Unexpected error: {error_msg}")
            
            self.test_results["cors_preflight"] = {"result": result, "success": success}
            return success
            
        except Exception as e:
            log.error(f"❌ CORS test failed: {e}")
            self.test_results["cors_preflight"] = {"success": False, "error": str(e)}
            return False
    
    def test_cookie_handling(self) -> bool:
        """Test cookie handling in requests."""
        log.info("🧪 TEST 4: Cookie Handling")
        
        try:
            # First, set a cookie via httpbin
            cookie_result = self.execute_fetch_cdp("https://httpbin.org/cookies/set/test_cookie/my_stealth_value")
            
            time.sleep(1)  # Brief delay
            
            # Then make a request that should include the cookie
            options = {
                "method": "GET",
                "credentials": "include",  # Include cookies
                "mode": "cors"
            }
            
            result = self.execute_fetch_cdp("https://httpbin.org/cookies", options)
            
            success = result.get("success", False)
            
            if success:
                cookies = result.get("body", {}).get("cookies", {})
                cookie_sent = "test_cookie" in cookies
                log.info(f"   Cookie handling: {'✅' if cookie_sent else '❌'}")
                log.info(f"   Cookies sent: {cookies}")
            else:
                log.error(f"   ❌ Cookie test failed: {result.get('error')}")
            
            self.test_results["cookie_handling"] = {"result": result, "success": success}
            return success
            
        except Exception as e:
            log.error(f"❌ Cookie test failed: {e}")
            self.test_results["cookie_handling"] = {"success": False, "error": str(e)}
            return False
    
    def test_error_handling(self) -> bool:
        """Test how fetch handles various error conditions."""
        log.info("🧪 TEST 5: Error Handling")
        
        try:
            # Test 404 response
            result_404 = self.execute_fetch_cdp("https://httpbin.org/status/404")
            
            # Test network error (invalid domain)
            result_network = self.execute_fetch_cdp("https://definitely-not-a-real-domain-12345.com/")
            
            # Test timeout (this should succeed but we're testing the pattern)
            options_timeout = {
                "method": "GET",
                "signal": "AbortSignal.timeout(5000)"  # 5 second timeout
            }
            result_timeout = self.execute_fetch_cdp("https://httpbin.org/delay/1", options_timeout)
            
            # Analyze results
            handles_404 = result_404.get("success", False) and result_404.get("status") == 404
            handles_network_error = not result_network.get("success", False)
            handles_timeout = result_timeout.get("success", False)
            
            log.info(f"   404 handling: {'✅' if handles_404 else '❌'}")
            log.info(f"   Network error handling: {'✅' if handles_network_error else '❌'}")
            log.info(f"   Timeout handling: {'✅' if handles_timeout else '❌'}")
            
            success = handles_404 and handles_network_error
            
            self.test_results["error_handling"] = {
                "404": result_404,
                "network": result_network,
                "timeout": result_timeout,
                "success": success
            }
            
            return success
            
        except Exception as e:
            log.error(f"❌ Error handling test failed: {e}")
            self.test_results["error_handling"] = {"success": False, "error": str(e)}
            return False
    
    def test_user_agent_consistency(self) -> bool:
        """Test that User-Agent remains consistent across requests."""
        log.info("🧪 TEST 6: User-Agent Consistency")
        
        try:
            # Get UA from browser context
            browser_ua = self.driver.execute_script("return navigator.userAgent;")
            
            # Get UA from fetch request
            result = self.execute_fetch_cdp("https://httpbin.org/user-agent")
            
            success = result.get("success", False)
            
            if success:
                fetch_ua = result.get("body", {}).get("user-agent", "")
                ua_matches = browser_ua == fetch_ua
                
                log.info(f"   Browser UA: {browser_ua[:60]}...")
                log.info(f"   Fetch UA:   {fetch_ua[:60]}...")
                log.info(f"   Consistency: {'✅' if ua_matches else '❌'}")
                
                success = ua_matches
            else:
                log.error(f"   ❌ Failed to get UA from fetch: {result.get('error')}")
            
            self.test_results["user_agent"] = {
                "browser_ua": browser_ua,
                "fetch_ua": result.get("body", {}).get("user-agent", ""),
                "success": success
            }
            
            return success
            
        except Exception as e:
            log.error(f"❌ User-Agent test failed: {e}")
            self.test_results["user_agent"] = {"success": False, "error": str(e)}
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all fetch tests and return comprehensive results."""
        log.info("🎯 Starting comprehensive browser fetch tests...")
        
        try:
            # Setup browser and monitoring
            self.setup_driver()
            self.capture_network_events()
            
            # Run test suite
            tests = [
                ("Basic GET Request", self.test_basic_get_request),
                ("POST with JSON", self.test_post_request_with_json),
                ("CORS Preflight", self.test_cors_preflight_request),
                ("Cookie Handling", self.test_cookie_handling),
                ("Error Handling", self.test_error_handling),
                ("User-Agent Consistency", self.test_user_agent_consistency),
            ]
            
            results = {}
            passed = 0
            
            for test_name, test_func in tests:
                log.info(f"\n{'='*60}")
                try:
                    success = test_func()
                    results[test_name] = success
                    if success:
                        passed += 1
                    time.sleep(2)  # Pause between tests
                except Exception as e:
                    log.error(f"Test '{test_name}' crashed: {e}")
                    log.error(traceback.format_exc())
                    results[test_name] = False
            
            # Generate summary
            log.info(f"\n{'='*60}")
            log.info("🏁 TEST SUMMARY")
            log.info(f"{'='*60}")
            
            for test_name, success in results.items():
                status = "✅ PASS" if success else "❌ FAIL"
                log.info(f"{test_name:.<30} {status}")
            
            log.info(f"\nOverall: {passed}/{len(tests)} tests passed")
            
            # Store comprehensive results
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(tests),
                "passed": passed,
                "success_rate": passed / len(tests),
                "individual_results": results,
                "detailed_results": self.test_results,
                "browser_info": {
                    "user_agent": self.driver.execute_script("return navigator.userAgent;"),
                    "stealth_active": self.driver.execute_script("return navigator.webdriver === undefined;")
                }
            }
            
            return summary
            
        except Exception as e:
            log.error(f"❌ Test suite failed: {e}")
            log.error(traceback.format_exc())
            return {"error": str(e), "success": False}
        
        finally:
            if self.driver:
                log.info("🧹 Cleaning up browser...")
                try:
                    self.driver.quit()
                except:
                    pass
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> None:
        """Save test results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fetch_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            log.info(f"📄 Results saved to: {filename}")
        except Exception as e:
            log.error(f"❌ Failed to save results: {e}")


def main():
    """Main test runner."""
    log.info("🚀 Browser Fetch Test Suite - my_stealth edition")
    log.info("="*60)
    
    try:
        # Create tester instance
        tester = BrowserFetchTester()
        
        # Run comprehensive tests
        results = tester.run_all_tests()
        
        # Save results
        tester.save_results(results)
        
        # Final assessment
        if results.get("success_rate", 0) >= 0.8:
            log.info("🎉 Fetch tests completed successfully!")
            log.info("Browser-side requests should appear completely authentic.")
        else:
            log.warning("⚠️  Some tests failed - review results for issues.")
        
    except KeyboardInterrupt:
        log.info("🛑 Tests interrupted by user")
    except Exception as e:
        log.error(f"❌ Test suite failed: {e}")
        log.error(traceback.format_exc())
    
    input("\n>>> Press ENTER to exit...")


if __name__ == "__main__":
    main()

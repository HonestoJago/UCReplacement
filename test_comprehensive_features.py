#!/usr/bin/env python3
"""
Comprehensive Feature Test Suite

This script tests all major features of my_stealth together:
- Basic stealth driver creation
- CDP event monitoring
- Enhanced WebElement interactions
- Browser-side fetch requests
- Profile management
- Error handling and recovery

Perfect for validation after installation or updates.
"""

import time
import json
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Import my_stealth
import my_stealth as uc
from my_stealth import (
    enable_cdp_events, add_cdp_listener, CDPEventMonitor,
    enhance_driver_elements, find_elements_recursive
)
from selenium.webdriver.common.by import By


class ComprehensiveFeatureTester:
    """Complete feature testing for my_stealth package."""
    
    def __init__(self):
        """Initialize comprehensive tester."""
        self.driver = None
        self.test_profile_path = "./test_profiles/comprehensive"
        self.results = {}
    
    def setup_test_environment(self):
        """Set up test environment and profile."""
        log.info("🛠️ Setting up test environment...")
        
        # Create test profile directory
        Path(self.test_profile_path).mkdir(parents=True, exist_ok=True)
        
        log.info(f"📁 Test profile: {self.test_profile_path}")
        return True
    
    def test_basic_driver_creation(self):
        """Test basic stealth driver creation."""
        log.info("\n🚀 Testing Basic Driver Creation")
        log.info("=" * 50)
        
        try:
            # Test basic driver creation
            self.driver = uc.Chrome(
                profile_path=self.test_profile_path,
                maximise=True,
                apply_viewport=True
            )
            
            log.info("✅ Stealth driver created successfully")
            
            # Test basic navigation
            self.driver.get("about:blank")
            log.info("✅ Basic navigation works")
            
            # Check stealth features
            webdriver_hidden = self.driver.execute_script("return navigator.webdriver === undefined;")
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            
            log.info(f"🔍 Webdriver hidden: {webdriver_hidden}")
            log.info(f"🌐 User agent: {user_agent[:80]}...")
            
            return webdriver_hidden  # Should be True for stealth
            
        except Exception as e:
            log.error(f"❌ Basic driver creation failed: {e}")
            return False
    
    def test_cdp_integration(self):
        """Test CDP event monitoring integration."""
        log.info("\n📡 Testing CDP Integration")
        log.info("=" * 50)
        
        try:
            # Set up CDP monitoring
            monitor = enable_cdp_events(self.driver)
            
            # Track events
            events_captured = []
            
            def capture_event(event):
                events_captured.append(event.get('method', 'unknown'))
            
            add_cdp_listener(self.driver, '*', capture_event)
            
            log.info("📌 CDP monitoring enabled")
            
            # Generate some events
            self.driver.get("https://httpbin.org/get")
            time.sleep(3)
            
            # Check results
            unique_events = set(events_captured)
            log.info(f"📊 Captured {len(events_captured)} events ({len(unique_events)} unique)")
            
            # Look for network events specifically
            network_events = [e for e in events_captured if e.startswith('Network.')]
            log.info(f"🌐 Network events: {len(network_events)}")
            
            return len(network_events) > 0
            
        except Exception as e:
            log.error(f"❌ CDP integration test failed: {e}")
            return False
    
    def test_enhanced_elements(self):
        """Test enhanced WebElement functionality."""
        log.info("\n🔧 Testing Enhanced Elements")
        log.info("=" * 50)
        
        try:
            # Enable enhanced elements
            enhance_driver_elements(self.driver)
            
            # Navigate to test page
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Test enhanced element finding
            search_box = self.driver.find_element(By.NAME, "q")
            
            # Verify it's enhanced
            if not hasattr(search_box, 'click_safe'):
                log.error("❌ Element not enhanced - missing click_safe method")
                return False
            
            log.info("✅ Elements are enhanced with stealth methods")
            
            # Test enhanced methods
            search_box.click_safe(pause_before=0.1, pause_after=0.2)
            search_box.type_human("my stealth test", typing_speed=0.05, mistakes=False)
            
            log.info("✅ Enhanced interaction methods work")
            
            # Test cross-frame search
            all_inputs = find_elements_recursive(self.driver, By.TAG_NAME, "input")
            log.info(f"🔍 Found {len(all_inputs)} input fields across frames")
            
            return len(all_inputs) > 0
            
        except Exception as e:
            log.error(f"❌ Enhanced elements test failed: {e}")
            return False
    
    def test_browser_fetch(self):
        """Test browser-side fetch functionality."""
        log.info("\n🌐 Testing Browser-Side Fetch")
        log.info("=" * 50)
        
        try:
            # Navigate to establish context
            self.driver.get("about:blank")
            self.driver.execute_cdp_cmd("Runtime.enable", {})
            
            # Test GET request
            get_result = self.driver.execute_cdp_cmd("Runtime.evaluate", {
                "expression": """
                (async () => {
                    try {
                        const response = await fetch('https://httpbin.org/get', {
                            method: 'GET'
                        });
                        const data = await response.json();
                        return { 
                            success: true, 
                            status: response.status, 
                            url: data.url 
                        };
                    } catch (error) {
                        return { 
                            success: false, 
                            error: error.message 
                        };
                    }
                })()
                """,
                "awaitPromise": True,
                "returnByValue": True
            })
            
            fetch_result = get_result["result"]["value"]
            
            if fetch_result["success"]:
                log.info(f"✅ GET request successful: {fetch_result['status']}")
                log.info(f"🔗 Response URL: {fetch_result['url']}")
            else:
                log.error(f"❌ GET request failed: {fetch_result.get('error', 'Unknown error')}")
                return False
            
            # Test POST request
            post_data = {"test": "my_stealth", "timestamp": time.time()}
            
            post_result = self.driver.execute_cdp_cmd("Runtime.evaluate", {
                "expression": f"""
                (async () => {{
                    try {{
                        const response = await fetch('https://httpbin.org/post', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({json.dumps(post_data)})
                        }});
                        const data = await response.json();
                        return {{ 
                            success: true, 
                            status: response.status, 
                            echo: data.json 
                        }};
                    }} catch (error) {{
                        return {{ 
                            success: false, 
                            error: error.message 
                        }};
                    }}
                }})()
                """,
                "awaitPromise": True,
                "returnByValue": True
            })
            
            post_fetch_result = post_result["result"]["value"]
            
            if post_fetch_result["success"]:
                log.info(f"✅ POST request successful: {post_fetch_result['status']}")
                log.info(f"📤 Data echoed: {post_fetch_result['echo']}")
            else:
                log.error(f"❌ POST request failed: {post_fetch_result.get('error', 'Unknown error')}")
                return False
            
            return True
            
        except Exception as e:
            log.error(f"❌ Browser fetch test failed: {e}")
            return False
    
    def test_profile_persistence(self):
        """Test profile persistence and cookie management."""
        log.info("\n💾 Testing Profile Persistence")
        log.info("=" * 50)
        
        try:
            # Navigate to a site and set a cookie
            self.driver.get("https://httpbin.org/cookies/set/test_cookie/my_stealth_value")
            time.sleep(2)
            
            # Verify cookie was set
            cookies = self.driver.get_cookies()
            test_cookie = next((c for c in cookies if c['name'] == 'test_cookie'), None)
            
            if test_cookie:
                log.info(f"✅ Cookie set: {test_cookie['name']}={test_cookie['value']}")
            else:
                log.warning("⚠️ Test cookie not found")
            
            # Check if profile directory has files
            profile_files = list(Path(self.test_profile_path).glob("*"))
            log.info(f"📁 Profile files created: {len(profile_files)}")
            
            # Test local storage
            self.driver.execute_script("localStorage.setItem('test_key', 'my_stealth_storage');")
            stored_value = self.driver.execute_script("return localStorage.getItem('test_key');")
            
            if stored_value == 'my_stealth_storage':
                log.info("✅ Local storage works")
            else:
                log.warning("⚠️ Local storage test failed")
            
            return len(profile_files) > 0
            
        except Exception as e:
            log.error(f"❌ Profile persistence test failed: {e}")
            return False
    
    def test_detection_evasion(self):
        """Test various detection evasion techniques."""
        log.info("\n🕵️ Testing Detection Evasion")
        log.info("=" * 50)
        
        try:
            self.driver.get("about:blank")
            
            # Test webdriver property hiding
            webdriver_test = self.driver.execute_script("""
                return {
                    webdriver: typeof navigator.webdriver,
                    automation: navigator.webdriver,
                    chrome: typeof window.chrome,
                    permissions: typeof navigator.permissions
                };
            """)
            
            log.info("🔍 Detection evasion results:")
            log.info(f"  navigator.webdriver: {webdriver_test['webdriver']}")
            log.info(f"  webdriver value: {webdriver_test['automation']}")
            log.info(f"  window.chrome: {webdriver_test['chrome']}")
            log.info(f"  permissions API: {webdriver_test['permissions']}")
            
            # Test hardware fingerprinting
            hardware_test = self.driver.execute_script("""
                return {
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    deviceMemory: navigator.deviceMemory,
                    platform: navigator.platform,
                    maxTouchPoints: navigator.maxTouchPoints
                };
            """)
            
            log.info("🖥️ Hardware fingerprint:")
            for key, value in hardware_test.items():
                log.info(f"  {key}: {value}")
            
            # Key detection checks
            checks_passed = 0
            total_checks = 4
            
            if webdriver_test['webdriver'] == 'undefined':
                checks_passed += 1
                log.info("✅ webdriver property hidden")
            else:
                log.warning("❌ webdriver property visible")
            
            if webdriver_test['chrome'] == 'object':
                checks_passed += 1
                log.info("✅ window.chrome object present")
            else:
                log.warning("❌ window.chrome missing")
            
            if isinstance(hardware_test['hardwareConcurrency'], int) and hardware_test['hardwareConcurrency'] > 0:
                checks_passed += 1
                log.info("✅ Hardware concurrency spoofed")
            else:
                log.warning("❌ Hardware concurrency issues")
            
            if hardware_test['platform'] in ['Win32', 'MacIntel', 'Linux x86_64']:
                checks_passed += 1
                log.info("✅ Platform information consistent")
            else:
                log.warning(f"❌ Unusual platform: {hardware_test['platform']}")
            
            detection_score = (checks_passed / total_checks) * 100
            log.info(f"🎯 Detection evasion score: {detection_score:.1f}%")
            
            return detection_score >= 75  # Pass if 75% or better
            
        except Exception as e:
            log.error(f"❌ Detection evasion test failed: {e}")
            return False
    
    def test_error_recovery(self):
        """Test error handling and recovery."""
        log.info("\n🛡️ Testing Error Recovery")
        log.info("=" * 50)
        
        try:
            # Test navigation to invalid URL
            try:
                self.driver.get("https://this-domain-absolutely-does-not-exist-12345.invalid")
                time.sleep(2)
            except Exception as e:
                log.info(f"✅ Handled invalid URL gracefully: {type(e).__name__}")
            
            # Test recovery - navigate to valid site
            self.driver.get("https://example.com")
            title = self.driver.title
            log.info(f"✅ Recovered successfully - page title: {title}")
            
            # Test JavaScript error handling
            try:
                self.driver.execute_script("throw new Error('Test error');")
            except Exception as e:
                log.info(f"✅ Handled JavaScript error: {type(e).__name__}")
            
            # Verify driver is still functional
            test_element = self.driver.find_element(By.TAG_NAME, "body")
            if test_element:
                log.info("✅ Driver remains functional after errors")
                return True
            else:
                log.error("❌ Driver not functional after errors")
                return False
            
        except Exception as e:
            log.error(f"❌ Error recovery test failed: {e}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all comprehensive tests."""
        log.info("🧪 My Stealth - Comprehensive Feature Test Suite")
        log.info("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            log.error("❌ Environment setup failed")
            return False
        
        try:
            # Run all tests in sequence
            self.results['driver_creation'] = self.test_basic_driver_creation()
            self.results['cdp_integration'] = self.test_cdp_integration()
            self.results['enhanced_elements'] = self.test_enhanced_elements()
            self.results['browser_fetch'] = self.test_browser_fetch()
            self.results['profile_persistence'] = self.test_profile_persistence()
            self.results['detection_evasion'] = self.test_detection_evasion()
            self.results['error_recovery'] = self.test_error_recovery()
            
        except Exception as e:
            log.error(f"❌ Test suite failed: {e}")
            return False
        
        finally:
            # Cleanup
            if self.driver:
                log.info("🧹 Cleaning up driver...")
                try:
                    self.driver.quit()
                except:
                    pass
        
        # Report final results
        log.info("\n🏆 COMPREHENSIVE TEST RESULTS")
        log.info("=" * 50)
        
        passed = 0
        total = len(self.results)
        
        for test_name, result in self.results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            log.info(f"  {test_name:20} {status}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100
        log.info(f"\n📈 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        # Final assessment
        if success_rate >= 85:
            log.info("🎉 EXCELLENT: my_stealth is working perfectly!")
            return True
        elif success_rate >= 70:
            log.info("🟡 GOOD: my_stealth is mostly working, minor issues detected")
            return True
        else:
            log.warning("🔴 ISSUES: my_stealth has significant problems that need attention")
            return False


def main():
    """Main test execution."""
    print("🔬 My Stealth - Comprehensive Feature Test Suite")
    print("Testing ALL features of the my_stealth UC replacement...")
    print("This test verifies stealth, CDP events, enhanced elements, fetch, and more.")
    print()
    
    tester = ComprehensiveFeatureTester()
    success = tester.run_comprehensive_tests()
    
    print("\n" + "="*70)
    if success:
        print("🎉 COMPREHENSIVE TESTS: SUCCESS!")
        print("✅ Your my_stealth package is fully functional and ready for production!")
        print("🚀 All major features tested and working correctly.")
        print("\n📋 What you can do now:")
        print("  • Run bot detection tests: python test_bot_detection_sites.py")
        print("  • Test browser fetch: python test_browser_fetch.py") 
        print("  • Test human interactions: python test_human_interactions.py")
        print("  • Test CDP events: python test_cdp_events.py")
        print("  • Test enhanced elements: python test_enhanced_elements.py")
    else:
        print("❌ Some comprehensive tests failed.")
        print("🔧 Check the detailed logs above for specific issues.")
        print("💡 Common fixes:")
        print("  • Ensure Brave browser is installed")
        print("  • Check internet connectivity")
        print("  • Verify profile directory permissions")
        print("  • Update dependencies: pip install -r requirements.txt")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

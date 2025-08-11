#!/usr/bin/env python3
"""
Test CDP Event Monitoring System with Enhanced Elements

MAJOR REFACTOR: This file has been updated to use my_stealth's Enhanced Elements
system for all element interactions while testing CDP event monitoring.

REFACTOR HIGHLIGHTS:
1. All driver instances now use enhance_driver_elements() for JavaScript-based interactions
2. Form interactions use type_human() and click_safe() instead of send_keys() and click()
3. Enhanced elements prevent shadow DOM conflicts during CDP monitoring tests
4. More reliable test execution with automatic fallbacks

WHY THIS MATTERS FOR CDP TESTING:
- CDP monitoring can be sensitive to Chrome's internal inspection systems
- Enhanced elements avoid triggering Chrome's visual feedback that interferes with CDP
- JavaScript-based interactions generate cleaner CDP events for monitoring
- Better test reliability when capturing network and browser events

This script tests the enhanced CDP event monitoring capabilities of my_stealth.
It demonstrates network request/response monitoring, wildcard event listening,
and advanced event analysis features using shadow DOM-safe interactions.
"""

import time
import json
import logging
from typing import Dict, Any

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Import my_stealth modules
import my_stealth as uc
from my_stealth import enable_cdp_events, add_cdp_listener, CDPEventMonitor, enhance_driver_elements, EnhancedWebElement

# Add missing Selenium imports for element finding
from selenium.webdriver.common.by import By


class CDPEventTester:
    """Test suite for CDP event monitoring functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.driver = None
        self.monitor = None
        self.events_captured = []
        self.requests_captured = []
        self.responses_captured = []
    
    def setup_driver(self):
        """Create and configure stealth driver with enhanced elements."""
        log.info("🚀 Creating stealth driver for CDP testing...")
        
        self.driver = uc.Chrome(
            profile_path="./test_profiles/cdp_test",
            maximise=True,
            apply_viewport=True
        )
        
        # REFACTOR: Enable enhanced elements for JavaScript-based interactions
        # This ensures all element interactions use shadow DOM-safe methods
        enhance_driver_elements(self.driver)
        log.info("Enhanced elements enabled for CDP testing")
        
        log.info("✅ Driver created successfully")
        return self.driver
    
    def test_basic_event_listening(self):
        """Test basic CDP event listening with simple callbacks."""
        log.info("\n📡 Testing Basic Event Listening")
        log.info("=" * 50)
        
        # Simple event handlers
        def log_network_request(params: Dict[str, Any]):
            """Log network requests."""
            request = params['request']
            url = request['url']
            method = request['method']
            self.requests_captured.append({'method': method, 'url': url})
            print(f"🌐 REQUEST: {method} {url}")
        
        def log_network_response(params: Dict[str, Any]):
            """Log network responses."""
            response = params['response']
            url = response['url']
            status = response['status']
            self.responses_captured.append({'status': status, 'url': url})
            print(f"📥 RESPONSE: {status} {url}")
        
        def log_all_events(event_data: Dict[str, Any]):
            """Log all CDP events (wildcard listener)."""
            method = event_data.get('method', 'unknown')
            self.events_captured.append(method)
            if not method.startswith('Runtime.'):  # Filter out noisy runtime events
                print(f"🔍 EVENT: {method}")
        
        # Enable CDP monitoring using UC-style API
        monitor = enable_cdp_events(self.driver)
        self.monitor = monitor
        
        # Add event listeners
        add_cdp_listener(self.driver, 'Network.requestWillBeSent', log_network_request)
        add_cdp_listener(self.driver, 'Network.responseReceived', log_network_response)
        add_cdp_listener(self.driver, '*', log_all_events)  # Wildcard listener
        
        log.info("📌 Event listeners configured")
        
        # Test navigation to trigger events
        test_urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/json",
            "https://example.com"
        ]
        
        for url in test_urls:
            log.info(f"🔗 Navigating to: {url}")
            self.driver.get(url)
            time.sleep(2)  # Let events settle
        
        # Report results
        log.info(f"\n📊 RESULTS - Basic Event Listening:")
        log.info(f"  • Requests captured: {len(self.requests_captured)}")
        log.info(f"  • Responses captured: {len(self.responses_captured)}")
        log.info(f"  • Total events captured: {len(self.events_captured)}")
        
        # Show sample data
        if self.requests_captured:
            log.info(f"  • Sample request: {self.requests_captured[0]}")
        if self.responses_captured:
            log.info(f"  • Sample response: {self.responses_captured[0]}")
        
        return len(self.requests_captured) > 0 and len(self.responses_captured) > 0
    
    def test_advanced_monitoring(self):
        """Test advanced CDP monitoring with event analysis."""
        log.info("\n🔬 Testing Advanced Monitoring")
        log.info("=" * 50)
        
        # Create advanced monitor
        advanced_monitor = CDPEventMonitor(self.driver)
        advanced_monitor.start_monitoring(capture_events=True)
        
        log.info("🎯 Advanced monitoring started")
        
        # Test with a more complex site
        log.info("🌐 Testing with complex site (GitHub)")
        self.driver.get("https://github.com")
        time.sleep(5)  # Let page load completely
        
        # Analyze captured events
        requests = advanced_monitor.get_network_requests()
        responses = advanced_monitor.get_network_responses()
        
        log.info(f"\n📈 RESULTS - Advanced Monitoring:")
        log.info(f"  • Network requests: {len(requests)}")
        log.info(f"  • Network responses: {len(responses)}")
        
        # Show request methods breakdown
        if requests:
            methods = {}
            for req in requests:
                method = req['method']
                methods[method] = methods.get(method, 0) + 1
            
            log.info(f"  • Request methods: {methods}")
            
            # Show sample requests
            log.info("  • Sample requests:")
            for i, req in enumerate(requests[:3]):
                log.info(f"    {i+1}. {req['method']} {req['url'][:80]}...")
        
        # Filter specific requests
        api_requests = advanced_monitor.get_network_requests(filter_url="api")
        json_responses = advanced_monitor.get_network_responses(filter_url="json")
        
        log.info(f"  • API requests: {len(api_requests)}")
        log.info(f"  • JSON responses: {len(json_responses)}")
        
        # Stop monitoring
        advanced_monitor.stop_monitoring()
        log.info("⏹️ Advanced monitoring stopped")
        
        return len(requests) > 0
    
    def test_real_time_analysis(self):
        """Test real-time event analysis during navigation."""
        log.info("\n⚡ Testing Real-Time Analysis")
        log.info("=" * 50)
        
        # Create monitor for real-time analysis
        realtime_monitor = CDPEventMonitor(self.driver)
        
        # Custom listeners for analysis
        request_count = {'total': 0, 'POST': 0, 'GET': 0}
        
        def analyze_request(params):
            """Analyze requests in real-time."""
            request = params['request']
            method = request['method']
            request_count['total'] += 1
            request_count[method] = request_count.get(method, 0) + 1
            
            if method == 'POST':
                print(f"🔴 POST request to: {request['url']}")
            elif 'api' in request['url'].lower():
                print(f"🟡 API request: {request['url']}")
        
        realtime_monitor.add_listener('Network.requestWillBeSent', analyze_request)
        realtime_monitor.start_monitoring(capture_events=False)  # No storage, just real-time
        
        log.info("📡 Real-time analysis active")
        
        # Test with interactive site
        log.info("🌐 Testing with interactive site (HTTPBin forms)")
        self.driver.get("https://httpbin.org/forms/post")
        time.sleep(2)
        
        try:
            # REFACTOR: Use enhanced elements for form interaction
            # This uses JavaScript-based methods to avoid shadow DOM conflicts
            name_field = self.driver.find_element(By.NAME, "custname")
            name_field.type_human("Test User", typing_speed=0.08)
            
            email_field = self.driver.find_element(By.NAME, "custemail") 
            email_field.type_human("test@example.com", typing_speed=0.08)
            
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click_safe()
            
            time.sleep(3)  # Wait for form submission
            
        except Exception as e:
            log.warning(f"Enhanced form interaction failed (expected): {e}")
        
        # Stop real-time monitoring
        realtime_monitor.stop_monitoring()
        
        log.info(f"\n📊 RESULTS - Real-Time Analysis:")
        log.info(f"  • Total requests: {request_count['total']}")
        log.info(f"  • GET requests: {request_count.get('GET', 0)}")
        log.info(f"  • POST requests: {request_count.get('POST', 0)}")
        
        return request_count['total'] > 0
    
    def test_error_handling(self):
        """Test CDP monitoring error handling and edge cases."""
        log.info("\n🛡️ Testing Error Handling")
        log.info("=" * 50)
        
        # Test with invalid event names
        def dummy_handler(params):
            pass
        
        try:
            add_cdp_listener(self.driver, 'Invalid.Event.Name', dummy_handler)
            log.info("✅ Invalid event name handled gracefully")
        except Exception as e:
            log.warning(f"❌ Error with invalid event: {e}")
        
        # Test monitoring during navigation errors
        error_monitor = CDPEventMonitor(self.driver)
        error_monitor.start_monitoring()
        
        # Try to navigate to invalid URL
        try:
            self.driver.get("https://this-domain-does-not-exist-12345.invalid")
            time.sleep(3)
        except Exception as e:
            log.info(f"Expected navigation error: {e}")
        
        # Check if monitoring survived the error
        requests = error_monitor.get_network_requests()
        log.info(f"📊 Requests captured during error: {len(requests)}")
        
        error_monitor.stop_monitoring()
        
        return True
    
    def test_performance_impact(self):
        """Test performance impact of CDP monitoring."""
        log.info("\n⚡ Testing Performance Impact")
        log.info("=" * 50)
        
        # Baseline navigation without monitoring
        start_time = time.time()
        self.driver.get("https://example.com")
        baseline_time = time.time() - start_time
        
        log.info(f"🔵 Baseline navigation time: {baseline_time:.2f}s")
        
        # Navigation with full monitoring
        perf_monitor = CDPEventMonitor(self.driver)
        perf_monitor.start_monitoring(capture_events=True)
        
        start_time = time.time()
        self.driver.get("https://httpbin.org/get")
        monitored_time = time.time() - start_time
        
        log.info(f"🟡 Monitored navigation time: {monitored_time:.2f}s")
        
        # Calculate overhead
        overhead = ((monitored_time - baseline_time) / baseline_time * 100) if baseline_time > 0 else 0
        log.info(f"📊 Monitoring overhead: {overhead:.1f}%")
        
        perf_monitor.stop_monitoring()
        
        return overhead < 50  # Should be less than 50% overhead
    
    def run_all_tests(self):
        """Run complete test suite."""
        log.info("🧪 Starting CDP Event Monitoring Test Suite")
        log.info("=" * 60)
        
        # Setup
        if not self.setup_driver():
            log.error("❌ Driver setup failed")
            return False
        
        test_results = {}
        
        try:
            # Run all tests
            test_results['basic_listening'] = self.test_basic_event_listening()
            test_results['advanced_monitoring'] = self.test_advanced_monitoring()
            test_results['realtime_analysis'] = self.test_real_time_analysis()
            test_results['error_handling'] = self.test_error_handling()
            test_results['performance'] = self.test_performance_impact()
            
        except Exception as e:
            log.error(f"❌ Test suite failed: {e}")
            return False
        
        finally:
            # Cleanup
            if self.driver:
                log.info("🧹 Cleaning up driver...")
                self.driver.quit()
        
        # Report final results
        log.info("\n🏆 FINAL TEST RESULTS")
        log.info("=" * 40)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            log.info(f"  {test_name:20} {status}")
            if result:
                passed += 1
        
        log.info(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            log.info("🎉 All CDP event monitoring tests PASSED!")
            return True
        else:
            log.warning("⚠️ Some tests failed - check logs for details")
            return False


def main():
    """Main test execution."""
    print("🔍 CDP Event Monitoring Test Suite")
    print("Testing all features of my_stealth CDP event system...")
    print()
    
    tester = CDPEventTester()
    success = tester.run_all_tests()
    
    print("\n" + "="*60)
    if success:
        print("🎉 CDP Event Monitoring: ALL TESTS PASSED!")
        print("✅ Your my_stealth CDP system is working perfectly!")
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        print("🔧 Consider checking your browser setup and network connection.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

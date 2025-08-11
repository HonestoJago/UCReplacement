#!/usr/bin/env python3
"""
Test Enhanced WebElement Methods

This script tests all enhanced WebElement functionality provided by my_stealth,
including stealth clicking, human-like typing, cross-frame searching, and
natural interaction patterns.
"""

import time
import random
import logging
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Import my_stealth modules
import my_stealth as uc
from my_stealth import enhance_driver_elements, find_elements_recursive, EnhancedWebElement


class EnhancedElementTester:
    """Test suite for enhanced WebElement functionality."""
    
    def __init__(self):
        """Initialize test suite."""
        self.driver = None
        self.test_results = {}
    
    def setup_driver(self):
        """Create and configure stealth driver with enhanced elements."""
        log.info("🚀 Creating stealth driver for element testing...")
        
        self.driver = uc.Chrome(
            profile_path="./test_profiles/elements_test",
            maximise=True,
            apply_viewport=True
        )
        
        # Enable enhanced elements for all find operations
        enhance_driver_elements(self.driver)
        
        # Ensure window has valid dimensions for testing
        try:
            window_size = self.driver.get_window_size()
            if window_size['width'] <= 0 or window_size['height'] <= 0:
                log.warning("⚠️ Invalid window size detected, fixing...")
                self.driver.set_window_size(1280, 720)
                time.sleep(1)
                self.driver.maximize_window()
                time.sleep(1)
            log.debug(f"Window size: {window_size}")
        except Exception as e:
            log.warning(f"Window size check failed: {e}")
        
        log.info("✅ Driver created with enhanced elements enabled")
        return self.driver
    
    def test_stealth_clicking(self):
        """Test stealth clicking methods."""
        log.info("\n🖱️ Testing Stealth Clicking")
        log.info("=" * 50)
        
        try:
            # Navigate to a page with clickable elements
            self.driver.get("https://httpbin.org/")
            time.sleep(2)
            
            # Find links to test clicking
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            if not links:
                log.warning("⚠️ No links found for click testing")
                return False
            
            log.info(f"🔗 Found {len(links)} links to test")
            
            # Test enhanced click_safe method
            test_link = links[0]  # This is already an EnhancedWebElement
            
            log.info(f"🎯 Testing click_safe() on: {test_link.text[:50]}...")
            
            # Test with custom timing
            test_link.click_safe(pause_before=0.2, pause_after=0.3)
            
            log.info("✅ click_safe() executed successfully")
            
            # Test hover method
            if len(links) > 1:
                hover_link = links[1]
                log.info("🖱️ Testing hover() method...")
                hover_link.hover(duration=1.5)
                log.info("✅ hover() executed successfully")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Stealth clicking test failed: {e}")
            return False
    
    def test_human_typing(self):
        """Test human-like typing functionality."""
        log.info("\n⌨️ Testing Human-Like Typing")
        log.info("=" * 50)
        
        try:
            # Navigate to a page with input fields
            self.driver.get("https://httpbin.org/forms/post")
            time.sleep(2)
            
            # Find input fields
            try:
                name_field = self.driver.find_element(By.NAME, "custname")
                email_field = self.driver.find_element(By.NAME, "custemail")
            except NoSuchElementException:
                log.warning("⚠️ Input fields not found, trying Google search instead")
                self.driver.get("https://www.google.com")
                time.sleep(2)
                name_field = self.driver.find_element(By.NAME, "q")
                email_field = None
            
            # Test human typing with different speeds
            test_texts = [
                ("John Doe", 0.1),
                ("test@example.com", 0.15),
                ("Human-like typing test", 0.08)
            ]
            
            for i, (text, speed) in enumerate(test_texts):
                if i == 0:
                    current_field = name_field
                elif i == 1 and email_field:
                    current_field = email_field
                else:
                    # Clear and reuse first field
                    name_field.clear()
                    current_field = name_field
                
                log.info(f"⌨️ Typing '{text}' with speed {speed}...")
                
                # Test type_human method
                current_field.type_human(text, typing_speed=speed, mistakes=True)
                
                time.sleep(1)  # Pause between tests
            
            log.info("✅ Human typing tests completed successfully")
            return True
            
        except Exception as e:
            log.error(f"❌ Human typing test failed: {e}")
            return False
    
    def test_dom_traversal(self):
        """Test DOM traversal methods (children, recursive searching)."""
        log.info("\n🌳 Testing DOM Traversal")
        log.info("=" * 50)
        
        try:
            # Navigate to a page with complex DOM structure
            self.driver.get("https://example.com")
            time.sleep(2)
            
            # Get the body element to test children() method
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Test direct children
            direct_children = body.children(recursive=False)
            log.info(f"📋 Body has {len(direct_children)} direct children")
            
            # Test recursive children
            all_descendants = body.children(recursive=True)
            log.info(f"🌲 Body has {len(all_descendants)} total descendants")
            
            # Test tag filtering
            div_children = body.children(tag="div", recursive=True)
            p_children = body.children(tag="p", recursive=True)
            
            log.info(f"📦 Found {len(div_children)} div elements")
            log.info(f"📄 Found {len(p_children)} p elements")
            
            # Test element properties
            if direct_children:
                first_child = direct_children[0]
                log.info(f"🔍 First child tag: {first_child.tag_name}")
                
                # Test enhanced methods on child
                first_child.scroll_to()
                log.info("✅ scroll_to() worked on child element")
            
            return len(all_descendants) > len(direct_children)
            
        except Exception as e:
            log.error(f"❌ DOM traversal test failed: {e}")
            return False
    
    def test_cross_frame_search(self):
        """Test cross-frame element searching."""
        log.info("\n🖼️ Testing Cross-Frame Element Search")
        log.info("=" * 50)
        
        try:
            # Navigate to simpler pages that are less likely to have shadow DOM issues
            test_sites = [
                "https://httpbin.org/",
                "https://example.com",
                "https://google.com"  # Fallback with lots of elements
            ]
            
            iframe_found = False
            
            for site in test_sites:
                try:
                    log.info(f"🔗 Testing iframe search on: {site}")
                    self.driver.get(site)
                    time.sleep(3)
                    
                    # Look for iframes
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    
                    if iframes:
                        log.info(f"🖼️ Found {len(iframes)} iframe(s)")
                        iframe_found = True
                        break
                    else:
                        log.info("❌ No iframes found, trying next site...")
                        
                except Exception as e:
                    log.warning(f"⚠️ Error testing {site}: {e}")
                    continue
            
            # Test recursive element finding across frames
            log.info("🔍 Testing find_elements_recursive()...")
            
            # Search for buttons across all frames
            all_buttons = find_elements_recursive(self.driver, By.TAG_NAME, "button")
            log.info(f"🔘 Found {len(all_buttons)} buttons across all frames")
            
            # Search for links across all frames
            all_links = find_elements_recursive(self.driver, By.TAG_NAME, "a")
            log.info(f"🔗 Found {len(all_links)} links across all frames")
            
            # Search for inputs across all frames
            all_inputs = find_elements_recursive(self.driver, By.TAG_NAME, "input")
            log.info(f"📝 Found {len(all_inputs)} input fields across all frames")
            
            # Test interaction with cross-frame elements
            if all_buttons:
                log.info("🎯 Testing interaction with cross-frame button...")
                try:
                    first_button = all_buttons[0]
                    first_button.scroll_to()
                    first_button.hover(duration=0.5)
                    log.info("✅ Cross-frame button interaction successful")
                except Exception as e:
                    log.warning(f"⚠️ Cross-frame interaction failed: {e}")
            
            return len(all_buttons) > 0 or len(all_links) > 0 or len(all_inputs) > 0
            
        except Exception as e:
            log.error(f"❌ Cross-frame search test failed: {e}")
            return False
    
    def test_waiting_and_timing(self):
        """Test element waiting and timing methods."""
        log.info("\n⏱️ Testing Element Waiting and Timing")
        log.info("=" * 50)
        
        try:
            # Navigate to a page where we can test waiting
            self.driver.get("https://httpbin.org/delay/2")
            
            # The page should load after 2 seconds
            start_time = time.time()
            
            # Try to find an element that should appear after load
            try:
                # Wait for page to load by finding body
                body = self.driver.find_element(By.TAG_NAME, "body")
                
                # Test wait_for_clickable
                is_clickable = body.wait_for_clickable(timeout=5)
                wait_time = time.time() - start_time
                
                log.info(f"⏱️ Page loaded in {wait_time:.2f} seconds")
                log.info(f"🖱️ Element clickable: {is_clickable}")
                
                # Test scroll timing
                log.info("📜 Testing scroll timing...")
                body.scroll_to(behavior='smooth')
                time.sleep(1)
                
                return True
                
            except TimeoutException:
                log.warning("⚠️ Element wait timed out")
                return False
            
        except Exception as e:
            log.error(f"❌ Waiting and timing test failed: {e}")
            return False
    
    def test_natural_interactions(self):
        """Test natural, human-like interaction patterns."""
        log.info("\n🧑 Testing Natural Human-Like Interactions")
        log.info("=" * 50)
        
        try:
            # Navigate to Google for interaction testing
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Find search box
            search_box = self.driver.find_element(By.NAME, "q")
            
            # Test natural typing sequence
            log.info("⌨️ Testing natural typing sequence...")
            
            # Type with varying speeds and pauses
            search_queries = [
                "python automation",
                "web scraping tools",
                "selenium tutorial"
            ]
            
            for i, query in enumerate(search_queries):
                # Clear previous search
                search_box.clear()
                time.sleep(random.uniform(0.3, 0.8))
                
                # Click to focus (with natural timing)
                search_box.click_safe(pause_before=0.2, pause_after=0.3)
                
                # Type with human-like characteristics
                typing_speed = random.uniform(0.08, 0.15)
                search_box.type_human(query, typing_speed=typing_speed, mistakes=True)
                
                # Natural pause before next action
                time.sleep(random.uniform(1.0, 2.0))
                
                log.info(f"✅ Typed query {i+1}: '{query}'")
            
            # Test natural mouse movements
            log.info("🖱️ Testing natural mouse movements...")
            
            # Find multiple elements to move between
            elements = self.driver.find_elements(By.TAG_NAME, "a")[:3]
            
            for element in elements:
                try:
                    # Natural hover with timing
                    element.hover(duration=random.uniform(0.5, 1.5))
                    time.sleep(random.uniform(0.3, 0.7))
                except Exception as e:
                    log.warning(f"⚠️ Hover failed on element: {e}")
            
            log.info("✅ Natural interaction tests completed")
            return True
            
        except Exception as e:
            log.error(f"❌ Natural interactions test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test error handling for enhanced elements."""
        log.info("\n🛡️ Testing Error Handling")
        log.info("=" * 50)
        
        try:
            self.driver.get("https://example.com")
            time.sleep(1)
            
            # Test operations on non-existent elements
            try:
                fake_element = self.driver.find_elements(By.ID, "non-existent-element-12345")
                if not fake_element:
                    log.info("✅ Correctly handled non-existent element")
                else:
                    log.warning("⚠️ Unexpectedly found fake element")
            except NoSuchElementException:
                log.info("✅ Correctly raised NoSuchElementException")
            
            # Test with existing element but invalid operations
            body = self.driver.find_element(By.TAG_NAME, "body")
            
            # Test children with invalid tag
            invalid_children = body.children(tag="nonexistenttag")
            log.info(f"✅ Invalid tag search returned {len(invalid_children)} elements")
            
            # Test wait with short timeout
            short_wait = body.wait_for_clickable(timeout=0.1)
            log.info(f"✅ Short timeout wait returned: {short_wait}")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Error handling test failed: {e}")
            return False
    
    def test_performance_comparison(self):
        """Compare performance of enhanced vs standard elements."""
        log.info("\n⚡ Testing Performance Comparison")
        log.info("=" * 50)
        
        try:
            self.driver.get("https://example.com")
            time.sleep(2)
            
            # Time standard operations
            start_time = time.time()
            
            # Standard element finding
            standard_elements = self.driver.find_elements(By.TAG_NAME, "a")
            standard_time = time.time() - start_time
            
            log.info(f"⏱️ Standard find_elements: {standard_time:.4f}s ({len(standard_elements)} elements)")
            
            # Time enhanced operations
            start_time = time.time()
            
            # Enhanced element operations
            if standard_elements:
                enhanced_elem = standard_elements[0]  # Already enhanced due to monkey-patching
                enhanced_elem.children(recursive=True)
            
            enhanced_time = time.time() - start_time
            
            log.info(f"⏱️ Enhanced operations: {enhanced_time:.4f}s")
            
            # Calculate overhead
            if standard_time > 0:
                overhead = ((enhanced_time - standard_time) / standard_time * 100)
                log.info(f"📊 Enhanced element overhead: {overhead:.1f}%")
            else:
                log.info("📊 Enhanced element overhead: negligible")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Performance comparison failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete enhanced elements test suite."""
        log.info("🧪 Starting Enhanced WebElement Test Suite")
        log.info("=" * 60)
        
        # Setup
        if not self.setup_driver():
            log.error("❌ Driver setup failed")
            return False
        
        test_results = {}
        
        try:
            # Run all tests
            test_results['stealth_clicking'] = self.test_stealth_clicking()
            test_results['human_typing'] = self.test_human_typing()
            test_results['dom_traversal'] = self.test_dom_traversal()
            test_results['cross_frame_search'] = self.test_cross_frame_search()
            test_results['waiting_timing'] = self.test_waiting_and_timing()
            test_results['natural_interactions'] = self.test_natural_interactions()
            test_results['error_handling'] = self.test_error_handling()
            test_results['performance'] = self.test_performance_comparison()
            
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
            log.info("🎉 All enhanced element tests PASSED!")
            return True
        else:
            log.warning("⚠️ Some tests failed - check logs for details")
            return False


def main():
    """Main test execution."""
    print("🧪 Enhanced WebElement Test Suite")
    print("Testing all enhanced element features of my_stealth...")
    print()
    
    tester = EnhancedElementTester()
    success = tester.run_all_tests()
    
    print("\n" + "="*60)
    if success:
        print("🎉 Enhanced WebElements: ALL TESTS PASSED!")
        print("✅ Your my_stealth enhanced elements are working perfectly!")
        print("🚀 Ready for human-like automation with stealth interactions!")
    else:
        print("❌ Some tests failed. Check the logs above for details.")
        print("🔧 Consider checking your browser setup and target sites.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

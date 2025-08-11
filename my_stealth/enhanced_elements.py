#!/usr/bin/env python3
"""
Enhanced WebElement Methods for my_stealth

Provides UC-style enhanced element interactions with improved stealth:
- click_safe() for undetectable clicking
- children() for DOM traversal
- find_elements_recursive() for cross-frame searching
- Human-like interaction patterns
"""

import random
import time
from typing import List, Optional, Union
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class EnhancedWebElement:
    """
    Enhanced WebElement wrapper providing UC-style stealth methods.
    
    This class extends standard WebElement functionality with:
    - Stealth clicking that avoids detection
    - DOM traversal utilities
    - Human-like interaction timing
    - Cross-frame element finding
    """
    
    def __init__(self, element: WebElement, driver):
        """Initialize enhanced element wrapper."""
        self.element = element
        self.driver = driver
        
        # Copy all original WebElement methods/properties
        for attr in dir(element):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(element, attr))
    
    def click_safe(self, pause_before: float = None, pause_after: float = None) -> None:
        """
        Perform stealth click using JavaScript execution.
        
        This method uses direct JavaScript execution instead of ActionChains to avoid
        Chrome's visual feedback systems that cause shadow DOM conflicts.
        More stealthy as it mimics legitimate page JavaScript execution.
        
        Args:
            pause_before: Seconds to wait before clicking (random if None)
            pause_after: Seconds to wait after clicking (random if None)
        """
        # Human-like delay before action
        if pause_before is None:
            pause_before = random.uniform(0.1, 0.4)
        time.sleep(pause_before)
        
        try:
            # Scroll element into view first (using JavaScript to avoid screenshot issues)
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'center'
                });
            """, self.element)
            
            # Small delay for scroll to complete
            time.sleep(random.uniform(0.2, 0.5))
            
            # Simulate human-like interaction timing with multiple approaches
            click_methods = [
                # Method 1: Direct click (most common)
                "arguments[0].click();",
                
                # Method 2: Dispatch click event (more realistic)
                """
                const element = arguments[0];
                const event = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                element.dispatchEvent(event);
                """,
                
                # Method 3: Focus then click (form-like interaction)
                """
                arguments[0].focus();
                setTimeout(() => arguments[0].click(), 50);
                """
            ]
            
            # Randomly choose a click method (varies behavior)
            chosen_method = random.choice(click_methods)
            self.driver.execute_script(chosen_method, self.element)
            
        except Exception as e:
            # Fallback to standard Selenium click as last resort
            try:
                self.element.click()
            except Exception:
                # Ultimate fallback - simple JavaScript click
                self.driver.execute_script("arguments[0].click();", self.element)
        
        # Human-like delay after action
        if pause_after is None:
            pause_after = random.uniform(0.2, 0.6)
        time.sleep(pause_after)
    
    def children(self, tag: str = None, recursive: bool = False) -> List['EnhancedWebElement']:
        """
        Get child elements with optional filtering.
        
        Args:
            tag: Optional tag name to filter by (e.g., 'div', 'span')
            recursive: If True, find all descendants; if False, direct children only
            
        Returns:
            List of enhanced child elements
        """
        if recursive:
            # Find all descendants
            if tag:
                xpath = f".//{tag}"
            else:
                xpath = ".//*"
        else:
            # Find direct children only
            if tag:
                xpath = f"./{tag}"
            else:
                xpath = "./*"
        
        try:
            child_elements = self.element.find_elements(By.XPATH, xpath)
            return [EnhancedWebElement(elem, self.driver) for elem in child_elements]
        except NoSuchElementException:
            return []
    
    def type_human(self, text: str, typing_speed: float = 0.1, mistakes: bool = True) -> None:
        """
        Type text with human-like characteristics using JavaScript.
        
        Uses JavaScript to simulate natural typing patterns while avoiding
        Selenium's ActionChains that can trigger shadow DOM conflicts.
        
        Args:
            text: Text to type
            typing_speed: Base delay between characters (seconds)
            mistakes: Whether to simulate occasional typos
        """
        # Clear existing content using JavaScript (more reliable)
        self.driver.execute_script("""
            const element = arguments[0];
            element.value = '';
            element.focus();
        """, self.element)
        
        time.sleep(random.uniform(0.1, 0.3))
        
        # Click to focus using our safe method
        self.click_safe(pause_before=0.1, pause_after=0.2)
        
        typed_text = ""
        i = 0
        
        while i < len(text):
            char = text[i]
            
            # Simulate occasional typos (5% chance)
            if mistakes and random.random() < 0.05 and char.isalpha():
                # Type wrong character first using JavaScript
                wrong_chars = 'qwertyuiopasdfghjklzxcvbnm'
                wrong_char = random.choice(wrong_chars)
                
                self.driver.execute_script("""
                    const element = arguments[0];
                    const char = arguments[1];
                    
                    // Simulate typing a character
                    const event = new InputEvent('input', {
                        inputType: 'insertText',
                        data: char,
                        bubbles: true
                    });
                    
                    element.value += char;
                    element.dispatchEvent(event);
                """, self.element, wrong_char)
                
                typed_text += wrong_char
                
                # Pause (realizing mistake)
                time.sleep(random.uniform(0.2, 0.5))
                
                # Backspace to correct using JavaScript
                self.driver.execute_script("""
                    const element = arguments[0];
                    element.value = element.value.slice(0, -1);
                    
                    const event = new InputEvent('input', {
                        inputType: 'deleteContentBackward',
                        bubbles: true
                    });
                    element.dispatchEvent(event);
                """, self.element)
                
                typed_text = typed_text[:-1]
                time.sleep(random.uniform(0.1, 0.2))
            
            # Type the correct character using JavaScript
            self.driver.execute_script("""
                const element = arguments[0];
                const char = arguments[1];
                
                // Simulate natural typing
                const keydownEvent = new KeyboardEvent('keydown', {
                    key: char,
                    bubbles: true
                });
                
                const inputEvent = new InputEvent('input', {
                    inputType: 'insertText',
                    data: char,
                    bubbles: true
                });
                
                const keyupEvent = new KeyboardEvent('keyup', {
                    key: char,
                    bubbles: true
                });
                
                element.dispatchEvent(keydownEvent);
                element.value += char;
                element.dispatchEvent(inputEvent);
                element.dispatchEvent(keyupEvent);
            """, self.element, char)
            
            typed_text += char
            
            # Variable typing speed (same timing logic)
            if char == ' ':
                # Longer pause after spaces
                delay = random.uniform(typing_speed * 1.5, typing_speed * 3.0)
            elif char in '.,!?;:':
                # Pause after punctuation
                delay = random.uniform(typing_speed * 2.0, typing_speed * 4.0)
            else:
                # Normal character
                delay = random.uniform(typing_speed * 0.5, typing_speed * 2.0)
            
            time.sleep(delay)
            i += 1
    
    def hover(self, duration: float = None) -> None:
        """
        Hover over element using JavaScript to avoid shadow DOM issues.
        
        Simulates mouse hover events directly via JavaScript rather than
        using ActionChains which can trigger Chrome's visual feedback systems.
        
        Args:
            duration: How long to hover (random if None)
        """
        if duration is None:
            duration = random.uniform(0.5, 2.0)
        
        try:
            # Dispatch mouseover and mouseenter events via JavaScript
            self.driver.execute_script("""
                const element = arguments[0];
                
                // Create realistic mouse events
                const mouseenterEvent = new MouseEvent('mouseenter', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                
                const mouseoverEvent = new MouseEvent('mouseover', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                
                // Dispatch events in natural order
                element.dispatchEvent(mouseenterEvent);
                element.dispatchEvent(mouseoverEvent);
            """, self.element)
            
            time.sleep(duration)
            
            # Dispatch mouseleave event when hover ends
            self.driver.execute_script("""
                const element = arguments[0];
                
                const mouseleaveEvent = new MouseEvent('mouseleave', {
                    bubbles: true,
                    cancelable: true,
                    view: window
                });
                
                element.dispatchEvent(mouseleaveEvent);
            """, self.element)
            
        except Exception:
            # Fallback to ActionChains if JavaScript fails
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(self.element)
                actions.perform()
                time.sleep(duration)
            except Exception:
                # Silent fail for hover operations
                time.sleep(duration)
    
    def scroll_to(self, behavior: str = 'smooth') -> None:
        """
        Scroll element into view using pure JavaScript.
        
        This method is now fully JavaScript-based to avoid any potential
        screenshot or visual feedback triggers from Chrome.
        
        Args:
            behavior: 'smooth', 'instant', or 'auto'
        """
        try:
            # Use pure JavaScript scrolling - no screenshot triggers
            self.driver.execute_script(f"""
                const element = arguments[0];
                
                // Ensure element exists and is visible
                if (element && element.scrollIntoView) {{
                    element.scrollIntoView({{
                        behavior: '{behavior}',
                        block: 'center',
                        inline: 'center'
                    }});
                    
                    // Dispatch scroll event for realism
                    const scrollEvent = new Event('scroll', {{
                        bubbles: true,
                        cancelable: true
                    }});
                    window.dispatchEvent(scrollEvent);
                }}
            """, self.element)
            
            # Natural delay for scroll completion
            time.sleep(random.uniform(0.3, 0.8))
            
        except Exception:
            # Ultimate fallback - simplest possible scroll
            try:
                self.driver.execute_script("arguments[0].scrollIntoView();", self.element)
                time.sleep(0.5)
            except Exception:
                pass  # Silent fail for scroll operations - non-critical
    
    def wait_for_clickable(self, timeout: float = 10) -> bool:
        """
        Wait for element to become clickable.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if element becomes clickable, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(self.element)
            )
            return True
        except TimeoutException:
            return False


def find_elements_recursive(driver, by: By, value: str, 
                           start_frame: int = 0, max_depth: int = 3) -> List[EnhancedWebElement]:
    """
    Find elements across multiple frames recursively.
    
    This UC-style function searches for elements in the current frame and all
    nested iframes, which is essential for complex web applications.
    
    Args:
        driver: WebDriver instance
        by: Locator strategy (By.ID, By.CLASS_NAME, etc.)
        value: Locator value
        start_frame: Frame index to start from (0 = main frame)
        max_depth: Maximum iframe nesting depth to search
        
    Returns:
        List of enhanced elements found across all frames
    """
    found_elements = []
    original_frame = None
    
    try:
        # Remember current frame context
        try:
            original_frame = driver.execute_script("return window.name || 'main';")
        except:
            original_frame = 'main'
        
        def search_in_frame(depth: int = 0):
            """Recursive frame searching."""
            if depth > max_depth:
                return
            
            # Search in current frame
            try:
                elements = driver.find_elements(by, value)
                for elem in elements:
                    found_elements.append(EnhancedWebElement(elem, driver))
            except NoSuchElementException:
                pass
            
            # Search in all iframes within current frame
            try:
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for i, iframe in enumerate(iframes):
                    try:
                        # Check if iframe is accessible before switching
                        iframe_src = iframe.get_attribute('src')
                        if iframe_src and ('javascript:' in iframe_src or iframe_src.startswith('data:')):
                            continue  # Skip problematic iframe types
                        
                        driver.switch_to.frame(iframe)
                        search_in_frame(depth + 1)
                        driver.switch_to.parent_frame()  # Go back to parent
                    except Exception as e:
                        # Frame might be inaccessible (shadow DOM, CORS, etc.), continue with others
                        try:
                            driver.switch_to.parent_frame()
                        except:
                            try:
                                driver.switch_to.default_content()
                            except:
                                pass
                        continue
            except Exception:
                pass
        
        # Start recursive search
        search_in_frame(0)
        
    finally:
        # Always return to original frame context
        try:
            driver.switch_to.default_content()
            if original_frame != 'main':
                # Try to switch back to original frame if possible
                frames = driver.find_elements(By.TAG_NAME, "iframe")
                for frame in frames:
                    try:
                        driver.switch_to.frame(frame)
                        current_name = driver.execute_script("return window.name;")
                        if current_name == original_frame:
                            break
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
                        continue
        except:
            pass
    
    return found_elements


def enhance_driver_elements(driver):
    """
    Monkey-patch driver to return enhanced elements automatically.
    
    After calling this function, all find_element() calls will return
    EnhancedWebElement instances with stealth methods.
    """
    original_find_element = driver.find_element
    original_find_elements = driver.find_elements
    
    def enhanced_find_element(by, value):
        element = original_find_element(by, value)
        return EnhancedWebElement(element, driver)
    
    def enhanced_find_elements(by, value):
        elements = original_find_elements(by, value)
        return [EnhancedWebElement(elem, driver) for elem in elements]
    
    driver.find_element = enhanced_find_element
    driver.find_elements = enhanced_find_elements
    
    # Add recursive find method to driver
    driver.find_elements_recursive = lambda by, value: find_elements_recursive(driver, by, value)


# Module can be imported and used directly
# For testing, see test_enhanced_elements.py in the root directory

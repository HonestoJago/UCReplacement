#!/usr/bin/env python3
"""
CDP Event System for my_stealth - Enhanced Network Monitoring

Provides UC-style CDP event listening with modern Python patterns.
Allows real-time monitoring of network requests, responses, and browser events.
"""

import json
import logging
import threading
import time
from typing import Dict, List, Callable, Any, Optional
from selenium.webdriver.chrome.webdriver import WebDriver

log = logging.getLogger(__name__)


class CDPEventMonitor:
    """
    Enhanced CDP event monitoring system for stealth automation.
    
    Provides UC-compatible API with modern Python improvements:
    - Thread-safe event handling
    - Wildcard event matching  
    - Network request/response capture
    - Real-time debugging capabilities
    """
    
    def __init__(self, driver: WebDriver):
        """Initialize CDP event monitor for a WebDriver instance."""
        self.driver = driver
        self.listeners: Dict[str, List[Callable]] = {}
        self.wildcard_listeners: List[Callable] = []
        self.captured_events: List[Dict] = []
        self.monitoring = False
        self._lock = threading.Lock()
        
        # Enable required CDP domains
        self._enable_domains()
    
    def _enable_domains(self) -> None:
        """Enable CDP domains needed for comprehensive monitoring."""
        domains = [
            "Network",
            "Runtime", 
            "Security",
            "Performance",
            "Log"
        ]
        
        for domain in domains:
            try:
                self.driver.execute_cdp_cmd(f"{domain}.enable", {})
                log.debug(f"Enabled CDP domain: {domain}")
            except Exception as e:
                log.warning(f"Failed to enable {domain} domain: {e}")
        
        # Additional setup for network monitoring
        try:
            # Enable more detailed network monitoring
            self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": False})
            self.driver.execute_cdp_cmd("Network.setRequestInterception", {"patterns": []})
            log.debug("Enhanced network monitoring enabled")
        except Exception as e:
            log.debug(f"Optional network enhancements failed: {e}")
    
    def _setup_logging(self) -> None:
        """Setup and validate logging capabilities for CDP event monitoring."""
        try:
            # Check what log types are available
            available_logs = self.driver.get_log_types()
            log.debug(f"Available log types: {available_logs}")
            
            if 'performance' not in available_logs:
                log.info("Performance logging not natively available, will use alternative methods")
                # Try to enable it anyway via CDP
                try:
                    self.driver.execute_cdp_cmd("Log.enable", {})
                    log.debug("Enabled CDP logging via Log.enable command")
                except Exception as e:
                    log.debug(f"Could not enable CDP logging via command: {e}")
            else:
                log.debug("Performance logging is available")
                
        except Exception as e:
            log.warning(f"Could not check or setup logging capabilities: {e}")
            log.info("Will proceed with alternative CDP monitoring methods")
    
    def add_listener(self, event: str, callback: Callable[[Dict], None]) -> None:
        """
        Add event listener for specific CDP events.
        
        Args:
            event: CDP event name (e.g., 'Network.requestWillBeSent') or '*' for all
            callback: Function to call when event occurs
        """
        with self._lock:
            if event == '*':
                self.wildcard_listeners.append(callback)
                log.debug("Added wildcard event listener")
            else:
                if event not in self.listeners:
                    self.listeners[event] = []
                self.listeners[event].append(callback)
                log.debug(f"Added listener for: {event}")
    
    def remove_listener(self, event: str, callback: Callable[[Dict], None]) -> None:
        """Remove specific event listener."""
        with self._lock:
            if event == '*':
                if callback in self.wildcard_listeners:
                    self.wildcard_listeners.remove(callback)
            else:
                if event in self.listeners and callback in self.listeners[event]:
                    self.listeners[event].remove(callback)
    
    def start_monitoring(self, capture_events: bool = True) -> None:
        """
        Start monitoring CDP events in background thread.
        
        Args:
            capture_events: Whether to store events for later analysis
        """
        if self.monitoring:
            return
            
        self.monitoring = True
        self.captured_events.clear()
        
        # Check logging capabilities and enable what we can
        self._setup_logging()
        
        def monitor_loop():
            """Background thread for event monitoring."""
            while self.monitoring:
                try:
                    # Try multiple approaches to get CDP events
                    logs = []
                    
                    # Method 1: Performance logs (if available)
                    try:
                        logs = self.driver.get_log('performance')
                    except Exception:
                        # Method 2: Browser logs as fallback
                        try:
                            logs = self.driver.get_log('browser')
                        except Exception:
                            # Method 3: Alternative event capture via direct navigation monitoring
                            # When logging is not available, we can still capture some events
                            try:
                                # Generate synthetic events based on current page state
                                current_url = self.driver.current_url
                                if hasattr(self, '_last_url') and self._last_url != current_url:
                                    # URL changed - simulate navigation event
                                    synthetic_event = {
                                        'method': 'Page.frameNavigated',
                                        'params': {
                                            'frame': {
                                                'id': 'main',
                                                'url': current_url,
                                                'loaderId': str(int(time.time() * 1000))
                                            }
                                        }
                                    }
                                    self._handle_event(synthetic_event, capture_events)
                                self._last_url = current_url
                            except Exception:
                                pass
                    
                    for log_entry in logs:
                        if log_entry.get('level') == 'INFO':
                            try:
                                message = json.loads(log_entry['message'])
                                if 'message' in message:
                                    event_data = message['message']
                                    self._handle_event(event_data, capture_events)
                            except json.JSONDecodeError:
                                continue
                                
                    time.sleep(0.1)  # Small delay to prevent CPU spinning
                    
                except Exception as e:
                    log.debug(f"CDP monitoring error (will retry): {e}")
                    time.sleep(0.5)  # Longer delay on error
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        log.info("CDP event monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop CDP event monitoring."""
        self.monitoring = False
        log.info("CDP event monitoring stopped")
    
    def _handle_event(self, event_data: Dict, capture: bool) -> None:
        """Handle incoming CDP event."""
        event_method = event_data.get('method', '')
        
        if capture:
            with self._lock:
                self.captured_events.append({
                    'timestamp': time.time(),
                    'method': event_method,
                    'params': event_data.get('params', {})
                })
        
        # Call specific listeners
        with self._lock:
            if event_method in self.listeners:
                for callback in self.listeners[event_method]:
                    try:
                        callback(event_data.get('params', {}))
                    except Exception as e:
                        log.error(f"Event listener error: {e}")
            
            # Call wildcard listeners
            for callback in self.wildcard_listeners:
                try:
                    callback(event_data)
                except Exception as e:
                    log.error(f"Wildcard listener error: {e}")
    
    def get_network_requests(self, filter_url: str = None) -> List[Dict]:
        """
        Get captured network requests with optional URL filtering.
        
        Args:
            filter_url: Optional URL substring to filter by
            
        Returns:
            List of network request events
        """
        requests = []
        
        with self._lock:
            for event in self.captured_events:
                if event['method'] == 'Network.requestWillBeSent':
                    request_data = event['params']['request']
                    if not filter_url or filter_url in request_data['url']:
                        requests.append({
                            'timestamp': event['timestamp'],
                            'url': request_data['url'],
                            'method': request_data['method'],
                            'headers': request_data['headers'],
                            'postData': request_data.get('postData', '')
                        })
        
        return requests
    
    def get_network_responses(self, filter_url: str = None) -> List[Dict]:
        """Get captured network responses with optional URL filtering."""
        responses = []
        
        with self._lock:
            for event in self.captured_events:
                if event['method'] == 'Network.responseReceived':
                    response_data = event['params']['response']
                    if not filter_url or filter_url in response_data['url']:
                        responses.append({
                            'timestamp': event['timestamp'],
                            'url': response_data['url'],
                            'status': response_data['status'],
                            'headers': response_data['headers'],
                            'mimeType': response_data['mimeType']
                        })
        
        return responses
    
    def clear_events(self) -> None:
        """Clear captured events."""
        with self._lock:
            self.captured_events.clear()


# Convenience functions for UC-style API compatibility
def enable_cdp_events(driver: WebDriver) -> CDPEventMonitor:
    """
    Enable CDP event monitoring for a driver (UC-compatible API).
    
    Returns:
        CDPEventMonitor instance for adding listeners
    """
    monitor = CDPEventMonitor(driver)
    monitor.start_monitoring()
    
    # Store monitor on driver for later access
    driver._cdp_monitor = monitor
    return monitor


def add_cdp_listener(driver: WebDriver, event: str, callback: Callable) -> None:
    """
    Add CDP event listener (UC-compatible API).
    
    Args:
        driver: WebDriver instance
        event: CDP event name or '*' for all events
        callback: Function to call when event occurs
    """
    if not hasattr(driver, '_cdp_monitor'):
        enable_cdp_events(driver)
    
    driver._cdp_monitor.add_listener(event, callback)


# Module can be imported and used directly
# For testing, see test_cdp_events.py in the root directory

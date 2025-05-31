#!/usr/bin/env python3
"""
Test script for Edge Bridge Service.

This script tests the Edge Bridge functionality without requiring actual hardware.
Useful for development and CI/CD testing.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any

import requests
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdgeBridgeTest:
    """Test suite for Edge Bridge Service."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.mqtt_client = None
        self.test_results = []
    
    def run_all_tests(self):
        """Run all test cases."""
        logger.info("Starting Edge Bridge Test Suite")
        
        # HTTP API Tests
        self.test_health_endpoint()
        self.test_status_endpoint()
        self.test_command_endpoint()
        
        # MQTT Tests (if broker available)
        self.test_mqtt_connectivity()
        
        # Print results
        self.print_results()
        
        return all(result["passed"] for result in self.test_results)
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        test_name = "Health Endpoint"
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    self.add_result(test_name, True, "Health endpoint responding correctly")
                else:
                    self.add_result(test_name, False, "Health endpoint missing status field")
            else:
                self.add_result(test_name, False, f"Health endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.add_result(test_name, False, f"Health endpoint unreachable: {e}")
    
    def test_status_endpoint(self):
        """Test the status endpoint."""
        test_name = "Status Endpoint"
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["service", "version", "modbus", "mqtt", "command_queue"]
                
                if all(field in data for field in required_fields):
                    self.add_result(test_name, True, "Status endpoint returning complete data")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.add_result(test_name, False, f"Status endpoint missing fields: {missing}")
            else:
                self.add_result(test_name, False, f"Status endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.add_result(test_name, False, f"Status endpoint unreachable: {e}")
    
    def test_command_endpoint(self):
        """Test the command submission endpoint."""
        test_name = "Command Endpoint"
        try:
            test_command = {
                "command_type": "read_register",
                "data": {
                    "register": "battery_voltage"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/commands",
                json=test_command,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if "command_id" in data and "status" in data:
                    command_id = data["command_id"]
                    
                    # Test command status retrieval
                    status_response = requests.get(
                        f"{self.base_url}/commands/{command_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        self.add_result(test_name, True, "Command endpoint working correctly")
                    else:
                        self.add_result(test_name, False, "Command status retrieval failed")
                else:
                    self.add_result(test_name, False, "Command response missing required fields")
            else:
                self.add_result(test_name, False, f"Command endpoint returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.add_result(test_name, False, f"Command endpoint unreachable: {e}")
    
    def test_mqtt_connectivity(self):
        """Test MQTT connectivity (if broker available)."""
        test_name = "MQTT Connectivity"
        try:
            # Try to connect to MQTT broker
            client = mqtt.Client(client_id="test-client")
            client.username_pw_set("nattery", "password")
            
            result = client.connect("localhost", 1883, 60)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                client.disconnect()
                self.add_result(test_name, True, "MQTT broker accessible")
            else:
                self.add_result(test_name, False, f"MQTT connection failed: {mqtt.error_string(result)}")
                
        except Exception as e:
            self.add_result(test_name, False, f"MQTT test failed: {e}")
    
    def add_result(self, test_name: str, passed: bool, message: str):
        """Add a test result."""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
    
    def print_results(self):
        """Print test results summary."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        
        print("\n" + "="*60)
        print("EDGE BRIDGE TEST RESULTS")
        print("="*60)
        
        for result in self.test_results:
            status = "✓" if result["passed"] else "✗"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("-"*60)
        print(f"Total: {total_tests}, Passed: {passed_tests}, Failed: {total_tests - passed_tests}")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
        else:
            print("❌ Some tests failed!")
        
        print("="*60)


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Edge Bridge Service")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL for Edge Bridge Service"
    )
    
    args = parser.parse_args()
    
    tester = EdgeBridgeTest(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 
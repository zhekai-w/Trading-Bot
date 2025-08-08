#!/usr/bin/env python3
"""
Test script to demonstrate API usage
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_symbols():
    """Test symbols endpoint"""
    print("📈 Testing Symbols Endpoint...")
    response = requests.get(f"{BASE_URL}/api/symbols")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available symbols: {len(data['symbols'])}")
    print(f"First 5 symbols: {data['symbols'][:5]}")
    print()

def test_intervals():
    """Test intervals endpoint"""
    print("⏰ Testing Intervals Endpoint...")
    response = requests.get(f"{BASE_URL}/api/intervals")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available intervals: {len(data['intervals'])}")
    for interval in data['intervals'][:3]:
        print(f"  - {interval['label']}: {interval['value']}")
    print()

def test_backtest():
    """Test backtest endpoint"""
    print("🔄 Testing Backtest Endpoint...")
    
    backtest_config = {
        "days_back": 7,
        "timezone": "Asia/Singapore",
        "take_profit": 0.02,
        "stop_loss": 0.01,
        "fast_length": 12,
        "slow_length": 26,
        "signal_smoothing": 9
    }
    
    response = requests.post(
        f"{BASE_URL}/api/backtest/ROSEUSDT/5m",
        json=backtest_config,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("✅ Backtest successful!")
            print(f"Results: {json.dumps(data['results'], indent=2)}")
        else:
            print(f"❌ Backtest failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error: {response.text}")
    print()

def test_stream_start():
    """Test start streaming endpoint"""
    print("🔴 Testing Start Stream Endpoint...")
    
    stream_config = {
        "symbol": "ROSEUSDT",
        "interval": "5m",
        "timezone": "Asia/Singapore"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/stream/start",
        json=stream_config,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_stream_stop():
    """Test stop streaming endpoint"""
    print("⏹️ Testing Stop Stream Endpoint...")
    
    response = requests.post(f"{BASE_URL}/api/stream/stop")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("🚀 Trading API Test Suite")
    print("=" * 50)
    
    try:
        # Basic endpoint tests
        test_health()
        test_symbols()
        test_intervals()
        
        # Advanced functionality tests
        test_backtest()
        
        # Streaming tests
        test_stream_start()
        time.sleep(2)  # Let it run briefly
        test_stream_stop()
        
        print("✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the API server is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
🚀 Interactive MACD Strategy Launcher
Quick launcher for different levels of interactivity
"""

import sys
import os
import webbrowser
from pathlib import Path

def show_menu():
    print("=" * 60)
    print("🚀 Interactive MACD Trading Strategy Dashboard")
    print("=" * 60)
    print()
    print("Choose your level of interactivity:")
    print()
    print("1. 📊 Basic Interactive Chart (View Only)")
    print("   - Interactive plotly chart with zoom/pan")
    print("   - Time range selectors")
    print("   - Professional TradingView styling")
    print()
    print("2. 🎯 Advanced Dashboard (UI Controls)")
    print("   - Parameter input forms")
    print("   - Performance metrics display")
    print("   - Mock interactivity (UI only)")
    print()
    print("3. 🚀 Full Real-Time Server (Complete Functionality)")
    print("   - Live parameter updates")
    print("   - Real-time chart regeneration")
    print("   - Full backend integration")
    print()
    print("4. 🔧 Generate New Strategy Data")
    print("   - Run backtest with custom parameters")
    print("   - Generate fresh HTML files")
    print()
    print("5. ❌ Exit")
    print()

def open_basic_chart():
    chart_file = "ROSEUSDT_5m_interactive_macd.html"
    if os.path.exists(chart_file):
        print(f"📊 Opening {chart_file} in your browser...")
        webbrowser.open(f"file://{os.path.abspath(chart_file)}")
        print("✅ Chart opened! Enjoy the interactive features:")
        print("   • Zoom and pan the chart")
        print("   • Use time range selectors")
        print("   • Hover over data points")
        print("   • Toggle chart elements")
    else:
        print(f"❌ File {chart_file} not found.")
        print("💡 Run option 4 to generate new strategy data first.")

def open_advanced_dashboard():
    dashboard_file = "ROSEUSDT_5m_interactive_dashboard.html"
    if os.path.exists(dashboard_file):
        print(f"🎯 Opening {dashboard_file} in your browser...")
        webbrowser.open(f"file://{os.path.abspath(dashboard_file)}")
        print("✅ Dashboard opened! Features available:")
        print("   • Parameter input controls")
        print("   • Performance metrics display")
        print("   • Professional trading interface")
        print("   • Mock parameter updates (shows alert)")
    else:
        print(f"❌ File {dashboard_file} not found.")
        print("💡 Run option 4 to generate new strategy data first.")

def start_real_time_server():
    try:
        print("🚀 Starting Real-Time Interactive Dashboard Server...")
        print("📡 This will provide full functionality with live updates")
        print()
        print("🔧 Server features:")
        print("   • Real-time parameter updates")
        print("   • Live chart regeneration")
        print("   • Dynamic symbol switching")
        print("   • Instant backtesting")
        print()
        
        # Check if Flask is installed
        try:
            import flask
            import flask_cors
        except ImportError:
            print("❌ Missing dependencies!")
            print("📦 Please install: pip install flask flask-cors")
            return
            
        print("🌐 Server will be available at: http://localhost:5000")
        print("⚡ Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Import and run the server
        import subprocess
        subprocess.run([sys.executable, "interactive_dashboard_server.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def generate_new_data():
    print("🔧 Generating new strategy data...")
    print("📊 This will run the backtest and create fresh HTML files")
    print()
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, "interactive_macd_strategy.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ New strategy data generated successfully!")
            print("📁 Files created:")
            print("   • ROSEUSDT_5m_interactive_macd.html")
            print("   • ROSEUSDT_5m_interactive_dashboard.html")
            print()
            print("🎯 You can now use options 1-3 to view the results!")
        else:
            print("❌ Error generating data:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    while True:
        show_menu()
        
        try:
            choice = input("👉 Enter your choice (1-5): ").strip()
            print()
            
            if choice == "1":
                open_basic_chart()
            elif choice == "2":
                open_advanced_dashboard()
            elif choice == "3":
                start_real_time_server()
            elif choice == "4":
                generate_new_data()
            elif choice == "5":
                print("👋 Goodbye! Happy trading!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-5.")
            
            print()
            input("⏎ Press Enter to continue...")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

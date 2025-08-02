#!/usr/bin/env python3
"""
Fixed version of the spider runner with better error handling and proxy fallback
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

def run_spider_with_fallback(link=None, product=None, no_proxy=False):
    """Run the spider with fallback options"""
    
    # Check if PROXY_PASS is set
    proxy_pass = os.getenv('PROXY_PASS')
    if not proxy_pass and not no_proxy:
        print("❌ PROXY_PASS environment variable not set")
        print("💡 You can either:")
        print("   1. Set PROXY_PASS environment variable")
        print("   2. Run with --no-proxy flag")
        return False
    
    # Build the command
    cmd = [
        "scrapy", "crawl", "amazon_products",
        "-s", "LOG_LEVEL=INFO"
    ]
    
    # Add arguments
    if link:
        cmd.extend(["-a", f"link={link}"])
    elif product:
        cmd.extend(["-a", f"product={product}"])
    else:
        print("❌ You must provide either --link or --product")
        return False
    
    # Add no-proxy flag if requested
    if no_proxy:
        cmd.extend(["-a", "no_proxy=true"])
        print("🚀 Running spider without proxy...")
    else:
        print("🚀 Running spider with proxy...")
    
    print(f"📋 Command: {' '.join(cmd)}")
    print("=" * 50)
    
    try:
        # Run the spider
        result = subprocess.run(cmd, cwd="amazon", check=True)
        print("✅ Spider completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Spider failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️ Spider interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Amazon scraper with improved error handling")
    parser.add_argument("--link", help="Direct product link to scrape")
    parser.add_argument("--product", help="Product name to search for")
    parser.add_argument("--no-proxy", action="store_true", help="Run without proxy")
    parser.add_argument("--test-proxy", action="store_true", help="Test proxy connection first")
    
    args = parser.parse_args()
    
    # Test proxy if requested
    if args.test_proxy:
        print("🔍 Testing proxy connection...")
        try:
            from test_proxy import main as test_proxy_main
            test_proxy_main()
        except ImportError:
            print("❌ test_proxy.py not found")
        return
    
    # Validate arguments
    if not args.link and not args.product:
        print("❌ You must provide either --link or --product")
        print("💡 Example usage:")
        print("   python run_spider_fixed.py --link 'https://www.amazon.in/product-url'")
        print("   python run_spider_fixed.py --product 'iphone'")
        print("   python run_spider_fixed.py --product 'iphone' --no-proxy")
        return
    
    # Run the spider
    success = run_spider_with_fallback(
        link=args.link,
        product=args.product,
        no_proxy=args.no_proxy
    )
    
    if success:
        print("\n🎉 Scraping completed successfully!")
        print("📁 Check the output.json file for results")
    else:
        print("\n💡 Troubleshooting tips:")
        print("   1. Check your internet connection")
        print("   2. Verify your proxy credentials")
        print("   3. Try running with --no-proxy flag")
        print("   4. Run --test-proxy to diagnose proxy issues")

if __name__ == "__main__":
    main() 
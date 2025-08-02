#!/usr/bin/env python3
"""
Test script to verify Playwright route blocking works
"""
import asyncio
from playwright.async_api import async_playwright

async def blocking(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Set up route blocking
        await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())
        
        print("🔍 Navigating to Amazon product page...")
        await page.goto(url)
        
        print("📸 Taking screenshot...")
        await page.screenshot(path="test_no_images.png")
        
        print("✅ Test completed! Check test_no_images.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(blocking("https://www.amazon.in/Samsung-Galaxy-Smartphone-Titanium-Storage/dp/B0CS5XW6TN/")) 
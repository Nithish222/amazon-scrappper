import scrapy
from amazon.items import ProductItem
from scrapy_playwright.page import PageMethod
import json
import random
import os
from config import PROXY_HOST, PROXY_PORTS, PROXY_USER, PLAYWRIGHT_ABORT_RULES
from dotenv import load_dotenv
from scrapy.exceptions import IgnoreRequest

load_dotenv()
class AmazonProductsSpider(scrapy.Spider):
    name = "amazon_products"
    allowed_domains = ["amazon.in"]

    def __init__(self, link=None, product=None, no_proxy=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.no_proxy = no_proxy
        if link:
            self.mode = "link"
            self.start_url = link
            self.logger.info(f"Spider will crawl link: {self.start_url}")
        elif product:
            self.mode = "product"
            self.start_url = f"https://www.amazon.in/s?k={product}"
            self.logger.info(f"Spider will crawl search for product url: {self.start_url}")
        else:
            raise ValueError("You must provide either -a link=<url> or -a product=<product_name>")
        
        if self.no_proxy:
            self.logger.info("Running in no-proxy mode")

    def store_dynamic_data(self, data):
        """Handler for data sent from the browser via expose_function."""
        self.dynamic_data = data
        self.logger.info(f"Received dynamic data: {data}")



    def start_requests(self):
        if self.mode == "link":
            # Don't use playwright in the request - we'll handle it manually
            yield scrapy.Request(
                self.start_url,
                callback=self.parse_link_with_page,
                meta={"url": self.start_url}
            )
        elif self.mode == "product":
            yield scrapy.Request(
                self.start_url,
                callback=self.parse_product_mode
            )

    async def parse_link_with_page(self, response):
        # Manually create Playwright page to control navigation
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                # Set up route blocking before navigation (like in scraper.py)
                await page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font", "stylesheet"] else route.continue_())
                
                # Navigate to the URL with blocking enabled
                url = response.meta["url"]
                await page.goto(url, timeout=60000)
                
                # Wait for the page to load
                await page.wait_for_selector("#productTitle", timeout=20000)
                await page.wait_for_timeout(2000)
                
                content = await page.content()
                
                # Debug: Log the page title and URL to see what actually loaded
                page_title = await page.title()
                page_url = page.url
                self.logger.info(f"🔍 Debug: Page title: {page_title}")
                self.logger.info(f"🔍 Debug: Page URL: {page_url}")
                
                # Detect block/CAPTCHA
                if "Enter the characters you see below" in content or "not a robot" in content or "Sorry, we just need to make sure you're not a robot" in content:
                    self.logger.warning(f"Blocked or CAPTCHA page for {url}, will retry with new proxy.")
                    raise IgnoreRequest("Blocked or CAPTCHA page detected")
                
                self.logger.info("Page loaded, starting extraction...")
                
                # Extract dynamic data using JavaScript
                dynamic_data = await page.evaluate("""
                    () => {
                        const data = {};
                        try {
                            // Add a timeout for the entire operation
                            const startTime = Date.now();
                            const timeout = 10000; // 10 seconds
                            
                            const boughtElement = document.querySelector('#social-proofing-faceout-title-tk_bought');
                            data.bought = boughtElement ? boughtElement.textContent.trim() : '';
                            
                            const pricingElement = document.querySelector('#corePriceDisplay_desktop_feature_div');
                            if (pricingElement) {
                                const discountElement = pricingElement.querySelector('span.savingPriceOverride');
                                const symbolElement = pricingElement.querySelector('span.a-price-symbol');
                                const wholeElement = pricingElement.querySelector('span.a-price-whole');
                                const mrpElement = pricingElement.querySelector('span.aok-relative span.a-offscreen');
                                data.discount = discountElement ? discountElement.textContent.trim() : '';
                                const symbol = symbolElement ? symbolElement.textContent.trim() : '';
                                const whole = wholeElement ? wholeElement.textContent.trim() : '';
                                const mrp = mrpElement ? mrpElement.textContent.trim() : '';
                                data.price = symbol + whole;
                                data.mrp = mrp;
                            }
                            
                            // Frequently bought together
                            try {
                                const frequentlyList = [];
                                const freqElement = document.querySelector("div[data-csa-c-content-id='sims-productBundle']");
                                if (freqElement) {
                                    const productTitles = freqElement.querySelectorAll("span[class='a-size-base']");
                                    const productPrices = freqElement.querySelectorAll("span[class='a-price']");
                                    for (let i = 0; i < Math.min(productTitles.length, productPrices.length); i++) {
                                        const title = productTitles[i].textContent.trim();
                                        const priceText = productPrices[i].textContent;
                                        const price = priceText ? priceText.trim().replace("\\n", ".") : '';
                                        if (title && price) frequentlyList.push({name: title, price: price});
                                    }
                                }
                                data.frequently_bought = frequentlyList;
                            } catch (e) { data.frequently_bought = []; }
                            
                            // Summary
                            try {
                                const summaryElement = document.querySelector('div#product-summary p.a-spacing-small');
                                data.summary = summaryElement ? summaryElement.textContent.trim() : '';
                            } catch (e) { data.summary = ''; }
                            
                            // Mentions
                            try {
                                const mentionsList = [];
                                const mentionElements = document.querySelectorAll("div[aria-label='Commonly Mentioned Aspects'] a");
                                mentionElements.forEach(mention => {
                                    const text = mention.textContent.trim();
                                    if (text) mentionsList.push(text);
                                });
                                data.mentions = mentionsList;
                            } catch (e) { data.mentions = []; }
                            
                            // Check for timeout
                            if (Date.now() - startTime > timeout) {
                                throw new Error('Operation timed out');
                            }
                            
                            return data;
                        } catch (error) {
                            console.error('Error in data extraction:', error);
                            return { error: error.message };
                        }
                    }
                """)
                
                self.logger.info(f"Dynamic data extracted: {dynamic_data}")
                
                # Extract product data using page selectors instead of response
                item = ProductItem()
                
                # Basic product information
                asin_element = await page.query_selector('input[name="ASIN"]')
                item['asin'] = await asin_element.get_attribute('value') if asin_element else None
                if not item['asin']:
                    # Try to extract ASIN from URL
                    asin_match = url.split('/dp/')
                    if len(asin_match) > 1:
                        item['asin'] = asin_match[1].split('/')[0]
                
                title_element = await page.query_selector('#productTitle')
                item['name'] = await title_element.text_content() if title_element else ''
                item['url'] = url
                
                availability_element = await page.query_selector('#availability .a-color-success')
                item['is_available'] = 'yes' if availability_element else 'no'
            
                # Brand information
                brand_element = await page.query_selector('#bylineInfo')
                item['brand'] = await brand_element.text_content() if brand_element else ''
                
                brand_url_element = await page.query_selector('#bylineInfo')
                item['brand_url'] = await brand_url_element.get_attribute('href') if brand_url_element else ''
                
                # Seller information
                seller_element = await page.query_selector('#sellerProfileTriggerId')
                item['seller'] = await seller_element.text_content() if seller_element else ''
                
                seller_url_element = await page.query_selector('#sellerProfileTriggerId')
                item['seller_url'] = await seller_url_element.get_attribute('href') if seller_url_element else ''
                
                # Rating and reviews
                rating_element = await page.query_selector('#acrPopover')
                rating_text = await rating_element.get_attribute('title') if rating_element else None
                if rating_text:
                    try:
                        item['rating'] = float(rating_text.split(' ')[0])
                    except:
                        item['rating'] = None
                
                review_count_element = await page.query_selector('#acrCustomerReviewText')
                review_count_text = await review_count_element.text_content() if review_count_element else None
                if review_count_text:
                    try:
                        item['review_count'] = int(''.join(filter(str.isdigit, review_count_text)))
                    except:
                        item['review_count'] = None
                
                # Dynamic data from JavaScript
                if dynamic_data and not isinstance(dynamic_data, dict):
                    dynamic_data = {}
                
                item['past_count'] = dynamic_data.get('bought', '')
                item['discount'] = dynamic_data.get('discount', '')
                item['price'] = dynamic_data.get('price', '')
                item['mrp'] = dynamic_data.get('mrp', '')
                item['frequently_bought'] = dynamic_data.get('frequently_bought', [])
                item['summary'] = dynamic_data.get('summary', '')
                item['mentions'] = dynamic_data.get('mentions', [])
                
                # Convert price strings to numbers if possible
                if item['price']:
                    try:
                        price_clean = ''.join(filter(str.isdigit, item['price']))
                        if price_clean:
                            item['price'] = float(price_clean)
                    except:
                        pass
                
                if item['mrp']:
                    try:
                        mrp_clean = ''.join(filter(str.isdigit, item['mrp']))
                        if mrp_clean:
                            item['mrp'] = float(mrp_clean)
                    except:
                        pass
                
                # Timestamp
                from datetime import datetime
                item['scraped_at'] = datetime.now().isoformat()
                
                self.logger.info(f"✅ Extracted product: {item['name']}")
                yield item
                
            except Exception as e:
                self.logger.error(f"Error in parse_link_with_page: {e}")
                raise
            

    def safe_extract(self, selector, desc):
        """Safely extract text from selector with error handling"""
        try:
            element = selector
            if element:
                text = element.get().strip()
                self.logger.info(f"✅ {desc}: {text}")
                return text
            else:
                self.logger.warning(f"⚠️ {desc}: Not found")
                return ""
        except Exception as e:
            self.logger.error(f"❌ Error extracting {desc}: {e}")
            return ""

    def parse_product_mode(self, response):
        # 1. Collect all product URLs from the search results page
        product_links = response.css('a[href*="/dp/"]::attr(href)').getall()
        
        # Filter and clean URLs
        cleaned_links = []
        for link in product_links:
            if '/dp/' in link and 'ref=' in link:
                # Extract the base product URL
                base_url = link.split('ref=')[0]
                if base_url not in cleaned_links:
                    cleaned_links.append(base_url)
        
        self.logger.info(f"Found {len(cleaned_links)} product links")
        
        # 2. For each product URL, make a request with Playwright
        for i, product_url in enumerate(cleaned_links[:5]):  # Limit to first 5 for testing
            self.logger.info(f"Processing product {i+1}/{min(5, len(cleaned_links))}: {product_url}")
            
            # Ensure URL has proper scheme
            if not product_url.startswith('http'):
                product_url = response.urljoin(product_url)
            
            meta = {
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    # Don't navigate automatically - we'll do it manually with blocking
                ],
                "playwright_page_goto_kwargs": {"timeout": 60000},
            }
            
            # Add proxy configuration only if not in no-proxy mode
            if not self.no_proxy:
                meta["playwright_context_kwargs"] = {
                    "proxy": {
                        "server": f"http://{PROXY_HOST}:{random.choice(PROXY_PORTS)}",
                        "username": PROXY_USER,
                        "password": os.getenv('PROXY_PASS')
                    }
                }
            
            yield scrapy.Request(
                product_url,
                callback=self.parse_link_with_page,
                meta=meta
            )

    def get_proxy(self):
        """Get a random proxy configuration"""
        if self.no_proxy:
            return None
        proxy_port = random.choice(PROXY_PORTS)
        proxy_pass = os.getenv('PROXY_PASS')
        if proxy_pass:
            return f"http://{PROXY_USER}:{proxy_pass}@{PROXY_HOST}:{proxy_port}"
        return None
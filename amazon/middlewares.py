# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter

import random
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROXY_HOST, PROXY_PORTS, PROXY_USER

class RotateProxyOnRetryMiddleware:
    def process_request(self, request, spider):
        if request.meta.get('retry_times', 0) > 0:
            proxy_port = random.choice(PROXY_PORTS)
            proxy_pass = os.getenv('PROXY_PASS')
            proxy_url = f"http://{PROXY_USER}:{proxy_pass}@{PROXY_HOST}:{proxy_port}"
            request.meta['proxy'] = proxy_url
            spider.logger.info(f"[RotateProxyOnRetryMiddleware] Rotating proxy for retry: {proxy_url}")
        return None


class ProxyFallbackMiddleware:
    def __init__(self):
        self.proxy_failures = {}
        self.max_failures = 3
    
    def process_request(self, request, spider):
        # Check if we should use proxy
        if not spider.settings.getbool('PROXY_ENABLED', True):
            return None
            
        # If proxy has failed too many times, try without proxy
        if self.proxy_failures.get(request.meta.get('proxy', 'direct'), 0) >= self.max_failures:
            if 'proxy' in request.meta:
                del request.meta['proxy']
                spider.logger.info(f"[ProxyFallbackMiddleware] Falling back to direct connection due to proxy failures")
            return None
            
        # Set proxy if not already set
        if 'proxy' not in request.meta:
            proxy_port = random.choice(PROXY_PORTS)
            proxy_pass = os.getenv('PROXY_PASS')
            if proxy_pass:
                proxy_url = f"http://{PROXY_USER}:{proxy_pass}@{PROXY_HOST}:{proxy_port}"
                request.meta['proxy'] = proxy_url
                spider.logger.info(f"[ProxyFallbackMiddleware] Using proxy: {proxy_url}")
        
        return None
    
    def process_exception(self, request, exception, spider):
        # Track proxy failures
        proxy = request.meta.get('proxy', 'direct')
        if proxy != 'direct':
            self.proxy_failures[proxy] = self.proxy_failures.get(proxy, 0) + 1
            spider.logger.warning(f"[ProxyFallbackMiddleware] Proxy {proxy} failed ({self.proxy_failures[proxy]}/{self.max_failures})")
            
            # If this proxy has failed too many times, remove it from future requests
            if self.proxy_failures[proxy] >= self.max_failures:
                spider.logger.error(f"[ProxyFallbackMiddleware] Proxy {proxy} has failed {self.max_failures} times, disabling it")
        
        return None


class AmazonSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class AmazonDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

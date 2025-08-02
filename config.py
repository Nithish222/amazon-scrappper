BQ_PRODUCT_TABLE="amazon_product_data"

PROXY_HOST="gate.decodo.com"
PROXY_PORTS=["10001", "10002", "10003", "10004", "10005", "10006", "10007", "10008", "10009", "10010"]
PROXY_USER="speqxibe5h"

# Data usage optimization - abort rules for Playwright
PLAYWRIGHT_ABORT_RULES = [
    # Block Amazon media CDN (most important - catches all media)
    {"url": "https://m.media-amazon.com/**", "action": "abort"},
    {"url": "**/*m.media-amazon.com*", "action": "abort"},
    {"url": "**/*amazonaws*", "action": "abort"},
    {"url": "**/*s3.amazonaws*", "action": "abort"},
    {"url": "**/*cloudfront*", "action": "abort"},
    
    # Block all media files by extension (very specific)
    {"url": "**/*.png", "action": "abort"},
    {"url": "**/*.jpg", "action": "abort"},
    {"url": "**/*.jpeg", "action": "abort"},
    {"url": "**/*.gif", "action": "abort"},
    {"url": "**/*.webp", "action": "abort"},
    {"url": "**/*.svg", "action": "abort"},
    {"url": "**/*.ico", "action": "abort"},
    {"url": "**/*.mp4", "action": "abort"},
    {"url": "**/*.webm", "action": "abort"},
    {"url": "**/*.avi", "action": "abort"},
    {"url": "**/*.mov", "action": "abort"},
    {"url": "**/*.mp3", "action": "abort"},
    {"url": "**/*.wav", "action": "abort"},
    {"url": "**/*.ogg", "action": "abort"},
    {"url": "**/*.flv", "action": "abort"},
    {"url": "**/*.3gp", "action": "abort"},
    
    # Block all non-essential resource types
    {"url": "**/*", "resource_types": ["image", "media", "font", "stylesheet"], "action": "abort"},
    
    # Block tracking and analytics
    {"url": "**/*google-analytics*", "action": "abort"},
    {"url": "**/*doubleclick*", "action": "abort"},
    {"url": "**/*facebook*", "action": "abort"},
    {"url": "**/*twitter*", "action": "abort"},
    {"url": "**/*googlesyndication*", "action": "abort"},
    {"url": "**/*amazon-adsystem*", "action": "abort"},
    {"url": "**/*googletagmanager*", "action": "abort"},
    {"url": "**/*googletagservices*", "action": "abort"},
    {"url": "**/*amazon-ads*", "action": "abort"},
    
    # Block social media and external scripts
    {"url": "**/*instagram*", "action": "abort"},
    {"url": "**/*linkedin*", "action": "abort"},
    {"url": "**/*youtube*", "action": "abort"},
    
    # Block more ad networks
    {"url": "**/*adnxs*", "action": "abort"},
    {"url": "**/*criteo*", "action": "abort"},
    {"url": "**/*taboola*", "action": "abort"}
]
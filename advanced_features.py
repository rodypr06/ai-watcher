#!/usr/bin/env python3.11

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
try:
    import requests
except ImportError:
    print("Warning: requests not installed. Install with: pip install requests")
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Warning: beautifulsoup4 not installed. Install with: pip install beautifulsoup4")


class ImageExtractor:
    """Extract and process images from web articles"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Common image selectors for different sites
        self.image_selectors = {
            'og:image': {'tag': 'meta', 'attrs': {'property': 'og:image'}},
            'twitter:image': {'tag': 'meta', 'attrs': {'name': 'twitter:image'}},
            'featured_image': {'tag': 'img', 'class_contains': ['featured', 'hero', 'main', 'article']},
            'article_image': {'tag': 'img', 'parent_contains': ['article', 'content', 'story']},
            'first_large_image': {'tag': 'img', 'min_width': 300, 'min_height': 200}
        }
        
    def extract_images_from_url(self, article_url: str, max_images: int = 3) -> List[Dict[str, Any]]:
        """Extract images from an article URL"""
        try:
            response = self.session.get(article_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = f"{urlparse(article_url).scheme}://{urlparse(article_url).netloc}"
            
            extracted_images = []
            
            # Try different extraction methods in order of priority
            extraction_methods = [
                self._extract_og_image,
                self._extract_twitter_image, 
                self._extract_featured_images,
                self._extract_article_images,
                self._extract_large_images
            ]
            
            for method in extraction_methods:
                if len(extracted_images) >= max_images:
                    break
                    
                images = method(soup, base_url, article_url)
                for img in images:
                    if len(extracted_images) >= max_images:
                        break
                    # Check for duplicates by URL instead of full dict comparison
                    img_urls = [existing_img.get('url') for existing_img in extracted_images]
                    if img.get('url') not in img_urls:
                        extracted_images.append(img)
            
            # Validate and enrich image data
            validated_images = []
            for img in extracted_images:
                validated_img = self._validate_and_enrich_image(img)
                if validated_img:
                    validated_images.append(validated_img)
                    
            return validated_images
            
        except Exception as e:
            print(f"Error extracting images from {article_url}: {e}")
            return []
    
    def _extract_og_image(self, soup: BeautifulSoup, base_url: str, article_url: str) -> List[Dict[str, Any]]:
        """Extract Open Graph image"""
        og_image_tag = soup.find('meta', property='og:image')
        if og_image_tag and og_image_tag.get('content'):
            img_url = self._resolve_url(og_image_tag['content'], base_url)
            
            # Get alt text from og:title
            og_title_tag = soup.find('meta', property='og:title')
            alt_text = og_title_tag.get('content', '') if og_title_tag else ''
            
            return [{
                'url': img_url,
                'type': 'og_image',
                'alt': alt_text,
                'source': 'open_graph'
            }]
        return []
    
    def _extract_twitter_image(self, soup: BeautifulSoup, base_url: str, article_url: str) -> List[Dict[str, Any]]:
        """Extract Twitter Card image"""
        twitter_image_tag = soup.find('meta', {'name': 'twitter:image'})
        if twitter_image_tag and twitter_image_tag.get('content'):
            img_url = self._resolve_url(twitter_image_tag['content'], base_url)
            
            # Get alt text from twitter:title
            twitter_title_tag = soup.find('meta', {'name': 'twitter:title'})
            alt_text = twitter_title_tag.get('content', '') if twitter_title_tag else ''
            
            return [{
                'url': img_url,
                'type': 'twitter_image',
                'alt': alt_text,
                'source': 'twitter_card'
            }]
        return []
    
    def _extract_featured_images(self, soup: BeautifulSoup, base_url: str, article_url: str) -> List[Dict[str, Any]]:
        """Extract featured/hero images"""
        images = []
        
        # Look for images with featured/hero classes
        featured_selectors = [
            'img.featured-image', 'img.hero-image', 'img.main-image',
            '.featured-image img', '.hero-image img', '.article-hero img',
            'img[class*="featured"]', 'img[class*="hero"]'
        ]
        
        for selector in featured_selectors:
            img_tags = soup.select(selector)
            for img in img_tags[:2]:  # Limit to first 2 featured images
                img_data = self._extract_img_data(img, base_url)
                if img_data:
                    img_data['type'] = 'featured_image'
                    img_data['source'] = 'html_class'
                    images.append(img_data)
                    
        return images
    
    def _extract_article_images(self, soup: BeautifulSoup, base_url: str, article_url: str) -> List[Dict[str, Any]]:
        """Extract images from article content"""
        images = []
        
        # Look for images within article content
        article_selectors = [
            'article img', '.article-content img', '.post-content img',
            '.content img', '.story-content img', 'main img'
        ]
        
        for selector in article_selectors:
            img_tags = soup.select(selector)
            for img in img_tags[:3]:  # Limit to first 3 content images
                img_data = self._extract_img_data(img, base_url)
                if img_data:
                    img_data['type'] = 'content_image'
                    img_data['source'] = 'article_content'
                    images.append(img_data)
                    
        return images
    
    def _extract_large_images(self, soup: BeautifulSoup, base_url: str, article_url: str) -> List[Dict[str, Any]]:
        """Extract large images as fallback"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags[:5]:  # Check first 5 images
            img_data = self._extract_img_data(img, base_url)
            if img_data:
                # Try to determine if image is large enough to be relevant
                width = img.get('width')
                height = img.get('height')
                
                if width and height:
                    try:
                        if int(width) >= 300 and int(height) >= 200:
                            img_data['type'] = 'large_image'
                            img_data['source'] = 'size_filter'
                            images.append(img_data)
                    except ValueError:
                        pass
                else:
                    # If no size info, include it anyway as potential image
                    img_data['type'] = 'potential_image'
                    img_data['source'] = 'fallback'
                    images.append(img_data)
                    
        return images
    
    def _extract_img_data(self, img_tag, base_url: str) -> Optional[Dict[str, Any]]:
        """Extract data from an img tag"""
        src = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-lazy-src')
        if not src:
            return None
            
        img_url = self._resolve_url(src, base_url)
        
        return {
            'url': img_url,
            'alt': img_tag.get('alt', ''),
            'title': img_tag.get('title', ''),
            'width': img_tag.get('width'),
            'height': img_tag.get('height'),
            'class': img_tag.get('class', []),
            'loading': img_tag.get('loading', '')
        }
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if url.startswith(('http://', 'https://')):
            return url
        elif url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{base_url}{url}"
        else:
            return urljoin(base_url, url)
    
    def _validate_and_enrich_image(self, img_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate image URL and enrich with metadata"""
        try:
            # Quick HEAD request to validate image exists
            response = self.session.head(img_data['url'], timeout=5)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if content_type.startswith('image/'):
                    img_data['content_type'] = content_type
                    img_data['file_size'] = response.headers.get('content-length')
                    img_data['validated'] = True
                    img_data['last_modified'] = response.headers.get('last-modified')
                    return img_data
                    
        except Exception as e:
            print(f"Image validation failed for {img_data['url']}: {e}")
            
        return None


class SocialSentimentAnalyzer:
    """Analyze social media sentiment around AI news stories"""
    
    def __init__(self):
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        self.reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        
    def analyze_story_sentiment(self, headline: str, url: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze sentiment for a specific news story"""
        sentiment_data = {
            'headline': headline,
            'url': url,
            'overall_sentiment': 0.0,
            'social_mentions': 0,
            'platforms': {}
        }
        
        # Analyze Twitter sentiment
        if self.twitter_bearer_token:
            twitter_sentiment = self._analyze_twitter_sentiment(keywords)
            sentiment_data['platforms']['twitter'] = twitter_sentiment
            
        # Analyze Reddit sentiment
        if self.reddit_client_id and self.reddit_client_secret:
            reddit_sentiment = self._analyze_reddit_sentiment(keywords)
            sentiment_data['platforms']['reddit'] = reddit_sentiment
            
        # Calculate overall sentiment
        platform_sentiments = [data.get('sentiment', 0) for data in sentiment_data['platforms'].values()]
        if platform_sentiments:
            sentiment_data['overall_sentiment'] = sum(platform_sentiments) / len(platform_sentiments)
            sentiment_data['social_mentions'] = sum(data.get('mentions', 0) for data in sentiment_data['platforms'].values())
            
        return sentiment_data
    
    def _analyze_twitter_sentiment(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze Twitter sentiment for keywords"""
        if not self.twitter_bearer_token:
            return {'sentiment': 0.0, 'mentions': 0, 'sample_tweets': []}
            
        headers = {
            'Authorization': f'Bearer {self.twitter_bearer_token}',
            'Content-Type': 'application/json'
        }
        
        # Search for recent tweets
        query = ' OR '.join(keywords[:3])  # Limit to avoid API limits
        url = f'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': f'{query} -is:retweet',
            'max_results': 20,
            'tweet.fields': 'created_at,public_metrics,context_annotations'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                tweets = data.get('data', [])
                
                sentiment_scores = []
                sample_tweets = []
                
                for tweet in tweets[:10]:  # Analyze first 10 tweets
                    text = tweet.get('text', '')
                    sentiment = self._calculate_text_sentiment(text)
                    sentiment_scores.append(sentiment)
                    
                    sample_tweets.append({
                        'text': text[:100] + '...' if len(text) > 100 else text,
                        'sentiment': sentiment,
                        'created_at': tweet.get('created_at'),
                        'metrics': tweet.get('public_metrics', {})
                    })
                
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                
                return {
                    'sentiment': avg_sentiment,
                    'mentions': len(tweets),
                    'sample_tweets': sample_tweets
                }
                
        except Exception as e:
            print(f"Twitter API error: {e}")
            
        return {'sentiment': 0.0, 'mentions': 0, 'sample_tweets': []}
    
    def _analyze_reddit_sentiment(self, keywords: List[str]) -> Dict[str, Any]:
        """Analyze Reddit sentiment for keywords"""
        # This would require Reddit API implementation
        # For now, return placeholder data
        return {'sentiment': 0.0, 'mentions': 0, 'sample_posts': []}
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Simple sentiment calculation (-1 to 1)"""
        positive_words = [
            'breakthrough', 'amazing', 'incredible', 'revolutionary', 'excellent',
            'fantastic', 'great', 'awesome', 'impressive', 'innovative',
            'exciting', 'promising', 'powerful', 'efficient', 'successful'
        ]
        
        negative_words = [
            'terrible', 'awful', 'bad', 'horrible', 'disappointing',
            'concerning', 'dangerous', 'risky', 'problematic', 'failure',
            'disaster', 'scary', 'worried', 'threat', 'bias'
        ]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
            
        return (pos_count - neg_count) / (pos_count + neg_count)


class StockPriceTracker:
    """Track stock prices for AI companies mentioned in news"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        
        # Mapping of company names to stock symbols
        self.company_symbols = {
            'openai': ['MSFT'],  # Microsoft has stake in OpenAI
            'microsoft': ['MSFT'],
            'google': ['GOOGL'],
            'alphabet': ['GOOGL'],
            'meta': ['META'],
            'facebook': ['META'],
            'nvidia': ['NVDA'],
            'amd': ['AMD'],
            'intel': ['INTC'],
            'amazon': ['AMZN'],
            'apple': ['AAPL'],
            'tesla': ['TSLA'],
            'palantir': ['PLTR'],
            'snowflake': ['SNOW'],
            'databricks': [],  # Private company
            'anthropic': [],   # Private company
        }
    
    def get_stock_movements(self, mentioned_companies: List[str]) -> Dict[str, Any]:
        """Get stock price movements for mentioned companies"""
        stock_data = {}
        
        for company in mentioned_companies:
            company_lower = company.lower()
            symbols = []
            
            # Find matching stock symbols
            for company_key, symbol_list in self.company_symbols.items():
                if company_key in company_lower or company_lower in company_key:
                    symbols.extend(symbol_list)
            
            # Get stock data for each symbol
            for symbol in symbols:
                if symbol not in stock_data:
                    price_data = self._get_stock_price(symbol)
                    if price_data:
                        stock_data[symbol] = price_data
        
        return stock_data
    
    def _get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current stock price and recent movement"""
        if self.alpha_vantage_key:
            return self._get_alpha_vantage_data(symbol)
        elif self.finnhub_key:
            return self._get_finnhub_data(symbol)
        else:
            return None
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data from Alpha Vantage API"""
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                
                if quote:
                    return {
                        'symbol': symbol,
                        'price': float(quote.get('05. price', 0)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%').rstrip('%'),
                        'volume': int(quote.get('06. volume', 0)),
                        'timestamp': quote.get('07. latest trading day')
                    }
        except Exception as e:
            print(f"Alpha Vantage API error for {symbol}: {e}")
            
        return None
    
    def _get_finnhub_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock data from Finnhub API"""
        url = f'https://finnhub.io/api/v1/quote'
        params = {
            'symbol': symbol,
            'token': self.finnhub_key
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                current_price = data.get('c', 0)
                previous_close = data.get('pc', 0)
                
                if current_price and previous_close:
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100
                    
                    return {
                        'symbol': symbol,
                        'price': current_price,
                        'change': change,
                        'change_percent': f"{change_percent:.2f}%",
                        'volume': data.get('v', 0),
                        'timestamp': datetime.now().strftime('%Y-%m-%d')
                    }
        except Exception as e:
            print(f"Finnhub API error for {symbol}: {e}")
            
        return None


class NewsEnhancer:
    """Enhance news articles with additional context and data"""
    
    def __init__(self):
        self.sentiment_analyzer = SocialSentimentAnalyzer()
        self.stock_tracker = StockPriceTracker()
        self.image_extractor = ImageExtractor()
    
    def enhance_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance articles with sentiment, stock data, images, and other metrics"""
        enhanced_articles = []
        
        for article in articles:
            enhanced_article = article.copy()
            
            # Extract keywords for analysis
            keywords = self._extract_keywords(article)
            companies = self._extract_companies(article)
            
            # Extract images from article URL
            article_url = article.get('url', '')
            if article_url:
                print(f"🖼️ Extracting images from: {article_url}")
                images = self.image_extractor.extract_images_from_url(article_url, max_images=2)
                if images:
                    enhanced_article['images'] = images
                    enhanced_article['has_images'] = True
                    print(f"✅ Found {len(images)} images")
                else:
                    enhanced_article['images'] = []
                    enhanced_article['has_images'] = False
            
            # Add sentiment analysis
            if keywords:
                sentiment_data = self.sentiment_analyzer.analyze_story_sentiment(
                    article.get('headline', ''),
                    article.get('url', ''),
                    keywords
                )
                enhanced_article['social_sentiment'] = sentiment_data
            
            # Add stock price data
            if companies:
                stock_data = self.stock_tracker.get_stock_movements(companies)
                enhanced_article['stock_movements'] = stock_data
            
            # Add credibility and impact scores
            enhanced_article['credibility_score'] = self._calculate_credibility(article)
            enhanced_article['impact_score'] = self._calculate_impact(article)
            
            enhanced_articles.append(enhanced_article)
            
            # Rate limiting to avoid API issues
            time.sleep(0.2)  # Increased to allow for image extraction
        
        return enhanced_articles
    
    def _extract_keywords(self, article: Dict[str, Any]) -> List[str]:
        """Extract relevant keywords from article"""
        text = f"{article.get('headline', '')} {article.get('summary', '')}".lower()
        
        ai_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning',
            'neural network', 'gpt', 'llm', 'transformer', 'ai model',
            'computer vision', 'nlp', 'robotics', 'automation'
        ]
        
        found_keywords = []
        for keyword in ai_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords[:5]  # Limit to top 5
    
    def _extract_companies(self, article: Dict[str, Any]) -> List[str]:
        """Extract company names from article"""
        text = f"{article.get('headline', '')} {article.get('summary', '')} {' '.join(article.get('stakeholders', []))}".lower()
        
        companies = []
        company_names = [
            'openai', 'microsoft', 'google', 'alphabet', 'meta', 'facebook',
            'nvidia', 'amd', 'intel', 'amazon', 'apple', 'tesla',
            'anthropic', 'deepmind', 'palantir', 'snowflake'
        ]
        
        for company in company_names:
            if company in text:
                companies.append(company)
        
        return list(set(companies))  # Remove duplicates
    
    def _calculate_credibility(self, article: Dict[str, Any]) -> int:
        """Calculate credibility score (1-10)"""
        # This would use the existing calculate_credibility_score function
        # For now, return a placeholder
        return article.get('credibility_score', 5)
    
    def _calculate_impact(self, article: Dict[str, Any]) -> int:
        """Calculate impact score (1-10)"""
        # This would use the existing calculate_impact_score function  
        # For now, return a placeholder
        return article.get('impact_score', 5)
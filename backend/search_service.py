"""
Internet Search Service using DuckDuckGo
========================================

This service provides internet search functionality using DuckDuckGo's search API.
It's designed to be integrated with the RAG system to provide real-time information
when internet search is enabled for a session.
"""

import requests
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
import time
import re

class DuckDuckGoSearchService:
    """Service for performing internet searches using DuckDuckGo"""
    
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"
        self.instant_answer_url = "https://api.duckduckgo.com/"
        self.web_search_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def search_instant_answer(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for instant answers using DuckDuckGo's instant answer API
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, content, and URL
        """
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(
                self.instant_answer_url, 
                params=params, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Extract abstract (main answer)
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Instant Answer'),
                    'content': data.get('Abstract', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo Instant Answer',
                    'type': 'instant_answer'
                })
            
            # Extract related topics
            for topic in data.get('RelatedTopics', [])[:max_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('FirstURL', '').split('/')[-1].replace('_', ' ').title(),
                        'content': topic.get('Text', ''),
                        'url': topic.get('FirstURL', ''),
                        'source': 'DuckDuckGo Related Topics',
                        'type': 'related_topic'
                    })
            
            return results[:max_results]
            
        except Exception as e:
            print(f"Error in instant answer search: {e}")
            return []
    
    def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo's HTML search
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of web search results
        """
        try:
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            response = requests.get(
                self.web_search_url, 
                params=params, 
                headers=self.headers, 
                timeout=15
            )
            response.raise_for_status()
            
            # Parse HTML response to extract search results
            results = self._parse_html_results(response.text, max_results)
            return results
            
        except Exception as e:
            print(f"Error in web search: {e}")
            return []
    
    def _parse_html_results(self, html_content: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Parse HTML content to extract search results
        
        Args:
            html_content: HTML content from DuckDuckGo search
            max_results: Maximum number of results to extract
            
        Returns:
            List of parsed search results
        """
        import re
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Find result containers
            result_containers = soup.find_all('div', class_='result')
            
            for container in result_containers[:max_results]:
                try:
                    # Extract title and URL
                    title_link = container.find('a', class_='result__a')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    url = title_link.get('href', '')
                    
                    # Extract snippet
                    snippet_elem = container.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    # Extract domain
                    domain_elem = container.find('a', class_='result__url')
                    domain = domain_elem.get_text(strip=True) if domain_elem else ''
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'content': snippet,
                            'url': url,
                            'domain': domain,
                            'source': 'DuckDuckGo Web Search',
                            'type': 'web_result'
                        })
                        
                except Exception as e:
                    print(f"Error parsing result container: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"Error parsing HTML results: {e}")
            return []
    
    def search(self, query: str, max_results: int = 5, include_instant: bool = True) -> List[Dict[str, Any]]:
        """
        Perform a comprehensive search combining instant answers and web results
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            include_instant: Whether to include instant answers
            
        Returns:
            List of search results
        """
        results = []
        
        # Get instant answers first (if enabled)
        if include_instant:
            instant_results = self.search_instant_answer(query, max_results=2)
            results.extend(instant_results)
        
        # Get web results
        remaining_results = max_results - len(results)
        if remaining_results > 0:
            web_results = self.search_web(query, max_results=remaining_results)
            results.extend(web_results)
        
        return results[:max_results]
    
    def format_search_results_for_llm(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results for LLM consumption
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string for LLM
        """
        if not results:
            return "No search results found."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_result = f"{i}. {result['title']}\n"
            formatted_result += f"   Content: {result['content']}\n"
            if result.get('url'):
                formatted_result += f"   URL: {result['url']}\n"
            if result.get('domain'):
                formatted_result += f"   Domain: {result['domain']}\n"
            formatted_result += f"   Source: {result['source']}\n"
            formatted_results.append(formatted_result)
        
        return "\n".join(formatted_results)
    
    def is_search_needed(self, query: str) -> bool:
        """
        Determine if a query would benefit from internet search
        
        Args:
            query: User query
            
        Returns:
            True if search is recommended, False otherwise
        """
        # Keywords that suggest need for current information
        search_keywords = [
            'current', 'latest', 'recent', 'today', 'now', '2024', '2025',
            'news', 'update', 'happening', 'trending', 'price', 'weather',
            'stock', 'market', 'crypto', 'bitcoin', 'ethereum', 'covid',
            'pandemic', 'election', 'war', 'crisis', 'breaking', 'live',
            'real-time', 'time-sensitive', 'what is happening', 'what\'s new'
        ]
        
        query_lower = query.lower()
        
        # Check for search keywords
        for keyword in search_keywords:
            if keyword in query_lower:
                return True
        
        # Check for question patterns that suggest current information
        current_patterns = [
            r'what.*happening.*now',
            r'what.*latest.*on',
            r'current.*status.*of',
            r'recent.*developments.*in',
            r'what.*new.*in',
            r'latest.*news.*about',
            r'current.*price.*of',
            r'what.*weather.*today',
            r'breaking.*news',
            r'live.*updates'
        ]
        
        for pattern in current_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False

# Global search service instance
search_service = DuckDuckGoSearchService()

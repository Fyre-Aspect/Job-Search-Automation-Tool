"""
Indeed RSS Scraper
Fetches job listings from Indeed's public RSS feeds.
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime
import time
import re


class IndeedRSSScraper:
    """
    Scrapes job listings from Indeed using their public RSS feed.
    No authentication required.
    """
    
    BASE_URL = "https://www.indeed.com/rss"
    
    # Keywords to search for
    SEARCH_QUERIES = [
        "junior web developer",
        "junior software developer", 
        "software engineer intern",
        "web developer intern",
        "entry level developer",
        "frontend developer entry level",
        "backend developer junior",
        "full stack developer junior",
        "software developer internship",
        "junior programmer",
    ]
    
    # Locations to search
    LOCATIONS = [
        "remote",
        "Kitchener, ON",
        "Waterloo, ON",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _build_url(self, query: str, location: str) -> str:
        """Build RSS feed URL for a specific query and location."""
        params = {
            'q': query,
            'l': location,
            'sort': 'date',
            'fromage': '1',  # Jobs from last 1 day
        }
        query_string = '&'.join(f"{k}={requests.utils.quote(str(v))}" for k, v in params.items())
        return f"{self.BASE_URL}?{query_string}"
    
    def _parse_rss_feed(self, xml_content: str) -> List[Dict]:
        """Parse RSS XML content and extract job listings."""
        jobs = []
        
        try:
            root = ET.fromstring(xml_content)
            channel = root.find('channel')
            
            if channel is None:
                return jobs
            
            for item in channel.findall('item'):
                job = self._parse_job_item(item)
                if job:
                    jobs.append(job)
                    
        except ET.ParseError as e:
            print(f"[Indeed RSS] XML parse error: {e}")
        
        return jobs
    
    def _parse_job_item(self, item: ET.Element) -> Optional[Dict]:
        """Parse a single job item from RSS feed."""
        try:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            description_elem = item.find('description')
            
            if title_elem is None or link_elem is None:
                return None
            
            title = title_elem.text or ""
            url = link_elem.text or ""
            
            # Extract company from title (Indeed format: "Job Title - Company Name")
            company = "Unknown Company"
            if ' - ' in title:
                parts = title.rsplit(' - ', 1)
                if len(parts) == 2:
                    title = parts[0].strip()
                    company = parts[1].strip()
            
            # Parse date
            posted_date = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    posted_date = datetime.strptime(
                        pub_date_elem.text, 
                        "%a, %d %b %Y %H:%M:%S %Z"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    posted_date = pub_date_elem.text
            
            # Extract skills from description
            description = description_elem.text if description_elem is not None else ""
            skills = self._extract_skills(description)
            
            # Determine job type
            job_type = self._determine_job_type(title, description)
            
            # Determine compensation (if mentioned)
            compensation = self._extract_compensation(description)
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': self._extract_location(description),
                'job_type': job_type,
                'compensation': compensation,
                'skills': skills,
                'posted_date': posted_date,
                'source': 'Indeed',
                'description': description[:500] if description else ""
            }
            
        except Exception as e:
            print(f"[Indeed RSS] Error parsing job item: {e}")
            return None
    
    def _extract_skills(self, text: str) -> str:
        """Extract mentioned technical skills from job description."""
        skill_keywords = [
            'JavaScript', 'Python', 'Java', 'C#', 'C++', 'Ruby', 'Go', 'Rust',
            'React', 'Angular', 'Vue', 'Node.js', 'Express', 'Django', 'Flask',
            'HTML', 'CSS', 'TypeScript', 'SQL', 'MongoDB', 'PostgreSQL', 'MySQL',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Git', 'Linux',
            'REST API', 'GraphQL', '.NET', 'Spring', 'PHP', 'Laravel',
            'TailwindCSS', 'Bootstrap', 'SASS', 'Redux', 'Next.js'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills[:8]) if found_skills else "Not specified"
    
    def _determine_job_type(self, title: str, description: str) -> str:
        """Determine the job type from title and description."""
        text = (title + " " + description).lower()
        
        if 'intern' in text:
            return 'Internship'
        elif 'entry level' in text or 'entry-level' in text:
            return 'Entry-Level'
        elif 'junior' in text or 'jr.' in text or 'jr ' in text:
            return 'Junior'
        elif 'summer' in text:
            return 'Summer Position'
        elif 'contract' in text:
            return 'Contract'
        elif 'part-time' in text or 'part time' in text:
            return 'Part-Time'
        else:
            return 'Full-Time'
    
    def _extract_compensation(self, text: str) -> str:
        """Extract compensation information if available."""
        text_lower = text.lower()
        
        # Check for salary mentions
        salary_pattern = r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|\/)\s*(?:hour|hr|year|yr|month|mo))?'
        match = re.search(salary_pattern, text, re.IGNORECASE)
        
        if match:
            return match.group(0)
        elif 'paid' in text_lower and 'unpaid' not in text_lower:
            return 'Paid'
        elif 'unpaid' in text_lower:
            return 'Unpaid'
        else:
            return 'Not specified'
    
    def _extract_location(self, text: str) -> str:
        """Extract location from description."""
        text_lower = text.lower()
        
        if 'remote' in text_lower:
            return 'Remote'
        elif 'kitchener' in text_lower or 'waterloo' in text_lower:
            return 'Kitchener-Waterloo, ON'
        else:
            return 'See listing'
    
    def scrape(self) -> List[Dict]:
        """
        Scrape job listings from all configured queries and locations.
        Returns a list of job dictionaries.
        """
        all_jobs = []
        seen_urls = set()
        
        print("[Indeed RSS] Starting scrape...")
        
        for query in self.SEARCH_QUERIES:
            for location in self.LOCATIONS:
                try:
                    url = self._build_url(query, location)
                    print(f"[Indeed RSS] Fetching: {query} in {location}")
                    
                    response = self.session.get(url, timeout=30)
                    
                    if response.status_code == 200:
                        jobs = self._parse_rss_feed(response.text)
                        
                        for job in jobs:
                            if job['url'] not in seen_urls:
                                seen_urls.add(job['url'])
                                all_jobs.append(job)
                    else:
                        print(f"[Indeed RSS] HTTP {response.status_code} for {query}")
                    
                    # Rate limiting - be respectful
                    time.sleep(2)
                    
                except requests.RequestException as e:
                    print(f"[Indeed RSS] Request error for {query}: {e}")
                    continue
        
        print(f"[Indeed RSS] Found {len(all_jobs)} unique jobs")
        return all_jobs


if __name__ == "__main__":
    # Test the scraper
    scraper = IndeedRSSScraper()
    jobs = scraper.scrape()
    
    for job in jobs[:5]:
        print(f"\n{'='*50}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Type: {job['job_type']}")
        print(f"URL: {job['url']}")

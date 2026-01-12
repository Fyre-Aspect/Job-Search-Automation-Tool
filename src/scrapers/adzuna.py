"""
Adzuna API Scraper
Fetches job listings from Adzuna's public job search API.
Free tier available with API key registration.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import os
import time
import re


class AdzunaScraper:
    """
    Scrapes job listings from Adzuna's API.
    Requires free API key from https://developer.adzuna.com/
    Falls back gracefully if no API key is configured.
    """
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    
    # Countries to search (ca = Canada, us = USA for remote)
    COUNTRIES = ['ca', 'us']
    
    # Search queries
    SEARCH_QUERIES = [
        "junior developer",
        "web developer intern",
        "software developer entry level",
        "frontend developer",
        "backend developer",
    ]
    
    def __init__(self):
        self.app_id = os.environ.get('ADZUNA_APP_ID', '')
        self.app_key = os.environ.get('ADZUNA_APP_KEY', '')
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobSearchBot/1.0',
            'Accept': 'application/json'
        })
    
    def _is_configured(self) -> bool:
        """Check if Adzuna API credentials are configured."""
        return bool(self.app_id and self.app_key)
    
    def _build_url(self, country: str, page: int = 1) -> str:
        """Build API URL for a specific country."""
        return f"{self.BASE_URL}/{country}/search/{page}"
    
    def _build_params(self, query: str) -> Dict:
        """Build query parameters for API request."""
        return {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'what': query,
            'what_or': 'intern junior entry-level remote',
            'max_days_old': 7,
            'results_per_page': 50,
            'sort_by': 'date',
            'content-type': 'application/json',
        }
    
    def _parse_job(self, job_data: Dict) -> Optional[Dict]:
        """Parse a single job from API response."""
        try:
            title = job_data.get('title', 'Unknown Position')
            
            # Clean HTML from title
            title = re.sub(r'<[^>]+>', '', title)
            
            company = job_data.get('company', {}).get('display_name', 'Unknown Company')
            url = job_data.get('redirect_url', '')
            
            # Get location
            location_data = job_data.get('location', {})
            location_parts = location_data.get('display_name', 'Not specified')
            
            # Check if remote
            description = job_data.get('description', '')
            if 'remote' in description.lower() or 'remote' in title.lower():
                location_parts = f"Remote / {location_parts}"
            
            # Parse date
            created = job_data.get('created', '')
            posted_date = None
            if created:
                try:
                    posted_date = datetime.fromisoformat(
                        created.replace('Z', '+00:00')
                    ).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    posted_date = created[:10] if len(created) >= 10 else None
            
            # Get salary info
            salary_min = job_data.get('salary_min')
            salary_max = job_data.get('salary_max')
            
            if salary_min and salary_max:
                compensation = f"${int(salary_min):,} - ${int(salary_max):,}"
            elif salary_min:
                compensation = f"${int(salary_min):,}+"
            else:
                compensation = "Not specified"
            
            # Extract skills from description
            skills = self._extract_skills(description)
            
            # Determine job type
            job_type = self._determine_job_type(title, description)
            
            # Clean description
            description = re.sub(r'<[^>]+>', ' ', description)
            description = re.sub(r'\s+', ' ', description).strip()
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': location_parts,
                'job_type': job_type,
                'compensation': compensation,
                'skills': skills,
                'posted_date': posted_date,
                'source': 'Adzuna',
                'description': description[:500]
            }
            
        except Exception as e:
            print(f"[Adzuna] Error parsing job: {e}")
            return None
    
    def _extract_skills(self, text: str) -> str:
        """Extract technical skills from job description."""
        skill_keywords = [
            'JavaScript', 'Python', 'Java', 'C#', 'Ruby', 'Go', 'PHP',
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
            'HTML', 'CSS', 'TypeScript', 'SQL', 'MongoDB', 'PostgreSQL',
            'AWS', 'Azure', 'Docker', 'Git', 'Linux', 'REST', 'API'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills[:6]) if found_skills else "Not specified"
    
    def _determine_job_type(self, title: str, description: str) -> str:
        """Determine job type from title and description."""
        text = (title + " " + description).lower()
        
        if 'intern' in text:
            return 'Internship'
        elif 'entry level' in text or 'entry-level' in text:
            return 'Entry-Level'
        elif 'junior' in text or 'jr.' in text:
            return 'Junior'
        elif 'graduate' in text:
            return 'Graduate Program'
        elif 'contract' in text:
            return 'Contract'
        else:
            return 'Full-Time'
    
    def _is_valid_location(self, location: str) -> bool:
        """Check if location is remote or in Kitchener-Waterloo."""
        loc_lower = location.lower()
        
        # Accept remote jobs
        if 'remote' in loc_lower:
            return True
        
        # Accept Kitchener-Waterloo area
        if 'kitchener' in loc_lower or 'waterloo' in loc_lower:
            return True
        
        # Accept general Ontario/Canada for broader matches
        if 'ontario' in loc_lower or ', on' in loc_lower:
            return True
        
        # For US jobs, only accept if marked remote
        return False
    
    def scrape(self) -> List[Dict]:
        """
        Fetch and parse job listings from Adzuna API.
        Returns a list of job dictionaries.
        """
        all_jobs = []
        seen_urls = set()
        
        if not self._is_configured():
            print("[Adzuna] No API credentials configured. Skipping.")
            print("[Adzuna] Set ADZUNA_APP_ID and ADZUNA_APP_KEY environment variables.")
            return all_jobs
        
        print("[Adzuna] Starting API scrape...")
        
        for country in self.COUNTRIES:
            for query in self.SEARCH_QUERIES:
                try:
                    url = self._build_url(country, page=1)
                    params = self._build_params(query)
                    
                    print(f"[Adzuna] Fetching: {query} in {country.upper()}")
                    
                    response = self.session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        for job_data in results:
                            # Filter by location
                            location = job_data.get('location', {}).get('display_name', '')
                            description = job_data.get('description', '')
                            
                            # Check remote mention in description
                            if 'remote' in description.lower():
                                pass  # Include remote jobs
                            elif not self._is_valid_location(location):
                                continue
                            
                            job = self._parse_job(job_data)
                            if job and job['url'] not in seen_urls:
                                seen_urls.add(job['url'])
                                all_jobs.append(job)
                    else:
                        print(f"[Adzuna] HTTP {response.status_code} for {query}")
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except requests.RequestException as e:
                    print(f"[Adzuna] Request error: {e}")
                    continue
                except ValueError as e:
                    print(f"[Adzuna] JSON parse error: {e}")
                    continue
        
        print(f"[Adzuna] Found {len(all_jobs)} relevant jobs")
        return all_jobs


if __name__ == "__main__":
    # Test the scraper
    scraper = AdzunaScraper()
    jobs = scraper.scrape()
    
    for job in jobs[:5]:
        print(f"\n{'='*50}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Type: {job['job_type']}")
        print(f"URL: {job['url']}")

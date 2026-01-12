"""
The Muse API Scraper
Fetches job listings from The Muse's public API.
Good for startup and tech company jobs.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import time


class TheMuseScraper:
    """
    Scrapes job listings from The Muse's free public API.
    No authentication required for basic access.
    """
    
    BASE_URL = "https://www.themuse.com/api/public/jobs"
    
    # Categories relevant to software/web development
    CATEGORIES = [
        "Software Engineering",
        "Software Engineer",
        "Data and Analytics",
        "Design and UX",
        "IT",
    ]
    
    # Experience levels to target
    LEVELS = [
        "Entry Level",
        "Internship",
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobSearchBot/1.0 (Educational Project)',
            'Accept': 'application/json'
        })
    
    def _build_params(self, category: str, level: str, page: int = 0) -> Dict:
        """Build query parameters for API request."""
        return {
            'category': category,
            'level': level,
            'page': page,
            'descending': 'true',
        }
    
    def _parse_job(self, job_data: Dict) -> Optional[Dict]:
        """Parse a single job from API response."""
        try:
            title = job_data.get('name', 'Unknown Position')
            
            # Get company info
            company_data = job_data.get('company', {})
            company = company_data.get('name', 'Unknown Company')
            
            # Build URL
            job_id = job_data.get('id', '')
            short_name = job_data.get('short_name', '')
            url = f"https://www.themuse.com/jobs/{company_data.get('short_name', 'company')}/{short_name}"
            
            # Or use refs if available
            refs = job_data.get('refs', {})
            if refs.get('landing_page'):
                url = refs['landing_page']
            
            # Get locations
            locations = job_data.get('locations', [])
            location_str = ', '.join([loc.get('name', '') for loc in locations[:2]])
            if not location_str:
                location_str = 'Not specified'
            
            # Parse levels/job type
            levels = job_data.get('levels', [])
            level_names = [lvl.get('name', '') for lvl in levels]
            job_type = self._determine_job_type(level_names)
            
            # Get categories as skills
            categories = job_data.get('categories', [])
            skills = ', '.join([cat.get('name', '') for cat in categories[:5]])
            if not skills:
                skills = 'Not specified'
            
            # Parse date
            pub_date = job_data.get('publication_date', '')
            posted_date = None
            if pub_date:
                try:
                    posted_date = datetime.fromisoformat(
                        pub_date.replace('Z', '+00:00')
                    ).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    posted_date = pub_date[:10] if len(pub_date) >= 10 else None
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': location_str,
                'job_type': job_type,
                'compensation': 'Not specified',  # The Muse doesn't expose salary in API
                'skills': skills,
                'posted_date': posted_date,
                'source': 'The Muse',
                'description': job_data.get('contents', '')[:500]
            }
            
        except Exception as e:
            print(f"[The Muse] Error parsing job: {e}")
            return None
    
    def _determine_job_type(self, levels: List[str]) -> str:
        """Determine job type from level names."""
        levels_lower = [l.lower() for l in levels]
        
        if any('intern' in l for l in levels_lower):
            return 'Internship'
        elif any('entry' in l for l in levels_lower):
            return 'Entry-Level'
        elif any('junior' in l for l in levels_lower):
            return 'Junior'
        else:
            return 'Full-Time'
    
    def _is_remote_or_kw(self, locations: List[Dict]) -> bool:
        """Check if job is remote or in Kitchener-Waterloo area."""
        for loc in locations:
            name = loc.get('name', '').lower()
            if 'remote' in name:
                return True
            if 'kitchener' in name or 'waterloo' in name:
                return True
            if 'canada' in name or 'ontario' in name:
                return True  # Include broader Canada/Ontario for more results
        return False
    
    def scrape(self) -> List[Dict]:
        """
        Fetch and parse job listings from The Muse API.
        Returns a list of job dictionaries.
        """
        all_jobs = []
        seen_urls = set()
        
        print("[The Muse] Starting API scrape...")
        
        for level in self.LEVELS:
            for category in self.CATEGORIES:
                try:
                    params = self._build_params(category, level, page=0)
                    print(f"[The Muse] Fetching: {level} - {category}")
                    
                    response = self.session.get(
                        self.BASE_URL, 
                        params=params, 
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        for job_data in results:
                            # Filter for remote or local jobs
                            locations = job_data.get('locations', [])
                            if not self._is_remote_or_kw(locations):
                                continue
                            
                            job = self._parse_job(job_data)
                            if job and job['url'] not in seen_urls:
                                seen_urls.add(job['url'])
                                all_jobs.append(job)
                    else:
                        print(f"[The Muse] HTTP {response.status_code} for {category}")
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except requests.RequestException as e:
                    print(f"[The Muse] Request error: {e}")
                    continue
                except ValueError as e:
                    print(f"[The Muse] JSON parse error: {e}")
                    continue
        
        print(f"[The Muse] Found {len(all_jobs)} relevant jobs")
        return all_jobs


if __name__ == "__main__":
    # Test the scraper
    scraper = TheMuseScraper()
    jobs = scraper.scrape()
    
    for job in jobs[:5]:
        print(f"\n{'='*50}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Type: {job['job_type']}")
        print(f"URL: {job['url']}")

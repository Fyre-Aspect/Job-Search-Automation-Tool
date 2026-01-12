"""
RemoteOK API Scraper
Fetches remote job listings from RemoteOK's public JSON API.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import re


class RemoteOKScraper:
    """
    Scrapes remote job listings from RemoteOK's free public API.
    Returns JSON data directly, no authentication required.
    """
    
    API_URL = "https://remoteok.com/api"
    
    # Tags/keywords to filter for relevant jobs
    TARGET_TAGS = [
        'dev', 'developer', 'engineer', 'software', 'web', 
        'frontend', 'backend', 'fullstack', 'full-stack',
        'junior', 'entry', 'intern', 'javascript', 'python',
        'react', 'node', 'typescript'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'JobSearchBot/1.0 (Educational Project)',
            'Accept': 'application/json'
        })
    
    def _is_relevant_job(self, job: Dict) -> bool:
        """Check if job matches our target criteria."""
        # Combine searchable text
        searchable = (
            job.get('position', '') + ' ' +
            job.get('company', '') + ' ' +
            ' '.join(job.get('tags', []))
        ).lower()
        
        # Must match at least one target tag
        return any(tag in searchable for tag in self.TARGET_TAGS)
    
    def _is_recent(self, date_str: str, days: int = 7) -> bool:
        """Check if job was posted within the last N days."""
        if not date_str:
            return True  # Include if no date available
        
        try:
            # RemoteOK uses ISO format
            posted_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            cutoff = datetime.now(posted_date.tzinfo) - timedelta(days=days)
            return posted_date >= cutoff
        except (ValueError, TypeError):
            return True
    
    def _parse_job(self, job_data: Dict) -> Optional[Dict]:
        """Parse a single job from API response."""
        try:
            # Skip the first item which is metadata
            if 'position' not in job_data:
                return None
            
            title = job_data.get('position', 'Unknown Position')
            company = job_data.get('company', 'Unknown Company')
            
            # Build application URL
            slug = job_data.get('slug', '')
            job_id = job_data.get('id', '')
            url = job_data.get('url', f"https://remoteok.com/remote-jobs/{job_id}-{slug}")
            
            # If URL is relative or missing, construct it
            if not url.startswith('http'):
                url = f"https://remoteok.com/remote-jobs/{job_id}"
            
            # Extract skills from tags
            tags = job_data.get('tags', [])
            skills = ', '.join(tags[:8]) if tags else 'Not specified'
            
            # Parse date
            date_str = job_data.get('date', '')
            posted_date = None
            if date_str:
                try:
                    posted_date = datetime.fromisoformat(
                        date_str.replace('Z', '+00:00')
                    ).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    posted_date = date_str[:10] if len(date_str) >= 10 else None
            
            # Extract salary info
            salary_min = job_data.get('salary_min', 0)
            salary_max = job_data.get('salary_max', 0)
            
            if salary_min and salary_max:
                compensation = f"${salary_min:,} - ${salary_max:,}/year"
            elif salary_min:
                compensation = f"${salary_min:,}+/year"
            else:
                compensation = "Not specified"
            
            # Determine job type
            job_type = self._determine_job_type(title, ' '.join(tags))
            
            # Get description snippet
            description = job_data.get('description', '')
            # Clean HTML tags
            description = re.sub(r'<[^>]+>', ' ', description)
            description = re.sub(r'\s+', ' ', description).strip()
            
            return {
                'title': title,
                'company': company,
                'url': url,
                'location': 'Remote (Global)',
                'job_type': job_type,
                'compensation': compensation,
                'skills': skills,
                'posted_date': posted_date,
                'source': 'RemoteOK',
                'description': description[:500] if description else ""
            }
            
        except Exception as e:
            print(f"[RemoteOK] Error parsing job: {e}")
            return None
    
    def _determine_job_type(self, title: str, tags: str) -> str:
        """Determine job type from title and tags."""
        text = (title + " " + tags).lower()
        
        if 'intern' in text:
            return 'Internship'
        elif 'entry' in text or 'junior' in text or 'jr' in text:
            return 'Entry-Level'
        elif 'contract' in text:
            return 'Contract'
        elif 'part-time' in text or 'part time' in text:
            return 'Part-Time'
        else:
            return 'Full-Time'
    
    def scrape(self) -> List[Dict]:
        """
        Fetch and parse job listings from RemoteOK API.
        Returns a list of job dictionaries.
        """
        all_jobs = []
        
        print("[RemoteOK] Fetching jobs from API...")
        
        try:
            response = self.session.get(self.API_URL, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # First item is metadata, skip it
                job_list = data[1:] if len(data) > 1 else []
                
                for job_data in job_list:
                    # Filter for relevant jobs
                    if not self._is_relevant_job(job_data):
                        continue
                    
                    # Check if recent
                    if not self._is_recent(job_data.get('date', ''), days=7):
                        continue
                    
                    job = self._parse_job(job_data)
                    if job:
                        all_jobs.append(job)
                
                print(f"[RemoteOK] Found {len(all_jobs)} relevant jobs")
            else:
                print(f"[RemoteOK] HTTP {response.status_code}")
                
        except requests.RequestException as e:
            print(f"[RemoteOK] Request error: {e}")
        except ValueError as e:
            print(f"[RemoteOK] JSON parse error: {e}")
        
        return all_jobs


if __name__ == "__main__":
    # Test the scraper
    scraper = RemoteOKScraper()
    jobs = scraper.scrape()
    
    for job in jobs[:5]:
        print(f"\n{'='*50}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Type: {job['job_type']}")
        print(f"Compensation: {job['compensation']}")
        print(f"URL: {job['url']}")

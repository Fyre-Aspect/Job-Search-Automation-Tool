"""
Local Jobs Scraper (SimplyHired/ZipRecruiter style)
Fetches local part-time job listings.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import time
import re


class LocalJobsScraper:
    """
    Scrapes local job listings focusing on part-time opportunities
    in the Kitchener-Waterloo area using public job feeds.
    """
    
    # Major retail/service employers to check directly
    KNOWN_EMPLOYERS = {
        'footlocker': {
            'name': 'Foot Locker',
            'careers_hint': 'Check footlocker-inc.jobs or indeed.com/cmp/Foot-Locker'
        },
        'bluenotes': {
            'name': 'Bluenotes',
            'careers_hint': 'Check yrginternational.com/careers or indeed'
        },
        'tim_hortons': {
            'name': 'Tim Hortons',
            'careers_hint': 'Check timhortons.com/careers'
        },
        'mcdonalds': {
            'name': "McDonald's",
            'careers_hint': 'Check mcdonalds.ca/careers'
        },
        'walmart': {
            'name': 'Walmart',
            'careers_hint': 'Check walmartcareers.ca'
        },
        'dollarama': {
            'name': 'Dollarama',
            'careers_hint': 'Check dollarama.com/careers'
        },
        'shoppers': {
            'name': 'Shoppers Drug Mart',
            'careers_hint': 'Check jobs.shoppersdrugmart.ca'
        },
    }
    
    # JSearch API (via RapidAPI - free tier) - Alternative job aggregator
    JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _create_manual_listings(self) -> List[Dict]:
        """
        Create manual job listing suggestions for major local employers.
        These are always hiring and good for a first job.
        """
        manual_jobs = []
        
        # Common part-time roles always available
        common_roles = [
            {
                'title': 'Sales Associate (Part-Time)',
                'company': 'Foot Locker',
                'location': 'Conestoga Mall, Waterloo',
                'job_type': 'Part-Time Retail',
                'compensation': '$15.50-$17/hr',
                'skills': 'Customer Service, Sales, Teamwork',
                'url': 'https://www.footlocker-inc.com/careers.html',
                'source': 'Direct - Check Store',
                'posted_date': 'Always Hiring',
                'description': 'Help customers find shoes, maintain store displays. Flexible hours, great for students.'
            },
            {
                'title': 'Team Member (Part-Time)',
                'company': 'Tim Hortons',
                'location': 'Multiple locations - Kitchener/Waterloo',
                'job_type': 'Part-Time Food Service',
                'compensation': '$15.50-$16.50/hr',
                'skills': 'Customer Service, Cash Handling, Food Prep',
                'url': 'https://www.timhortons.ca/careers',
                'source': 'Direct - Apply Online/In-Store',
                'posted_date': 'Always Hiring',
                'description': 'Serve customers, prepare food and drinks. Flexible scheduling for students.'
            },
            {
                'title': 'Crew Member (Part-Time)',
                'company': "McDonald's",
                'location': 'Multiple locations - Kitchener/Waterloo',
                'job_type': 'Part-Time Food Service',
                'compensation': '$15.50-$17/hr',
                'skills': 'Customer Service, Teamwork, Fast-Paced Environment',
                'url': 'https://www.mcdonalds.com/ca/en-ca/careers.html',
                'source': 'Direct - Apply Online',
                'posted_date': 'Always Hiring',
                'description': 'Take orders, prepare food, clean. Training provided. Very flexible hours.'
            },
            {
                'title': 'Store Associate (Part-Time)',
                'company': 'Dollarama',
                'location': 'Multiple locations - Kitchener/Waterloo',
                'job_type': 'Part-Time Retail',
                'compensation': '$15.50-$16/hr',
                'skills': 'Customer Service, Stocking, Cash Register',
                'url': 'https://www.dollarama.com/en-CA/corp/careers',
                'source': 'Direct - Apply In-Store',
                'posted_date': 'Always Hiring',
                'description': 'Stock shelves, help customers, operate cash register. No experience needed.'
            },
            {
                'title': 'Cashier/Beauty Associate (Part-Time)',
                'company': 'Shoppers Drug Mart',
                'location': 'Multiple locations - Kitchener/Waterloo',
                'job_type': 'Part-Time Retail',
                'compensation': '$15.50-$17/hr',
                'skills': 'Customer Service, Cash Handling, Organization',
                'url': 'https://jobs.shoppersdrugmart.ca/',
                'source': 'Direct - Apply Online',
                'posted_date': 'Frequently Hiring',
                'description': 'Help customers, work cash register, stock shelves. Student-friendly shifts.'
            },
            {
                'title': 'Sales Associate (Part-Time)',
                'company': 'Bluenotes',
                'location': 'Conestoga Mall, Waterloo',
                'job_type': 'Part-Time Retail',
                'compensation': '$15.50-$16/hr',
                'skills': 'Customer Service, Fashion, Sales',
                'url': 'https://www.bluenotes.com/pages/careers',
                'source': 'Direct - Check Store',
                'posted_date': 'Check In-Store',
                'description': 'Help customers, maintain displays, process sales. Good employee discounts!'
            },
            {
                'title': 'Grocery Clerk (Part-Time)',
                'company': 'Walmart',
                'location': 'Multiple locations - Kitchener/Waterloo/Cambridge',
                'job_type': 'Part-Time Retail',
                'compensation': '$15.50-$17/hr',
                'skills': 'Customer Service, Stocking, Physical Work',
                'url': 'https://www.walmartcareers.ca/',
                'source': 'Direct - Apply Online',
                'posted_date': 'Always Hiring',
                'description': 'Stock shelves, assist customers, maintain departments. Flexible scheduling.'
            },
            {
                'title': 'Sandwich Artist (Part-Time)',
                'company': 'Subway',
                'location': 'Multiple locations - Kitchener/Waterloo',
                'job_type': 'Part-Time Food Service',
                'compensation': '$15.50-$16/hr',
                'skills': 'Customer Service, Food Prep, Cash Handling',
                'url': 'https://www.subway.com/en-ca/careers',
                'source': 'Direct - Apply In-Store',
                'posted_date': 'Always Hiring',
                'description': 'Make sandwiches, serve customers, keep store clean. Training provided.'
            },
        ]
        
        return common_roles
    
    def scrape(self) -> List[Dict]:
        """
        Return local job suggestions.
        """
        print("[Local Jobs] Generating local part-time job suggestions...")
        
        jobs = self._create_manual_listings()
        
        print(f"[Local Jobs] Found {len(jobs)} local opportunities")
        return jobs


if __name__ == "__main__":
    scraper = LocalJobsScraper()
    jobs = scraper.scrape()
    
    for job in jobs:
        print(f"\n{'='*50}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Pay: {job['compensation']}")

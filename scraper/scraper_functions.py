import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Base URL for completed events
BASE_URL_ALL_EVENTS = "http://ufcstats.com/statistics/events/completed?page=all"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def safe_text(element):
    return element.text.strip() if element else 'N/A'

def convert_time_to_seconds(time_str):
    """Convert time format (MM:SS) to total seconds"""
    if not time_str or time_str == 'N/A':
        return 'N/A'
    
    try:
        if ':' in time_str:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + int(seconds)
        else:
            return int(time_str)
    except (ValueError, TypeError):
        return 'N/A'

def is_womens_fight(weight_class):
    """Check if the fight is a women's division fight"""
    if not weight_class or weight_class == 'N/A':
        return False
    
    womens_divisions = [
        'women\'s', "women's", 'women', 'woman', 
        'strawweight', 'flyweight', 'bantamweight', 'featherweight',
        'wstraw', 'wfly', 'wbantam', 'wfeather'
    ]
    
    weight_class_lower = weight_class.lower()
    return any(division in weight_class_lower for division in womens_divisions)

def randomize_fighter_positions(fight_data):
    """Randomly swap Fighter 1 and Fighter 2 positions to remove bias"""
    if random.random() < 0.5:
        # Swap all fighter data
        fight_data['Fighter_1'], fight_data['Fighter_2'] = fight_data['Fighter_2'], fight_data['Fighter_1']
        fight_data['Fighter_1_KD'], fight_data['Fighter_2_KD'] = fight_data['Fighter_2_KD'], fight_data['Fighter_1_KD']
        fight_data['Fighter_1_STR'], fight_data['Fighter_2_STR'] = fight_data['Fighter_2_STR'], fight_data['Fighter_1_STR']
        fight_data['Fighter_1_TD'], fight_data['Fighter_2_TD'] = fight_data['Fighter_2_TD'], fight_data['Fighter_1_TD']
        fight_data['Fighter_1_SUB'], fight_data['Fighter_2_SUB'] = fight_data['Fighter_2_SUB'], fight_data['Fighter_1_SUB']
        fight_data['Winner_Label'] = 0
    else:
        fight_data['Winner_Label'] = 1
    
    return fight_data

def get_latest_events_up_to_target(target_event_name, max_events=3):
    """Get latest UFC events up to target event"""
    urls = []
    event_names = []
    
    logger.info(f"🔍 Fetching events from: {BASE_URL_ALL_EVENTS}")
    
    try:
        res = requests.get(BASE_URL_ALL_EVENTS, headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        
        event_links = soup.find_all('a', href=True, class_='b-link b-link_style_black')
        
        for link in event_links:
            href = link['href']
            event_name = safe_text(link)
            
            if '/event-details/' in href and href not in urls and event_name:
                urls.append(href)
                event_names.append(event_name)
                
                if target_event_name.lower() in event_name.lower():
                    logger.info(f"🎯 Found target event: {event_name}")
                    break
                    
    except Exception as e:
        logger.error(f"❌ Error fetching events: {e}")
        return []
    
    latest_events = list(zip(urls, event_names))[:max_events]
    logger.info(f"✅ Found {len(latest_events)} events to process")
    
    for i, (url, name) in enumerate(latest_events):
        logger.info(f"   {i+1}. {name}")
    
    return [url for url, name in latest_events]

def scrape_event_fights(event_url):
    """Scrape fights from a single event"""
    logger.info(f"🥊 Scraping event: {event_url}")
    fights = []
    
    try:
        res = requests.get(event_url, headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Extract event name
        event_name_elem = soup.find('h2', class_='b-content__title')
        event_name = safe_text(event_name_elem) if event_name_elem else 'UFC Event'
        
        fight_table = soup.find('tbody') 
        if not fight_table:
            logger.warning("⚠️ No fight table found in this event")
            return fights

        rows = fight_table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: 
                continue

            # Fighter names
            fighter_elements = cols[1].find_all('p', class_='b-fight-details__table-text')
            fighter1 = safe_text(fighter_elements[0].find('a')) if len(fighter_elements) > 0 else 'N/A'
            fighter2 = safe_text(fighter_elements[1].find('a')) if len(fighter_elements) > 1 else 'N/A'

            # Fighter stats
            fighter1_kd = safe_text(cols[2].find('p', class_='b-fight-details__table-text')) if len(cols) > 2 else 'N/A'
            fighter1_str = safe_text(cols[3].find('p', class_='b-fight-details__table-text')) if len(cols) > 3 else 'N/A'
            fighter1_td = safe_text(cols[4].find('p', class_='b-fight-details__table-text')) if len(cols) > 4 else 'N/A'
            fighter1_sub = safe_text(cols[5].find('p', class_='b-fight-details__table-text')) if len(cols) > 5 else 'N/A'

            fighter2_kd = safe_text(cols[2].find_all('p', class_='b-fight-details__table-text')[1]) if len(cols) > 2 and len(cols[2].find_all('p', class_='b-fight-details__table-text')) > 1 else 'N/A'
            fighter2_str = safe_text(cols[3].find_all('p', class_='b-fight-details__table-text')[1]) if len(cols) > 3 and len(cols[3].find_all('p', class_='b-fight-details__table-text')) > 1 else 'N/A'
            fighter2_td = safe_text(cols[4].find_all('p', class_='b-fight-details__table-text')[1]) if len(cols) > 4 and len(cols[4].find_all('p', class_='b-fight-details__table-text')) > 1 else 'N/A'
            fighter2_sub = safe_text(cols[5].find_all('p', class_='b-fight-details__table-text')[1]) if len(cols) > 5 and len(cols[5].find_all('p', class_='b-fight-details__table-text')) > 1 else 'N/A'

            # Fight details
            weight_class = safe_text(cols[6].find('p', class_='b-fight-details__table-text')) if len(cols) > 6 else 'N/A'
            method = safe_text(cols[7].find('p', class_='b-fight-details__table-text')) if len(cols) > 7 else 'N/A'
            
            round_ = safe_text(cols[8].find('p', class_='b-fight-details__table-text')) if len(cols) > 8 else 'N/A'
            try:
                round_ = int(round_)
            except (ValueError, TypeError):
                round_ = 'N/A'

            time_ = safe_text(cols[9].find('p', class_='b-fight-details__table-text')) if len(cols) > 9 else 'N/A'
            
            # Skip women's fights
            if is_womens_fight(weight_class):
                logger.info(f"🚫 Skipping women's fight: {weight_class}")
                continue

            # Convert time to seconds
            time_in_seconds = convert_time_to_seconds(time_)

            # Create fight data
            fight_data = {
                'Fighter_1': fighter1,
                'Fighter_1_KD': fighter1_kd,
                'Fighter_1_STR': fighter1_str,
                'Fighter_1_TD': fighter1_td,
                'Fighter_1_SUB': fighter1_sub,
                'Fighter_2': fighter2,
                'Fighter_2_KD': fighter2_kd,
                'Fighter_2_STR': fighter2_str,
                'Fighter_2_TD': fighter2_td,
                'Fighter_2_SUB': fighter2_sub,
                'Weight_Class': weight_class,
                'Method': method,
                'Round': round_,
                'Time': time_in_seconds,
                'Event_Name': event_name,
                'Winner_Label': None  # Will be set by randomize_fighter_positions
            }

            # Randomize positions and add winner label
            fight_data = randomize_fighter_positions(fight_data)
            fights.append(fight_data)
            
        logger.info(f"✅ Scraped {len(fights)} fights from event")
            
    except Exception as e:
        logger.error(f"❌ Error scraping event {event_url}: {e}")
        
    return fights

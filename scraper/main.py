import os
import sys
import logging
from datetime import datetime
from database import MySQLHandler
from notification import EmailNotifier
from scraper_functions import get_latest_events_up_to_target, scrape_event_fights

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper/logs/scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the UFC data pipeline"""
    logger.info("🚀 Starting UFC Data Pipeline")
    
    try:
        # Initialize database handler
        db_config = {
            'host': os.getenv('DB_HOST'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        
        db_handler = MySQLHandler(db_config)
        
        # Initialize email notifier
        email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': os.getenv('EMAIL_USER'),
            'sender_password': os.getenv('EMAIL_PASSWORD'),
            'receiver_email': os.getenv('TO_EMAIL')
        }
        email_notifier = EmailNotifier(email_config)
        
        # Scrape latest events
        logger.info("🔍 Scraping latest UFC events...")
        target_event = "Fight Night:"
        event_urls = get_latest_events_up_to_target(target_event, max_events=3)
        
        all_fights = []
        for i, url in enumerate(event_urls):
            logger.info(f"📊 Scraping event {i+1}/{len(event_urls)}: {url}")
            fights = scrape_event_fights(url)
            all_fights.extend(fights)
        
        # Save to database
        if all_fights:
            fights_added = db_handler.save_fights(all_fights)
            logger.info(f"💾 Saved {fights_added} fights to database")
            
            # Send success notification
            email_notifier.send_success_notification(
                events_processed=len(event_urls),
                fights_added=fights_added,
                total_fights=len(all_fights)
            )
            
            logger.info(f"🎉 Pipeline completed successfully! {fights_added} new fights added.")
        else:
            logger.warning("😔 No fights were scraped")
            email_notifier.send_error_notification("No fights were scraped from the events")
            
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {str(e)}")
        # Send error notification
        try:
            email_notifier.send_error_notification(str(e))
        except:
            pass  # If email fails, at least we logged the error
        sys.exit(1)

if __name__ == "__main__":
    main()

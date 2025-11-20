import mysql.connector
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MySQLHandler:
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.connect()
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("✅ Connected to MySQL database")
        except mysql.connector.Error as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def save_fights(self, fights_data):
        """Save fights data to latest_fights table"""
        if not fights_data:
            return 0
            
        cursor = self.connection.cursor()
        fights_added = 0
        
        try:
            insert_query = """
            INSERT INTO latest_fights 
            (fighter_1, fighter_1_kd, fighter_1_str, fighter_1_td, fighter_1_sub,
             fighter_2, fighter_2_kd, fighter_2_str, fighter_2_td, fighter_2_sub,
             weight_class, method, round, time_seconds, winner_label, event_name, event_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for fight in fights_data:
                # Use current date as event date (since we don't scrape actual event dates)
                current_date = datetime.now().strftime('%Y-%m-%d')
                
                cursor.execute(insert_query, (
                    fight['Fighter_1'], fight['Fighter_1_KD'], fight['Fighter_1_STR'], 
                    fight['Fighter_1_TD'], fight['Fighter_1_SUB'],
                    fight['Fighter_2'], fight['Fighter_2_KD'], fight['Fighter_2_STR'],
                    fight['Fighter_2_TD'], fight['Fighter_2_SUB'],
                    fight['Weight_Class'], fight['Method'], fight['Round'],
                    fight['Time'], fight['Winner_Label'],
                    fight.get('Event_Name', 'UFC Event'), current_date
                ))
                fights_added += 1
            
            self.connection.commit()
            logger.info(f"💾 Successfully added {fights_added} fights to latest_fights table")
            
        except mysql.connector.Error as e:
            logger.error(f"❌ Error saving fights to database: {e}")
            self.connection.rollback()
            fights_added = 0
        finally:
            cursor.close()
            
        return fights_added
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("🔌 Database connection closed")

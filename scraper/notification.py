import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self, config):
        self.config = config
        
    def send_success_notification(self, events_processed, fights_added, total_fights):
        """Send success email notification"""
        subject = f"✅ UFC Data Pipeline Success - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        🥊 UFC Data Pipeline Report
        
        📊 STATUS: SUCCESS
        🕒 Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        📈 Results:
           • Events Processed: {events_processed}
           • Fights Scraped: {total_fights}
           • New Fights Added to Database: {fights_added}
           • Database Table: latest_fights
        
        🎯 Next Steps:
           • Check your MySQL database
           • Review the new fight data
           • Update your ML model if needed
        
        ¡Buena suerte hermano! 🥊
        """
        
        self._send_email(subject, body)
        logger.info("📧 Success notification sent")
        
    def send_error_notification(self, error_message):
        """Send error email notification"""
        subject = f"❌ UFC Data Pipeline Failed - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        🥊 UFC Data Pipeline Report
        
        📊 STATUS: FAILED
        🕒 Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        ❌ Error Details:
        {error_message}
        
        🔧 Action Required:
           • Check GitHub Actions logs
           • Verify database connection
           • Review UFC stats website availability
        
        ¡Necesitamos arreglar esto hermano! 🔧
        """
        
        self._send_email(subject, body)
        logger.info("📧 Error notification sent")
        
    def _send_email(self, subject, body):
        """Send email using SMTP"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['receiver_email']
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['sender_email'], self.config['sender_password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            raise

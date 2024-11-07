 
import psycopg2
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

# Database connection details
db_config = {
    'dbname': '',
    'user': '',
    'password': '',
    'host': '',
    'port': ''
}

# Email notification details
email_sender = 'no-reply-jenkins@eficens.com'
email_receiver = 'vijays@eficens.com,neelgopal@eficens.com'
smtp_server = ''
smtp_port = 587
smtp_user = 'no-reply-jenkins@eficens.com'
smtp_password = ''

def send_email(token_id, expire_time):
    message = MIMEText(f"Token with ID {token_id} is expiring on {expire_time}.")
    message['Subject'] = 'Token Expiry Notification'
    message['From'] = email_sender
    message['To'] = email_receiver
    
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(email_sender, email_receiver, message.as_string())
        print(f"Notification sent for token ID {token_id}")

def check_expiring_tokens():
    # Calculate the expiry date range (next 2 days)
    now = datetime.now()
    expiry_threshold = now + timedelta(days=2)
    
    try:
        # Connect to the database
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        # Query for tokens expiring in the next two days
        cursor.execute("""
            SELECT id, expire_time FROM public.scheduler_access_tokens
            WHERE expire_time BETWEEN %s AND %s
        """, (now, expiry_threshold))
        
        # Send notification for each expiring token
        tokens = cursor.fetchall()
        for token_id, expire_time in tokens:
            send_email(token_id, expire_time)
            
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    check_expiring_tokens()

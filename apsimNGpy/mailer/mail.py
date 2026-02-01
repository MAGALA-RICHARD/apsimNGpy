import os
from email import encoders
import smtplib
import logging

logger = logging.getLogger(__name__)


def send_report(sms, subject, attachment_path=None):
    # Works only on the local machine for the robot to run automatically and send results of what is going on
    # the env vars are set manually on the local machine for security purposes
    all_envs = False
    sender = None
    receiver = None
    key = None
    if os.environ.get('REPORT_TESTS', None):
        sender = os.environ.get('SENDER', sender)
        receiver = os.environ.get('RECEIVER', receiver)
        key = os.environ.get('PASSCODE', key)
        all_envs = all([receiver, sender, key])
    if all_envs:
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        # Email credentials
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587
        EMAIL_SENDER = sender
        EMAIL_PASSWORD = key
        EMAIL_RECEIVER = receiver

        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject

        # Attach text message
        msg.attach(MIMEText(sms, "plain"))

        # Attach a file if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        # Send the email
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Secure the connection
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
                logger.info("Email sent successfully!")
        except Exception as e:
            print("Error:", e)

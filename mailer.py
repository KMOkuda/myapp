import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr, formatdate
from config import SMTP_HOST, SMTP_PORT, MAIL_FROM_ADDR, MAIL_FROM_NAME

def send_mail(to_email: str, subject: str, body: str):
    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(MAIL_FROM_NAME, "utf-8")), MAIL_FROM_ADDR))
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
        s.sendmail(MAIL_FROM_ADDR, [to_email], msg.as_string())
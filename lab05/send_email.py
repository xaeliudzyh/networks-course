import sys
import smtplib
from email.message import EmailMessage

def send_text_email(smtp_host, smtp_port, username, password, sender, recipient, subject, body):
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)
    print(f"[+] Text email sent to {recipient}")

def main():
    if len(sys.argv) < 5:
        print("Usage: python send_email.py <text|html> <recipient> <subject> <body_file>")
        sys.exit(1)

    mode = sys.argv[1].lower()
    recipient = sys.argv[2]
    subject = sys.argv[3]
    body_file = sys.argv[4]

    smtp_host = "smtp.mail.ru"
    smtp_port = 587
    username = "tsagol10@mail.ru"
    password = "Ywvq5*******"

    sender = username

    with open(body_file, "r", encoding="utf-8") as f:
        content = f.read()

    if mode == "text":
        send_text_email(smtp_host, smtp_port, username, password, sender, recipient, subject, content)
    else:
        print("Mode must be 'text'")
        sys.exit(1)

if __name__ == "__main__":
    main()

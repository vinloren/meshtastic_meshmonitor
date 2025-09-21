import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendGmail(corpo,password,mittente,destinatario):
    smtp_server = "out.alice.it"
    port = 587
    message = MIMEMultipart()
    message["From"] = mittente
    message["Subject"] = "Alarm ch0"
    message["To"] = destinatario
    message.attach(MIMEText(corpo, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  # Secure the connection
        server.login(mittente, password)
        server.sendmail(mittente, destinatario, message.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")
        server.quit()
    finally:
        print("Chiudo mail")
        server.quit()

    
        
import smtplib
from email.mime.text import MIMEText

def sendGmail(corpo,password_app,mittente,destinatario):
    # Crea il messaggio
    mittente = mittente
    msg = MIMEText(corpo)
    msg["Subject"] = "ch0 Alert"
    msg["From"] = mittente
    msg["To"] = destinatario

    try:
        print("Connessione al server SMTP...")
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.ehlo()
        print("Login in corso...")
        server.login(mittente, password_app)
        print("Login riuscito. Invio in corso...")
        server.send_message(msg)
        server.quit()
        print("Email inviata con successo!")
    except smtplib.SMTPAuthenticationError as e:
        print("Errore di autenticazione:", e.smtp_error.decode())
    except Exception as e:
        print("Errore:", str(e))

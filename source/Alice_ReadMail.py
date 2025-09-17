import imaplib
import os,time
import ssl
from dotenv import load_dotenv
import sqlite3 as dba
from datetime import datetime
import email
from email.header import decode_header
from apscheduler.schedulers.blocking import BlockingScheduler
import logging,re
from logging.handlers import RotatingFileHandler

class callDB(): 
    Db = '../app.db'

    def insertMsg(self,testo):
        data = datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.now().strftime("%T")    
        try:
            conn = dba.connect(self.Db)
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print("Errore apertura Db")
            return
        testo = testo.replace("'", ' ')
        qr = "insert into messaggi (data,ora,msg) values('"+data+"','"+ora+"','"+testo+"')"
        cur = conn.cursor()
        try:
            cur.execute(qr)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(f"errore insert: {qr}")
        cur.close()
        conn.close()

class Alice_ReadMail():
    
    IMAP_SERVER = 'in.alice.it'
    IMAP_PORT = 143
    EMAIL = None
    PASSWORD = None
    testo = None

    def loadCredenziali(self):
        # Carica le variabili d'ambiente dal file .env
        load_dotenv()
        # Recupera credenziali
        self.EMAIL = os.getenv("EMAIL_USER")
        self.PASSWORD = os.getenv("EMAIL_PASS")

    def decode_str(self,s):
        """Decodifica le intestazioni delle email"""
        if s:
            decoded, charset = decode_header(s)[0]
            if isinstance(decoded, bytes):
                return decoded.decode(charset if charset else "utf-8", errors="ignore")
            return decoded
        return ""
    
    def print_email_body(self, msg):
        """Estrae e restituisce il corpo dell'email (solo testo)"""
        body = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    if body:
                        decoded_body = body.decode(charset, errors="ignore")
                        print("\n--- Corpo del messaggio (solo testo) ---\n")
                        print(decoded_body)
                        return decoded_body
                else:
                    body = msg.get_payload(decode=True)
                    charset = msg.get_content_charset() or "utf-8"  
                    if body:
                        decoded_body = body.decode(charset, errors="ignore")
                        print("\n--- Corpo del messaggio (solo testo) ---\n")
                        print(decoded_body)
                        return decoded_body
    
        # Fallback su text/html se text/plain non è disponibile
        if not body and content_type == "text/html" and "attachment" not in content_disposition:
            body = part.get_payload(decode=True)
            charset = part.get_content_charset() or "utf-8"
            decoded_html = body.decode(charset, errors="ignore")
    	    # Rimuovi tag HTML o estrai solo il testo
            text_only = re.sub('<[^<]+?>', '', decoded_html)
            return text_only
    
        # Se non è stato trovato un body valido
        print("Nessun contenuto testuale trovato nell'email.")
        logger.warning("Email ricevuta senza contenuto 'text/plain'.")
        return None


    def read_mail_starttls(self):
        self.loadCredenziali()
        self.testo = None
        try:
            print(f"Connessione a {self.IMAP_SERVER}:{self.IMAP_PORT} (STARTTLS)...")
            mail = imaplib.IMAP4(self.IMAP_SERVER, self.IMAP_PORT)
            # Attiva connessione sicura STARTTLS
            mail.starttls(ssl.create_default_context())
            # Login
            mail.login(self.EMAIL, self.PASSWORD)
            mail.select("inbox")

            # Recupera tutte le email
            status, messages = mail.search(None, "ALL")
            if status != "OK":
                print("Errore durante la ricerca delle email.")
                return

            mail_ids = messages[0].split()
            total = len(mail_ids)
            if total == 0:
                print("Nessuna email trovata.")
                return

            # Mostra le ultime 5 email (o meno se ce ne sono di meno)
            last_5_ids = mail_ids[-5:]
            last_5_ids = list(enumerate(last_5_ids, 1))

            emails = []

            print("\nUltime email trovate:\n")
            for idx, i in last_5_ids:
                status, msg_data = mail.fetch(i, "(RFC822)")
                if status != "OK":
                    print(f"Errore nel recupero dell'email ID {i}")
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = self.decode_str(msg["Subject"])
                        from_ = self.decode_str(msg.get("From"))
                        print(f"{idx}) Da: {from_}")
                        #print(f"   Oggetto: {subject}")
                        if subject == '/^':
                            print(f"   Oggetto: {subject}")
                            logger.info(f"Email ricevuta da: {from_}")
                            emails.append((i, msg))  # Salva ID e messaggio per dopo

            if len(emails) < 1:
                pass    
            else:
                selected_id, selected_msg = emails[0]
                _,selected_msg = emails[0]
                self.testo = self.print_email_body(selected_msg)
                # Contrassegna per cancellazione
                mail.store(selected_id, '+FLAGS', '\\Deleted')
                mail.expunge()
                print("Email eliminata con successo.")
            mail.logout()
            print(f"Testo ricevuto: {self.testo}")
            return self.testo
        except Exception as e:
            print("Errore:", e)
            logger.error(f"Errore in read_mail: {e}")

aliceRead = Alice_ReadMail()
callDb = callDB()
scheduler = BlockingScheduler()

def job():
    testo = aliceRead.read_mail_starttls()
    if testo:
        if len(testo) > 188:
            testo = testo[0:188]
        testo = testo.replace('\n', ' ').rstrip()
        logger.info(f"Email ricevuta e salvata nel DB: {testo}")
        callDb.insertMsg('^' + testo)

basedir = os.path.abspath(os.path.dirname(__file__))
basedir = os.path.join(basedir, '../logs/alice_readmail.log')
print(f"Basedir: {basedir}")
log_file_path = basedir

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(
    log_file_path, maxBytes=1_048_576, backupCount=5, encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)
scheduler.add_job(job, 'interval', minutes=5)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('apscheduler').addHandler(handler)
print("Scheduler avviato. Job ogni 5 minuti.")
scheduler.start()

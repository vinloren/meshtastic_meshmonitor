import os,datetime
import sqlite3 as dba
from imap_tools import MailBox, A
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

basedir = os.path.abspath(os.path.dirname(__file__))
log_file_path = os.path.join(basedir, '../logs/gmail_readmail.log')
print(f"log_file_path: {log_file_path}")

handler = RotatingFileHandler(
    log_file_path, maxBytes=1_048_576, backupCount=5, encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
scheduler = BlockingScheduler()

class callDB(): 
    Db = '../app.db'

    def insertMsg(self,testo):
        data = datetime.datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.datetime.now().strftime("%T")    
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


class GmailRead():
    def Ricevi_mail(self):
        messaggi = []
        EMAIL = os.getenv("GMAIL_USER")
        PASSWORD = os.getenv("GMAIL_PASS")

        try:
            mailbox = MailBox('imap.gmail.com')
            mailbox.login(EMAIL,PASSWORD , 'INBOX')
        except:
            logger.error("Accesso a gmail rifiutato")
            print("Accesso a gmail rifiutato")
            return

        for msg in mailbox.fetch(A(seen=False)):
            #print(msg.date, msg.subject, len(msg.text or msg.html))
            #print(msg.text)
            dati ={}
            dati['Da']=msg.from_
            dati['Data']=msg.date
            dati['testo']=msg.text
            dati['Oggetto']=msg.subject
            if msg.subject == '/^':
                messaggi.append(dati)
        try:
            mailbox.logout()
            print("Logout OK")
        except:
            print("Errore su logout")
        return messaggi

    def getMail(self):
        messaggi = self.Ricevi_mail()
        if(messaggi is not None):
            for msg in messaggi:
                print(f"il {msg['Data']} Da: {msg['Da']} Oggetto: {msg['Oggetto']}")
                if msg['Oggetto'] == '/^':
                    testo = msg['testo']
                    print(testo)
                    if len(testo) > 188:
                        testo = testo[0:188]
                    testo = testo.replace('\n', ' ').rstrip()
                    logger.info(f"il {msg['Data']} Da: {msg['Da']} Oggetto: {msg['Oggetto']}")
                    logger.info(f"Salvato in DB: {testo}")
                    callDb.insertMsg('^' + testo)
                    break
        else:
            print("Nessun messaggio ricevuto")
    

gmailRead = GmailRead()
callDb = callDB()

def job():
    gmailRead.getMail()

scheduler.add_job(job, 'interval', minutes=5)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('apscheduler').addHandler(handler)
print("Scheduler avviato. Job ogni 5 minuti.")
gmailRead.getMail()
scheduler.start()


import os,datetime
import sqlite3 as dba
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from logging.handlers import RotatingFileHandler
import ReadGmail_api

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

callDb = callDB()

def job():
    testo = ReadGmail_api.Leggi()
    if testo:
        if len(testo) > 188:
            testo = testo[0:188]
        testo = testo.replace('\n', ' ').rstrip()
        logger.info(f"Email ricevuta e salvata nel DB: {testo}")
        callDb.insertMsg('^' + testo)

scheduler.add_job(job, 'interval', minutes=5)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
logging.getLogger('apscheduler').addHandler(handler)
print("Scheduler avviato. Job ogni 5 minuti.")
scheduler.start()


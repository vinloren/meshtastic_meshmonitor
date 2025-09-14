import string, sys, ast, io, time,datetime
import paho.mqtt.client as mqtt
from random import seed, random
import sqlite3 as dba
import argparse
import requests

#########################################################
# Subscribe a brocker.emqx.io per ricevere dati nodi    #
# collegati con topic uguale a questo che invianino i   #
# loro aggiornamenti che finiranno in tabella loranodes #
# del Db cui mesh_controller_py accede permettendo al   #
# Server Flask di avere una visuale anche su reti       #
# diverse da quella statutaria 'Lombardia e Ticino'.    #
#########################################################

class callDB(): 
    Db = '../app.db'

    def insertDB(self,dato):
        fields = ['data','ora','lat','lon','alt','longname','batt','snr','temperat','pressione','umidita','node_id']
        campi = []
        valori = []

        try:
            conn = dba.connect(self.Db)
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print("Errore apertura Db")
            return
        
        i = 0
        while i<len(fields):
            if dato[fields[i]] != 'None' and dato[fields[i]] != '':
                campi.append(fields[i])
                valori.append("'"+dato[fields[i]]+"'")
            i+=1
        cur  = conn.cursor()
        qr = "insert into loranodes ("
        
        primo = True
        for campo in campi:
            if primo:
                qr += campo
                primo = False
            else:
                qr += ","+campo
        qr += ") values("
        primo = True
        for val in valori:
            if primo:
                qr += val
                primo = False
            else:
                qr += ","+val
        qr += ")"
        #print(f"qr= {qr}")
        cur = conn.cursor()
        try:
            cur.execute(qr)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(f"errore insert loranodes: {qr}")
        cur.close()
        conn.close()


    def insupdtDB(self,dati):
        upfields = ['data','ora','lat','lon','alt','longname','batt','snr','temperat','pressione','umidita']
        inseriti   = 0
        aggiornati = 0

        try:
            conn = dba.connect(self.Db)
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print("Errore apertura Db")
            return

        cur  = conn.cursor()
        for dato in dati:
            # fai update in loranodes di record con node_id = dato['node_id]
            # se non presente inseriscilo. Se presente con data/ora superiore
            # a quella del record in arrivo salta aggiornamento
            qr = "select node_id,data,ora from loranodes where node_id = '"+dato['node_id']+"'"
            res = cur.execute(qr)
            record = res.fetchone()
            if not record:
                self.insertDB(dato)
                inseriti += 1
                continue
            # se record in arrivo ha data-ora < di quella presente i Db salta aggiornamento 
            #print(f"esistente: {record[1]} {record[2]} in arrivo: {dato['data']} {dato['ora']}")
            precedente = record[1]+" "+record[2]
            attuale = dato['data']+" "+dato['ora']
            if (precedente >= attuale ):
                continue

            qr = "update loranodes set "
            i = 0
            while (i<len(upfields)-1):
                if dato[upfields[i]] != 'None' and dato[upfields[i]] != '':
                    if i==0:
                        qr += upfields[i]+"='"+dato[upfields[i]]+"'"
                    else:
                        qr += ","+upfields[i]+"='"+dato[upfields[i]]+"'"
                else:
                    if i==0:
                        qr += upfields[i]+"=null"
                    else:
                        qr += ","+upfields[i]+"=null" 
                i+=1

            if dato[upfields[i]] != 'None' and dato[upfields[i]] != '':
                qr += ","+upfields[i]+"='"+dato[upfields[i]]+"' where node_id='"+dato['node_id']+"'"
            else:
                qr += ","+upfields[i]+"=null where node_id='"+dato['node_id']+"'"
            
            try:
                cur.execute(qr)
                conn.commit()
                aggiornati += 1
            except dba.Error as er:
                print('SQLite error: %s' % (' '.join(er.args)))
                print("Exception class is: ", er.__class__)
                print(f"errore update loranodes: {qr}")
                break            
        cur.close()
        conn.close()
        print(f"{str(inseriti)} record inseriti - {str(aggiornati)} record aggiornati")

MQTT_Broker = "broker.emqx.io"  
channel     = "meshtastic/vinloren"
subtopic    = channel

parser = argparse.ArgumentParser(description="MQTT subscriber for Lora nodes")
parser.add_argument('--channel', type=str, required=False, help='MQTT topic to subscribe to')
args = parser.parse_args()
if args.channel:
    channel = args.channel
subtopic = channel

count       = 0
nodilora    = []

print("MQTT_Broker = "+MQTT_Broker)
print("Channel id  = "+channel)

# seed random number generator
seed(7)
s = str(random())
cname = "Myclient-"+s[2:19]
print("Client ID:", cname)

calldb = callDB()

# === Callbacks ===
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc == 0:
        client.subscribe(subtopic, qos=1)
        print(f"Subscribed to {subtopic}")
    else:
        print("Connessione fallita")

def on_message(client, userdata, msg):
    global count, nodilora
    try:
        b = msg.payload
        dats = ast.literal_eval(b.decode("utf-8"))    
        ora = datetime.datetime.now().strftime('%T')
        count += 1
        nodilora.append(dats)
        print(f"ricevuti {str(count)} recs\r", end="")
 
        if count >= int(dats['nrec']):
            print(f"\nDati ricevuti at: {ora} in numero di {nodilora[0]['nrec']}")
            calldb.insupdtDB(nodilora)
            print(f"{str(count)} nodi esaminati")
            count = 0
            nodilora = []
    except Exception as e:
        print(f"Errore nel trattamento del messaggio: {e}")

# === Setup client ===
client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo", password='none')
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_Broker, 1883, 60)
client.loop_start()

# === Mantieni attivo ===
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrotto dall'utente")
    client.loop_stop()
    client.disconnect()

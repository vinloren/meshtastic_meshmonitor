import threading,sqlite3,datetime,sys,time
import paho.mqtt.client as mqtt
from random import seed
from random import random  

#=============================================================#
# mqtt_send_all.py risiede nella stessa directory che ospita  #
# meshcontroller.py e ha lo scopo di inviare a un server mqtt #
# i dati dei nodi registrati attivi in giornata in modo che   #
# chi fosse collegato in subscribe possa gestire questi dati  #
# un suo applicativo. Per ottenere ciò mqtt_send accede al DB #
# ogni 300 secs per leggere tutti i record resenti in tabella #
# meshnodes e inviarli al server mqtt sicché siano ricevuti   # 
# da chi ha sottoscritto il topic.                            #
#=============================================================#

# Database Manager Class
class DatabaseManager():
	
    def __init__(self):
        self.conn = sqlite3.connect(DB_Name)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()
        print("Sqlite DB connected..")
		
    def retrieve_db_record(self, sql_query, args=()):
        self.cur.execute(sql_query)
        #self.conn.commit()
        rows = self.cur.fetchall()
        return rows
    
    def __del__(self):
        try:
            if hasattr(self, 'cur'):
                self.cur.close()
            if hasattr(self, 'conn'):
                self.conn.close()
        except Exception as e:
            print(f"Errore durante la chiusura del DB: {e}")
#==========================================================

# SQLite DB Name
DB_Name =  "../app.db"
topic = "vinloren"

def checkLast(dbObj):
    oggi = datetime.datetime.now()
    oggi = oggi.strftime('%y/%m/%d')
    qr = "select data,ora,lat,lon,alt,longname,batt,snr,temperat,pressione,umidita,node_id from \
        meshnodes where longname is not null"
    #qr = "select * from meshnodes where data ='"+oggi+"' and longname is not null order by node_id"
    res = dbObj.retrieve_db_record(qr)
    fields = ['data','ora','lat','lon','alt','longname','batt','snr','temperat','pressione','umidita','node_id']
    messages = []
    r = 0
    for row in res:
        msg = {}
        i = 0
        for field in fields:
            msg[field] = str(row[i])
            i += 1   
        messages.append(msg)
        r+=1
    print("numero record:"+str(r))
    for msg in messages:
        msg.update({'nrec': r})
        publish_To_Topic(pubtopic,str(msg))
        
    ora = datetime.datetime.now().strftime('%T')
    print(f"{ora} record trasmessi: {str(r)} ===========================================================")
    return
    
MQTT_Broker = "broker.emqx.io"
pubtopic = "meshtastic/"+topic

# seed random number generator
seed(7)
s = str(random())
cname = "Myclient-"+s[2:19]
print(cname)
count = 1

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc != 0:
        print ("Unable to connect to MQTT Broker...")
        pass
    else:
        print ("Connected with MQTT Broker: " + str(MQTT_Broker))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


def on_publish(client, userdata, mid):
    print ("Message "+str(count)+" sent")
    pass
		
def on_disconnect(client, userdata, rc):
    print ("Disconnect status = "+str(rc))
    if rc !=0:
	    pass

def publish_To_Topic(pubtopic,message):
    client.publish(pubtopic,message)
    time.sleep(0.25)
    dataora = datetime.datetime.now().strftime("%d/%m/%y %T")
    print(f"{dataora} Published: {message} on Topic: {str(pubtopic)}")

client = mqtt.Client()
client.client_id = cname
client.username_pw_set(username="enzo",password='none')
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_Broker, 1883, 60)

def publish_to_MQTT():
    dbObj = DatabaseManager()
    tmr = threading.Timer(300.0, publish_to_MQTT)
    tmr.start()
    checkLast(dbObj)
    del dbObj

def connetti():
    global pubtopic
    pubtopic = "meshtastic/"+topic
    publish_to_MQTT()
    client.loop_start()


if __name__ == '__main__':
    if len(sys.argv) > 2:
        topic = sys.argv[1]
        MyName = sys.argv[2]
    elif len(sys.argv) > 1:
        topic = sys.argv[1]
        MyName = "Mesh_controller"
    else:
        topic = "vinloren"
    print(f"topic: {topic}")
    connetti()



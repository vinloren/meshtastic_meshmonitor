import meshtastic
import meshtastic.serial_interface
from threading import Thread
from threading import Event
from pubsub import pub
import time
import datetime
import sys,math
import queue
import sqlite3 as dba
import requests

class send_node():
    # Invia la richiesta POST
    def manda_nodo(self,datas):
        url = "https://vinmqtt.hopto.org/add_node"

        nodo = {}
        nodo['date']    = datas[0]
        nodo['ora']     = datas[1]
        nodo['lat']     = datas[2]
        nodo['lon']     = datas[3]
        nodo['alt']     = datas[4]
        nodo['nome']    = datas[5]
        nodo['node_id'] = datas[10]
        print(f"Nodo= {nodo}")
        response = requests.post(url, json=nodo,verify=False)
        # Controlla la risposta
        if response.status_code == 200:
            print("Richiesta inviata con successo!")
            print("Risposta del server:", response.json())  # Se la risposta è in formato JSON
        else:
            print(f"Errore nella richiesta: {response.status_code}")
            print("Dettagli errore:", response.text)
    
    def checkNodo(self,nodnum):
        print("Tento invio dati a server globale")
        datas = calldb.getCoord(nodnum)
        if(datas[5] is not None):
            try:
                self.manda_nodo(datas)
            except Exception as e:
                print("Errore in callFlask: ",e)
        else:
            print("Invio dati non fatto per assenza longname.")


class meshInterface(Thread):
    def __init__(self, port=None, data_queue=None, MyName=None):
        super().__init__()
        self.port = port
        self.MyName = MyName
        self.interface = None
        self.data_queue = data_queue
        self.stop_event = Event()  # ➕ Flag per fermare il thread

    def setInterface(self):
        try:
            self.interface = meshtastic.serial_interface.SerialInterface(self.port)
            pub.subscribe(self.onReceive, "meshtastic.receive")
            print("Set interface..")
            return True
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Time out in attesa meshtastic.SerialInterface")
            return False

    def sendImmediate(self,msg):
        currTime = datetime.datetime.now().strftime("%H:%M:%S")
        msg = currTime+" "+ msg
        self.interface.sendText(msg)
        print("Messaggio mandato su CH0: " + msg)

    def run(self):
        print("meshInterface started..")
        if not self.setInterface():
            return

        # ➕ Verifica il flag di stop
        while not self.stop_event.is_set():
            time.sleep(0.1)

        print("meshInterface stopping...")

    def stop(self):
        self.stop_event.set()  # ➕ Metodo per richiedere lo stop del thread

    def onReceive(self, packet, interface):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"{ts} Packet ricevuto")
        if self.data_queue:
            self.data_queue.put(packet)

class callDB(): 
    Db = '../app.db'

    def insertTracking(self,dati):
        data = datetime.datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.datetime.now().strftime("%T")
        try:
            conn = dba.connect(self.Db)
            #print("callDB conn.dba..")
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print("Errore ininsertTrackeing")
            return
        
        query = "insert into tracking (data,ora,node_id,lat,lon,alt,batt,temperat,pressione,umidita,longname) values('"
        query += data+"','"+ora+"','"+dati['node_id']+"','"+str(dati['lat'])+"','"+str(dati['lon'])+"','"
        query += str(dati['alt'])+"','"+str(dati['batt'])+"','"+str(dati['temperat'])+"','"+str(dati['pressione'])+"','"
        query += str(dati['umidita'])+"','"+dati['longname']+"')"
        #print(query)
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(f"errore insert: {query}")
        cur.close()
        conn.close()

    # ottieni coordinate gps di nodenum richiesto
    def getCoord(self,nodenum):
        qr = "select data,ora,lat,lon,alt,longname,batt,temperat,pressione,umidita,node_id from meshnodes where nodenum = "+str(nodenum)
        conn = dba.connect(self.Db)
        cur  = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchone()
        #print(f"Attributi Nodo: {datas}")
        cur.close()
        conn.close()
        return datas

    def execInsUpdtDB(self,dict):
        #print("Inizio InsUpdt")
        print(dict)
        self.timstart = time.perf_counter_ns()
        chiave = dict['chiave']
        del dict['chiave']
        qr = "select count(*) from meshnodes where nodenum = "+str(chiave)
        data = datetime.datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.datetime.now().strftime("%T") 
        conn = dba.connect(self.Db)
        cur  = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchall()
        nr = datas[0][0]
        cur.close()
        conn.close()
        #print("Update o Insert?")
        campi = list(dict.keys())
        if(nr > 0):
            qr = "update meshnodes set data='"+data+"',ora='"+ora+"'"
            i = 0
            while(i < len(campi)):
                qr += ","+campi[i]+"='"+str(dict.get(campi[i]))+"'"
                i += 1           
            qr += " where nodenum="+str(chiave)
            #print(qr)
            self.insertDB(qr)
        else:
            qr = "insert into meshnodes (nodenum,data,ora,"
            i = 0
            while(i < len(campi)-1):
                qr += campi[i]+","
                i += 1
            qr += campi[i]+") values("+str(chiave)+",'"+data+"','"+ora+"','"
            i=0
            while(i < len(campi)-1):
                qr += str(dict.get(campi[i]))+"','"
                i += 1
            qr += str(dict.get(campi[i]))+"')"
            #print(qr)
            self.insertDB(qr)
        self.timtot = time.perf_counter_ns() - self.timstart
        print(f"InsUpdtDB eseguita in {self.timtot // 1000000}ms.")

    def insertDB(self,query):
        #print("callDB: Insert/Update")
        #print(query)
        try:
            conn = dba.connect(self.Db)
            #print("callDB conn.dba..")
        except:
            print("conn time-out in InsUpdtDB")
            return
        cur = conn.cursor()
        try:
            cur.execute(query)
            conn.commit()
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print(query)
        cur.close()
        conn.close()


# MAIN
if __name__ == "__main__":
    if len(sys.argv) > 2:
        port = sys.argv[1]
        MyName = sys.argv[2]
        print(f"Mio nome: {MyName} port: {port}")
    elif len(sys.argv) > 1:
        port = sys.argv[1]
        MyName = "Mesh_controller"
    else:
        port = None
        print("⚠️ Nessuna porta specificata. Uso default (None).")

    # Coda thread-safe per ricevere dati
    data_queue = queue.Queue()

    # Avvio thread
    lancio = meshInterface(port=port, data_queue=data_queue, MyName=MyName)
    lancio.start()

    calldb = callDB()
    sendNode = send_node()

    print("🟢 Inizio elaborazione principale")

    #trova distanza fra due punti gps
    def haversine(coord1,coord2):
        R = 6372800  # Earth radius in meters
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        phi1, phi2 = math.radians(lat1), math.radians(lat2) 
        dphi       = math.radians(lat2 - lat1)
        dlambda    = math.radians(lon2 - lon1)
        
        a = math.sin(dphi/2)**2 + \
            math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))
    

    def onPacketRcv(packet):
        #print(packet)
        dataora = datetime.datetime.now().strftime("%d/%m/%y %T")
        from_ = packet['from']
        # trasforma nodenum da decimale a esadecimale = fromid
        node_id = ['!','\0','\0','\0','\0','\0','\0','\0','\0']
        trd = ['0','1','2','3','4','5','6','7','8','9','a','b','c','d','e','f']
        j = 8
        x = int(from_)
        while(j>0):
            y = x%16
            node_id[j] = trd[y]
            j -= 1
            x = int(x/16)
        node_id = "".join(node_id)
        print(f"➡️node_id: {node_id}")
        to_ = packet['to']
        if (isinstance(packet['fromId'],str)):
            dachi = packet['fromId']
        else:
            dachi = 'None'
        if (isinstance(packet['toId'],str)):
            achi = packet['toId']
        else:
            achi = 'None'
        if ('decoded' in packet):
            tipmsg = str(packet['decoded']['portnum'])
            #print(tipmsg)
            if (packet['decoded']['portnum'] == 'NODEINFO_APP'):
                tipmsg = 'NODEINFO_APP'
                print(tipmsg)
                pdict = {}
                nome = packet['decoded']['user']['longName'].replace("'",' ')
                pdict.update({'longname': nome})
                pdict.update({'chiave': from_})
                pdict.update({'node_id': node_id})
                calldb.execInsUpdtDB(pdict)
            elif (packet['decoded']['portnum'] == 'POSITION_APP'):
                tipmsg = 'POSITION_APP'
                print(tipmsg)
                if('longitude' in packet['decoded']['position']):
                    coord1 = None
                    try:  
                        result = calldb.getCoord(from_)
                        coord1 = [float(result[2]),float(result[3])] # indici lat lon in result
                    except:
                        print("Assenza coordinate gps precedenti")
                    if('longitude' in  packet['decoded']['position'] and 'latitude' in  packet['decoded']['position']):
                        if(coord1):
                            coord2 = [packet['decoded']['position']['latitude'],packet['decoded']['position']['longitude']]
                            distance = haversine(coord1,coord2)
                            print(f"Distanza dalla pecedente posizione: {distance}")
                            # se la distanza fra i due punti è > 10 mt inserisci in tracking
                            if abs(distance) > 75.0:
                                print("Inserisco record di tracking")
                                # inserisci nuovo record in tracking
                                pdict = {}
                                pdict.update({'lon': packet['decoded']['position']['longitude']})
                                pdict.update({'lat': packet['decoded']['position']['latitude']})
                                if('altitude' in packet['decoded']['position']):
                                    pdict.update({'alt': packet['decoded']['position']['altitude']})
                                else:
                                    pdict.update({'alt': '0'})
                                    #data,ora,lat,lon,alt,longname,batt,temperat,pressione,umidita,node_id 
                                pdict.update({'longname': result[5]}) 
                                pdict.update({'batt': result[6]})
                                pdict.update({'temperat': result[7]})
                                pdict.update({'pressione': result[8]})
                                pdict.update({'umidita': result[9]})
                                pdict.update({'node_id': result[10]})
                                if(pdict['longname'] is not None):
                                    calldb.insertTracking(pdict)
                                #inserito tracking aggiorna meshnodes con nuova posizione
                                pdict = {}
                                pdict.update({'lon': packet['decoded']['position']['longitude']})
                                pdict.update({'lat': packet['decoded']['position']['latitude']})
                                #pdict.update({'lon': coord2[1]})
                                if('altitude' in packet['decoded']['position']):
                                    pdict.update({'alt': packet['decoded']['position']['altitude']})
                                    pdict.update({'chiave': from_})
                                    pdict.update({'node_id': node_id})
                                    #calldb.execInsUpdtDB(pdict)
                                else:
                                    pdict.update({'alt': 0})
                                    pdict.update({'chiave': from_})
                                    pdict.update({'node_id': node_id})
                                    #calldb.execInsUpdtDB(pdict)
                                calldb.execInsUpdtDB(pdict)
                            else:
                                # aggiorna solo data ora
                                pdict = {}
                                pdict.update({'chiave': from_})
                                pdict.update({'node_id': node_id})
                                calldb.execInsUpdtDB(pdict)
                        else:
                            # assenza di coordinate precedenti, inserisci quelle attuali
                            pdict ={}
                            pdict.update({'chiave': from_})
                            pdict.update({'node_id': node_id})
                            pdict.update({'lon': packet['decoded']['position']['longitude']})
                            pdict.update({'lat': packet['decoded']['position']['latitude']})
                            if('altitude' in packet['decoded']['position']):
                                pdict.update({'alt': packet['decoded']['position']['altitude']})
                            else:
                                pdict.update({'alt': 0})
                            calldb.execInsUpdtDB(pdict)
                        #vai a leggere record di from_ in meshnodes e se longname,node_id,lat,lon,alt, presenti
                        #invia dati a server vinmqtt.hopto.org
                        sendNode.checkNodo(from_)


                if('rxSnr' in packet):
                    #updateSnr(from_,str(packet['rxSnr']))
                    pdict = {}
                    pdict.update({'snr': packet['rxSnr']})
                    pdict.update({'chiave': from_})
                    pdict.update({'node_id': node_id})
                    calldb.execInsUpdtDB(pdict)
                
            elif (packet['decoded']['portnum'] == 'TELEMETRY_APP'):
                    tipmsg = 'TELEMETRY_APP'
                    print(tipmsg)
                    if('deviceMetrics' in packet['decoded']['telemetry']):
                        battlvl = ' '
                        chanutil = 0
                        airutil = 0
                        pdict ={}
                        if('batteryLevel' in packet['decoded']['telemetry']['deviceMetrics']):
                            battlvl = packet['decoded']['telemetry']['deviceMetrics']['batteryLevel']
                            pdict.update({'batt': battlvl})
                            pdict.update({'chiave': from_})
                            pdict.update({'node_id': node_id})
                            calldb.execInsUpdtDB(pdict)
                        else: 
                            try:
                                #updateTelemetry(packet['from'],battlvl,chanutil,airutil) 
                                pdict.update({'batt': battlvl})
                                #pdict.update({'chanutil': chanutil})
                                #pdict.update({'airutiltx': airutil})
                                pdict.update({'chiave': from_})
                                pdict.update({'node_id': node_id})
                                calldb.execInsUpdtDB(pdict)
                            except:
                                print("Update saltata per campi nulli in Telemetry")
                            
                    if('environmentMetrics' in packet['decoded']['telemetry']):
                        temperatura = 0
                        pressione = 0
                        humidity = 0
                        voltage = 0
                        current = 0
                        if('temperature' in packet['decoded']['telemetry']['environmentMetrics']):
                            temperatura = packet['decoded']['telemetry']['environmentMetrics']['temperature']
                        if('barometricPressure' in packet['decoded']['telemetry']['environmentMetrics']):
                            pressione = packet['decoded']['telemetry']['environmentMetrics']['barometricPressure']
                        if('relativeHumidity' in packet['decoded']['telemetry']['environmentMetrics']):
                            humidity = packet['decoded']['telemetry']['environmentMetrics']['relativeHumidity']  
                        if('voltage' in packet['decoded']['telemetry']['environmentMetrics']):
                            voltage = packet['decoded']['telemetry']['environmentMetrics']['voltage']  
                        if('current' in packet['decoded']['telemetry']['environmentMetrics']):
                            current =packet['decoded']['telemetry']['environmentMetrics']['current'] 
                        try:
                            #updateSensors(packet['from'],temperatura,pressione,humidity,voltage,current)
                            pdict ={}
                            pdict.update({'pressione': pressione})
                            pdict.update({'temperat': temperatura})
                            pdict.update({'umidita': humidity})
                            pdict.update({'chiave': from_})
                            pdict.update({'node_id': node_id})
                            calldb.execInsUpdtDB(pdict)
                        except:
                            testo = datetime.datetime.now().strftime("%d/%m/%y %T")+" Dati sporchi in packet[decoded]telemetry]"
                            print(testo)

            elif (packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP'):
                tipmsg = 'TEXT_MESSAGE_APP'
                #data,ora,lat,lon,alt,longname,batt,temperat,pressione,umidita,node_id
                datas = calldb.getCoord(from_)
                if not datas:
                    return
                if datas[5]:
                    msgda = datas[5]
                    snr = packet['rxSnr']
                    rssi = packet['rxRssi']
                    try:
                        testo = datetime.datetime.now().strftime("%d/%m/%y %T") + \
                            " "+packet['decoded']['text']+"snr:"+str(snr)+",rssi:"+str(rssi)+" de "+msgda
                        #self.ricevuti.append(testo) 
                        if('QSL?' in testo.upper()):
                            print(lancio.MyName)
                            rmsg = "RX qsl da "+lancio.MyName+" a: "
                            rmsg = rmsg + packet['decoded']['text']+"snr:"+str(snr)+",rssi:"+str(rssi)+" da "+msgda
                            rmsg = rmsg.replace('?',' ')  #replace ? with ' ' to avoid mesh flooding if 2+ broadcast_msg_pyq5 running in mesh
                            lancio.sendImmediate(rmsg)
                    except:
                        testo = datetime.datetime.now().strftime("%d/%m/%y %T")+" "+msgda+" Dati sporchi in packet[decoded][text]"
                        print(testo)

    try:
        while True:
            try:
                # Attende al massimo 1 secondo un nuovo pacchetto
                data = data_queue.get(timeout=1)
                print(f"➡️ Dati ricevuti") #: {data}
                # Qui puoi elaborare il pacchetto
                onPacketRcv(data)
            except queue.Empty:
                pass  # Nessun dato ricevuto in questo intervallo
    except KeyboardInterrupt:
        print("\n🛑 Arresto richiesto.")
        lancio.stop()      # ➕ Ferma il thread
        lancio.join()      # ➕ Attende la sua chiusura
        print("✅ Thread terminato correttamente.")
        

    

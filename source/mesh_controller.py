import meshtastic
import meshtastic.serial_interface
from threading import Thread
from pubsub import pub
import time
import datetime
import sys,math
import queue
import sqlite3 as dba

class meshInterface(Thread):
    def __init__(self, port=None, data_queue=None):
        super().__init__()
        self.port = port
        self.interface = None
        self.data_queue = data_queue  # Coda per inviare dati al thread principale

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

    def run(self):
        print("meshInterface started..")
        if not self.setInterface():
            return

        # il thread si mette in ascolto passivamente
        while True:
            time.sleep(0.1)  # evita CPU al 100%, ma il lavoro ora avviene su onReceive()

    def onReceive(self, packet, interface):
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"{ts} Packet ricevuto")
        if self.data_queue:
            self.data_queue.put(packet)

class callDB(): 

    def insertTracking(self,dati):
        data = datetime.datetime.now().strftime("%y/%m/%d") 
        ora  = datetime.datetime.now().strftime("%T")
        try:
            conn = dba.connect('app.db')
            #print("callDB conn.dba..")
        except dba.Error as er:
            print('SQLite error: %s' % (' '.join(er.args)))
            print("Exception class is: ", er.__class__)
            print("Errore ininsertTrackeing")
            return
        
        query = "insert into tracking (data,ora,node_id,lat,lon,alt,batt,temperat,pressione,umidita) values('"
        query += data+"','"+ora+"','"+dati['node_id']+"','"+str(dati['lat'])+"','"+str(dati['lon'])+"','"
        query += str(dati['alt'])+','+str(dati['batt'])+"','"+str(dati['temperat'])+"','"+str(dati['pressione'])+"','"
        query += str(dati['umidita'])+"')"
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
        qr = "select lat,lon,longname,batt,temperat,pressione,umidita,node_id from meshnodes where nodenum = "+str(nodenum)
        conn = dba.connect('app.db')
        cur  = conn.cursor()
        rows = cur.execute(qr)
        datas = rows.fetchall()
        print(f"coords={datas}")
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
        conn = dba.connect('app.db')
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
            conn = dba.connect('app.db')
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
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = None
        print("⚠️ Nessuna porta specificata. Uso default (None).")

    # Coda thread-safe per ricevere dati
    data_queue = queue.Queue()

    # Avvio thread
    lancio = meshInterface(port=port, data_queue=data_queue)
    lancio.start()

    calldb = callDB()

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
                        coord1 = [float(result[0][0]),float(result[0][1])]
                    except:
                        print("Assenza coordinate gps precedenti")
                    if('longitude' in  packet['decoded']['position'] and 'latitude' in  packet['decoded']['position']):
                        if(coord1):
                            coord2 = [packet['decoded']['position']['latitude'],packet['decoded']['position']['longitude']]
                            distance = haversine(coord1,coord2)
                            print(f"Distanza dalla pecedente posizione: {distance}")
                            # se la distanza fra i due punti è > 10 mt inserisci in tracking
                            if abs(distance) > 10.0:
                                print("Inserisco record di tracking")
                                # inserisci nuovo record in tracking
                                pdict = {}
                                pdict.update({'lon': packet['decoded']['position']['longitude']})
                                pdict.update({'lat': packet['decoded']['position']['latitude']})
                                if('altitude' in packet['decoded']['position']):
                                    pdict.update({'alt': packet['decoded']['position']['altitude']})
                                else:
                                    pdict.update({'alt': '0'})
                                pdict.update({'longname': result[0][2]}) 
                                pdict.update({'batt': result[0][3]})
                                pdict.update({'temperat': result[0][4]})
                                pdict.update({'pressione': result[0][5]})
                                pdict.update({'umidita': result[0][6]})
                                pdict.update({'node_id': result[0][7]})
                                callDB.insertTracking(pdict)
                        # aggiorna Db
                        pdict = {}
                        pdict.update({'lon': packet['decoded']['position']['longitude']})
                        pdict.update({'lat': packet['decoded']['position']['latitude']})
                        #pdict.update({'lon': coord2[1]})
                        if('altitude' in packet['decoded']['position']):
                            pdict.update({'alt': packet['decoded']['position']['altitude']})
                            pdict.update({'chiave': from_})
                            pdict.update({'node_id': node_id})
                            calldb.execInsUpdtDB(pdict)
                        else:
                            #updateUser(from_,coord2,'0',distance,rilev)
                            pdict.update({'alt': 0})
                            pdict.update({'chiave': from_})
                            pdict.update({'node_id': node_id})
                            calldb.execInsUpdtDB(pdict)

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
                        #if('channelUtilization' in packet['decoded']['telemetry']['deviceMetrics']):
                        #    chanutil  = packet['decoded']['telemetry']['deviceMetrics']['channelUtilization']
                        #if('airUtilTx' in packet['decoded']['telemetry']['deviceMetrics']):
                        #    airutil   = packet['decoded']['telemetry']['deviceMetrics']['airUtilTx'] 
                        #if(packet['from'] == mynodeId):
                        #    ora = "Ore "+datetime.datetime.now().strftime("%T")
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

    
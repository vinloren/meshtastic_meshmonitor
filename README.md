# Meshtastic_meshmonitor

E' il nome del progetto orientato al controllo dalla rete meshtastic cui siamo affiliati.
Il progetto fa affidamento sulla applicazione python di seguiguito descritta.

## Requisiti python

Occorre avere installato python 3.11.x o superiore. Pur non essendo indispensabile lavorare in ambiente virtuale python, è bene farlo per circoscrivere l'installazione in un ambiente che non sarà modificato in seguito da aggiornamenti che potrebbero disturbare il funzionamento dell'applicazione.

### Creazione ambiente virtuale

Posizionati sulla directory base del progetto battere python -m ven venv per creare l'ambiente virtuale che andremo poi ad attivare. Al termine dell'operazione se su Windows battere venv/Scripts/activate mentre su Linux battere source/bin/activate. In entrambi i casi apparirà (venv) in verde a sinistra del prompt.

A questo punto tutti i comandi di gestione python saranno sotto controllo dell'installazione virtuale separata dall'installazione globale. Ora si tratta di installare i moduli python necessari all'applicazione che nel nostro caso consistono nell'installatione delle librerie python meshtastic da eseguire col comando pip install meshtastic.

Ora tutto è pronto per l'esecuzione dell'applicazione in ambiente virtuale. Fare attenzione ogni volta che si riaccende il computer per eseguire questa applicazione di eseguire venv/Scripts/activate o in Linux source/bin/activate per entrare in ambiente virtuale.

## mesh_controller.py

L’obiettivo da raggiungere è quello di poter porre in mappa OpenStreet map la posizione dei nodi che vediamo dal nodo centrale della nostra rete, e volendo, rendere questa accessibile al mondo esterno. Occorre così per prima cosa che, grazie all'interfaccia API meshtastic, mesh_controller.py veda via collegamento seriale un' unita Tlora che riceve i messaggi di protocollo in rete meshtastic via radio, sia in grado di elaborare questi messaggi salvandone i risultati su un DB Sqlite3.

Questo stesso DB, messo in comune con altra applicazione Python Flask, sarà la base da cui il Server Flask (che vedremo in seguito come capitolo a parte) farà riferimento in sola lettura per pubblicare i dati su una mappa OpenStreet.

## Descrizione funzionalità

Fra tutti i mesaggi di protocollo ricevuti dal nodo di controllo collegato in seriele vengono elaborati:

1. NODEINFO
2. POSITION
3. TELEMETRY

Che insieme a DATA e ORA vanno a riempire / aggiornare la tabella "meshnodes" nel Db app.db residente nella stessa directoty che ospita l'applicazione.

I record sono registrati in tabella avendo come chuave primaria non duplicabile 'nodenum' che è l'identificatico del nodo sorgente del messaggio in arrivo. Da 'nodenum', che è l'esprssione in numero intero del MAC del nodo, si ricava 'node_id' senza cercarlo nel corpo del messaggio (anche perché spesso assente) semplicemente traducendolo in espressione esadecimale per poi apporvi in testa un punto esclamativo.

L'aggiornamento della tabella "meshnodes" ha luogo pr ciascun singolo messaggio di tipo 1. 2. o 3. Infine in tabella avremo le caratteristiche di ciascun nodo visto in rete con data e ora dell'ulima comparsa. Più in dettaglio abbiamo:

 CREATE TABLE "meshnodes" (
 "data" TEXT,
 "ora" TEXT,
 "nodenum" INTEGER UNIQUE PRIMARY KEY,
 "node_id"   TEXT,
 "longname" TEXT,
 "alt" INTEGER,
 "lat" REAL,
 "lon" REAL,
 "batt" INTEGER,
 "snr" REAL,
 "pressione" REAL,
 "temperat" REAL,
 "umidita" REAL
 )

    Elementi questi sufficienti e necessari a qualificare il nodo in tutti li aspetti che lo caratterizzano, rappresentabili poi su una mappa geografica tramite ulteriore risorsa che va ad accedere al Db app.db in lettura. Verosimilmente quasta risorsa sarà costituita da un Server accessibile da internet, come nel caso del Python Flask Server che andrò a costruire sullo stile semplificato del già attivo vinmqtt.hopto.org (non fatevi ingannare dal nome, non sitratta di mqtt ma di https, il nome è rimasto quello che anni or sono identivicava davvero mqtt).

    In mappa (OpenStreetMap) avremo quindi la posizione dei nodi in tempo reale così come sono posizionati, fissi o mobili che siano, in stile foto istantanea. Se vogliamo anche identificare i percorsi seguiti nel tempo da nodi mobili dobbiamo allora fare affidamento a una tabella aggiuntiva (che chiamiamo 'tracking') e ad un'elaborazione ulteriore in mesh_controller.py

### Il tracking dei nodi

Ad ogni messaggio di POSITION ricevuto da un 'nodenum'/'node_id', se in 'meshnodes' è già presente sotto chiave 'nodenum' una registrazione gps, viene misurata la distanza in metri fra la precedente posizione e quella attuale da registrare. Se la distanza è inferiora a 75mt la nuova posizione non viene registrata ma solo aggiornato 'data' e 'ora' del messaggio. Se il record non conteneva coordinate gps il record in 'meshnodes' viene aggiornato con quelle ricevute con data e ora. Se la distanza rilevata è > 75mt viene interessata la tabella 'tracking' prima di aggiornare 'meshnodes'. La tabella tracking è così costituita:

CREATE TABLE "tracking" (
 "node_id" TEXT,
 "longname" TEXT,
 "data" TEXT,
 "ora" TEXT,
 "lon" REAL,
 "lat" REAL,
 "alt" INTEGER,
 "batt" INTEGER,
 "temperat" REAL,
 "pressione" REAL,
 "umidita" REAL,
 "_id" INTEGER UNIQUE PRIMARY KEY
)

Sulla risorsa Server ci sarà un accesso riservato all'elaborazione dei dati tracking per la rappresentazione dei percorsi evvettuati nel tempo dai nodi mobili. Avremo allora due situazioni rappresedue: una di tipo foto istantanea dove non gioca selezione di data e che riguarda la mappa in tempo reale, l'altra di tipo storico selezionabile per data che riguarda i nodi in movimeto tracciati in tabella 'tracking'.

## Come lanciare applicazione

Avendo collegato un Tlora alla seriale USB ci posizioniamo, da finestra Windows Power Shell su Win10/11 o da finestra terminal in Linux, sulla directory che contiene applicazione python e Db app.db

Occore sapere su quale porta seriale  è connessa la nostra Tlora e per fare questo abbiamo due strade:

1. Su Windows battere tasto WinLogo + x poi all'apparizione della lista menu battere lettera g (gestione dispositivi) per poi cliccare su 'Porte (COM e LPT' per veder la COMn dove n è il numero che definisce la COM dove si trova il driver CH340 del Tlora).
2. Su Linux da finestra di terminale battere sudo dmesg | grep tty per avere la lista delle porte USB cui è connesso un device in seriale. ttyUSBx o ttyACMx sono risposte tipiche

una volta trovata la seriale connessa lanciare python mesh_controller.py /dev/ttyUSBx o /dev/ttyACMx se in Linux ovvero python mesh_controller.py COMx se in Windows.

## Stato dello sviluppo del progetto

Alla data di oggi 16 Agosto 2025 mesh_controller.py è funzionante e pronto ad essere utilizzato in campo. Già ora semplicemente utilizzando indifferentemente su Win10/11 o su Linux DBbrowser for Sqlite (scaricabile gratuitamente per Windows e installabile via apt-get install su Linux) si può avere contezza di come gira il fumo rinfrescano la visione delle tabelle su menzionate attraverso di esso.

Riferimenti al Server Flask che sto allestendo riguardo al progetto Meshtastic_meshmonitor qui accennato li darò via via che lo sviluppo procede.

## Struttura del Server

Ipotizzo un server Flask semplificato con le seguenti caratteristiche di base:

1. Accesso aperto senza necessità di affiliazione
2. Semplice HTTP, no HTTPS / SSL
3. Scelta fra mappa in tempo reale e traking per data e nodo in lista
4. Nginx non necessario, basta Gunicorn

## Installazione moduli python a supporto

Avendo attivato ambiente virtuale:

1. pip install flask
2. pip install python-dotenv nota: se si ha errore di interpretazione file al lancio di flask run usare notepad++ per leggere .flaslenv e riscriverlo in formato utf-8 (default è utf-16 non supportato da python)
3. pip install flask_sqlalchemy
4. pip install flask_migrate
5. A questo punto ocorre fissare le caratteristiche delle tabelle del Db nel contesto Flask ovvero Flask migrate che per il Db presente in questo repositpry è già stato effettuato. Andrà ripetuto qualora si aggiungessere tabelle o si modificasse una presente. Il processo di Flask migrate si attua eseguendo in sequenza flask db init, flask db update, flask db upgrade.
6. pip install folium a supporto del display delle mappe

### Esecuzione

Occorre aprire due terminali, uno per meh_controller.py, l'atro per il server.

1. si entra da un terminale nella directory base del progetto e si esegue venv/Scripts/activate se in windows, source/bin/activate se il Linux
2. si va su ./source e da lì si lancia python mesh_controller.py COMx (Windows) o /dev/ttyUSBx o ACMx se in Linux. Ora dobbiamo far partire il server..
3. si apre un secondo terminale e dalla directory base del progetto si fa di nuovo venv/Script/activate o source/bin/activate se in Linux
4. eseguire 'flask run' (senza apici) per far partire il server
5. Si apra un browser e si batta lo url 'localhost:5000/showmap' (senza apici) per vedere la mappa attuale in real time

Allo stato attuale di sviluppo è attiva solo showmap della rete Brianza Bergamasca e Pavese a livello foto istantanea da aggiornare con reload della pagina di tanto in tanto. Funzioni più elaborate e selezioni specifiche saranno aggiunte via via.

Se dovessero essere inseriti nuovi nodi di iscritti alla rete questi vanno aggiunti in tabella Modes usando DBBrowser for Sqlite strumento indispensabile sia su Windows che su Linux. Leggendo la tabella è intuitivo capire come i nuovi record vanno aggiunti, il colore dei marker è determinato dal campo 'mode' e per ragioni storiche che non sto qui a spiegare per avere il blu mode = MEDIUM_FAST, per il verde LONG_FAST e freq = 433, per il rosso freq = 868 e mode = LONG_SLOW. anche se sappiamo che anche qui lavoriamo in MEDIUM_FAST. Ci sono ragioni storiche come accennato prima e lascio tutto così anche se in apparenza questi dati sembrano fuorvianti.

### Note

Allo atato attuale sia mesh_controller.py che il server (limitatamente a /showmap senza selezioni) funzionano. Per vedere la mappa basta aprireun browser su localhost:5000/showmap e rinfrescare la pagina ogni tanto per vedere gli aggirnamenti. Se si mette il server in connessione con un dynamic DNS vi si potrà accedere dal mondo esterno via internet. 

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

Il 24 Agosto, in fase di rifinitura e test dell'insieme Meshtastic_meshmonitor è emersa l'opportunità di integrare il server già attivo at https://vinmqtt.hopto.org fruendo oltre che di broadcast_msg_pyqt5.py anche del nuovo mesh_controller.py permettendo così al suddetto server di fornire informazioni anche sulla parte 433Mhz di chi avesse questi nodi e avesse messo in uso l'approccio attuale anziché broadcast_msg_pyqt5.py. L'aggiornamento del 24 Agosto prevede così questa innovazione.

A riga 337 di mesh_controller.py c'è la chiamata all'invio dati verso https://vinmqtt.hopto.org. Chi non volesse contribuire ad allargare la visuale sulla nostra rete "Lombardia e Canton Ticino" può commentare la riga tranquillamente. Chi non commenta la riga e non ha aperto accesso a internet non avrà comunque nessun danno, tutto funziona ugualmente, solo messaggi nel log diranno che il collegamento non può aver luogo.

## Descrizione funzionalità

Fra tutti i mesaggi di protocollo ricevuti dal nodo di controllo collegato in seriele vengono elaborati:

1. NODEINFO
2. POSITION
3. TELEMETRY
4. TEXT_APP

Che insieme a DATA e ORA, a parte TEXT_APP, vanno a riempire / aggiornare la tabella "meshnodes" nel Db app.db residente nella stessa directoty che ospita l'applicazione.

I record sono registrati in tabella avendo come chiave primaria non duplicabile 'nodenum' che è l'identificatico del nodo sorgente del messaggio in arrivo. Da 'nodenum', che è l'esprssione in numero intero del MAC del nodo, si ricava 'node_id' senza cercarlo nel corpo del messaggio (anche perché spesso assente) semplicemente traducendolo in espressione esadecimale per poi apporvi in testa un punto esclamativo.

L'aggiornamento della tabella "meshnodes" ha luogo per ciascun singolo messaggio di tipo 1. 2. o 3. Infine in tabella avremo le caratteristiche di ciascun nodo visto in rete con data e ora dell'ulima comparsa. Più in dettaglio abbiamo:

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

### Risposta automatica a qsl?

I messaggi testuali ricevuti sotto TEXT_APP vengono controllati nel contenuto e se questo
contiene qsl? o QSL? o qsl? scritto in qualunque forma allora mesh_controller.py provvede a inviare una risposta automatica sul canale 0. In questo modo si aiuta che fa prove di accesso che vede il suo messaggio passare senza chiedere aiuto a nessuno.

### Registrazione messaggi intercosi su ch0

Il Db contiene la tabella 'messaggi' che raccoglie i messaggi intercorsi su ch0 nel corso della
giornata. Il caricamento dei messaggi intabella avviene da parte di mesh_controller ad ogni
messaggio testuale ricevuto. Il server poi da parte sua è in grado di accedere a questa tabella
su richiesta mostrandone il contenuto a video (orario e testo ricevuto). I dati mantenuti in questa tabella riguardano solo il giorno attuale venendo cancellati i dati eventuali di giorni precedenti.

### Invio messaggi su ch0

A questo provvedono il server e mesh_controller insieme. Attraverso il server si invia un messaggio alla tabella 'messaggi' del Db dove al messaggio viene preposto il carattere ^ per
identificare messaggio che deve essere inviato su cah0. A questo provvede mesh_controller ad ogni ciclo di ricezione di un qualunque messaggio di protocollo ricevuto andando a controllare se l'ultimo messaggio ricevuto contiene ^ nel qual caso esso viene inviato in rete. 

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

Alla data di oggi 29 Agosto 2025 abbiamo:

1. mesh_controller.py integrato con invio dati a server globale https://vinmqtt.hopto.org 
ad ogni messaggio di POSITION ricevuto.
2. mesh_controller.py ora gestisce anche TEXT_MESSAGE_APP nel senso che acqusisce i messaggi di testo ricevuti su ch0 salvandoli in tabella messaggi del Db per poter essere visualizzati su richiesta dal server flask di questo progetto.
3. mesh_controller.py ora provvede a dare risposta automatica di ricezione ai messaggi testuali che contengono al loro interno la richiesta di qsl?
4. il server permette l'inserimeto e l'aggiornamento dei nodi autorizzati ad apparire in mappa attraverso una pagina dedicata allo scopo.
5. il server prevede il tracciamento dei nodi mobili attraverso una richiesta specifica basata su data e nome del nodo che appare già in lista alla pagina Home.
6. il server permette la visualizzazione del log messaggi ricevuti su ch0 in una pagina dedicata elencati in una textarea in ordine cronologico per il giorno corrente.
7. il server in associazione con mesh_controller.py permette ora l'invio di messaggi su ch0 attarverso in Db in comune

## Struttura del Server

Ipotizzo un server Flask semplificato con le seguenti caratteristiche di base:

1. Accesso aperto senza necessità di affiliazione
2. Semplice HTTP, no HTTPS / SSL
3. Scelta fra mappa in tempo reale e traking per data e nodo in lista
4. Nginx non necessario, basta Gunicorn

## Installazione moduli python a supporto

Avendo attivato ambiente virtuale:

Da directory di base eseguire pip install -r requirements.txt che provvede a installare quanto specificato di seguito in dettaglio.

1. pip install flask
2. pip install python-dotenv nota: se si ha errore di interpretazione file al lancio di flask run usare notepad++ per leggere .flaslenv e riscriverlo in formato utf-8 (default è utf-16 non supportato da python)
3. pip install flask_sqlalchemy
4. pip install flask_migrate
5. pip install flask_session per sicurezza di sessione che in memoria può saturarsi
6. pip install paho.mqtt per supporto discrezionale a server mqtt broker.emqx.io
7. pip install folium a supporto del display delle mappe
8. pip install requests a supporto comunicazioni con altri server. Nella fattispecie attuale il server di riferimento è il già noto e attivo https://vinmqtt.hopt.org che verrà così integrato oltre che dagli utenti di broadcast_msg_pyqt5.py anche da chi usasse l'applicazione attuale.
9. pip install apscheduler per supporto ricezione email
10. pip install imaplib    per supporto ricezione email
11. pip install imap_tools per supporto ricezione email

### Esecuzione

Occorre aprire due terminali, uno per meh_controller.py, l'atro per il server.
Poi se si decide di accedere a server mqtt pubblico aprire altri due termnali uno per mqtt_send.all.py l'altro per mqtt_subscribe.py

1. si entra da un terminale nella directory base del progetto e si esegue venv/Scripts/activate se in windows, source/bin/activate se il Linux
2. si va su ./source e da lì si lancia python mesh_controller.py COMx (Windows) o /dev/ttyUSBx o ACMx se in Linux. Ora dobbiamo far partire il server..
3. si apre un secondo terminale e dalla directory base del progetto si fa di nuovo venv/Script/activate o source/bin/activate se in Linux
4. eseguire 'flask run' (senza apici) per far partire il server
5. Si apra un browser e si batta lo url 'localhost:5000/showmap' (senza apici) per vedere la mappa attuale in real time

Se dovessero essere inseriti nuovi nodi di iscritti alla rete questi vanno aggiunti in tabella Modes usando il form presente alla pagina Abilita_nodo che va a modificae la tabella modes. Il colore dei marker è determinato dal campo 'mode' e per ragioni storiche che non sto qui a spiegare per avere il blu mode = MEDIUM_FAST, per il verde LONG_FAST e freq = 433, per il rosso freq = 868 e mode = LONG_SLOW. anche se sappiamo che anche qui lavoriamo in MEDIUM_FAST. Quindi niente paura vedendo in rsposta all'inserimento il campo 'mode' come LONG_SLOW quando sappiamo di lavorare in MEDIUM_FAST, in ealtà LONG_SLOW sta per rischiamere il colore rosso nel marker così come LONG_FAST richiama il verde (433Mhz) e il MEDIUM_FAST il blu, questi indicatori non hanno nessuna attinenza con la modalità reale.

### Note

In data 22 Agosto 2015 completate le funzioni di selezione e ambiente grafico sul server. Per vedere la mappa basta aprire un browser su localhost:5000/ e accedere alle varie scelte proposte
sul video. per lanciare il server battere flask --debug run da riga di comando se non si mette
--debug abbiamo un problema di cache in flask che fa sempre vesere l'ultima mappa mostrata
anche se cambiamo le scelte. Al momento l'unico modo per risolvere il problema è lavorare in
debug mode. Se si mette il server in connessione con un dynamic DNS vi si potrà accedere dal mondo esterno via internet. 

Altra nota importante qualora si volesse far accedere al server dall'esterno anziché da localhost riguarda il lancio stesso che se fatto come indicato sopra vincola accesso solo
da localhost. Occorre allora eseguire python run.py dove in run.py ci sono le direttive per permettere accesso universale.

Il 26 Agosto 2025 inserito nuova funzionalità sul server che è qualle di permettere inserimento e
aggiornamento nodi in tabella modes in modo da permettere agevole autorizzazione ad essere visti
in mappa secondo criteri di banda e di appartenenza al gruppo WA 'Lora Lombardia e Ticino' 

Il 27 Agosto 2025 inserita risposta automatica in mesh_controller.py
il 28 Agosto 2025 inserita visibilità della lista messaggi text ricevuti o trasmessi su ch0
il 29 Agosto 2025 aggiunta possibilità di inveare messaggi su ch0 che appariranno immediatamente 
nel log messaggi (tabella messaggi in Db)
il 9 Settembre apportato aggiornamento a file __init__.py per modificare la session che in memoria non era più sufficinte a gestire i cookies di sessione necessari alla gestione dei mesaggi testuali su ch0. Passati da sessione in memoria a sessione su filesystem. E' stato necessario aggiungere pip install flask_session che prima non c'era.

il 14 Settembre aggiunto supporto a mqtt server per aggiornamento mappa da fonti diverse dalla nostra e possibilità di inviare dati sui nodi visti da noi verso il server per condivisione da altri. Leggere ./Doc/Meshtastic_meshmonitor_ver1.1.pdf

il 17 Settembre aggiunto supporto a ricezione mail per invio del testo su ch0. Leggere documento in ./Doc/Ricezione_Mail_su_Meshmonitor.pdf

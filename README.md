##mesh_controller.py##

L’obiettivo da raggiungere è quello di poter porre in mappa OpenStreet map la posizione dei nodi che vediamo dal nodo centrale della nostra rete su una mappa e volendo, rendere questa accessibile in rete al mondo esterno. Occorre così per prima cosa che, grazie alla
interfaccia API meshtastic, mesh_controller.py vedendo via collegamento seriale una unita Tlora che riceve i messaggi di protocollo in rete meshtastic via radio, è in grado di elaborare questi messaggi salvandone i risultati su un DB Sqlite3.

Questo stessa DB, messo in comune con altra applicazione Python Flask, sarà la base da cui il Server Flask (che vedremo in seguito come capitolo a parte) farà riferimento in sola lettura per pubblicare i dati su una mappa OpenStreet.

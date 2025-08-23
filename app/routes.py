import sqlalchemy as sa
import app as app
from app import app,db
from app.models import Meshnodes
from app.models import Modes
from app.models import Tracking
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request

#from datetime import datetime
import folium, json, time, os
from folium import Element

@app.route('/')
@app.route('/index')
def index():
    return redirect (url_for('listanodi'))
    #return render_template('index.html')

@app.route("/listanodi")
def listanodi():
    nodi = Tracking.get_nodi()   
    nodi = [nodo[0] for nodo in nodi]
    return render_template('index.html', nodi=nodi) 

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@app.route('/showmap', methods=['GET','POST'])
def showmap():
    oggi = request.form.get("giorno")
    opzione = request.form.get('opzione')
    print("========")
    print(f"Oggi = {oggi}")
    print(f"opzione = {opzione}")
    print("========")
    
    percorso = []
    
    # Creiamo la mappa centrata su una posizione specifica
    mappa = folium.Map(location=[45.71167, 9.31603], zoom_start=13)  # Milano, Italia
    # Aggiungiamo un marker sulla mappa
    folium.Marker([45.7116, 9.318], popup="Home ",icon = folium.Icon(color='black')).add_to(mappa)
    
    if(opzione is not None and oggi is not None and oggi != 'None' and opzione != 'tutti'):
        # siamo in tracking
        nodes = Tracking.getTrack(oggi,opzione)
        numpos = True
        for node in nodes:
            if(numpos is True):
                #marker di start
                folium.Marker([node.lat, node.lon], icon=folium.Icon(color='red'),
                popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                tooltip=node.longname).add_to(mappa)
            else:
                folium.Marker([node.lat, node.lon], icon=folium.Icon(color='green'),
                popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
            numpos = False
            percorso.append([node.lat,node.lon])
            app.logger.info(f"{opzione}:{percorso}")
        
        if len(percorso) > 1:
            # Collega i marker con una Polyline blu
            folium.PolyLine(locations=percorso, color="blue", weight=3, opacity=0.6).add_to(mappa)
        # Riquadro bianco in alto a sinistra
        html_box = '''
            <div style="
            position: fixed;
            top: 10px;
            left: 50px;
            width: 300px;
            padding: 15px;
            background-color: white;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
            z-index: 9999;
            font-family: Arial, sans-serif;
            font-size: 14px;
            ">
            <h4><b>Rete Lora Lombardia e Canton Ticino</b></h4>
            <p><b>I colori dei marker mostrano:</b><br>
	        <font color="red"><b>Rosso:</b></font> questa rete medium_fast 868Mhz<br>
	        <font color="blue"><b>Blu:</b></font> rete Ticino medium_fast 868Mhz<br>
	        <font color="green"><b>Verde:</b></font> questa rete long_fast 433Mhz</p>
            </div>
        '''
        mappa.get_root().html.add_child(Element(html_box))
        mappa.save('app/templates/map.html')
        # Inserisci un timestamp nell'URL del file JS della mappa
        #timestamp = int(time.time())
        #mappa_ts = mappa._repr_html_() + f"?v={timestamp}"
        oggi = None
        opzione = None
        return render_template('map.html')

    nodes = Meshnodes.chiamaNodi()
    opzione = "tutti" #forzo tutti per mappa istantanea non tracking
    #print(f"Nodes: {nodes}")
    for node in nodes:
        modi = Modes.getMode(node.node_id)
        caract = {}
        if modi is not None:
            caract['freq'] = modi[0]   # freq
            caract['mode'] = modi[1]   # mode
        else:
            caract['freq'] = 868
            caract['mode'] = 'MEDIUM_FAST'
            app.logger.info(f'Nodo: {node.longname}')
            app.logger.info(f"Non trovato in Modes:{node.node_id}")
            continue

        #print(f"id: {node.nodenum}")
        #print(f"node_id: {node.node_id}")
        #print(f"nome_nodo: {node.longname}")
        #print(f"giorno: {node.data}")
        #print(f"orario: {node.ora}")
        #print(f"Latitude: {node.lat}")
        #print(f"Longitude: {node.lon}")
        #print(f"Quota: {node.alt}")

        if opzione == "tutti":
            if caract['freq'] == 433:
                folium.Marker([node.lat, node.lon], icon=folium.Icon(color='green'),
                popup=node.nome + " giorno " + node.data + " ora " + node.ora,
                tooltip=node.nome).add_to(mappa)  # Aggiungi la label con il nome del nodo
                folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)

            else:
                if caract['mode'] =='MEDIUM_FAST':
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='darkblue'),
                    popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                    folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)

                else:
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='red'),
                    popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                    folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)

            #app.logger.info(f"{caract['freq']}:{caract['mode']}")
        elif opzione == "433":
            if caract['freq'] == 433:
                folium.Marker([node.lat, node.lon], icon=folium.Icon(color='green'),
                popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)

        
        elif opzione == "868":
            if caract['freq'] == 868:
                if caract['mode'] == "MEDIUM_FAST":
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='darkblue'),
                    popup=node.nome + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                    folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)

                else:
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='red'),
                    popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                    folium.Marker(location=[node.lat, node.lon],icon=folium.DivIcon(
                    icon_size=(150,36),icon_anchor=(0,0),
                    html=f'<div style="font-size: 12px; color: black;">{node.longname}</div>')
                ).add_to(mappa)


        elif node.longname == opzione:
            if caract['freq'] == 433:
                folium.Marker([node.lat, node.lon], icon=folium.Icon(color='green'),
                popup=node.nome + " giorno " + node.data + " ora " + node.ora,
                tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
            else:
                if caract['mode'] =='MEDIUM_FAST':
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='darkblue'),
                    popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa)  # Aggiungi la label con il nome del nodo
                else:
                    folium.Marker([node.lat, node.lon], icon=folium.Icon(color='red'),
                    popup=node.longname + " giorno " + node.data + " ora " + node.ora,
                    tooltip=node.longname).add_to(mappa) 
            percorso.append([node.lat,node.lon])
            print(percorso)
            app.logger.info(f"{opzione}:{percorso}")
        print('-' * 40)  # Separator for better readability
    if len(percorso) > 1:
        # Collega i marker con una Polyline blu
        folium.PolyLine(locations=percorso, color="blue", weight=3, opacity=0.6).add_to(mappa)

    # Riquadro bianco in alto a sinistra
    html_box = '''
        <div style="
        position: fixed;
        top: 10px;
        left: 50px;
        width: 300px;
        padding: 15px;
        background-color: white;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        z-index: 9999;
        font-family: Arial, sans-serif;
        font-size: 14px;
        ">
        <h4><b>Rete Lora Lombardia e Canton Ticino</b></h4>
        <p><b>I colori dei marker mostrano:</b><br>
	<font color="red"><b>Rosso:</b></font> questa rete medium_fast 868Mhz<br>
	<font color="blue"><b>Blu:</b></font> rete Ticino medium_fast 868Mhz<br>
	<font color="green"><b>Verde:</b></font> questa rete long_fast 433Mhz</p>
        </div>
    '''
    mappa.get_root().html.add_child(Element(html_box)) 


    # Salviamo la mappa in un file HTML]
    mappa.save('app/templates/map.html')
    # Inserisci un timestamp nell'URL del file JS della mappa
    timestamp = int(time.time())
    mappa_ts = mappa._repr_html_() + f"?v={timestamp}"
    #mappa_ts.save('app/templates/mappa_ts.html')
    # Renderizziamo la mappa nella pagina
    return render_template('map.html')


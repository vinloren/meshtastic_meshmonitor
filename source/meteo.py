import openmeteo_requests

import pandas as pd
import requests_cache
import math
from retry_requests import retry
from datetime import datetime

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

Tempo = False

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
def getMeteo(lat,lon):
    tempo = {0:'Sereno',1:'Poco nuvoloso',2:'Nuvoloso',3:'Coperto',45:'Nebbia',48:'Nebbia',
             51:'Pioviggine1',53:'Pioviggine2',55:'Pioviggine3',56:'Pioviggine1 gelida',
             57:'Pioviggine2 gelida',61:'Pioggia leggera',63:'Pioggia moderata',
             65:'Forte pioggia',66:'Leggera pioggia gelata',67:'Intensa pioggia gelata',
             71:'Leggera nevicata',73:'Discreta nevicata',75:'Intensa nevicata',77:'Nevischio',
             80:'Leggeri rovesci',81:'Discreti rovesci',82:'Forti rovesci',85:'Tempesta di neve',
             86:'Leggere pioggia di neve',87:'Forte pioggia di neve',95:'Temporali',96:'Discreti temporali',
             99:'Forti temporale'}
    
    url = "https://api.open-meteo.com/v1/forecast"
    nuvolosita = {0:'Libero',1:'1/8',2:'2/8',3:'3/8',4:'4/8',
                  5:'5/8',6:'6/8',7:'7/8',8:'8/8'}
    
    params = {
		"latitude": lat,
		"longitude": lon,
		"current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "precipitation", "rain", "showers", "weather_code", "cloud_cover"],
	}
    responses = openmeteo.weather_api(url, params=params)

	# Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

	# Process current data. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_relative_humidity_2m = current.Variables(1).Value()
    current_wind_speed_10m = current.Variables(2).Value()
    current_wind_direction_10m = current.Variables(3).Value()
    current_wind_gusts_10m = current.Variables(4).Value()
    current_precipitation = current.Variables(5).Value()
    current_rain = current.Variables(6).Value()
    current_showers = current.Variables(7).Value()
    current_weather_code = current.Variables(8).Value()
    current_cloud_cover = current.Variables(9).Value()

    previs = {}
    qth = findProvince([response.Latitude(),response.Longitude()])
    previs['Qth'] = qth #str(round(response.Latitude(),2))+"°N "+str(round(response.Longitude(),2))+"°E"
    previs['Mt.slm'] = response.Elevation()
    previs['data'] = datetime.now().strftime("%d/%m/%y")
    previs['Temp.'] = str(round(current.Variables(0).Value(),1))+"°C"
    previs['Umid.'] = str(round(current.Variables(1).Value(),1))+"%"
    previs['Vento'] = str(round(current.Variables(2).Value(),1))+"Km/h"
    previs['Dirz.'] = str(round(current.Variables(3).Value(), 1))+"°"
    previs['Raff.'] = str(round(current.Variables(4).Value(),1))+"Km/h"
    if current.Variables(6).Value() > 0:
        previs['Pioggia'] = str(current.Variables(6).Value())+"mm"
    if current.Variables(7).Value() > 0:
        previs['Temporali'] = str(current.Variables(7).Value())+'mm'
    previs['Tempo'] = tempo[current.Variables(8).Value()]
    #previs['Cop.Cielo'] = nuvolosita[current.Variables(9).Value()]
    
    s = ""
    for elm in previs:
        s+= elm + " "+ str(previs[elm])+'\n'
    	#print(len(s))
    print(len(s))
    return(s)

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

# coord sono le coordinate del devicece richdente il servizio
# con le quali si va a calcolare la minima distanza con una
# delle province sotto elencate che costituirà la risposta qth
def findProvince(coord):
    dist = 1000000
    qth = ""
    prov = {'Como':[45.8165,9.09],'Varese':[45.8155,8.8354],'Milano':[45.4752,9.1731],'Monza':[45.5865, 9.2756],
            'Novara':[45.44558,8.6253],'Pavia':[45.1921,9.1332],'Lodi':[45.3091, 9.5023],'Bergamo':[45.6928, 9.6725],
            'Brescia':[45.547, 10.222],'Sondrio':[46.175, 9.848],'Cremona':[45.131, 9.962],'Lecco':[45.854, 9.392],
            'Piacenza':[45.057, 9.71],'Mantova':[45.1625,10.794],'Parma':[44.803,10.327],'Modena':[44.644, 10.913],
            'Vercelli':[45.323, 8.4213],'Asti':[44.902,8.208],'Cuneo':[44.3988, 7.536],'Alessandria':[44.906, 8.59],
            'Torino':[45.072, 7.6824],'Ivrea':[45.4673, 7.8796],'Lugano':[46.0053, 8.95],'Chiasso':[45.841, 9.009],
            'Seveso(MB)':[45.641,9.12]}

    for prv in prov:
        d = haversine(prov[prv],coord)
        if dist > d:
            dist = d
            qth = prv
    return qth
        
#res = getMeteo(45.64, 9.11)
#print(res)
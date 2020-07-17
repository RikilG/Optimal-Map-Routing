#!/usr/bin/env python

import json
import math
import psycopg2
import requests
import pandas as pd
from tqdm import tqdm
from point import Point

conn = psycopg2.connect(dbname="gis", host="/var/run/postgresql/")
cur = conn.cursor()

def getNodes(size='large', dec_limit=15):
    if size=='large':
        cur.execute("""select st_y(st_transform(st_startpoint(way),4326)), st_x(st_transform(st_startpoint(way),4326)) 
                        from planet_osm_roads;""")
    elif size=='medium':
        cur.execute("""select st_y(st_transform(st_startpoint(way),4326)), st_x(st_transform(st_startpoint(way),4326)) 
                        from planet_osm_roads where highway='trunk' or highway='primary' or highway='motorway' or highway='secondary';""")
    elif size=='wards':
        # cur.execute("""select name from planet_osm_polygon where name like 'Ward%'""")
        # names = cur.fetchall()
        # with open('wardNames.txt', 'w') as f:
        #     for name in names:
        #         name = ' '.join(name[0].split()[2:])
        #         f.write(name+'\n')
        # you can add name to select to get name of wards
        cur.execute("""select st_y(st_transform(st_centroid(way),4326)), st_x(st_transform(st_centroid(way),4326)) 
                        from planet_osm_polygon where name like 'Ward%';""")
    else:
        raise Exception('Unknown size given')
    res = cur.fetchall()
    # res is a list of (lat, lat) points
    nodes = list()
    for r in res:
        nodes.append(Point(lat=round(r[0], dec_limit), lon=round(r[1], dec_limit)))
    return nodes

def getBingMapsKey():
    with open("APIkeys.json", 'r') as f:
        j = f.read()
    j = json.loads(j)
    return j["BingMapsKey"]

def getDistTime(src, dest, distframe=None, timeframe=None):
    assert type(src[0]) == Point and type(dest[0]) == Point, "getDistTime: Assert: Type Error"
    assert len(src)*len(dest) <= 2500, "geDistTime: Assert: Size Error"
    if distframe is None: distframe = pd.DataFrame(columns=dest, index=src)
    if timeframe is None: timeframe = pd.DataFrame(columns=dest, index=src)
    origins = [ {"latitude": p.lat, "longitude": p.lon} for p in src ]
    destinations = [ {"latitude": p.lat, "longitude": p.lon} for p in dest ]
    url = f"https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?key={getBingMapsKey()}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "origins": origins,
        "destinations": destinations,
        "travelMode": "driving",
    }
    try:
        res = requests.post(url, headers=headers, json=data)
    except Exception as e:
        print("Request Error: ", e)
        return
    assert res.status_code == 200, f"Status code {res.status_code} is not 200"
    res = res.json()
    # check if valid data received
    assert res['authenticationResultCode'] == 'ValidCredentials' and res['statusDescription'] == 'OK'
    resources = res['resourceSets'][0]['resources'][0]
    # assert resources['errorMessage'] == 'Request completed.', resources['errorMessage']
    results = resources['results']
    # rows - origin/src :: cols - destination/dest
    for r in results:
        s = src[ r['originIndex'] ]
        d = dest[ r['destinationIndex'] ]
        distframe.at[s, d] = distframe.at[d, s] = float(r['travelDistance'])
        timeframe.at[s, d] = timeframe.at[d, s] = float(r['travelDuration'])
    return distframe, timeframe

def getMatrices(nodes, chunk_size=50, store_prefix='', cont=False, conti=0):
    try:
        distframe = pd.read_pickle(store_prefix+'Distframe.pkl')
        timeframe = pd.read_pickle(store_prefix+'Timeframe.pkl')
        nodes = distframe.index
        if cont != True:
            return distframe, timeframe
    except Exception as e:
        print("No stored data found. Calculating...")
    
    chunks = math.ceil(len(nodes)/chunk_size)
    if cont != True:
        distframe = pd.DataFrame(columns=nodes, index=nodes)
        timeframe = pd.DataFrame(columns=nodes, index=nodes)
    try:
        for i in tqdm(range(conti, chunks), desc="Outer"):
            sb = i*chunk_size   # src begin
            se = min((i+1)*chunk_size, len(nodes)) # src end
            for j in tqdm(range(i, chunks), desc="Inner"):
                db = j*chunk_size   # dest begin
                de = min((j+1)*chunk_size, len(nodes)) # dest end
                # print(sb, se, db, de)
                getDistTime(nodes[sb:se], nodes[db:de], distframe, timeframe)
        # for node in nodes:
        #     distframe, timeframe = getDistTime(src, dest, distframe, timeframe)
        for i in range(len(nodes)):
            distframe.iat[i, i] = 0
            timeframe.iat[i, i] = 0
    except Exception as e:
        print("Matrix Error: ", e)
    finally:
        distframe.to_pickle(store_prefix+'Distframe.pkl')
        timeframe.to_pickle(store_prefix+'Timeframe.pkl')
    
    return distframe, timeframe

def main():
    size = input('Enter required size of graph to calculate Distance matrix (medium, large, wards) (default: large): ') # 'medium'
    if size != 'medium' and size != 'wards': size = 'large'
    nodes = getNodes(size)
    # add src and destination to nodes
    nodes.append(Point(17.547323, 78.572519)) # BITS location
    nodes.append(Point(17.240852, 78.429417)) # RGIA location
    distframe, timeframe = getMatrices(nodes, chunk_size=50, store_prefix=size, cont=True, conti=5) #for medium to continue
    # print(distframe)
    # print(timeframe)
    print(f"Distance dataframe is stored to Distframe.pkl and Time dataframe is sotred to Timeframe.pkl")

if __name__ == "__main__":
    main()

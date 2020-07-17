#!/usr/bin/env python

import math
import pickle
import psycopg2
import numpy as np
import pandas as pd
from point import Point
from pprint import pprint

conn = psycopg2.connect(dbname="gis", host="/var/run/postgresql/")
cur = conn.cursor()

def calcDist(p1, p2):
    lat1 = p1.lat
    lon1 = p1.lon
    lat2 = p2.lat
    lon2 = p2.lon
    R = 6371e3; # metres
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2-lat1)
    delta_lam = math.radians(lon2-lon1)
    a = math.sin(delta_phi/2)*math.sin(delta_phi/2)+math.cos(phi_1)*math.cos(phi_2)*math.sin(delta_lam/2)*math.sin(delta_lam/2);
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
    d = R * c;
    return d

def getEdges(src, dest, size='large', dec_limit=15):
    if size=='large':
        cur.execute("""select st_y(st_transform(st_startpoint(way),4326)), st_x(st_transform(st_startpoint(way),4326)), 
                        st_y(st_transform(st_endpoint(way),4326)), st_x(st_transform(st_endpoint(way),4326)), st_length(way) 
                        from planet_osm_roads""")
    elif size=='medium':
        cur.execute("""select st_y(st_transform(st_startpoint(way),4326)), st_x(st_transform(st_startpoint(way),4326)), 
                        st_y(st_transform(st_endpoint(way),4326)), st_x(st_transform(st_endpoint(way),4326)), st_length(way) 
                        from planet_osm_roads where highway='trunk' or highway='primary' or highway='motorway' or highway='secondary';""")
    else: 
        raise Exception("unknown size value")
    res = cur.fetchall()
    points = set([src, dest])
    edgeList = []
    for edge in res:
        s = Point(edge[0], edge[1])
        d = Point(edge[2], edge[3])
        points.add(s)
        points.add(d)
        edgeList.append((s, d, edge[4]))
    adjframe = pd.DataFrame(index=points, columns=points)
    for edge in edgeList:
        s = edge[0]
        d = edge[1]
        adjframe.at[s, d] = adjframe.at[d, s] = edge[2]
    # connect source and dest to nearby nodes
    s = sorted([ (calcDist(node, src), node) for node in points ])
    e = sorted([ (calcDist(node, dest), node) for node in points ])
    # pprint(s[:30])
    # pprint(e[:20])
    # exit()
    for n in s[:25]:
        adjframe.at[src, n[1]] = adjframe.at[n[1], src] = n[0]
        edgeList.append((src, n[1], n[0]))
    for n in e[:10]:
        adjframe.at[dest, n[1]] = adjframe.at[n[1], dest] = n[0]
        edgeList.append((n[1], dest, n[0]))
    return adjframe.astype(pd.SparseDtype("float", np.nan)), edgeList, points

def calcMatrix(origins, destinations):
    distMatrix = [ [ 0 for i in range(len(destinations)) ] for j in range(len(origins)) ]
    for i in range(len(origins)):
        for j in range(len(destinations)):
            dist = calcDist(origins[i]["latitude"], origins[i]["longitude"], destinations[j]["latitude"], destinations[j]["longitude"])
            distMatrix[i][j] = dist/1000 # in Km
    return distMatrix

def main():
    size = input('Enter required size of graph to calculate Distance matrix (medium, large, wards) (default: large): ') # 'medium'
    if size != 'medium' and size != 'wards': size = 'large'
    print(f"Creating dataframe for size: {size} ...")
    src = Point(17.547323, 78.572519) # bits
    dest = Point(17.248439100161267, 78.4743304) # rgia
    adjframe, edgeList, nodes = getEdges(src, dest, size)
    
    adjframe.to_pickle(size+'Adjframe.pkl')
    with open(size+'Edges.pkl', 'wb') as f:
        pickle.dump(edgeList, f)
    print("Edge and Adjacency Matrices created!")

    # nodes = [Point(17.5472, 78.5725), Point(17.492374, 78.336394), Point(17.2408, 78.4293), Point(17.495428, 78.335287)]
    # nodes.append(Point(17.547323, 78.572519)) # bits
    # nodes.append(Point(17.240852, 78.429417)) # rgia
    # distMatrix = calcMatrix(origins, destinations)
    # print_matrix(distMatrix)

if __name__ == "__main__":
    main()

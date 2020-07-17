#!/usr/bin/env python

import json
import heapq
import pickle
import gmplot
import webbrowser
import pandas as pd
from point import Point
from pprint import pprint
from calcDist import calcDist

def getSucc(node, edgeList):
    succ = []
    for edge in edgeList:
        if edge[0] == node and edge[1] != node:
            succ.append(edge[1])
    return succ

def betterThan(n, f, lst):
    for i in lst:
        if repr(i) == repr(n) and i.f <= f: # if s already in open and has lower heuristic value
            return True
    return False

def getPath(start, stop):
    path = [ stop ]
    while path[-1] != start:
        path.append(path[-1].parent)
    path.reverse()
    return path

def AStar(start, stop, matrix, edgeList):
    opened = [ start ]
    closed = []
    while len(opened) != 0:
        q = heapq.heappop(opened)
        succ = getSucc(q, edgeList)
        for s in succ:
            if s == stop:
                s.parent = q
                return getPath(start, s)
            g = q.g + matrix.at[q, s]
            # h = matrix.at[s, stop]
            h = calcDist(s, stop)
            f = g + h
            if s in opened and betterThan(s, f, opened):
                continue
            # print(s.f, f, s in closed)
            if s in closed and betterThan(s, f, closed):
                continue
            s.parent = q
            s.g = g
            s.h = h
            s.f = f
            heapq.heappush(opened, s)
        closed.append(q)
        # print(f"\rC:{len(closed)} O:{len(opened)}")
    x = sorted([ (calcDist(p, stop), p) for p in closed ])
    pprint(x[:min(10, len(x))])
    print(f"Remaining dist: {x[0][0]}")
    return getPath(start, x[0][1])

def showPathOnMap(filename):
    with open("APIkeys.json", 'r') as f:
        api_key = json.loads(f.read())['GoogleMapsKey']

    df = pd.read_csv(filename).drop(columns=["index"])
    gmap = gmplot.GoogleMapPlotter(17.4251, 78.4747, 11.5, apikey=api_key)
    gmap.scatter(df['latitude'], df['longitude'], '#00FF00', size = 120, marker = False)
    gmap.plot(df['latitude'], df['longitude'], 'cornflowerblue', edge_width = 3.0)
    gmap.draw("optimal_path.html")
    webbrowser.open("optimal_path.html", new=2)
    
def main():
    start = Point(17.547323, 78.572519) # bits
    stop = Point(17.248439100161267, 78.4743304) # rgia
    start.g = 0
    start.h = calcDist(start, stop)
    start.f = start.g + start.h
    stop.h = 0

    mat_size = 'large'
    mat_type = 'adj'

    try:
        # load distframe or timeframe matrtices according to mat_type
        if mat_type == 'time':
            matrix = pd.read_pickle(mat_size+'Timeframe.pkl')
        elif mat_type == 'adj':
            matrix = pd.read_pickle(mat_size+'Adjframe.pkl')
            with open(mat_size+'Edges.pkl', 'rb') as f:
                edgeList = pickle.load(f)
        else:
            matrix = pd.read_pickle(mat_size+'Distframe.pkl')
    except:
        print("No distance and/or time matrices defined. run getDist.py to get matrices")
        exit()
    
    path = AStar(start, stop, matrix, edgeList)
    filename = "FinalPath.csv"
    with open(filename, 'w') as f:
        index = 1
        f.write("index,latitude,longitude\n")
        for point in path:
            f.write(f"{index},{point.lat},{point.lon}\n")
            index += 1
        f.write(f"{index},17.240890, 78.433189\n") # final RGIA location
    print("Path saved to FinalPath.csv")
    showPathOnMap(filename)

if __name__ == "__main__":
    main()
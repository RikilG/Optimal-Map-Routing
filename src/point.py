#!/usr/bin/env python

class Point:
    def __init__(self, lat, lon, g=float('inf'), h=float('inf')):
        self.lat = lat
        self.lon = lon
        self.point = (lat, lon)
        self.g = g
        self.h = h
        self.f = g + h

    def __str__(self):
        return f"({round(self.lat, 4)}, {round(self.lon, 4)})"

    def __repr__(self):
        return f"({self.lat}, {self.lon})"
    
    def __eq__(self, p):
        if isinstance(p, Point):
            return self.lat==p.lat and self.lon==p.lon
        return False
    
    def __ne__(self, p):
        return not self.__eq__(p)
    
    def __hash__(self):
        return hash((self.lat, self.lon))
    
    def __lt__(self, p):
        if self.f == None: return p.f
        elif p.f == None: return self.f
        return self.f < p.f
    
    def __le__(self, p):
        if self.f == None: return p.f
        elif p.f == None: return self.f
        return self.f <= p.f
    
    def __gt__(self, p):
        return p < self
    
    def __ge__(self, p):
        return p <= self
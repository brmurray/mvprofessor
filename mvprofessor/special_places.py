# -*- coding: utf-8 -*-
"""

special_places.py

Noteworth places in Goleta relevant to the Professor feeder

"""
import numpy as np
from numpy.random import default_rng
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import geopandas
import networkx as nx
from shapely.geometry import Point
from geographiclib.geodesic import Geodesic

from mvprofessor.config import int_data_dir

# Places of Interest specific to the Professor feeder
poi_dict = {'isla_vista_ss':(34.43296569954078, -119.87130569500908),
       'deckers_corp':(34.428720518550485, -119.86292277548567),
       'deckers_outdoor':(34.42966833306866, -119.86192823530702),
       'deckers_showcase':(34.42968068228448, -119.86079192813382),
       'karl_storz':(34.43440614022403, -119.85560075564243),
       'goleta_city_hall':(34.4324736947165, -119.85524437479619),
       'sba_runway':(34.42713637168997, -119.84205540711429),
       'sba_atlantic':(34.429741284192474, -119.84435245054091),
       'sba_terminal':(34.42467434498243, -119.83649338389297)}

# Convert to GeoDataFrame and project to UTM11
y,x = list(zip(*list(poi_dict.values()))) # note reversal of y,x
poi_pts = geopandas.GeoSeries.from_xy(x,y,crs="EPSG:4326")
poi = geopandas.GeoDataFrame({'PoI':list(poi_dict.keys())},geometry=poi_pts,crs="EPSG:4326")
poi=poi.to_crs("EPSG:2955") # EPSG2955 for UTM11

# Save for access from other scripts
poi.to_pickle(int_data_dir/'PoI_Professor.pkl')


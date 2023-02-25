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

from mvprofessor.config import PoI_pkl_path

# Places of Interest specific to the Professor feeder
isla_vista_latlon = (34.43296569954078, -119.87130569500908)
#isla_vista = Point(isla_vista_substation_latlon)


places_df = pd.DataFrame({"PoI":['Isla_Vista_Substation'],
              'Latitude':[34.43296569954078],
              'Longitude':[-119.87130569500908]})

gdf = geopandas.GeoDataFrame(places_df,crs="EPSG:4326",
   geometry=geopandas.points_from_xy(places_df.Longitude, places_df.Latitude))
gdf = gdf.to_crs("EPSG:2955") # EPSG2955 for UTM11 
gdf.to_pickle(PoI_pkl_path)
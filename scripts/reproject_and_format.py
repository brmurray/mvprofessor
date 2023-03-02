# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 13:06:58 2023

@author: brmurray
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

# Custom components
from mvprofessor.config import raw_data_dir, int_data_dir

#%%
#gdf = geopandas.read_file(raw_data_dir / 'professor.geojson')
gdf = geopandas.read_file(raw_data_dir / 'ICA_Layer.geojson')


gdf=gdf.set_index('section_id')

# retain only columns which change (others cols are the same for every row)
gdf=gdf[["SHAPE__Length","objectid","node_id","geometry"]]

gdf['node_id'] =gdf['node_id'].apply(lambda x: int(x))

# add random number to make each LineString a different color when mapping
rng = default_rng()
gdf.loc[:,'randc'] = rng.choice(236*5,size=236,replace=False)


#%% Calculate the distance error introduced from re-projection
# Within WGS84 CRS, calculate geodesic (shortest path along ellipse)
bounds_wgs84 = gdf.total_bounds

# calculate the diagonal distance of the bounding box in WGS84
diag_ellipse = Geodesic.WGS84.Inverse(bounds_wgs84[1],bounds_wgs84[0],
                                      bounds_wgs84[3],bounds_wgs84[2])['s12']

# Re-project (WGS84 --> UTM11)
# DRPEP gives data in WGS84...re-project to UTM11 for northings/eastings in [m]
gdf = gdf.to_crs("EPSG:2955") # EPSG2955 for UTM11 

# calculate the diagonal distance of bounding box in UTM11
bounds_UTM11 = gdf.total_bounds
diag_11N = np.sqrt((bounds_UTM11[2]-bounds_UTM11[0])**2 
                   + (bounds_UTM11[3]-bounds_UTM11[1])**2)

# the Mercator projection requires a scale factor (1/cos(latitutde))
# NOT USED within UTM zones?
# k = 1/np.cos(np.deg2rad(34.43))

bounds_error = diag_11N/diag_ellipse # 11.5m over 3km, ~0.36%

# save to pickle (*.pkl) for easier access
gdf.to_pickle(int_data_dir / 'professor.pkl')
# -*- coding: utf-8 -*-
"""
blobs.py

Build "blobs" from buffered endpoints of LineStrings
"""

#%%
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
from mvprofessor.custom_funcs import get_endpoints

gdf = pd.read_pickle(int_data_dir/'professor.pkl')


#%% 
# First delete all the tiny segments
# quick look at the distribution of line lengths
#plt.hist(gdf['SHAPE__Length'],bins=np.arange(0,3000,20))  

buffer_radius = 20 #meters

gdf = gdf[gdf['SHAPE__Length'] > (0.9*2*buffer_radius)]
pts = get_endpoints(gdf)
pts = pts[['geometry']] # drop all other fields

halos = pts.copy()
halos['geometry'] = halos['geometry'].buffer(buffer_radius)

# option 1
# Find intersections between the halos
intersects = halos.sjoin(halos, how="left", predicate="intersects")

# dissolve intersections on right index indices using the minimum value
# This makes one giant multi-polygon
intersects_diss = intersects.dissolve(aggfunc="min")

# dissolve again on left index using minimum
blobs = intersects_diss.reset_index().dissolve(aggfunc="min")

# explode the giant multi-polygon into individual "blobs" 
blobs = blobs.explode(index_parts=True)
blobs = blobs.reset_index()

# drop the unnecessary columns
blobs = blobs[['geometry']]
blobs['blob_idx'] = blobs.index # shows in tooltip html map (via gdf.explore()) 

# Save for other functions
blobs.to_pickle(int_data_dir/'blobs.pkl')

# option 2 - didn't work, keep for later reference
#blobs2 = geopandas.overlay(halos,halos, how='union',keep_geom_type=True)

m = gdf.explore(column='randc',cmap='gist_rainbow')
#pts.explore(m=m,color='green',marker_kwds=dict(radius=2))
#halos.explore(m=m,marker_type='circle',marker_kwds=dict(fill=False))
#intersects_diss.explore(m=m,marker_kwds=dict(fill=False))
blobs.explore(m=m,marker_kwds=dict(fill=False))
m.save('blobs_test.html')

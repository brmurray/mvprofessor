# -*- coding: utf-8 -*-
"""
get_endpoints.py

"""

#%%
import numpy as np
from numpy.random import default_rng
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import geopandas
from shapely.geometry import Point

gdf = pd.read_pickle("professor.pkl")

#%% Block: Get all start/end points from LineStrings

# This is 2 nested list comprehensions
# inner comp. [y for y in x['geometry'].coords] returns ALL points along each linestring
# outer comp [Point(y[0] for y in gdf.apply())] makes a list of each *start* point
z = [Point(y[0]) for y in gdf.apply(lambda x: [y for y in x['geometry'].coords],axis=1)]

spts = gdf.copy()
epts = gdf.copy()

# This is 2 nested list comprehensions
# inner comp. [y for y in x['geometry'].coords] returns ALL points along each linestring
# outer comp. [Point(y[0] for y in gdf.apply())] makes a list of each *start* shapely.Point
spts['geometry'] = [Point(y[0]) for y in gdf.apply(lambda x: [y for y in x['geometry'].coords],axis=1)]
epts['geometry'] = [Point(y[-1]) for y in gdf.apply(lambda x: [y for y in x['geometry'].coords],axis=1)]

zm=spts.explore(color='green',marker_kwds=dict(radius=3))
epts.explore(m=zm,color='red',marker_kwds=dict(radius=3))
gdf.explore(m=zm,column='randc',cmap='gist_rainbow')
zm.save('zpoints.html')

# concatenate the startpoints and endpoints into a single dataframe
pts = pd.concat([spts,epts],ignore_index=True)



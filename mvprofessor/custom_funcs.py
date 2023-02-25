# -*- coding: utf-8 -*-
"""
custom_funcs.py

custom functions for the mvprofessor analysis


"""

import numpy as np
from numpy.random import default_rng
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import geopandas
from shapely.geometry import Point


def get_endpoints(gdf_linestrings):
    '''
    Accepts
    -------
    'gdf_linestrings': GeoDataframe where ['geometry'] is shapely.LineString
    representing the network's wires

    Returns
    -------
    'endpoints': GeoDataframe where ['geometry'] column is shapely.Point 
    of endpoints. The lengths of 'endpoints' should be twice the length of 
    'gdf_linestrings'
    
    
    ### Note an alternative (https://gis.stackexchange.com/questions/137909/intersecting-lines-to-get-crossings-using-python-with-qgis)
    endpts = [(Point(list(line.coords)[0]), Point(list(line.coords)[-1])) for line  in lines]
    # flatten the resulting list to a simple list of points
    endpts= [pt for sublist in endpts  for pt in sublist] 
    
    '''
    
    spts = gdf_linestrings.copy() #probably doesn't need to be a deep copy
    epts = gdf_linestrings.copy() #probably doesn't need to be a deep copy

    # This is 2 nested list comprehensions
    # Inner comp. [y for y in x['geometry'].coords] returns 
    #     ALL points along each linestring
    # Outer comp. [Point(y[0] for y in gdf.apply())] makes a 
    #    list of each *start* shapely.Point
    spts['geometry'] = [Point(y[0]) for y in gdf_linestrings.apply(
        lambda x: [y for y in x['geometry'].coords],axis=1)]
    
    # Apply the same nested list comprehension to get endpoints
    epts['geometry'] = [Point(y[-1]) for y in gdf_linestrings.apply(
        lambda x: [y for y in x['geometry'].coords],axis=1)]

    # concatenate the startpoints and endpoints into a single dataframe
    pts = pd.concat([spts,epts],ignore_index=True)
    
    return pts
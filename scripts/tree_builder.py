# -*- coding: utf-8 -*-
"""
tree_builder.py
An attempt to map the MV Professor feeder using a depth-first tree traversal

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

import geographiclib # https://geographiclib.sourceforge.io/Python/doc/geodesics.html
from geographiclib.geodesic import Geodesic

from mvprofessor.config import gdf_pkl_path

gdf = pd.read_pickle(gdf_pkl_path)

sid1 = 18619198
sid2 = 172773681
sid3 = 18618889
sid4 = 169484737
sid5 = 169484961
sid6 = 169484981
sid7 = 18619559
subsect = [sid1,sid2,sid3,sid4,sid5,sid6,sid7]


#%% Depth-First Tree Traversal
# This block is an attempt to map the entire Professor feeder
# using a variation of the Depth-First Search (DFS) tree travesal
# In DFS, for a given node, we find connected nodes and follow each to its
# leaf (terminal) node before returning to the current node and doing the same
# for the next neighbor

# In this implementation, each node is added as a node in a NetworkX graph
# structure. Hopefully, this will faciliate later restructuring of the MV grid.

# As of Feb. 22, this algorithm doesn't work! It does not capture every edge, 
# and also fails to handle islanded segments (which are sufficiently far from 
# any neighbors)


# Simplified test case with just 4 segments
#gdf2 = gdf.loc[gdf['section_id'].isin(subsect[:5])].copy()

# full 236 segment dataset
gdf2 = gdf.copy()
gdf2['explored'] = 0

# Initiate graph
G = nx.Graph()

# Choose the first point from inspection
root_idx = 27 
endpt0 = Point(gdf2.loc[root_idx].geometry.coords[0])
G.add_node(0,pos=gdf2.loc[root_idx].geometry.coords[0],point=endpt0)


# These are used for the DFS iteration
node_counter = 1
frontier = [0] # for DFS, frontier is a STACK, access via frontier.pop(-1)
explored = []

while len(frontier)>0:
    current_node = frontier.pop(-1)
    
    # Buffer the current point and find connecting segments
    buff0 = G.nodes[current_node]['point'].buffer(40)
    branches = gdf2.loc[gdf2.intersects(buff0,align=True)] # returns a dataframe
    branches = branches[branches.explored !=1]
    
    # Each segment (linestring) has exactly two endpoints (boundaries)
    # Find which endpoint is within the buffer, and which is the next node
    for idx,branch in branches.iterrows():
        pt0 = Point(branch.geometry.coords[0])
        pt1 = Point(branch.geometry.coords[-1])
        
        if buff0.covers(pt0):
            new_point = pt1
        else:
            new_point = pt0
            
        # Add the new node to the graph and to the frontier
        G.add_node(node_counter, pos=(new_point.coords[0]),point=new_point)
        frontier.append(node_counter) # we'll revisit this point later
        
        # Add the edge from first node to new node
        G.add_edge(current_node,node_counter,weight=branch.SHAPE__Length,
                       length=branch.SHAPE__Length,
                       section_id=branch.section_id,
                       objectid=branch.objectid,
                       node_id=branch.node_id,
                       geometry=branch.geometry)
        
        # Note which branaches have been mapped, so as not repeat them
        gdf2.loc[idx,'explored'] = 1
        
        node_counter = node_counter+1
    
    # Once we've mapped all the edge of the current node,
    # add it to the explored list so we don't visit it again
    explored.append(current_node)
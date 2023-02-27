# -*- coding: utf-8 -*-
"""
Node_Finder.py

Attempt to identify electrical nodes from a collection of
geographic coordinates of a MV feeder.


"""

#%%
import numpy as np
from numpy.random import default_rng
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import geopandas
import folium
from shapely.geometry import Point
from geographiclib.geodesic import Geodesic

from mvprofessor.config import int_data_dir
from mvprofessor.custom_funcs import get_endpoints


gdf = pd.read_pickle(int_data_dir/'professor.pkl')

# exclude tiniest linestrings from geodataframe
gdf = gdf[gdf['SHAPE__Length'] > 50] #with cutoff=20, len(gdf)=197

blobs = pd.read_pickle(int_data_dir/'blobs.pkl')
poi = pd.read_pickle(int_data_dir/'PoI_Professor.pkl')


#%% Find the root node    
isla_vista = poi.loc[poi['PoI']=='isla_vista_ss']['geometry']
isla_vista = isla_vista.iloc[0]

blob0 = blobs.sindex.nearest(isla_vista)[1][0] #index to nearest blob from IVSS

root_blob = blobs.iloc[blob0]['geometry'] # a shapely.Polygon
root_pt= root_blob.representative_point() #shapely.Point for pos arg to nx node

#%% Tree Growing Algorithm
# Inspired by a classic depth-first search (DFS) tree traversal
#
# This method current relies on an apriori list of the blobs
# Improve it by using sindex.nearest() for each distal linestring endpoint to
# create the blobs iteratively

# Initiate graph and add first point
G = nx.Graph()
G.add_node(blob0,pos=root_pt.coords[0],blob=root_blob)

# These are used for the DFS iteration
frontier = [blob0] # initiate frontier with the root node
gdf['explored'] = 0
gdf['leaf'] = 0
explored = []

while len(frontier)>0:
    current_node = frontier.pop(-1) # for DFS, frontier is a STACK (LIFO)
    
    # Find segments which connect to the current blob
    blob = G.nodes[current_node]['blob']
    branches = gdf.loc[gdf.intersects(blob,align=True)] # returns a dataframe
    branches = branches[branches.explored !=1]  
    
        
    # Each branch (linestring) has exactly two endpoints (boundaries)
    # Find which endpoint is within the buffer, and which is the next node
    for idx,branch in branches.iterrows():
        
        pt0 = Point(branch.geometry.coords[0])
        pt1 = Point(branch.geometry.coords[-1])
        
        if blob.covers(pt0):
            new_point = pt1
        else:
            new_point = pt0
        
        #endblobs = blobs.sjoin(branches,how='inner',predicate='intersects')
        #endblobs = blobs[blobs.intersects(branch['geometry'])]
        new_blob = blobs[blobs.covers(new_point)]
        
        # # if len(endblobs)==1, the branch starts and ends at the same blob
        # # We're only interested in branches that connect to a new blob
        # # (in graph theory language, edges which lead to a new node)
        # if len(endblobs)==3:
        #     endblobs.head()
        # #print(len(endblobs))
        
        # if len(endblobs)>1: 
        #     new_blob = endblobs[endblobs.index!=current_node]
            #new_blob = endblobs.iloc[-1]
        #---------
                
        # Add the new node to the graph and to the frontier
        G.add_node(new_blob.index[0], 
                   pos=(new_blob.representative_point().iloc[0].coords[0]),
                   blob=new_blob.iloc[0]['geometry'])
        frontier.append(new_blob.index[0]) # we'll revisit this point later
        
        # Add the edge from first node to new node
        # The entire branch (pd.Series) is added to the node
        # All the branch elements are also added for easy access later
        G.add_edge(current_node,new_blob.index[0],weight=branch.SHAPE__Length,
                       length=branch.SHAPE__Length,
                       section_id=branch.name,
                       objectid=branch.objectid,
                       node_id=branch.node_id,
                       geometry=branch.geometry,
                       branch=branch)
        
        # Note which branches have been mapped, so as not repeat them
        gdf.loc[idx,'explored'] = 1
    
#%% Make the electrical nodes (enodes) into a GDF
pos = nx.get_node_attributes(G,'pos')
enode_id = list(pos.keys())
x,y = list(zip(*list(pos.values())))

enode_pts = geopandas.GeoSeries.from_xy(x,y,crs="EPSG:2955")
enodes = geopandas.GeoDataFrame({'enode_id':enode_id},geometry=enode_pts,crs="EPSG:2955")

#%% Plot the DRPEP lines, blobs, and electrical nodes
m = gdf.explore(column='randc',cmap='gist_rainbow',legend=False,
                name="DRPEP Line Sections")
blobs.explore(m=m,color='green',marker_type='circle',
              style_kwds=dict(fillOpacity=0.2),
              name="Blobs (initial guess nodes)")
enodes.explore(m=m,color='red',marker_kwds=dict(radius=5),
               name="Electrical nodes (programmatic)")
poi.explore(m=m,color='green',marker_type='marker',name="Points of Interest")
folium.LayerControl().add_to(m)
m.save('enodes.html')

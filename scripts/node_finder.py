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
from mvprofessor.custom_funcs import get_endpoints, make_blobs

# Import the Professor feeder linestrings, and exclude the tiniest segments
gdf = pd.read_pickle(int_data_dir/'professor.pkl')
gdf = gdf[gdf['SHAPE__Length'] > 30] #with cutoff=20, len(gdf)=197

# Create other layers: linestring endpoints (pts) and combined buffers (blobs)
pts = get_endpoints(gdf)
blobs = make_blobs(pts,10)
blobs['powered'] = 0

# Points of Interest 
poi = pd.read_pickle(int_data_dir/'PoI_Professor.pkl')


#%% Find the root node    
isla_vista = poi.loc[poi['PoI']=='isla_vista_ss']['geometry']
isla_vista = isla_vista.iloc[0]

root_idx = blobs.sindex.nearest(isla_vista)[1][0] #index to nearest blob from IVSS

root_blob = blobs.iloc[root_idx]['geometry'] # a shapely.Polygon
root_pt= root_blob.representative_point() #shapely.Point for pos arg to nx node

#%% Tree Growing Algorithm
# Inspired by a classic depth-first search (DFS) tree traversal
#
# Beginning from a seed node, the inner "while" loop will conduct a DFS
# tree traversal to connect all the line segments sharing common "blobs"
# ("blobs" are buffered endpoints of each line segment, combined into polygons
# where the buffers overlap).
#
# The outer "while" loop re-seeds the DFS algorithm using a random blob from
# among the non-yet-connected blobs. This is necessary because the input line 
# segments (GIS data) may be imprecise, i.e., two endpoints may be electrially
# connected but separated geographically by more than the 2x buffer radius. 
# The opposite can also be true, where two points are close but not necessarily
# electrically connected. 

# Initiate graph and add first point
G = nx.Graph()
G.add_node(root_idx,pos=root_pt.coords[0],blob=root_blob)
blobs.loc[root_idx,'powered']=1

# These are used for the DFS iteration
frontier = [root_idx] # initiate frontier with the root node
gdf['explored'] = 0
gdf['leaf'] = 0
explored = []

# outer loop: re-seed the DFS algorithm if the network is discontinous
while not np.all(blobs['powered']):
    if len(frontier)==0:
        
        powered_blobs = blobs[blobs['powered']==1]
        unpowered_blobs = blobs[blobs['powered']==0]
        reinit_blob = blobs[blobs['powered']==0].iloc[0]['geometry']
        reinit_pt = reinit_blob.representative_point()
        
        frontier.append(blobs[blobs['powered']==0].iloc[0]['blob_idx'])
        
        G.add_node(frontier[0],pos=reinit_pt.coords[0],blob=reinit_blob)
        blobs.loc[frontier[0],'powered']=1

    # inner loop: DFS traversal of node connected by line segments
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
            
            new_blob = blobs[blobs.covers(new_point)]
                    
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
            
            # Note which branches and blobs have been mapped
            gdf.loc[idx,'explored'] = 1
            blobs.loc[new_blob.index,'powered']=1
    
#%% Make the electrical nodes (enodes) into a GDF
pos = nx.get_node_attributes(G,'pos')
enode_id = list(pos.keys())
x,y = list(zip(*list(pos.values())))

enode_pts = geopandas.GeoSeries.from_xy(x,y,crs="EPSG:2955")
enodes = geopandas.GeoDataFrame({'enode_id':enode_id},geometry=enode_pts,crs="EPSG:2955")
enodes = enodes.set_index('enode_id')

#%% Flag the electrical nodes by their subgraph
# add a random number column for coloring
S = [G.subgraph(c).copy() for c in nx.connected_components(G)]

enodes['subgraph'] = 0
enodes['randc'] = 0
rng = default_rng()
r = rng.choice(len(S)*2,size=len(S),replace=False)
for i,Si in enumerate(S):
    enodes.loc[enodes.index.isin(list(Si.nodes)),'subgraph']=i
    enodes.loc[enodes.index.isin(list(Si.nodes)),'randc']=r[i]
    
# save to pickle (*.pkl) for easier access
enodes.to_pickle(int_data_dir / 'enodes.pkl')

#%% Plot the DRPEP lines, blobs, and electrical nodes
# m = gdf.explore(column='randc',cmap='gist_rainbow',legend=False,
#                 name="DRPEP Line Sections")
# Step 0: Note some important Places of Interest
m = poi.explore(color='green',marker_type='marker',
                name="Step 0: Note Points of Interest")

# Step 1: Show DRPEP Line Segments
gdf.explore(m=m,name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=3))

# Step 2: Find Endpoints
pts.explore(m=m,color='blue',marker_kwds=dict(radius=2),show=False,
               name="Step 2: LineString endpoints")

blobs.explore(m=m,color='green',marker_type='circle',
              style_kwds=dict(fillOpacity=0.2),show=False,
              name="Step 3: Combine very-near endpoints into 'blobs'")

# Step 4: Infer Electrical Nodes
enodes.explore(m=m,column='randc',cmap='prism',marker_kwds=dict(radius=7),
                legend=False,style_kwds=dict(fillOpacity=1.0),
                name="Step 4: Infer Electrical Nodes (colored by sub-network)")

folium.LayerControl().add_to(m)
m.save('Map_Steps.html')




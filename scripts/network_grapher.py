# -*- coding: utf-8 -*-
"""
Network_Grapher.py

This script derives an electrical connectivity Graph from a layer of 
LineStrings provided by SoCalEdison's "DRPEP" platform. 

Author: Bryan Murray
Last Revision: March 21, 2023

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
from shapely.geometry import Point, LineString
from geographiclib.geodesic import Geodesic
import pickle

from mvprofessor.config import int_data_dir, maps_dir
import mvprofessor.custom_funcs as mvpf

# *****************************
# Layer 0: Points of Interest 
# *****************************
poi = pd.read_pickle(int_data_dir/'PoI_Professor.pkl')

# *****************************
# Layer 1: Professor feeder linstrings
# *****************************
gdf = pd.read_pickle(int_data_dir/'professor.pkl')
gdf = gdf[gdf['SHAPE__Length'] > 30] #with cutoff=20, len(gdf)=197

# Create other layers: linestring endpoints (pts) and combined buffers (blobs)
# *****************************
# Layer 2: LineSring endpoints
# *****************************
pts = mvpf.get_endpoints(gdf)

# *****************************
# Layer 3: Blobs
# *****************************
blobs = mvpf.make_blobs(pts,7)
blobs['powered'] = 0


#%% Define a shapely.Point as the desired starting point
# In this case, we want to start at the Isla Vista Substation  
isla_vista = poi.loc[poi['PoI']=='isla_vista_ss']['geometry']
isla_vista = isla_vista.iloc[0]

#%% Run the tree builder algorithm
G = mvpf.tree_builder(gdf,blobs,isla_vista)

#%% Make Enodes, flagged by their subgraph
enodes = mvpf.make_enodes(G)

# *****************************
# Layer 4: Electrical Nodes (enodes)
# *****************************
enodes.to_pickle(int_data_dir / 'enodes.pkl')
#%% Intermediate map to identify nodes that should be manually connected
# Step 0: Note some important Places of Interest
m = poi.explore(color='green',marker_type='marker', show=False,
                name="Step 0: Note Points of Interest")

# Step 1: Show DRPEP Line Segments
#gdf.explore(m=m,name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=3))
# gdf.explore(m=m,column='randc',cmap='gist_rainbow',legend=False,
#             name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=3))
gdf.explore(m=m,color='blue',legend=False, show=True,
            name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=2))


# Step 2: Find Endpoints
pts.explore(m=m,color='blue',marker_kwds=dict(radius=2),show=False,
               name="Step 2: LineString endpoints")


# Step 3: Blobs
blobs.explore(m=m,color='green',marker_type='circle',
              style_kwds=dict(fillOpacity=0.2),show=False,
              name="Step 3: Combine very-near endpoints into 'blobs'")

# Step 4: Electrical nodes with colors
enodes.explore(m=m,column='randc',cmap='prism',marker_kwds=dict(radius=4),
                legend=False,style_kwds=dict(fillOpacity=1.0),show=True,
                name="Step 4: Infer Electrical Nodes (colored by sub-network)")

folium.LayerControl().add_to(m)
m.save(maps_dir / 'Map_Steps_Intermediate.html')

   
#%% Manually combine nodes that are obviously the same electrical node
# The first entry in the tuple should be the "upstream" node, to be retained
# i.e. the first entry "absorbs" the second entry
pairs = [(50,47),(75,76),(85,84),(85,87),(125,126)]
#pairs=[]

for p in pairs:
    G=nx.contracted_nodes(G,p[0],p[1])
    
# Manually remove any erronous edges
#G.remove_edge(74,119)

# save graph object to file
pickle.dump(G, open(int_data_dir / 'professor_graph.pickle', 'wb'))

#%% Make Enodes, flagged by their subgraph
enodes = mvpf.make_enodes(G)

# *****************************
# Layer 4: Electrical Nodes (enodes)
# *****************************
enodes.to_pickle(int_data_dir / 'enodes.pkl')
    
#%% Focus on the subgraph around Goleta City Hall/ Karl Storz ("CHKS")
# S is a list of subgraphs (nx.graph objects)
S = [G.subgraph(c).copy() for c in nx.connected_components(G)]

sx = 0 # subgraph of interest. For City Hall/Karl Storz, sx=0
pickle.dump(S[sx], open(int_data_dir / 'chks_graph.pickle', 'wb'))

# *****************************
# Layer 5a: Enodes of City Hall/Karl Storz
# *****************************
chk_enodes = enodes[enodes.subgraph==sx]
chk_enodes.to_pickle(int_data_dir / 'CHKS_nodes.pkl')

# Edges of the subgraph
sedge_df = nx.to_pandas_edgelist(S[sx])

# *****************************
# Layer 5b: DRPEP LineStrings of City Hall/Karl Storz
# *****************************
enodes_chks = enodes[enodes.subgraph==sx]
chks_lines = geopandas.GeoDataFrame(sedge_df,geometry=sedge_df['geometry'],crs="EPSG:2955")
chks_lines = chks_lines.drop('branch',axis=1)
chks_lines.to_pickle(int_data_dir / 'CHKS_lines.pkl')

# *****************************
# Layer 5c: Direct lines connecting enodes of City Hall/Karl Storz
# *****************************
directlines = []
p = nx.get_node_attributes(S[sx],'pos')
for nodes in S[sx].edges:
    nor1, east1 = p[nodes[0]][0], p[nodes[0]][1]
    nor2, east2 = p[nodes[1]][0], p[nodes[1]][1]
    directlines.append(LineString([[nor1,east1],[nor2,east2]]))
dl = geopandas.GeoSeries(directlines,crs="EPSG:2955")
    
chks_direct = chks_lines
chks_direct = chks_direct.set_geometry(dl)
chks_direct.to_pickle(int_data_dir / 'CHKS_direct_lines.pkl')


#%% Plot the DRPEP lines, blobs, and electrical nodes
# m = gdf.explore(column='randc',cmap='gist_rainbow',legend=False,
#                 name="DRPEP Line Sections")


# Step 0: Note some important Places of Interest
m = poi.explore(color='green',marker_type='marker', show=False,
                name="Step 0: Note Points of Interest")

# Step 1: Show DRPEP Line Segments
#gdf.explore(m=m,name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=3))
# gdf.explore(m=m,column='randc',cmap='gist_rainbow',legend=False,
#             name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=3))
gdf.explore(m=m,color='blue',legend=False, show=False,
            name="Step 1: DRPEP Line Sections",style_kwds=dict(weight=2))


# Step 2: Find Endpoints
pts.explore(m=m,color='blue',marker_kwds=dict(radius=2),show=False,
               name="Step 2: LineString endpoints")


# Step 3: Blobs
blobs.explore(m=m,color='green',marker_type='circle',
              style_kwds=dict(fillOpacity=0.2),show=False,
              name="Step 3: Combine very-near endpoints into 'blobs'")

# Step 4: Electrical nodes with colors
enodes.explore(m=m,column='randc',cmap='prism',marker_kwds=dict(radius=4),
                legend=False,style_kwds=dict(fillOpacity=1.0),show=False,
                name="Step 4: Infer Electrical Nodes (colored by sub-network)")


# Step 5a: Highlight City Hall/ Karl Storz
chks_lines.explore(m=m,color='red',marker_kwds=dict(radius=7), show=False,
                legend=False,style_kwds=dict(fillOpacity=1.0,weight=3),
                name="Step 5a: Focus on the City Hall/ Karl Storz Subgraph")


# 5b: CHKS direct paths "spider web"
chks_direct.explore(m=m,color='purple',marker_kwds=dict(radius=4),
                legend=False,style_kwds=dict(fillOpacity=1.0,weight=4),
                name="Step 5b: Cleaner Map CHKS Subgraph")


# 5c: CHKS end nodes
chk_enodes.explore(m=m,color='black',marker_kwds=dict(radius=4),
                legend=False,style_kwds=dict(fillOpacity=1.0), 
                name="Step 5c: Electrical Nodes of CHKS Subgraph")

folium.LayerControl().add_to(m)
m.save(maps_dir /'Map_Steps.html')



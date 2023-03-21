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
import networkx as nx
import geopandas
from shapely.geometry import Point,LineString

from mvprofessor.config import int_data_dir

def get_endpoints(gdf_linestrings):
    '''
    Parameters
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


def make_blobs(gdf_points, buffer_radius):
    '''
    Buffer points and combine any overlapping areas into "blobs"
    
    Parameters
    ----------
    gdf_points: GeoDataFrame 
            Endpoints of various linestrings
    buffer_radius: float or int
            Distance (in meters) for buffer ('halos')

    Returns
    -------
    "blobs", a geodataframe of the combined polygons

    '''
    
    pts = gdf_points[['geometry']] # drop all other fields

    halos = pts.copy()
    halos['geometry'] = halos['geometry'].buffer(buffer_radius)
    
    halos = pts.copy()
    halos['geometry'] = halos['geometry'].buffer(buffer_radius)
    
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
    #blobs.to_pickle(int_data_dir/'blobs.pkl')
    
    return blobs
    
    
def tree_builder(lines,blobs,startpoint,verbose=False):
    '''
    Tree building algorithm inspired by a classic depth-first search 
    (DFS) tree traversal.
    
    Beginning from a root node, the inner "while" loop will conduct a DFS
    tree traversal to connect all the line segments sharing common "blobs"
    ("blobs" are buffered endpoints of each line segment, combined into polygons
    where the buffers overlap).
    
    The outer "while" loop re-seeds the DFS algorithm using a random blob from
    among the non-yet-connected blobs. This is necessary because the input line 
    segments (GIS data) may be imprecise, i.e., two endpoints may be electrially
    connected but separated geographically by more than the 2x buffer radius. 
    The opposite can also be true, where two points are close but not necessarily
    electrically connected. 

    Parameters
    ----------
    lines : GeoDataFrame in which geometry is shapely.LineString
        This layer is the DRPEP linestrings
    
    blobs : GeoDataFrame in which geometry is shapely.Polygon
        "Blobs" are irregular polygons created by buffering the endpoints
        of the linestrings in the lines layer and spatially joining the 
        buffers where they overlap.
    
    startpoint : shapely.point
        The blob closest to "startpoint" will be the root node when for the 
        Depth First Search algorithm.

    Returns
    -------
    G - a networkx.Graph containing the nodes and edges of the inferred
    electrical network.

    '''


    
    # Identify root from among the blobs
    root_idx = blobs.sindex.nearest(startpoint)[1][0] #index to nearest blob from IVSS
    root_blob = blobs.iloc[root_idx]['geometry'] # a shapely.Polygon
    root_pt= root_blob.representative_point() #shapely.Point for pos arg to nx node
    
    
    # Initiate graph and add first point
    G = nx.Graph()
    G.add_node(root_idx,
               kv=16,
               phases=3,
               inservice=True,
               pos=root_pt.coords[0],
               blob=root_blob)
    
    blobs.loc[root_idx,'powered']=1 # Mark root node as powered
    
    # These are used for the DFS iteration
    frontier = [root_idx] # initiate frontier with the root node
    lines['explored'] = 0
    lines['leaf'] = 0
    explored = []
    
    # outer loop: re-seed the DFS algorithm if the network is discontinous
    while not np.all(blobs['powered']):
        if len(frontier)==0:
            
            powered_blobs = blobs[blobs['powered']==1]
            unpowered_blobs = blobs[blobs['powered']==0]
            if verbose:
                print('\n ----------------------')
                print("reinit with blob {}".format(blobs[blobs['powered']==0].iloc[0]['blob_idx']))
            reinit_blob = blobs[blobs['powered']==0].iloc[0]['geometry']
            reinit_pt = reinit_blob.representative_point()
            
            frontier.append(blobs[blobs['powered']==0].iloc[0]['blob_idx'])
            
            #G.add_node(frontier[0],pos=reinit_pt.coords[0],blob=reinit_blob)
            G.add_node(frontier[0],
                       kv=16,
                       phases=3,
                       inservice=True,
                       pos=reinit_pt.coords[0],
                       blob=reinit_blob)
            blobs.loc[frontier[0],'powered']=1
    
        # inner loop: DFS traversal of node connected by line segments
        while len(frontier)>0:
            current_node = frontier.pop(-1) # for DFS, frontier is a STACK (LIFO)
            
            # Find segments which connect to the current blob
            blob = G.nodes[current_node]['blob']
            branches = lines.loc[lines.intersects(blob,align=True)] # returns a dataframe
            branches = branches[branches.explored !=1]  
            
                
            # Each branch (linestring) has exactly two endpoints (boundaries)
            # Find which endpoint is within the buffer, and which is the next node
            for idx,branch in branches.iterrows():
                
                pt0 = Point(branch.geometry.coords[0])
                pt1 = Point(branch.geometry.coords[-1])
                
                if blob.covers(pt0):
                    new_point = pt1
                elif blob.covers(pt1):
                    new_point = pt0
                else:
                    # to-do: this algorithm fails when a frontier line cross
                    # an unpowered line
                    pass 
                    #newpoint=pt0
                    
                new_blob = blobs[blobs.covers(new_point)]
                        
                # Add the new node to the graph and to the frontier
                G.add_node(new_blob.index[0], 
                           kv=16,
                           phases=3,
                           inservice=True,
                           pos=(new_blob.representative_point().iloc[0].coords[0]),
                           blob=new_blob.iloc[0]['geometry'],
                           secids=[idx])
                
                # The DFS algorithm will revisit this point
                frontier.append(new_blob.index[0]) 
                
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
                lines.loc[idx,'explored'] = 1
                blobs.loc[new_blob.index,'powered']=1
                if verbose:
                    print("Just Powered: {}".format(new_blob.index[0]))    
    
    
    return G
    
    
def make_enodes(G):
    '''
    Given a Graph representation of a network, return a pandas.DataFrame
    containing all the enodes, flagged by their subgraph

    Parameters
    ----------
    G : networkx.Graph
        Graph representation of an electrical network

    Returns
    -------
    enodes - a GeoDataFrame where "geometry" are shapely.Points of the 
    electrical nodes of the graph
    
    '''
    
    
    pos = nx.get_node_attributes(G,'pos')
    enode_id = list(pos.keys())
    x,y = list(zip(*list(pos.values())))

    enode_pts = geopandas.GeoSeries.from_xy(x,y,crs="EPSG:2955")
    enodes = geopandas.GeoDataFrame({'enode_id':enode_id},geometry=enode_pts,crs="EPSG:2955")
    enodes = enodes.set_index('enode_id')

    # Flag the electrical nodes by their subgraph
    # S is a list of subgraphs (nx.graph objects)
    S = [G.subgraph(c).copy() for c in nx.connected_components(G)]

    # add a random number column for coloring
    enodes['subgraph'] = 0
    enodes['randc'] = 0
    rng = default_rng()
    r = rng.choice(len(S)*2,size=len(S),replace=False)
    for i,Si in enumerate(S):
        enodes.loc[enodes.index.isin(list(Si.nodes)),'subgraph']=i
        enodes.loc[enodes.index.isin(list(Si.nodes)),'randc']=r[i]
            
    return enodes

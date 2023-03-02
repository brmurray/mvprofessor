
"""
Ingest_ICA_Data.py

Convert the ICA data (provided as a csv) to a Pandas dataframe
Save it to the intermediate data directory

"""

import numpy as np
from numpy.random import default_rng
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import geopandas
import folium
from shapely.geometry import Point
import chardet

from mvprofessor.config import raw_data_dir, int_data_dir
from mvprofessor.custom_funcs import get_endpoints, make_blobs

'''
ICA Field Definitions and Column in the Pandas Dataframe
DRPEP Interactive User Guide Reference:
    https://drpep.sce.com/drpep/drpep-interactive-user-guide/index.html#/lessons/CFSbzN585ktG1zCQB_KVMlmEQNuWD6iQ


--- Data Definitions ---
0. Month
1. Hour
2. Load Profile Type - max or min constraint?

--- Generation Constraints --- 
3. Uniform Generation Op Flexibility
    []
    
4. Uniform Generation
    []
    
5. Solar PV Operational Flexibility (kW)
    []
    
6. Solar PV (kW)
    []
    
7. Thermal (kW)
    Amount of generation that can be installed without causing THERMAL
    overloads anywhere in the system

8. SSV (kW)
    Amount of generation that can be installed without violating Rule 2 
    (+/-5% of nom. Steady State Volt.)
    
9. Voltage Fluctuation (kW)
    Amount of generation that can be installed without causing 3% variation
    in voltage

10.Protection (kW)
    Amount of generation that can be installed without causing the protective
    relays to NOT see end-of-line

11.ICA Operational Flexibility (kW)
    Amount of generation that can be installed without causing REVERSE POWER 
    FLOW at the substation or at ANY SCADA device

--- Load Constraints --- 
12.Uniform Load (kW)
    

13.Thermal Load (kW)
    Amount of load that can be installed without causing thermal overloads 
    anywhere in the system
    
14.Volt Variation Load (kW)
    Amount of load that can be installed without causing 3% variation in voltage

15.SSV Load (kW)
    Amount of load that can be installed without violating Rule 2 
    (+/-5% of nominal Steady State Voltage)   
    
-- Columns Defined Later (in this script)
16. Node_ID


'''

# Import the straight-from-DRPEP/ICA data file
phrs = pd.read_csv(raw_data_dir / "PROFESSOR_16KV_BH.csv",encoding = 'unicode_escape', engine ='python')

# Drop Node IDs that don't follow the convention
def clean_nodeid(nodeid_str):
    try: 
        return int(nodeid_str)
    except:
        return 999

phrs['Node_ID'] = phrs['Node ID'].apply(lambda x: clean_nodeid(x))
bad_nodeid = len(phrs[phrs['Node_ID']==999])
phrs = phrs[phrs['Node_ID']!=999]
phrs = phrs.drop(['Node ID'],axis=1)
print("Dropped {} rows for bad Node ID".format(bad_nodeid))

# Drop any nodes not in the Professor circuit
bad_circuit = len(phrs[phrs.iloc[:,0]!='PROFESSOR'])
phrs = phrs[phrs.iloc[:,0]=='PROFESSOR']
phrs = phrs.drop(columns=phrs.columns[0])
print("Dropped {} rows for bad circuit".format(bad_circuit))

# Report table contents
unique_nodeIDs = len(np.unique(phrs['Node_ID']))
total_rows = len(phrs)
rows_per_node = total_rows/unique_nodeIDs
print('{} total rows \n'.format(total_rows),
      '{} unique Node_ID \n'.format(unique_nodeIDs),
      '{} rows per node'.format(rows_per_node))

phrs.columns=phrs.columns.str.strip().str.replace(' ','_')

# save to pickle (*.pkl) for easier access
phrs.to_pickle(int_data_dir / 'Prof_ICA_data.pkl')




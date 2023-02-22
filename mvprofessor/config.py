# -*- coding: utf-8 -*-
"""
config.py


"""

from pathlib import Path  # pathlib is seriously awesome!

raw_data_dir = Path('/Users/Umberto/Documents/GitHub/mvprofessor/data/raw')
raw_data_path = raw_data_dir / 'professor.geojson'

intermediate_data_dir = Path('/Users/Umberto/Documents/GitHub/mvprofessor/data/intermediate')
gdf_pkl_path = intermediate_data_dir / 'professor.pkl'

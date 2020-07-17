import pandas as pd
import os
import argparse
import gc

import numpy as np


parser = argparse.ArgumentParser()

parser.add_argument('--county_level_file_path', 
    type=str, 
    help='File for county level Rts',
    default='../data/rt_county/rt_county.csv'
)

parser.add_argument('--state_level_file_path', 
    type=str, 
    help='File for state level Rts',
    default='../data/rt_state/rt_state.csv'
)

parser.add_argument('--output_level_file_path', 
    type=str, 
    help='Path for cleaned up county level Rts',
    default='../data/rt_county/rt_county.csv'
)


if __name__ == '__main__':
    
    args = parser.parse_args()

    RT_COUNTY_PATH = args.county_level_file_path
    RT_STATE_PATH = args.state_level_file_path

    OUTPUT_PATH = args.output_level_file_path
    
    rt_county = pd.read_csv(RT_COUNTY_PATH, index_col='Unnamed: 0')
    rt_state = pd.read_csv(RT_STATE_PATH, index_col='Unnamed: 0')

    rt_comb = pd.merge(
        rt_county,
        rt_state,
        how='left',
        left_on=['state','date'],
        right_on=['region','date']
    ).drop_duplicates()

    for col in rt_comb.filter(regex='_x').columns.tolist():
        rt_comb[col] = rt_comb[col].fillna(rt_comb[col.replace('_x','_y')])
        rt_comb = rt_comb.rename(columns={col:col.replace('_x','')})
        rt_comb = rt_comb.drop(col.replace('_x','_y'),axis=1)

    rt_comb.to_csv(OUTPUT_PATH)
    
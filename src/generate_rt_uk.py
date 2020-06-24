
'''
python generate_rt.py --state_level_only --filtered_states DE NY  --output_path='../data/rt_state/'
'''
# For some reason Theano is unhappy when I run the GP, need to disable future warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import os
import requests
import pymc3 as pm
import pandas as pd
import numpy as np
import theano
import theano.tensor as tt
import theano.tensor.slinalg

from matplotlib import pyplot as plt
from matplotlib import dates as mdates
from matplotlib import ticker

from datetime import date
from datetime import datetime

import os
from datetime import date
from datetime import timedelta
import time

import plotly.graph_objects as go
import plotly.express as px

from tqdm import tqdm
import gc
import sys
sys.path.append('../')

from src.utils.load_data import load_population_df, load_confirmed_cases_df 
from src.utils.p_delay_default import P_DELAY

from src.utils.load_data import load_uk_population_df
from src.utils.load_data import load_uk_confirmed_cases_df

from generate_rt import create_case_pop_df
from generate_rt import calc_p_delay, confirmed_to_onset, adjust_onset_for_right_censorship
from generate_rt import df_from_model, create_and_run_model, regional_rt_model

import argparse
import subprocess
import multiprocessing

from src.utils.p_delay_default import P_DELAY

parser = argparse.ArgumentParser()

parser.add_argument('--county_level_case_history', 
    type=str, 
    help='File Containing Case History by Date/Day',
    default='../data/uk/cases_uk.csv'
)
parser.add_argument('--county_level_population', 
    type=str,
    help='File Containing the Populations for each county',
    default='../data/uk/population.xls'
)
parser.add_argument('--onset_path', 
    type=str, 
    help='Directory for Onset vs Confirmation File Paths',
    default='../data/misc/latestdata.csv'
)
parser.add_argument('--output_path', 
    type=str, 
    help='Output directory for R(t) calculations',
    default='../data/uk/rt_county/'
)
parser.add_argument('--filtered_states', 
    nargs='*',
    help='List of States to calculate R(t) values for',
    required=False,
    default=None
)
parser.add_argument('--state_level_only', 
    help='If added, aggregations will be performed only at the state level',
    action='store_true'
)


def create_case_pop_df_uk(
                population_file_path='../data/uk/population.xls', 
                map_path='../data/uk/ulta_region_mapping.csv',
                cum_cases_col='totalLabConfirmedCases',
                date_col='date',
                pop_fips_col='areaCode',
                case_fips_col='areaCode',
                case_county_col='county',
                case_state_col='state'
    
      ):

    # Case Data at county level
    uk_cases_df = load_uk_confirmed_cases_df()
    uk_cases_df = uk_cases_df.rename(columns={'areaName':'county'})

    mapping_df = pd.read_csv(map_path)
    ltla_region_map = mapping_df[['LAD18CD','RGN18NM']]\
        .drop_duplicates().set_index('LAD18CD').to_dict()['RGN18NM']

    uk_cases_df['State'] = uk_cases_df['areaCode'].map(ltla_region_map).str.upper()
    uk_cases_df['state'] = uk_cases_df['areaCode'].map(ltla_region_map)
    uk_cases_df = uk_cases_df.rename(columns={'specimenDate':'date'})
    uk_cases_df['date'] = pd.to_datetime(uk_cases_df['date'])

    # POpulation Data at county level
    uk_pop_df = load_uk_population_df(population_df_path=population_file_path)

    ##############################################################

    cases_pop_df = pd.merge(
        left=uk_cases_df,
        right=uk_pop_df.rename(columns={pop_fips_col:case_fips_col}),
        left_on=case_fips_col,
        right_on=case_fips_col,
        how='left'
    ).drop_duplicates()


    cases_pop_df['County_State'] = cases_pop_df[case_county_col].str.title()\
                + ' ' + cases_pop_df[case_state_col].str.upper()
    # cases_pop_df['active_cases'] = cases_pop_df['cases'] - cases_pop_df['cases'].shift(14).fillna(0)
    # cases_pop_df['new_cases'] = cases_pop_df['cases'].diff()

    ##############################################################


    append_list = []
    for n, g in cases_pop_df.groupby('County_State'):
        g.sort_values(date_col, inplace=True)
        g['new_cases'] = g[cum_cases_col].diff().rolling(7,
            win_type='gaussian',
            min_periods=1,
            center=True).mean(std=2).round()
        g['active_cases'] = g[cum_cases_col] - g[cum_cases_col].shift(14).fillna(0)
        append_list.append(g)
    cases_pop_df = pd.concat(append_list)

    del append_list

    cases_pop_df[case_state_col] = cases_pop_df[case_state_col].str.upper()

    return cases_pop_df



if __name__ == '__main__':

    args = parser.parse_args()

    CASES_PATH = args.county_level_case_history
    POPULATION_PATH = args.county_level_population
    OUTPUT_PATH = args.output_path
    FILTERED_STATES = args.filtered_states
    STATE_LEVEL = args.state_level_only

    ONSET_CONFIRM_PATH = args.onset_path

    p_delay = P_DELAY

    if not os.path.exists(OUTPUT_PATH):
        os.mkdir(OUTPUT_PATH)

    cases_pop_df = create_case_pop_df_uk(population_file_path=POPULATION_PATH)

    if FILTERED_STATES is None:
        FILTERED_STATES = cases_pop_df['State'].unique().tolist()

    err_list_overall = []
    
    if STATE_LEVEL:
        agg_level = 'state'
        label = 'state'
        output_file = OUTPUT_PATH+'rt_state.csv'
    else:
        agg_level = 'County_State'
        label = 'county'
        output_file = OUTPUT_PATH+'rt_county.csv'

    print (f"DEBUGGING: {FILTERED_STATES}")

    err_list_overall = []
    for i, STATE in enumerate(FILTERED_STATES):
        
            print (f'{STATE} : {i+1} of {len(FILTERED_STATES)} states...')
            subset_df = cases_pop_df[cases_pop_df['State'] == STATE]

            print(f'DEBUGGING: {subset_df.shape}')
            if (subset_df.shape[0]) == 0:
                err_list_overall.append(STATE)
                print (f'{STATE} appears to be missing from the data set.')

            results, err_list = regional_rt_model(subset_df, 
                    case_col='new_cases', 
                    region_col=agg_level,
                    output_path=OUTPUT_PATH + f'rt_{label}_{STATE}.csv'
                    )

            err_list_overall = err_list_overall + err_list

    gc.collect()

    print ('Completed....')


    

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

import argparse
import subprocess
import multiprocessing


parser = argparse.ArgumentParser()

parser.add_argument('--county_level_case_history', 
    type=str, 
    help='File Containing Case History by Date/Day',
    default='../data/county_level/covid_confirmed_usafacts.csv'
)
parser.add_argument('--county_level_population', 
    type=str,
    help='File Containing the Populations for each county',
    default='../data/misc/CountyHealthRankings19.csv'
)
parser.add_argument('--onset_path', 
    type=str, 
    help='Directory for Onset vs Confirmation File Paths',
    default='../data/misc/latestdata.csv'
)
parser.add_argument('--output_path', 
    type=str, 
    help='Output directory for R(t) calculations',
    default='../data/rt_county/'
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


def calc_p_delay(onset_confirm_path):
    
    if not os.path.exists(onset_confirm_path):
        subprocess.call('./get_rt.sh')

    # Load the patient CSV
    patients = pd.read_csv(
        onset_confirm_path,
        parse_dates=False,
        usecols=[
            'date_confirmation',
            'date_onset_symptoms'],
        low_memory=False)

    patients.columns = ['Onset', 'Confirmed']

    # There's an errant reversed date
    patients = patients.replace('01.31.2020', '31.01.2020')

    # Only keep if both values are present
    patients = patients.dropna()

    # Must have strings that look like individual dates
    # "2020.03.09" is 10 chars long
    is_ten_char = lambda x: x.str.len().eq(10)
    patients = patients[is_ten_char(patients.Confirmed) & 
                        is_ten_char(patients.Onset)]

    # Convert both to datetimes
    patients.Confirmed = pd.to_datetime(\
        patients.Confirmed, format='%d.%m.%Y', errors='coerce')
    patients.Onset = pd.to_datetime(\
        patients.Onset, format='%d.%m.%Y', errors='coerce')
    
    # Only keep if both values are present
    patients = patients.dropna()

    # Only keep records where confirmed > onset
    patients = patients[patients.Confirmed >= patients.Onset]
    
    

    # Calculate the delta in days between onset and confirmation
    delay = (patients.Confirmed - patients.Onset).dt.days

    # Convert samples to an empirical distribution
    p_delay = delay.value_counts().sort_index()
    new_range = np.arange(0, p_delay.index.max()+1)
    p_delay = p_delay.reindex(new_range, fill_value=0)
    p_delay /= p_delay.sum()
    
    del patients

    return p_delay

def confirmed_to_onset(confirmed, p_delay):
    '''
    Function used to model the gap between test confirmation
    and probabilistic onset of Covid Virus.

    Inputs
    ------

    confirmed: pd.Series
        pandas Series of confirmed timestamps (as index) and positive cases 
    '''    
    assert not confirmed.isna().any()
    
    # Reverse cases so that we convolve into the past
    convolved = np.convolve(confirmed[::-1].values, p_delay)

    # Calculate the new date range
    dr = pd.date_range(end=confirmed.index[-1],
                       periods=len(convolved))

    # Flip the values and assign the date range
    onset = pd.Series(np.flip(convolved), index=dr)
    
    return onset


def adjust_onset_for_right_censorship(onset, p_delay):
    cumulative_p_delay = p_delay.cumsum()
    
    # Calculate the additional ones needed so shapes match
    ones_needed = len(onset) - len(cumulative_p_delay)
    padding_shape = (0, ones_needed)
    
    # Add ones and flip back
    cumulative_p_delay = np.pad(
        cumulative_p_delay,
        padding_shape,
        constant_values=1)
    cumulative_p_delay = np.flip(cumulative_p_delay)
    
    # Adjusts observed onset values to expected terminal onset values
    adjusted = onset / cumulative_p_delay
    
    return adjusted, cumulative_p_delay

class MCMCModel(object):
    
    def __init__(self, region, onset, cumulative_p_delay, window=50):
        
        # Just for identification purposes
        self.region = region
        
        # For the model, we'll only look at the last N
        self.onset = onset.iloc[-window:]
        self.cumulative_p_delay = cumulative_p_delay[-window:]
        
        # Where we store the results
        self.trace = None
        self.trace_index = self.onset.index[1:]

    def run(self, chains=1, tune=3000, draws=1000, cores=4 ,target_accept=.95):

        with pm.Model() as model:

            # Random walk magnitude
            step_size = pm.HalfNormal('step_size', sigma=.03)

            # Theta random walk
            theta_raw_init = pm.Normal('theta_raw_init', 0.1, 0.1)
            theta_raw_steps = pm.Normal('theta_raw_steps', shape=len(self.onset)-2) * step_size
            theta_raw = tt.concatenate([[theta_raw_init], theta_raw_steps])
            theta = pm.Deterministic('theta', theta_raw.cumsum())

            # Let the serial interval be a random variable and calculate r_t
            serial_interval = pm.Gamma('serial_interval', alpha=6, beta=1.5)
            gamma = 1.0 / serial_interval
            r_t = pm.Deterministic('r_t', theta/gamma + 1)

            inferred_yesterday = self.onset.values[:-1] / self.cumulative_p_delay[:-1]
            
            expected_today = inferred_yesterday * self.cumulative_p_delay[1:] * pm.math.exp(theta)

            # Ensure cases stay above zero for poisson
            mu = pm.math.maximum(.1, expected_today)
            observed = self.onset.round().values[1:]
            cases = pm.Poisson('cases', mu=mu, observed=observed)

            self.trace = pm.sample(
                chains=chains,
                tune=tune,
                draws=draws,
                cores=cores,
                target_accept=target_accept)
            
            return self
    
    def run_gp(self):
        with pm.Model() as model:
            gp_shape = len(self.onset) - 1

            length_scale = pm.Gamma("length_scale", alpha=3, beta=.4)

            eta = .05
            cov_func = eta**2 * pm.gp.cov.ExpQuad(1, length_scale)

            gp = pm.gp.Latent(mean_func=pm.gp.mean.Constant(c=0), 
                              cov_func=cov_func)

            # Place a GP prior over the function f.
            theta = gp.prior("theta", X=np.arange(gp_shape)[:, None])

            # Let the serial interval be a random variable and calculate r_t
            serial_interval = pm.Gamma('serial_interval', alpha=6, beta=1.5)
            gamma = 1.0 / serial_interval
            r_t = pm.Deterministic('r_t', theta / gamma + 1)

            inferred_yesterday = self.onset.values[:-1] / self.cumulative_p_delay[:-1]
            expected_today = inferred_yesterday * self.cumulative_p_delay[1:] * pm.math.exp(theta)

            # Ensure cases stay above zero for poisson
            mu = pm.math.maximum(.1, expected_today)
            observed = self.onset.round().values[1:]
            cases = pm.Poisson('cases', mu=mu, observed=observed)

            self.trace = pm.sample(chains=1, tune=1000, draws=1000, target_accept=.8)
        return self


def df_from_model(model):
    
    r_t = model.trace['r_t']
    mean = np.mean(r_t, axis=0)
    median = np.median(r_t, axis=0)
    hpd_90 = pm.stats.hpd(r_t, credible_interval=.9)
    hpd_50 = pm.stats.hpd(r_t, credible_interval=.5)
        
    idx = pd.MultiIndex.from_product([
            [model.region],
            model.trace_index
        ], names=['region', 'date'])
        
    df = pd.DataFrame(data=np.c_[mean, median, hpd_90, hpd_50], index=idx,
                 columns=['mean', 'median', 'lower_90', 'upper_90', 'lower_50','upper_50'])
    return df

def create_and_run_model(name, 
            county_state,
            case_col='new_cases', 
            cores=4,
            chains=1
            ):
    confirmed = county_state[case_col].dropna()
    onset = confirmed_to_onset(confirmed, p_delay)
    adjusted, cumulative_p_delay = adjust_onset_for_right_censorship(onset, p_delay)
    return MCMCModel(name, onset, cumulative_p_delay).run(chains=chains, cores=cores)


def create_case_pop_df(
                case_file_path, 
                population_file_path, 
                cum_cases_col='cases',
                date_col='date',
                pop_fips_col='fips',
                case_fips_col='countyFIPS',
                case_county_col='County Name',
                case_state_col='state'
    
      ):
    # Population Data at county level
    pop_df = load_population_df(population_file_path)
    print(pop_df.shape)

    # COVID Cases
    cases_df = load_confirmed_cases_df(case_file_path)
    print(cases_df.shape)


    ##############################################################

    cases_pop_df = pd.merge(
        left=cases_df,
        right=pop_df.rename(columns={pop_fips_col:case_fips_col}),
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
        g['new_cases'] = g[cum_cases_col].diff()
        g['active_cases'] = g[cum_cases_col] - g[cum_cases_col].shift(14).fillna(0)
        append_list.append(g)
    cases_pop_df = pd.concat(append_list)
    del append_list
    return cases_pop_df


def regional_rt_model(subset_df, 
                  region_col='County_State',
                  date_col='date',
                  case_col='new_cases',
                  output_path=None
                 ):

    
    ## Assuming no duplicates
    ## Consider the scenario where we intend to calculate these results 
    ## at a state level, instead of at the county level.
    
    subset_df = subset_df.groupby([region_col, date_col])\
        [case_col].sum().reset_index().sort_values(date_col)
    
    ######################################
    
    models = {}
    err_list = []
    NUM_REGIONS = subset_df[region_col].nunique()
    j = 0

    cores = multiprocessing.cpu_count()
    for region, grp in subset_df.set_index(date_col).groupby(region_col):
        
        j = j+1
        print (f'\t\t{j} of {NUM_REGIONS} regions in current subset...')
        
        
        try:
            if region in models:
                print(f'Skipping {region}, already in cache')
                continue

            models[region] = create_and_run_model(
                region, 
                grp, 
                case_col,
                cores=cores
                )
        except:
            err_list.append(region)

    gc.collect()

    ######################################
    
    # Check to see if there were divergences
    n_diverging = lambda x: x.trace['diverging'].nonzero()[0].size
    divergences = pd.Series([n_diverging(m) for m in models.values()], index=models.keys())
    has_divergences = divergences.gt(0)

    # print('Diverging states:')
    # display(divergences[has_divergences])

    # Rerun counties with divergences
    for region, n_divergences in divergences[has_divergences].items():
        models[region].run(chains=2)

    gc.collect()
    
    ######################################

    results = None

    for region, model in models.items():

        df = df_from_model(model)

        if results is None:
            results = df
        else:
            results = pd.concat([results, df], axis=0)

    ##################################

    if (output_path is not None): 
        if (results is not None):
            results.to_csv(output_path)
        else:
            err_list.append(region)

    return results, err_list 


if __name__ == '__main__':

    args = parser.parse_args()

    CASES_PATH = args.county_level_case_history
    POPULATION_PATH = args.county_level_population
    OUTPUT_PATH = args.output_path
    FILTERED_STATES = args.filtered_states
    STATE_LEVEL = args.state_level_only

    ONSET_CONFIRM_PATH = args.onset_path

    p_delay = calc_p_delay(ONSET_CONFIRM_PATH)

    if not os.path.exists(OUTPUT_PATH):
        os.mkdir(OUTPUT_PATH)

    cases_pop_df = create_case_pop_df(CASES_PATH, POPULATION_PATH)

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

        del results
        gc.collect()

    print ('Completed....')

    print ('Combining Files...')

    ## Combining them all
    df_list = []
    for f in map(lambda x: OUTPUT_PATH+x, os.listdir(OUTPUT_PATH)):
        if f'rt_{label}_' in f:
            df_list.append(pd.read_csv(f))
    rt_df = pd.concat(df_list)

    if not STATE_LEVEL:
        fips_mapping = cases_pop_df[['countyFIPS', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['countyFIPS']
        state_mapping = cases_pop_df[['state', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['state']
        county_mapping = cases_pop_df[['county', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['county']

    
        rt_df['countyFIPS'] = rt_df['region'].map(fips_mapping)
        rt_df['state'] = rt_df['region'].map(state_mapping)
        rt_df['county'] = rt_df['region'].map(county_mapping)


    rt_df.to_csv(output_file)
    del rt_df
    gc.collect()    

    
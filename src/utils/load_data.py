'''
helper functions
'''
import yaml
import pandas as pd
import requests
import numpy as np


### LOADING DATA/INPUTS ###


def load_population_df(population_df_path):
    pop_df = pd.read_csv(population_df_path)
    pop_df = pop_df[['COUNTY', 'FIPS','STATE', 'POPULATION']]
    pop_df['COUNTY'] = pop_df['COUNTY'].str.lower()
    pop_df.columns = [x.lower() for x in pop_df.columns]
    return pop_df

def load_confirmed_cases_df(confirmed_cases_df_path):
    raw_cases_df = pd.read_csv(confirmed_cases_df_path)
    cases_df = pd.melt(raw_cases_df,
                    id_vars=['countyFIPS', 'County Name', 'State', 'stateFIPS'],
                    var_name='date',
                    value_name='cases')
    cases_df['date'] = pd.to_datetime(cases_df['date'])
    return cases_df

def load_confirmed_deaths_df(confirmed_deaths_df_path):
    raw_deaths_df = pd.read_csv(confirmed_deaths_df_path)
    deaths_df = pd.melt(raw_deaths_df,
                    id_vars=['countyFIPS', 'County Name', 'State', 'stateFIPS'],
                    var_name='date',
                    value_name='deaths')
    deaths_df['date'] = pd.to_datetime(deaths_df['date'])
    return deaths_df

def load_announcements_df(announcements_df_path):
    announcements_df = pd.read_csv(announcements_df_path)
    shelter_cols = ['Stay at home order', 'Educational facilities closed', 'Non-essential services closed']
    for col in shelter_cols:
        announcements_df[col] = pd.to_datetime(announcements_df[col])
    return announcements_df



def fips_int_to_string(x):
    return '0' + str(x) if len(str(x)) == 4 else str(x)


def get_date_range(current_date, time_horizon):
    '''
    provides dates time_horizon days into the future
    + 1 accounts for current_date
    '''
    return pd.date_range(start = current_date, periods= time_horizon + 1, freq='D')

def get_weekly_results(raw_sim_results, date_range, quantile=.5, mean=False):
    weekly_df = pd.DataFrame(raw_sim_results)
    weekly_df.columns = date_range.values
    weekly_df = weekly_df.T.reset_index()
    if mean:
        weekly_df = weekly_df.groupby(pd.Grouper(key='index', freq='W-SUN')) \
                     .apply(lambda x: x.drop('index',axis=1) \
                                       .sum(axis=0) \
                                       .mean())
    else:
        weekly_df = weekly_df.groupby(pd.Grouper(key='index', freq='W-SUN')) \
                             .apply(lambda x: x.drop('index',axis=1) \
                                               .sum(axis=0) \
                                               .quantile(quantile))
    return weekly_df.iloc[:-1]

def get_county_avg_household_size():
    q = 'https://www.indexmundi.com/facts/united-states/quick-facts/json/average-household-size'
    r = requests.post(q)
    county_household = {int(data['FipsCode']):round(data['TotalAmount']) for data in r.json()['DataValues'] }
    return county_household


def load_uk_population_df(population_df_path):
    '''
    Parameters:
    -----------
    population_df_path : str

    Returns:
    ------------
    uk_pop_df : pd.DataFrame
    '''
    uk_pop_df = pd.read_excel(population_df_path, header=4, sheet_name='MYE2 - Persons')
    uk_pop_df = uk_pop_df[['Code', 'Name', 'All ages']].rename({'Code':'areaCode', 
                                                                'Name':'areaName', 
                                                                'All ages':'population'}, axis=1)
    uk_pop_df['areaName'] = uk_pop_df['areaName'].str.title()
    return uk_pop_df


def load_uk_confirmed_cases_df(
    case_address='https://coronavirus.data.gov.uk/downloads/json/coronavirus-cases_latest.json'):
    '''
    Parameters:
    -----------
    case_address : str

    Returns:
    ------------
    cases_df : pd.DataFrame
    '''
    # download data
    q = requests.get(case_address)
    raw_uk_case_df = pd.DataFrame(q.json()['ltlas'])
    # subset columns
    uk_case_df = raw_uk_case_df[['areaCode', 'areaName', 'specimenDate', 'totalLabConfirmedCases']]
    # format date type
    uk_case_df['specimenDate'] = pd.to_datetime(uk_case_df['specimenDate'])
    # get min/max case dates
    case_max_date = uk_case_df['specimenDate'].max()    
    case_min_date = uk_case_df['specimenDate'].min()
    # fill in missing dates
    cases_df = uk_case_df.groupby('areaCode') \
                         .apply(filling_missing_dates, min_date=case_min_date, max_date=case_max_date ) \
                         .reset_index(drop=True)
    return cases_df
                    

def filling_missing_dates(s, min_date=None, max_date=None, 
                          date_col='specimenDate', bfill_col_list=['areaCode','areaName'], 
                          val_col='totalLabConfirmedCases'):
    if (min_date is None) and (max_date is None):
        idx = pd.date_range(s[date_col].min(), s[date_col].max())
    else:
        idx = pd.date_range(min_date, max_date)
    s.index = pd.DatetimeIndex(s[date_col])
    s = s.reindex(idx)
    s[date_col] = s.index
    for col in bfill_col_list:
        s[col] = s[col].bfill()
        
    s[val_col].loc[(s[val_col].isna()) \
                   & (s[date_col]==min_date)] = 0
    s[val_col] = s[val_col].fillna(method='ffill')
    return s


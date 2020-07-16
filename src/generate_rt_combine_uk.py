import pandas as pd
import os
import argparse
import gc
import numpy as np

from generate_rt_uk import create_case_pop_df_uk

parser = argparse.ArgumentParser()

parser.add_argument('--files_path', 
    type=str, 
    help='Directory for R(t) calculations',
    default='../data/uk/rt_county/'
)

parser.add_argument('--state_level', 
    help='If added, implies aggregations are state level.',
    action='store_true'
)

parser.add_argument('--county_level_case_history', 
    type=str, 
    help='File Containing Case History by Date/Day',
    default='../data/county_level/covid_confirmed_usafacts.csv'
)
parser.add_argument('--county_level_population', 
    type=str,
    help='File Containing the Populations for each county',
    default='../data/uk/population.xls'
)


if __name__ == '__main__':
    
    args = parser.parse_args()

    CASES_PATH = args.county_level_case_history
    POPULATION_PATH = args.county_level_population
    
    OUTPUT_PATH = args.files_path
    STATE_LEVEL = args.state_level


    if STATE_LEVEL:
        label = 'state'
        output_file = OUTPUT_PATH+'rt_state.csv'
    else:
        label = 'county'
        output_file = OUTPUT_PATH+'rt_county.csv'

    cases_pop_df = create_case_pop_df_uk(POPULATION_PATH, cutoff=0)

    print ('Combining Files...')

    ## Combining them all
    df_list = []
    for f in map(lambda x: OUTPUT_PATH+x, os.listdir(OUTPUT_PATH)):
        if f'rt_{label}_' in f:
            df_list.append(pd.read_csv(f))
    rt_df = pd.concat(df_list)

    if not STATE_LEVEL:
        fips_mapping = cases_pop_df[['areaCode', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['areaCode']
        state_mapping = cases_pop_df[['state', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['state']
        county_mapping = cases_pop_df[['county', 'County_State']].drop_duplicates()\
            .set_index('County_State').to_dict()['county']

    
        rt_df['countyFIPS'] = rt_df['region'].map(fips_mapping)
        rt_df['state'] = rt_df['region'].map(state_mapping)
        rt_df['county'] = rt_df['region'].map(county_mapping)

        rt_df['date'] = pd.to_datetime(rt_df['date'], errors='coerce')
        DATE_LIST = np.sort(rt_df['date'].dropna().unique().tolist())

        cases_pop_df['date'] = pd.to_datetime(cases_pop_df['date'], errors='coerce')
        cases_pop_df = cases_pop_df.loc[cases_pop_df['date'].isin(DATE_LIST), :]

        rt_df = pd.merge(
            cases_pop_df[['countyFIPS','County_State','date', 'state', 'stateFIPS']],
            rt_df.drop('Unnamed: 0',axis=1),
            how='left',
            left_on=['County_State'],
            right_on=['region'],
        ).drop_duplicates()
        rt_df['date_y'] = pd.to_datetime(rt_df['date_y'].fillna(rt_df['date_x']))
        rt_df['region'] = rt_df['region'].fillna(rt_df['County_State'])
        rt_df = rt_df[rt_df['date_x']==rt_df['date_y']]
        for col in rt_df.filter(regex='_y').columns.tolist():
            rt_df = rt_df.drop(col,axis=1)
            rt_df = rt_df.rename(columns={col.replace('_y','_x'): col.replace('_y','')})

        rt_df = rt_df.sort_values(['countyFIPS','date'])

    rt_df.to_csv(output_file)
    del rt_df
    gc.collect()    

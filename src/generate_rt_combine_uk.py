import pandas as pd
import os
import argparse
import gc

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

    cases_pop_df = create_case_pop_df_uk(POPULATION_PATH)

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


    rt_df.to_csv(output_file)
    del rt_df
    gc.collect()    

#!/usr/bin/python

import pandas as pd
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('--county_level_population', 
    type=str,
    help='Donwloaded File Containing the Populations for each county',
    default='../../data/inputs/misc/CountyHealthRankings20.xlsx'
)
parser.add_argument('--output_path', 
    type=str,
    help='Output File Containing the Populations for each county',
    default='../../data/inputs/misc/CountyHealthRankings19.csv'
)

if __name__ == '__main__':

    args = parser.parse_args()

    DOWNLOADED_PATH = args.county_level_population
    OUTPUT_PATH = args.output_path
     
    xl_df = pd.read_excel(DOWNLOADED_PATH, sheet_name='Additional Measure Data', skiprows=1)#
    xl_df = xl_df.filter(regex='(?i)fips|county|state|population')
    xl_df = xl_df.rename(columns={col:col.upper() for col in xl_df.columns.tolist()})
    xl_df.to_csv(OUTPUT_PATH, index=False)
from utils.rt_plotting import set_up_defaults, \
    animate_country, animate_state,\
    map_rt, rt_live_error_plot,\
    rt_dashboard

import pandas as pd
import numpy as np
import geopandas as gp
import gc
import os
import argparse
import multiprocessing
from multiprocessing import Process, Queue, Pool, TimeoutError

from tqdm import tqdm

parser = argparse.ArgumentParser()

parser.add_argument('--country_name', 
    type=str, 
    help='Name of Country in analysis',
    default='UK'
)
parser.add_argument('--rt_county_file_path', 
    type=str,
    help='File Containing calculated Rt values for each county',
    default='../data/uk/rt_county/rt_county.csv'
)
parser.add_argument('--output_dir', 
    type=str,
    help='File Containing calculated Rt values for each county',
    default='../output/'
)

def state_map(st, path):
    print (path)
    # gc.collect()
    fig = map_rt(
            'county',
            st,
            'mean',
            True,
            '../data/misc/state_geojsons/',
            7,
            path
        )
    return path 


def add_js_header(text):
    text = text.replace('<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" />',
         '''<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" />
            <script type="text/javascript">
                function goToNewPage()
                {
                    var url = document.getElementById('list').value;
                    if(url != 'none') {
                        window.location = url;
                    }
                }
            </script>
        ''')

    return text
    
def dropdown_col(text, joined_list):
    
    li_str = '\n\t\t\t'.join(joined_list)
    text = text.replace('<body>',
            f'''
            <body>

        <form>
            <select name="list" id="list" accesskey="target">
            {li_str}
            
            </select>
            <input type=button value="Go" onclick="goToNewPage()" />
            </form>

    ''') 

    return text
def add_style_header(text):

    text = text.replace('<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" />',
         '''<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        <style>
                ul {
                list-style-type: none;
                margin: 0;
                padding: 0;
                overflow: hidden;
                background-color: #212121;
                }

                body{
                font-family: 'Nunito', sans-serif;
                }

                li {
                float: left;
                }

                li a {
                display: block;
                color: #ECEFF1;
                text-align: center;
                padding: 14px 16px;
                text-decoration: none;
                }

                li a:hover:not(.active) {
                background-color: #A8C3B3;
                }

                .active {
                background-color: #508668;
                font-family: 'Nunito';
                font-weight: 700;
                }
                .modebar{
                display: none !important;
                }
                input{
                display: inline-block;
                background: #518668;
                border-radius: 3px;
                cursor: pointer;
                color: #fff;
                fill: #fff;
                min-height: 1rem;
                line-height: 1;
                padding: 1rem 1.5rem;
                font-size: 1rem;
                letter-spacing: 1.25%;
                align-items: center;
                border: none;
                box-shadow: none;
                text-align: center;
                text-transform: uppercase;
                transition: all 0.15s ease-out; 
                font-family: 'Nunito', sans-serif;
                font-weight: 700;
                margin-right: 1rem;
                }
                #list{
                min-width: 20rem;
                background: #E2F1F8;
                border: 1px solid #A8c3B3;
                transition: all 0.1s ease-in-out;
                color: #212121;
                height: 3rem;
                font-size: 16px;
                }
                select {
                background-color: #fff;
                line-height: initial;
                max-width: initial;
                border-radius: 3px 3px 0 0;
                margin-top: 3rem;
                font-family: 'Nunito', sans-serif;
                background: #E2F1F8;
                }
        </style>
        '''
    )

    return text

def add_navbar(
    text,
    country=True,
    state=None,
    county=None
    ):

    text = add_style_header(text)
    
    country_state='active'

    if state is not None:
       state_str=f'''<li><a class="active" href="#state">{state} View</a></li>'''
       country_state='inactive'
    else:
        state_str=' '

    if county is not None:
        county_str=f'''<li><a class="active" href="#county">{county}</a></li>'''  
        state_str=f'''<li><a class="inactive" href="../state/state_{state}.html">{state} View</a></li>'''
        country_state='inactive' 
    else:
        county_str=' '

    text = text.replace(
        '<body>',
        f'''<body>
                <ul>
            <li><a class="{country_state}" href="../country/country_county_static.html">Country View</a></li>
            {state_str}
            {county_str}
            </ul>
        '''
    )

    return text
    

def fix_county_res(
    text,
    ):

    text = text.replace(
        'class="plotly-graph-div" style="height:600px; width:900px;"></div>',
        'class="plotly-graph-div" style="height:80vh; width:100vw;">'
    ).replace(
        '</body>',
        '\t\t</div>\n</body>'
    )
    return text
    


if __name__ == '__main__':

    args = parser.parse_args()

    COUNTRY_NAME = args.country_name
    RT_COUNTY_FILE_PATH = args.rt_county_file_path
    OUTPUT_DIR = args.output_dir

    rt_county_df = pd.read_csv(RT_COUNTY_FILE_PATH)
    if COUNTRY_NAME=='USA':
        rt_county_df['countyFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: f"{x:05d}")
        rt_county_df['stateFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: x[:2])

    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    if not os.path.exists(OUTPUT_DIR+f'{COUNTRY_NAME}/'):
        os.mkdir(OUTPUT_DIR+f'{COUNTRY_NAME}/')

    fips_col = 'lad19cd'
    geojson_df = gp.read_file('https://c19pub.azureedge.net/assets/geo/ltlas_v1.geojson')
    geojson_df = geojson_df.rename(columns={fips_col:'id'})
    
    SAMPLE_FREQUENCY = 7# in days
    DATE_SUBSET = [date for i, date in \
        enumerate(np.sort(rt_county_df.date.unique().tolist())) if i%SAMPLE_FREQUENCY==0]
    
    print ("Creating Country Plots....")
    ## Country Map
    COUNTRY_DIR = OUTPUT_DIR+f'{COUNTRY_NAME}/country/'
    if not os.path.exists(COUNTRY_DIR):
        os.mkdir(COUNTRY_DIR)
    
    for l in ['state','county']:
        
        
        fig = animate_country(
                        # state=st, 
                        data_df=rt_county_df,
                        geojson_df=geojson_df,
                        disp_col='mean',
                        date_list=DATE_SUBSET,
                        animate=False,
                        save_path=COUNTRY_DIR+f'country_{l}_static.html',
                        scope=None
                    )
        # fig = map_rt(
        #     map_view='county',
        #     state=None,
        #     animate=False,
        #     state_geojson_dir='../data/misc/state_geojsons/',
        #     sampling_frequency=7,
        #     save_path=COUNTRY_DIR+f'country_{l}_static.html',
        # )

        with open(COUNTRY_DIR+f'country_{l}_static.html', 'r') as f:
    
            text = f.read()
            
            text = add_style_header(text)
            text = add_js_header(text)
            joined_list = ["<option value='none' selected>Select Options...</option>"]
            for st in rt_county_df.loc[rt_county_df['mean'].notnull() , 'state'].unique().tolist():
                joined_list.append(f'<option value="../state/state_{st}.html">{st}</option>')
            
            text = dropdown_col(text, joined_list)
            text = add_navbar(text)

        with open(COUNTRY_DIR+f'country_{l}_static.html', 'w') as f:
            f.write(text)
        
    
    print ("Creating State Plots....")
    ## State Map
    STATE_DIR = OUTPUT_DIR+f'{COUNTRY_NAME}/state/'
    if not os.path.exists(STATE_DIR):
        os.mkdir(STATE_DIR)


    # gc.collect()

    # state_inputs = [(st, STATE_DIR+f'state_{st}.html') \
    #     for st in rt_county_df['state'].unique().tolist()[:3]]


    # with Pool(processes=os.cpu_count()-1) as pool:
    #     print ("ENTERING POOL")
    #     results = pool.starmap(state_map, state_inputs) 
    err_list = []
    # for st in tqdm(rt_county_df['state'].unique().tolist()):
    for st in tqdm(rt_county_df.loc[rt_county_df['mean'].notnull() , 'state'].unique().tolist()):
        try:
            # fig = map_rt(
            #     'county',
            #     st,
            #     'mean',
            #     True,
            #     '../data/misc/state_geojsons/',
            #     7,
            #     f'{STATE_DIR}state_{st}.html'
            # )
            fig = animate_state(state=st, 
                        data_df=rt_county_df[rt_county_df['state']==st],
                        geojson_df=geojson_df,
                        date_list=DATE_SUBSET,
                        disp_col='mean',
                        animate=True,
                        save_path=STATE_DIR+f'state_{st}.html'
                    )
        except Exception as e:
            print (f'\t{st} threw an error: {str(e)}')
            err_list.append(st)

    for st in rt_county_df.loc[rt_county_df['mean'].notnull() , 'state'].unique().tolist():
        if st not in err_list:
            with open(STATE_DIR+f'state_{st}.html', 'r') as fil:
                text = fil.read()
                
                text = add_style_header(text)
                text = add_js_header(text)
                joined_list = ["<option value='none' selected>Select Options...</option>"]
                
                county_list = rt_county_df[(rt_county_df['state']==st) & \
                    (rt_county_df['mean'].notnull())]['region']\
                    .sort_values().unique().tolist()

                for county in county_list:
                    county_str = '_'.join(county.split())
                    joined_list.append\
                        (f'<option value="../county/county_{county_str}.html">{county}</option>')
                
                text = dropdown_col(text, joined_list)
                text = add_navbar(text, state=st)
            
            with open(STATE_DIR+f'state_{st}.html', 'w') as fil:
                fil.write(text)
            




    print ("Creating County Plots....")
    ## County Map
    COUNTY_DIR = OUTPUT_DIR+f'{COUNTRY_NAME}/county/'
    if not os.path.exists(COUNTY_DIR):
        os.mkdir(COUNTY_DIR)

    ## Bug Fix Zero Case Error
    rt_county_df = rt_county_df.dropna(subset=['mean'])
    
    region_state_map = rt_county_df[['region','state']]\
        .drop_duplicates().set_index('region').to_dict()['state']


    for county in tqdm(rt_county_df['region'].unique().tolist()):

        fig = rt_dashboard(
            rt_df=rt_county_df[rt_county_df['region']==county],
            save_path=COUNTY_DIR+ f"county_{'_'.join(county.split())}.html"
            )

        FILE = COUNTY_DIR+ f"county_{'_'.join(county.split())}.html"

        with open(FILE, 'r') as fil:
            text = fil.read()
            text = add_style_header(text)
            text = add_js_header(text)
            
            text = add_navbar(text, state=region_state_map[county], county=county)
            text = fix_county_res(text)

        with open(FILE, 'w') as fil:
            fil.write(text)


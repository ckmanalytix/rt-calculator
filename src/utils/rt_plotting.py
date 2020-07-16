import plotly.express as px
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt 

from urllib.request import urlopen
import json
import zipfile

import requests

from plotly.subplots import make_subplots
import plotly.graph_objects as go

from plotly.offline import iplot
from plotly.offline import plot

import geopandas
import ast

import io
import os
import sys

sys.path.append('../../src/')

from utils.ckm_plotting import plot_rt, gen_dropdown
from utils.state_abbreviations import state_abbr_map, state_abbr_map_r

from generate_rt import create_case_pop_df


RT_COUNTY_DATA = '../data/rt_county/rt_county.csv'
RT_STATE_DATA = '../data/rt_state/rt_state.csv'

rt_color_palette = [
#     '#A1A1A1',
    '#E1E1E1',
    '#FAE6DA',
    '#E1BCB3',
    '#C8938C',
    '#B16A67',
    '#9A4342',
    '#842421'
]

ckm_color_palette = [
    'rgb(208,209,230)',
    'rgb(232,189,233)',
    'rgb(222,159,223)',
    'rgb(202,100,204)',
    'rgb(168,56,170)',
    'rgb(138,46,140)',
    'rgb(124,41,125)',
    'rgb(109,36,111)',
    'rgb(95,32,96)',
    'rgb(66,22,66)',
    'rgb(51,17,52)',
]

color_palette = ckm_color_palette

custom_color_scale = []
for i,colors in enumerate(color_palette):
    custom_color_scale += [[i/len(color_palette), colors]]
    custom_color_scale += [[(i+1)/len(color_palette), colors]]


def set_up_defaults(
        rt_county_data_path=RT_COUNTY_DATA,
        rt_state_data_path=RT_STATE_DATA,
        state_geojson_dir='../../data/misc/state_geojsons/',
        sampling_frequency=7# in days
    ):

    rt_county_df = pd.read_csv(rt_county_data_path)
    rt_county_df['countyFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: f"{x:05d}")
    rt_county_df['stateFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: x[:2])
    state_fips_map = rt_county_df[['stateFIPS','state']].drop_duplicates().set_index('stateFIPS').to_dict()['state']
    state_fips_map_r = {v:k for k,v in state_fips_map.items()}

    rt_state_df = pd.read_csv(rt_state_data_path)
    rt_state_df['state'] = rt_state_df.region.map(state_abbr_map)
    rt_state_df['stateFIPS'] = rt_state_df.state.map(state_fips_map_r)

    if state_geojson_dir is None:
        STATE_GEOJSON_DIR = '../../data/misc/state_geojsons/'
    else:
        STATE_GEOJSON_DIR = state_geojson_dir
    
    if not os.path.exists(STATE_GEOJSON_DIR):
        os.mkdir(STATE_GEOJSON_DIR)
        myzip = requests.get('https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip')
        with zipfile.ZipFile(io.BytesIO(myzip.content), 'r') as zip_ref:
            zip_ref.extractall(STATE_GEOJSON_DIR)

    for f in os.listdir(STATE_GEOJSON_DIR):
        if ('.shp' in f) and ('.shp.' not in f):
            STATE_GEOJSON_PATH = STATE_GEOJSON_DIR+f

            
    state_geojson_df = geopandas.read_file(STATE_GEOJSON_PATH)
    state_geojson_df['STATE_NAME'] = state_geojson_df['NAME'].map(state_abbr_map)

    county_geojson_df = geopandas.read_file('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json')
    county_geojson_df['STATE_NAME'] = county_geojson_df['STATE'].map(state_fips_map)

    DATE_SUBSET = [date for i, date in enumerate(np.sort(rt_county_df.date.unique().tolist())) if i%sampling_frequency==0]

    return rt_county_df, rt_state_df, state_geojson_df, county_geojson_df, DATE_SUBSET



def animate_country(
    data_df,
    geojson_df,
    date_list,
    disp_col='mean',
    date_col='date',
    featureidkey='properties.id',
    animate=False,
    locations='countyFIPS',
    save_path=None,
    scope='usa'
    ):

    if not animate:
        data_df = data_df.loc[data_df[date_col]==data_df[date_col].max(), :]

        fig = px.choropleth(
            data_frame=data_df[data_df[date_col]==data_df[date_col].max()], 
            #geojson=counties, 
            geojson=ast.literal_eval(geojson_df.to_json()), 
            locations=locations, 
            color=disp_col,
            color_continuous_scale=custom_color_scale,
            #animation_frame=None,
            # range_color=(data_df[disp_col].quantile(q=0.05), data_df[disp_col].quantile(q=0.95)),
            range_color=(0.5,1.7),
            hover_name='region',
            labels={disp_col: f'Rt ({disp_col})'},
            featureidkey=featureidkey,
            scope=scope,
            title=f"Last Updated: {data_df[date_col].max()}"
        )

        if scope is None:
            fig.update_geos(fitbounds="locations", visible=False)

        fig.update_layout(
            dragmode=False,
            margin={"r":0,"t":0,"l":0,"b":0},
            xaxis=dict(fixedrange= True),
            yaxis=dict(fixedrange= True),
            hoverlabel=dict(
                bgcolor="white", 
                font_size=14, 
                font_family="Nunito, Regular",
                font_color="black"
            ),
            font=dict(
                family="Nunito, Regular",
                size=14,
                color="black"
            )
        )

# return data_df, geojson_df, date_list, disp_col, date_col, featureidkey, locations
    else:

        fig = px.choropleth(
            data_frame=data_df[data_df[date_col].isin(date_list)], 
            #geojson=counties, 
            geojson=ast.literal_eval(geojson_df.to_json()), 
            locations=locations, 
            color=disp_col,
            color_continuous_scale=custom_color_scale,
            animation_frame=date_col,
            # range_color=(data_df[disp_col].quantile(q=0.05), data_df[disp_col].quantile(q=0.95)),
            range_color=(0.5,1.7),
            hover_name='region',
            labels={disp_col: f'Rt ({disp_col})'},
            featureidkey=featureidkey,
            scope=scope,
            title=f"Last Updated: {data_df[date_col].max()}"
        )

        if scope is None:
            fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(
            dragmode=False,
            xaxis=dict(fixedrange= True),
            yaxis=dict(fixedrange= True),
            margin={"r":0,"t":0,"l":0,"b":0},
            font=dict(
                family="Nunito, Regular",
                size=14,
                color="black"
            ),
            hoverlabel=dict(
                bgcolor="white", 
                font_size=14, 
                font_family="Nunito, Regular",
                font_color="black"
            )
        )

    if save_path is not None:
        plot(
            fig, 
            filename=save_path,
            include_plotlyjs='cdn', 
            include_mathjax='cdn', 
            auto_open=False
        )
        with open(save_path, 'r') as f:
            text = f.read()
            text = text.replace\
            ('<head><meta charset="utf-8" /></head>',
            '<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /><link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200;0,400;0,600;0,700;1,300&display=swap" rel="stylesheet"></head>')
        
        with open(save_path, 'w+') as f:
            f.write(text)


    return fig

def animate_state(data_df,
                  geojson_df,
                  date_list,
                  state='NY',
                  data_filter_col='state',
                  geo_filter_col='STATE_NAME',
                  disp_col='mean',
                  date_col='date',
                  featureidkey='properties.id',
                  locations='countyFIPS',
                  animate=False,
                  save_path=None
    ):
   
    state_df_subset = data_df[data_df[date_col].isin(date_list)]
    #geojson_subset = geojson_df[geojson_df[geo_filter_col]==state]
    state_df = state_df_subset[state_df_subset[data_filter_col]==state]

    if not animate:
        state_df = state_df.loc[state_df[date_col]==state_df[date_col].max(), :]

    ###
    # Bug Fix To Fix Boundary Issue
    state_df['hover_text'] = state_df[disp_col].apply(lambda x: f'{x:.2f}' if str(x)!='nan' else 'N/A')
    ###

    fig = px.choropleth(
        # data_frame=state_df, 
        data_frame=state_df.fillna(-1), 
        geojson=ast.literal_eval(geojson_df.to_json()), 
#         geojson=ast.literal_eval(geojson_subset.to_json()), 
        locations=locations, 
        color=disp_col,
        color_continuous_scale=custom_color_scale,
        animation_frame=date_col,
        # range_color=(state_df[disp_col].quantile(0.05), 
        #              state_df[disp_col].quantile(0.95)),
        range_color=(0.5,1.7),
        hover_name='region',
        # labels={disp_col:f'Rt ({disp_col})'},
        labels={'hover_text':f'Rt ({disp_col})'},
        featureidkey=featureidkey,
        hover_data={'hover_text':True, 'countyFIPS':False, disp_col:False},
        title=f"Last Updated: {state_df[date_col].max()}"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        dragmode=False,
        margin={"r":0,"t":0,"l":0,"b":0},
        xaxis=dict(fixedrange= True),
        yaxis=dict(fixedrange= True),
        hoverlabel=dict(
            bgcolor="white", 
            font_size=14, 
            font_family="Nunito, Regular",
            font_color="black"
        ),
        font=dict(
            family="Nunito, Regular",
            size=14,
            color="black"
        )
    )

    if save_path is not None:
        plot(
            fig, 
            filename=save_path, 
            include_plotlyjs='cdn', 
            include_mathjax='cdn', 
            auto_open=False
        )
        with open(save_path, 'r') as f:
            text = f.read()
            text = text.replace\
            ('<head><meta charset="utf-8" /></head>',
            '<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /><link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200;0,400;0,600;0,700;1,300&display=swap" rel="stylesheet"></head>')
        
        with open(save_path, 'w+') as f:
            f.write(text)


    return fig

def map_rt(
    map_view='state',
    state='NY',
    disp_col='mean',
    animate=False,
    state_geojson_dir='../../data/misc/state_geojsons/',
    sampling_frequency=7, 
    save_path=None
    ):
    
    rt_county_df, rt_state_df, state_geojson_df, county_geojson_df, DATE_SUBSET = \
        set_up_defaults(sampling_frequency=sampling_frequency,
                    state_geojson_dir=state_geojson_dir
        )

    if state is not None:
        if map_view=='county':
            fig = animate_state(state=state, 
                        data_df=rt_county_df,
                        geojson_df=county_geojson_df.dropna(subset=['STATE_NAME']),
                        date_list=DATE_SUBSET,
                        disp_col=disp_col,
                        animate=animate
                    )
        elif map_view=='state':
            fig = animate_state(state=state, 
                        data_df=rt_state_df,
                        geojson_df=state_geojson_df,
                        date_list=DATE_SUBSET,
                        disp_col=disp_col,
                        featureidkey='properties.GEOID',
                        locations='stateFIPS',
                        animate=animate
                    )
    else:
        if map_view=='county':
            fig = animate_country(
                        data_df=rt_county_df,
                        geojson_df=county_geojson_df.dropna(subset=['STATE_NAME']),
                        date_list=DATE_SUBSET,
                        disp_col=disp_col,
                        animate=animate
                    )
        elif map_view=='state':
            fig = animate_country(
                        data_df=rt_state_df,
                        geojson_df=state_geojson_df,
                        date_list=DATE_SUBSET,
                        disp_col=disp_col,
                        featureidkey='properties.GEOID',
                        locations='stateFIPS',
                        animate=animate
                    )    
    if save_path is not None:
        plot(
            fig, 
            filename=save_path, 
            include_plotlyjs='cdn', 
            include_mathjax='cdn', 
            auto_open=False
        )
        with open(save_path, 'r') as f:
            text = f.read()
            text = text.replace\
            ('<head><meta charset="utf-8" /></head>',
            '<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /><link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200;0,400;0,600;0,700;1,300&display=swap" rel="stylesheet"></head>')
        
        with open(save_path, 'w+') as f:
            f.write(text)


    return fig

def rt_live_error_plot(rt_df, 
                       filter_column='state', 
                       filter_field='NY',
                       height=800,
                       width=800,
                       save_path=None
            ):

    subset_df = rt_df[rt_df[filter_column]==filter_field]

    subset_df.loc[:, 'error_y_plus'] = subset_df['upper_90'] - subset_df['mean']
    subset_df.loc[:,'error_y_minus'] = subset_df['mean'] - subset_df['lower_90']
    subset_df.loc[:,'color'] = (subset_df['mean'] >= 1).map({True: 'High Risk', False: 'Low/Moderate Risk'})
    fig = px.scatter(
        data_frame=subset_df.loc[subset_df.date == subset_df.date.max(), :].sort_values('mean'),
        y='region',
        x='mean',
        error_x='error_y_plus',
        error_x_minus='error_y_minus',
        color='color',
        hover_name='region',
        width=width,
        height=height
    )
    
    if save_path is not None:
        plot(
            fig, 
            filename=save_path, 
            include_plotlyjs='cdn', 
            include_mathjax='cdn', 
            auto_open=False
        )
        with open(save_path, 'r') as f:
            text = f.read()
            text = text.replace\
            ('<head><meta charset="utf-8" /></head>',
            '<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /></head>')
        
        with open(save_path, 'w+') as f:
            f.write(text)


    return fig

def rt_dashboard(
    rt_df,
    disp_col='mean',
    upper_thresh='upper_90',
    lower_thresh='lower_90',
    date_col='date',
    save_path=None
    ):

    rt_df = rt_df.sort_values(date_col)

    fig = make_subplots(
        rows=3,
        cols=3,
        specs=[[{'type':'indicator'}, {'type':'indicator'}, {'type':'indicator'}],
            [{'colspan':3, 'rowspan':2,'type':'xy'}, None,None],
                [None, None,None]],
        subplot_titles=(
            # r"$\text{R}_t$",
            # r"$\text{Change}$",
            # r"$\text{Risk}$", 
            'Rt', 'Change', 'Risk',
            (rt_df.region.tolist()[0])
        )
    )

    fig.add_trace(go.Scatter(
        x=rt_df[date_col].tolist(), 
        y=rt_df[lower_thresh].tolist(),
        fill=None,
        mode='lines',
        fillcolor='rgba(0,255,0,0.1)',
        name=lower_thresh,
        line_color='rgba(0,255,0,0.1)',
        ),
        row=2,
        col=1
    )
    fig.add_trace(go.Scatter(
        x=rt_df[date_col].tolist(), 
        y=rt_df[upper_thresh].tolist(),
        fill='tonexty', # fill area between trace0 and trace1
        mode='lines', 
        fillcolor='rgba(0,255,0,0.1)',
        name=upper_thresh,
        line_color='rgba(0,255,0,0.1)',
        ),
        row=2,
        col=1
    )

    fig.add_trace(go.Scatter(
        x=rt_df[date_col].tolist(), 
        y=rt_df[disp_col].tolist(),
    #     fill='tonexty', # fill area between trace0 and trace1
        mode='markers+lines', 
        fillcolor='rgba(0,255,0,0.1)',
        name=disp_col,
        line_color='gray'
        ),
        row=2,
        col=1
    )


    fig.add_trace(go.Indicator(
        mode = "number",
        value = rt_df[disp_col].tolist()[-1],
        number={
            'valueformat':'0.3f',
            'font':{
                'color': '#3D9970' if (rt_df[disp_col].tolist()[-1] <1) else '#FF4136',
                'size' : 23,
                'family': 'Nunito, Regular'
            }
        }
        ),
        row=1,
        col=1
    )

    fig.add_trace(go.Indicator(
        mode = "delta",
        delta= {
            'reference': rt_df[disp_col].tolist()[0], 
            'relative':True,
            'increasing': {
                'color':'#FF4136'
            },
            'decreasing': {
                'color': '#3D9970'
            },
            'font':{
                'size' : 22,
                'family': 'Nunito, Regular',
            }
        },
        value = rt_df[disp_col].tolist()[-1],
        ),
        row=1,
        col=2
    )

    if rt_df[disp_col].tolist()[-1]>1:
        val = 'CRITICAL'
        col = 'red'
    elif (rt_df[disp_col].tolist()[-1])>0.6:
        val = 'MEDIUM'
        col = 'orange'
    else:
        val = 'LOW'
        col = 'green'

    fig.add_trace(go.Indicator(
        mode = "number",
        delta= {
            'reference': rt_df[disp_col].tolist()[0], 
            'relative':True,
            'increasing': {
                'color':'#FF4136'
            },
            'decreasing': {
                'color': '#3D9970'
            }
        },
        value = rt_df[disp_col].tolist()[-1],
        number={
            'valueformat':'0.3f',
            # using this string formattting prevents the font from being applied
            'prefix' : r'$\textbf{'+val+'}$',
            'font':{
                'color': col,
                'size':22,
                'family': 'Nunito, Regular'
            }
        }
        ),
        row=1,
        col=3
    )

    fig.update_layout(
        dragmode=False,
        xaxis=dict(fixedrange= True),
        yaxis=dict(fixedrange= True),
        showlegend=False, 
        title_text="", 
        width=900, 
        height=600,                
        font=dict(
            family="Nunito, Regular",
            size=14,
            color="black"
        ),
        hoverlabel=dict(
            bgcolor="white", 
            font_size=14, 
            font_family="Nunito, Regular",
            font_color="black"
        )
    )
    
    if save_path is not None:
        plot(
            fig, 
            filename=save_path, 
            include_plotlyjs='cdn', 
            include_mathjax='cdn', 
            auto_open=False
        )
        with open(save_path, 'r') as f:
            text = f.read()
            text = text.replace\
            ('<head><meta charset="utf-8" /></head>',
            '<head><meta http-equiv="content-type" content="text/html; charset=UTF-8" /><link href="https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,200;0,400;0,600;0,700;1,300&display=swap" rel="stylesheet"></head>')
        
        with open(save_path, 'w+') as f:
            f.write(text)


    return fig
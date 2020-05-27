import pytest
import subprocess

import pandas as pd
import numpy as np
import os


def calc_state_rt(state_name='DE'):
    curr_dir = os.getcwd()
    os.chdir('../src/')
    # python generate_rt.py --state_level_only --filtered_states DE NY  --output_path='../data/rt_state/'
    subprocess.run(
        ['python', 'generate_rt.py', '--state_level_only', 
        '--filtered_states', state_name,
        '--output_path', '../data/rt_state/'
        ]
    )
    os.chdir(curr_dir)

def calc_county_rt(state_name='DE'):
    curr_dir = os.getcwd()
    os.chdir('../src/')
    # python generate_rt.py --state_level_only --filtered_states DE NY  --output_path='../data/rt_state/'
    subprocess.run(
        ['python', 'generate_rt.py',  
        '--filtered_states', state_name,
        '--output_path', '../data/rt_county/'
        ]
    )
    os.chdir(curr_dir)

def test_state_rt():
    calc_state_rt()
    assert os.path.exists('../data/rt_state/rt_state.csv')
    calc_state_rt(state_name='DE')
    assert os.path.exists('../data/rt_state/rt_state_DE.csv')
    calc_state_rt(state_name='NY')
    assert os.path.exists('../data/rt_state/rt_state_NY.csv')

def test_county_rt():
    calc_county_rt()
    assert os.path.exists('../data/rt_county/rt_county.csv')
    calc_state_rt(state_name='DE')
    assert os.path.exists('../data/rt_county/rt_county_DE.csv')
    
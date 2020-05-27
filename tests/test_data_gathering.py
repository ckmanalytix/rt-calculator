import pytest 
import os
import subprocess


def cleanup_data():
    curr_dir = os.getcwd()
    os.chdir('../src/')
    subprocess.run(['chmod', 'u+x', 'cleanup.sh'])
    subprocess.run(['./cleanup.sh'], shell=True)
    os.chdir(curr_dir)

def get_county_data():
    curr_dir = os.getcwd()
    os.chdir('../src/')
    subprocess.run(['chmod', 'u+x', 'get_county_data.sh'])
    subprocess.run(['./get_county_data.sh'], shell=True)
    os.chdir(curr_dir)

def get_rt_supporting_data():
    curr_dir = os.getcwd()
    os.chdir('../src/')
    subprocess.run(['chmod', 'u+x', 'get_rt.sh'])
    subprocess.run(['./get_rt.sh'], shell=True)
    os.chdir(curr_dir)

def test_get_county_data():
    cleanup_data()
    get_county_data()
    assert os.path.exists('../data/county_level/covid_confirmed_usafacts.csv')
    assert os.path.exists('../data/misc/CountyHealthRankings19.csv')


def test_get_rt_supporting_data():
    cleanup_data()
    get_rt_supporting_data()
    assert os.path.exists('../data/misc/latestdata.csv')
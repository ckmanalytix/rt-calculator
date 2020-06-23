import os
import multiprocessing
from multiprocessing import Process, Queue, Pool, TimeoutError
import pandas as pd
from utils.rt_plotting import map_rt
import time
import gc

PATH = '../../DATA/test-processing/'
if not os.path.exists(PATH):
    os.mkdir(PATH)

def f(x):
    with open(PATH+f'{x}.csv', 'w+') as fil:
        fil.write(f'{x:04d}')
        return PATH+f'{x}.csv'

def state_map(st, path):
    path_x = f'{PATH}state_{st}.html'
    print (path_x)
    fig = map_rt(
            'county',
            st,
            'mean',
            True,
            '../data/misc/state_geojsons/',
            7,
            path_x
        )
    return path_x 

if __name__ == '__main__':
    
    
    rt_county_df = pd.read_csv('../data/rt_county/rt_county.csv')
    rt_county_df['countyFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: f"{x:05d}")
    rt_county_df['stateFIPS'] = rt_county_df['countyFIPS'].apply(lambda x: x[:2])
    
    
    gc.collect()

    dummy_input = [(st, f'{PATH}state_{st}.html') \
        for st in rt_county_df['state'].unique().tolist()[:6]]

    start_time = time.time()
    with Pool(processes=os.cpu_count()-1) as pool:
        print ("ENTERING POOL")
        res = pool.map(f, range(30))
        res2 = pool.starmap(state_map, dummy_input) 
    # exiting the 'with'-block has stopped the pool
    end_time = time.time()
    print (type(res), f'{res}')
    print(f"Now the pool is closed and no longer available. Completed in {end_time-start_time} sec.")

import multiprocessing
import os
import subprocess
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('--tot_pipelines', 
    type=int, 
    help='Number of Parallel Pipelines we Intend to Run',
    default=4
)

parser.add_argument('--pipeline_index', 
    type=int, 
    help='Index of Pipeline to be Run. Must lie in the range (both inclusive): [0, tot_pipelines-1]',
    default=0
)

parser.add_argument('--country_name', 
    type=str, 
    help='Name of Country in analysis',
    default='USA'
)

usa_county_dict = {'TX': 254, 'GA': 159, 'VA': 133, 'KY': 120, \
           'MO': 115, 'KS': 105, 'IL': 102, 'NC': 100, \
           'IA': 99, 'TN': 95, 'NE': 93, 'IN': 92, 'OH': 88,\
           'MN': 87, 'MI': 83, 'MS': 82, 'OK': 77, 'AR': 75,\
           'WI': 72, 'FL': 67, 'PA': 67, 'AL': 67, 'SD': 66,\
           'CO': 64, 'LA': 64, 'NY': 61, 'CA': 58, 'MT': 56,\
           'WV': 55, 'ND': 53, 'SC': 46, 'ID': 44, 'WA': 39,\
           'OR': 36, 'NM': 33, 'AK': 29, 'UT': 29, 'MD': 24,\
           'WY': 23, 'NJ': 21, 'NV': 17, 'ME': 16, 'AZ': 15,\
           'MA': 14, 'VT': 14, 'NH': 10, 'CT': 8, 'HI': 5,\
           'RI': 5, 'DE': 3, 'DC': 1}

uk_county_dict = {'EAST MIDLANDS': 40,\
        'EAST OF ENGLAND': 43,\
        'LONDON': 33,\
        'NORTH EAST': 12,\
        'NORTH WEST': 39,\
        'SOUTH EAST': 67,\
        'SOUTH WEST': 26,\
        'WEST MIDLANDS': 30,\
        'YORKSHIRE AND THE HUMBER': 21}

county_dict_map = {
    'USA' : usa_county_dict,
    'UK' : uk_county_dict
}

file_dict_map = {
    'USA' : ['generate_rt.py', '../data/rt_county/', '../data/rt_state/'],
    'UK' : ['generate_rt_uk.py', '../data/uk/rt_county/', '../data/uk/rt_state/']
}

if __name__ == '__main__':

    args = parser.parse_args()

    TOT_PIPELINES = args.tot_pipelines
    PIP_INDEX = args.pipeline_index
    COUNTRY_NAME = args.country_name

    if PIP_INDEX > TOT_PIPELINES - 1:
        print ("Incorrect --pipeline_index specified. Setting to Default.")
        PIP_INDEX = 0
    
    if COUNTRY_NAME in list(county_dict_map.keys()):
        state_county_dict = county_dict_map[COUNTRY_NAME]
        file_name = file_dict_map[COUNTRY_NAME][0]
        county_path = file_dict_map[COUNTRY_NAME][1]
        state_path = file_dict_map[COUNTRY_NAME][2]
    else:
        state_county_dict = county_dict_map['USA']
        file_name = file_dict_map['USA'][0]
        county_path = file_dict_map['USA'][1]
        state_path = file_dict_map['USA'][2]

    rt_list = list(state_county_dict.keys())
    n_elems = len(rt_list)

    state_list = [ []] * TOT_PIPELINES 
    threshold = sum(state_county_dict.values())/TOT_PIPELINES


    for i in range(TOT_PIPELINES):
        #print (i)
        if i< TOT_PIPELINES-1:
            run_sum = 0
            try:
                elem = rt_list.pop(0)
            except:
                break
            state_list[i] = state_list[i] + [elem]
            run_sum = run_sum + state_county_dict[elem]
                
            while (run_sum < threshold):
                try:
                    elem = rt_list.pop(-1)
                except:
                    break
                state_list[i] = state_list[i] + [elem]
                run_sum = run_sum + state_county_dict[elem]
                
        else:
            state_list[i] = rt_list


    print (state_list[PIP_INDEX])

    
    if len (state_list[PIP_INDEX]) > 0 :
        #state_name = ' '.join(state_list[PIP_INDEX])

        # print (state_name)

        # subprocess.run(
        #     ['python', 'generate_rt.py',  
        #     '--filtered_states'] + state_list[PIP_INDEX] +
        #     ['--output_path', '../data/rt_county/'
        #     ]
        # )

        # subprocess.run(
        #     ['python', 'generate_rt.py', '--state_level_only', 
        #     '--filtered_states'] + state_list[PIP_INDEX] +
        #     ['--output_path', '../data/rt_state/'
        #     ]
        # )

        subprocess.run(
            ['python', file_name,  
            '--filtered_states'] + state_list[PIP_INDEX] +
            ['--output_path', county_path
            ]
        )

        subprocess.run(
            ['python', file_name, '--state_level_only', 
            '--filtered_states'] + state_list[PIP_INDEX] +
            ['--output_path', state_path
            ]
        )
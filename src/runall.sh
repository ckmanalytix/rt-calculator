 
./cleanup.sh
./get_rt.sh
./get_county_data.sh

# To calculate Rts for all counties in a state, run the generate_rt.py files
# You can add multiple states to your list
python generate_rt.py --filtered_states DE --output_path='../data/rt_county/'
# To instead calculate Rt for the entire state, add the --state_level_only flag
python generate_rt.py --filtered_states DE --state_level_only --output_path='../data/rt_state/'

# To consolidate the various states you ran above into one file run the commands below
python generate_rt_combine.py --files_path='../data/rt_state/' --state_level
python generate_rt_combine.py --files_path='../data/rt_county/'

# Finally, to create your HTML output plots, run the command below
python generate_plots.py --country_name="USA"

# python generate_rt_uk.py --filtered_states 'NORTH EAST' --output_path='../data/uk/rt_county/'
# # To instead calculate Rt for the entire state, add the --state_level_only flag
# python generate_rt_uk.py --filtered_states 'NORTH EAST' --state_level_only --output_path='../data/uk/rt_state/'

# # To consolidate the various states you ran above into one file run the commands below
# python generate_rt_combine_uk.py --files_path='../data/uk/rt_state/' --state_level
# python generate_rt_combine_uk.py --files_path='../data/uk/rt_county/'

# # Finally, to create your HTML output plots, run the command below
# python generate_plots_uk.py --country_name="UK"


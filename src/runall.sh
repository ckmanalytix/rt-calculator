 
./cleanup.sh
./get_county_data.sh
./get_rt.sh

## Creating State Level Files
python generate_rt.py --state_level_only  --output_path='../data/rt_state/'
python generate_rt.py  --output_path='../data/rt_county/'

## Combining the files into a consolidated file for Simulation Use
python generate_rt_combine.py --files_path='../data/rt_state/' --state_level
python generate_rt_combine.py --files_path='../data/rt_county/'

## Combining the files into a consolidated file for Simulation Use
python generate_plots.py --rt_county_file_path='../data/rt_county/rt_county.csv'
 
./cleanup.sh
./get_county_data.sh
./get_rt.sh

python generate_rt.py --state_level_only  --output_path='../data/rt_state/'
python generate_rt.py  --output_path='../data/rt_county/'
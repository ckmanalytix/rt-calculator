#!/bin/bash
sudo yum -y install htop

OUT_DIR="${OUTPUT1_STAGING_DIR}"
TOT_PIPELINES="${NUM_PIPELINES}"
PIPELINE_INDEX="${PIPELINE_INDEX}"


# pull down source code
aws s3 cp s3://covid19-datapipeline/rt-calculator.tar.gz .

# extract source code
tar -xvf rt-calculator.tar.gz
cd rt-calculator

# install libs
pip install -r requirements.txt
# pull in relevant data
cd ./src/
chmod u+x ./get_rt.sh
chmod u+x ./get_county_data.sh 
./get_rt.sh
./get_county_data.sh
# run scripts 
python runtime.py --tot_pipelines ${TOT_PIPELINES} --pipeline_index ${PIPELINE_INDEX}
# python generate_rt.py --state_level_only  --output_path='../data/rt_state/'
# python generate_rt.py  --output_path='../data/rt_county/'

## Combining the files into a consolidated file for Simulation Use
python rt_combine.py --files_path='../data/rt_state/' --state_level
python rt_combine.py --files_path='../data/rt_county/'

# copy outputs to local staging directory
mkdir ${OUT_DIR}/rt_county/
mkdir ${OUT_DIR}/rt_state/
cp ../data/rt_county/* ${OUT_DIR}/rt_county/
cp ../data/rt_state/* ${OUT_DIR}/rt_state/

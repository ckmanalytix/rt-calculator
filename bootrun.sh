#!/bin/bash
sudo yum -y install htop

OUT_DIR="${OUTPUT1_STAGING_DIR}"

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
python generate_rt.py --state_level_only  --output_path='../data/rt_state/'
python generate_rt.py  --output_path='../data/rt_county/'

# copy outputs to local staging directory
cp -r ../data/rt_county/ ${OUT_DIR}
cp -r ../data/rt_state/ ${OUT_DIR}

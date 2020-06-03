source ~/anaconda3/etc/profile.d/conda.sh

if [ ! -d "/data" ]; then
    sudo mkfs -t xfs /dev/nvme1n1
    sudo mkdir /data
    sudo mount /dev/nvme1n1 /data
    sudo chown $(whoami):$(whoami) /data
fi
conda config --append envs_dirs /data/conda_envs
cd /data

CPU=$(nproc)
echo $CPU
CPU=$(($CPU-2))
CPU=26

echo "# pulling down source code..."
    aws s3 cp s3://ckm-covid-response/releases/rt-condax.sh .
    chmod +x rt-condax.sh
    aws s3 cp s3://ckm-covid-response/releases/rt-calculator.tar.gz .
    mkdir rt-calculator
echo "# extract source code..."
    tar -xvf rt-calculator.tar.gz -C rt-calculator
    cd rt-calculator
echo "# installing libs..."
    pip install -r requirements.txt
echo "# pull in relevant data.."
    cd ./src/
    chmod u+x ./get_rt.sh
    chmod u+x ./get_county_data.sh
    ./get_rt.sh
    ./get_county_data.sh

cd  ../..
rm rt*.log

echo "# creating base conda environment..."
conda create -y -n rt-base python=3.7
conda activate rt-base
pip install -r rt-calculator/requirements.txt
conda deactivate
echo "# done..."

echo "# spawn rt calculation processes.."
echo $(date)
for ((i=0; i<$CPU; i++))
do
 ENV="rtenv$i"
 echo "++ target conda environment = $ENV"
 ./rt-condax.sh $ENV $CPU $i &> $ENV.log &
done
echo "# waiting untill all processes have completed..."
wait

echo "# Combining all files effectively."
cd rt-calculator/src/
python rt_combine.py --files_path='../data/rt_state/' --state_level
python rt_combine.py --files_path='../data/rt_county/'
cd ../..

echo $(date)
echo "# done."
aws s3 cp rt-calculator/data/rt_county s3://ckm-covid-rt-calculator/output/rt_county  --recursive
aws s3 cp rt-calculator/data/rt_state s3://ckm-covid-rt-calculator/output/rt_state  --recursive

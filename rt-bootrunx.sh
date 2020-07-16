source ~/anaconda3/etc/profile.d/conda.sh

# format and mount storage, adjust to match your machine
# device for aws c5d.4 or 9xlarge is nvme1n1 
if [ ! -d "/data" ]; then
    sudo mkfs -t xfs /dev/nvme1n1
    sudo mkdir /data
    sudo mount /dev/nvme1n1 /data
    sudo chown $(whoami):$(whoami) /data
fi

conda config --append envs_dirs /data/conda_envs
cd /data

CPU=$(nproc)
echo "# using cpus=$CPU"

# remove these if running local
echo "# pulling down source code..."
    aws s3 cp s3://ckm-covid-response/releases/rt-condax.sh .
    chmod +x rt-condax.sh
    aws s3 cp s3://ckm-covid-response/releases/rt-condax_uk.sh .
    chmod +x rt-condax_uk.sh
    aws s3 cp s3://ckm-covid-response/releases/rt-calculator.tar.gz .
    mkdir rt-calculator
echo "# extracting source code..."
    tar -xvf rt-calculator.tar.gz -C rt-calculator


cd rt-calculator
echo "# installing libs..."
    pip install -r requirements.txt
echo "# pulling in relevant data.."
    cd ./src/
    chmod u+x ./get_rt.sh
    chmod u+x ./get_county_data.sh
    ./get_rt.sh
    ./get_county_data.sh
    
cd ../..

# delete previous run logs
rm rt*.log

echo "# creating base conda environment..."
conda create -y -n rt-base python=3.7
conda activate rt-base
pip install -r rt-calculator/requirements.txt
conda deactivate
echo "# done..."

echo "# Running the US calculations..."

echo "# spawning rt calculation processes.."
echo $(date)
for ((i=0; i<$CPU; i++))
do
 ENV="rtenv$i"
 echo "++ target conda environment = $ENV"
 ./rt-condax.sh $ENV $CPU $i &> $ENV.log &
done
echo "# waiting for all processes to finish..."
wait

echo "# Combining all files effectively."
cd rt-calculator/src/
python generate_rt_combine.py --files_path='../data/rt_state/' --state_level
python generate_rt_combine.py --files_path='../data/rt_county/'

echo "# Creating plot files."
python generate_plots.py --rt_county_file_path='../data/rt_county/rt_county.csv'

cd ../..

echo "# uploading US results to S3..."
aws s3 cp rt-calculator/data/rt_county s3://ckm-covid-rt-calculator/output/rt_county  --recursive
aws s3 cp rt-calculator/data/rt_state s3://ckm-covid-rt-calculator/output/rt_state  --recursive

echo "# Running the UK calculations..."

echo "# spawning rt calculation processes.."
echo $(date)
for ((i=0; i<$CPU; i++))
do
 ENV="rtenv$i-uk"
 echo "++ target conda environment = $ENV"
 ./rt-condax_uk.sh $ENV $CPU $i &> $ENV.log &
done
echo "# waiting for all processes to finish..."
wait

echo "# Combining all files effectively."
cd rt-calculator/src/
python generate_rt_combine_uk.py --files_path='../data/uk/rt_state/' --state_level
python generate_rt_combine_uk.py --files_path='../data/uk/rt_county/'

echo "# Creating plot files."
python generate_plots_uk.py --rt_county_file_path='../data/uk/rt_county/rt_county.csv'

cd ../..

echo "# Adding downloadable files to cloudfront paths."

cd rt-calculator/src/
./consolidate_rt_vals.sh
cd ../..

echo $(date)
echo "# done."

echo "# uploading UK results to S3..."

aws s3 cp rt-calculator/data/uk/rt_county s3://ckm-covid-rt-calculator/output/uk/rt_county  --recursive
aws s3 cp rt-calculator/data/uk/rt_state s3://ckm-covid-rt-calculator/output/uk/rt_state  --recursive

#aws s3 cp rt-calculator/output s3://ckm-covid-rt-calculator/web  --recursive


echo "# Uploading HTML files to S3..."

# these files are greater than the 10 mb cloudfront limit therefore we manually compress them 
mkdir rt-calculator/output/USA/state/compressed
for file in rt-calculator/output/USA/state/*.html; do pigz -9 -c "$file" > "rt-calculator/output/USA/state/compressed/${file##*/}"; done

mkdir rt-calculator/output/UK/state/compressed
for file in rt-calculator/output/UK/state/*.html; do pigz -9 -c "$file" > "rt-calculator/output/UK/state/compressed/${file##*/}"; done


# browser cache control max age 43200 = 12 hrs 
aws s3 cp rt-calculator/output s3://ckm-covid-rt-calculator/web  --recursive --cache-control max-age=43200
# set content-encoding to gzip
aws s3 cp rt-calculator/output/USA/state/compressed/ s3://ckm-covid-rt-calculator/web/USA/state/compressed --recursive --content-encoding gzip
aws s3 cp rt-calculator/output/UK/state/compressed/ s3://ckm-covid-rt-calculator/web/UK/state/compressed --recursive --content-encoding gzip

echo "# done uploading."

aws cloudfront create-invalidation --distribution-id ESZYIOIHVJ50T --paths "/*"
echo "# invalidated cloudfront."


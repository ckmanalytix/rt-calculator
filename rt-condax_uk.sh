source ~/anaconda3/etc/profile.d/conda.sh 
if [ ! -d "/data/conda_envs/$1" ]; then
        echo "++Creating conda environment: $1"
        conda create -y --clone rt-base --name $1 
        conda activate $1
fi
cd rt-calculator
RT_ENV="base_compiledir=/data/conda_envs/$1/theano.NOBACKUP"
echo $RT_ENV
#echo "+++installing libs"
#pip install --cache-dir=/data/pip-cache/ --build /data/pip-cache -r requirements.txt
cd src
echo "++Running calculations for $2 pipelines using index of $3"
THEANO_FLAGS=$RT_ENV python runtime.py --tot_pipelines $2 --pipeline_index $3 --country_name='UK'
conda deactivate


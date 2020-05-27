curl https://d14wlfuexuxgcm.cloudfront.net/covid/rt.csv --output ../data/misc/rt.csv
curl -o ../data/misc/latestdata.tar.gz -L https://github.com/beoutbreakprepared/nCoV2019/raw/master/latest_data/latestdata.tar.gz
tar -xzvf ../data/misc/latestdata.tar.gz -C ../data/misc/
rm -rf ../data/misc/latestdata.tar.gz
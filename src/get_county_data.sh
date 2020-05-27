
### Download Covid Case Files
curl https://static.usafacts.org/public/data/covid-19/covid_confirmed_usafacts.csv --output ../data/county_level/covid_confirmed_usafacts.csv
curl https://static.usafacts.org/public/data/covid-19/covid_deaths_usafacts.csv --output ../data/county_level/covid_deaths_usafacts.csv
curl https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv --output ../data/county_level/covid_nytimes.csv

### Download updated version of County Health Rankings
curl https://www.countyhealthrankings.org/sites/default/files/media/document/2020%20County%20Health%20Rankings%20Data%20-%20v1.xlsx --output ../data/misc/CountyHealthRankings20.xlsx
python ../src/utils/prep_pop_file.py --county_level_population ../data/misc/CountyHealthRankings20.xlsx --output_path ../data/misc/CountyHealthRankings19.csv


### Download Covid Case Files
curl https://static.usafacts.org/public/data/covid-19/covid_confirmed_usafacts.csv --output ../data/county_level/covid_confirmed_usafacts.csv
curl https://static.usafacts.org/public/data/covid-19/covid_deaths_usafacts.csv --output ../data/county_level/covid_deaths_usafacts.csv
curl https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv --output ../data/county_level/covid_nytimes.csv

### Download updated version of County Health Rankings
curl https://www.countyhealthrankings.org/sites/default/files/media/document/2020%20County%20Health%20Rankings%20Data%20-%20v1.xlsx --output ../data/misc/CountyHealthRankings20.xlsx
python ../src/utils/prep_pop_file.py --county_level_population ../data/misc/CountyHealthRankings20.xlsx --output_path ../data/misc/CountyHealthRankings19.csv

### Download the supporting census files for the State Geojsons
curl https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip --output ../data/misc/state_geojsons.zip
unzip -d ../data/misc/state_geojsons/ ../data/misc/state_geojsons.zip
rm -rf ../data/misc/state_geojsons.zip


# Download UK data

curl -L https://coronavirus.data.gov.uk/downloads/csv/coronavirus-cases_latest.csv --output ../data/uk/cases_uk.csv
curl -L https://coronavirus.data.gov.uk/downloads/csv/coronavirus-deaths_latest.csv --output ../data/uk/deaths_uk.csv
curl https://www.ons.gov.uk/file?uri=%2fpeoplepopulationandcommunity%2fpopulationandmigration%2fpopulationestimates%2fdatasets%2fpopulationestimatesforukenglandandwalesscotlandandnorthernireland%2fmid2019april2020localauthoritydistrictcodes/ukmidyearestimates20192020ladcodes.xls \
    --output ../data/uk/population.xls
# Mapping LTLAS - UTLAS
curl https://opendata.arcgis.com/datasets/3e4f4af826d343349c13fb7f0aa2a307_0.csv --output ../data/uk/ltla_utla_mapping.csv 
curl https://opendata.arcgis.com/datasets/0c3a9643cc7c4015bb80751aad1d2594_0.csv --output ../data/uk/ulta_region_mapping.csv

mkdir ../data/uk/geojsons/
curl https://c19pub.azureedge.net/assets/geo/utlas_v1.geojson --output ../data/uk/geojsons/utlas_v1.geojson
curl https://c19pub.azureedge.net/assets/geo/ltlas_v1.geojson --output ../data/uk/geojsons/ltlas_v1.geojson
curl https://c19pub.azureedge.net/assets/geo/regions_v1.geojson --output ../data/uk/geojsons/regions_v1.geojson
curl https://c19pub.azureedge.net/assets/geo/countries_v1.geojson --output ../data/uk/geojsons/countries_v1.geojson
curl https://c19pub.azureedge.net/assets/population/population.json --output ../data/uk/population.json
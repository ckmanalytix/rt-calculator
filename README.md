# README.md

This codebase is designed to track measures of $R_t$ (the reproduction number), an epidemiological value tracking the growth and spread of a virus. Track the map for your county on [ckmanalytix.com](https://www.ckmanalytix.com)

Simply put, it represents the mean number of cases generated by an infectious individual.  For a number less than 1, this implies less than 1 person, on average, is infected by an infectious individual and therefore leads to a decrease in the spread of the virus. For a number greater than 1, this implies an increasing spread of the virus.

## Initial Setup instructions

To setup your environment using `pip`: 

```bash
pip install -r requirements.txt
```

Recommended `python` versions: > `3.5`

## Quickstart Example

To verify if the codebase can indeed run on your local system, run the following:

```bash
cd ./src/
chmod +x *sh

# The shell files below pull in data and shapefiles for the various geographies
./get_rt.sh
./get_county_data.sh

# To calculate Rts for all counties in a state, run the generate_rt.py files
# You can add multiple states to your list
python generate_rt.py --filtered_states DE --output_path='../data/rt_county/'
# To instead calculate Rt for the entire state, add the --state_level_only flag
python generate_rt.py --filtered_states DE --state_level_only --output_path='../data/rt_state/'

# To consolidate the various states you ran above into one file run the commands below
python generate_rt_combine.py --files_path='../data/rt_state/' --state_level
python generate_rt_combine.py --files_path='../data/rt_county/'

# Finally, to create your HTML output plots, run the command below
python generate_plots.py --country_name="USA"

cd ../
```

If this works correctly, you should see a folder for "USA" created in the `output/`
folder. 

Navigate to `./output/USA/country_county_static.html` to play around locally.


## FAQs

1. What geographies are currently supported?
- Currently the US and England are the only supported geographies.


2. How do I add a new geography?
- To add a new geography, you require access to Daily Case Values for your country, states and counties (or equivalent geographical breakdowns).
- This codebase has expanded to include England in an updated iteration. You could build a similar pipeline using 
[this notebook](./notebooks/UK-Rt-Generation.ipynb) as a kick-off point.


3. The codebase takes very long to run. What can I do to speed things up?
- Powerful computation could greatly boost calculations (especially at the county level). Additional tips and tricks can be viewed in the [rt-condax.sh](./rt-condax.sh) file (as an example). Theano's thread locks limit parallelization. This can be overcome by leveraging the `theano.NOBACKUP` flag. You can read further about Theano flags [here](http://deeplearning.net/software/theano/library/config.html?highlight=flags)

## Data Sources

Case Count Data is sourced from: [USA Facts](https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/) (USA) and [Data.gov.uk](https://coronavirus.data.gov.uk/) (England).

Population Data sourced from: [County Health Rankings](https://www.countyhealthrankings.org/) (USA) and Data.gov.uk (England)"  

## License

This repo is licensed under [the MIT license](./LICENSE.txt)

## References

1. Bettencourt, Ribeiro (2008). Real Time Bayesian Estimation of the Epidemic Potentialof Emerging Infectious Diseases. Link [here](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2366072/pdf/pone.0002185.pdf)
2. Salvatier J., Wiecki T.V., Fonnesbeck C. (2016) Probabilistic programming in Python using PyMC3. PeerJ Computer Science 2:e55 [DOI: 10.7717/peerj-cs.55](https://doi.org/10.7717/peerj-cs.55)
3. [Kevin Systrom](https://twitter.com/kevin) and [Thomas Vladeck](https://twitter.com/tvladeck) (2020). Realtime Rt mcmc. Source Notebook Link [here](https://github.com/k-sys/covid-19/blob/master/Realtime%20Rt%20mcmc.ipynb)
4. Oliphant, T. E. (2006). A guide to NumPy (Vol. 1). Trelgol Publishing USA.
5. Kumar, Ravin and Colin, Carroll and Hartikainen, Ari and Martin, Osvaldo A (2019). [ArviZ](https://github.com/arviz-devs/arviz) a unified library for exploratory analysis of Bayesian models in Python.
6. Plotly Technologies Inc. Collaborative data science. Montréal, QC, 2015. Link: [here](https://plot.ly).

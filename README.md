
# 🔎 DAO Governance Analysis

## Prerequisites

A Python 3.10+ environment.
The dependencies listed in [requirements-dev.txt](./requirements-dev.txt):

```bash
pip install -r ./requirements-dev.txt
```

## Plutocracy Report

```console
$ python pluto_report.py --help
Usage: pluto_report.py [OPTIONS]

Options:
  -n, --number INTEGER RANGE  Get the top `n` DAOs. Has no effect if `-d` is
                              used.  [default: 60; 1<=x<=60]
  -d, --dao_name TEXT         Name of the DAO you would like to run the report
                              on. [default: Get all DAOs]
  -t, --use_tally             Whether or not to run the report on on-chain vote data.
                              [default: Use Off-Chain data]
  -b, --blacklist JSON_LIST   Exclude the listed DAOs. e.g. '["Fei", "OlympusDAO"]'
  --help                      Show this message and exit.
```

The notebooks found in `./book` depend on the `.csv.gzip` files the script generated and stored in the `./plutocracy_data/full_report` directory.

To edit and run the notebooks it's recommended that you use the [Jupyter Notebook Interface](https://github.com/jupyter/notebook):

```console
jupyter notebook ./book/
```

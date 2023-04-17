# DAO Governance Analysis
### Prerequisites
A Python 3.9+ environment.
The dependencies listed in [requirements.txt](./requirements.txt):
```bash
pip install -r ./requirements.txt
```
## Plutocracy Report
### Usage
```bash
python pluto_report.py [--dao_name <name_of_dao>]
```

By default, it will run the report for the top 60 DAOs. If the name of the DAO is passed in the `--dao_name` option (e.g. `Aave`), it will attempt to search for the given DAO and generate the data for its report for its last 10 proposals.

Two `.csv.gzip` files will be generated in the cloned project's `plutocracy_data/full_report` directory as `plutocracy_report.csv.gzip` and `plutocracy_report_filtered.csv.gzip`.

The report generated depends on these files to update the data on the notebooks in `./book/`.

To run the notebook, you can run `jupyter notebook ./book/` and access the book, via your browser, from the provided link in your terminal.

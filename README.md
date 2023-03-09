# DAO Governance Analysis
### Prerequisites
A python 3.9+ environment.
The dependencies listed in [requirements.txt](./requirements.txt):
```bash
pip install -r ./requirements.txt
```
## Plutocracy Report
### Usage
```bash
python pluto_report.py
```
Two `.csv.gzip` files will be generated in the cloned project's `plutocracy_data/full_report` directory as `plutocracy_report.csv.gzip` and `plutocracy_report_filtered.csv.gzip`.

The report generated depends on these files to update the data on the notebooks in `./book/`.

To run the notebook, you can run `jupyter notebook ./book/` and access the book, via your browser, from the provided link in your terminal.

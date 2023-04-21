# DAO Governance Analysis
### Prerequisites
A Python 3.9+ environment.
The dependencies listed in [requirements.txt](./requirements.txt):
```bash
pip install -r ./requirements.txt
```
## Whale Pivotality Data
### Usage
```bash
python pluto_report.py [--dao_name <name_of_dao>]
# e.g. python pluto_report.py --dao_name "euler finance"
```

By default, it will run the report for the top 60 DAOs. If the name of the DAO is passed in the `--dao_name` option (e.g. `Aave`), it will attempt to search for the given DAO and generate the data for its report for its last 10 proposals.

Two `.csv.gzip` files will be generated in the cloned project's `plutocracy_data/full_report` directory as `plutocracy_report.csv.gzip` and `plutocracy_report_filtered.csv.gzip`.

The report generated depends on these files to update the data on the notebooks in `./book/`.

To view and edit the Notebook, you can run `jupyter notebook ./book/` and access the book from the provided link in your terminal.

### Expansion

If you would like to create a report for a single DAO, we encourage you to fork this project and create your own Notebook (i.e. a `.ipynb`) in `/book/` based on your own needs.

Once done, you will need to create a Github Action (a `.yml` file found in the [workflows](./.github/workflows/) directory) to build and deploy your Notebook. Here's an [example action](./.github/workflows/publish_analysis.yml) you can use to help create your own.

For more on deploying Jupyter Notebooks, please refer to their [documentation](https://jupyterbook.org/en/stable/publish/gh-pages.html) on deploying Notebooks using Github Actions.

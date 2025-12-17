# muniAdvisors_pbf
For the paper with Dan Garrett on Municipal Advisors for the Public Budgeting and Finance journal.

First, we need the comphrehensive list of CIK firms that submit Form MA filings to [the SEC](https://www.sec.gov/data-research/statistics-data-visualizations/municipal-advisors). To obtain this, we download the monthly filings on the SEC webpage using [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step1_getCIKma_SEC.ipynb).

Next, we use the unique values of the CIK firms to obtain the Form MA filings from the SEC EDGAR using [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step2_getSEC_maFilings.ipynb).The code will obtain both .txt and .xml versions of the filings.

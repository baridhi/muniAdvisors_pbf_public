# muniAdvisors_pbf
All code used to collect data for this paper are housed in [.\Code](https://github.com/baridhi/muniAdvisors_pbf_public/tree/main/Code) subfolder of this repository.
First, we need the comphrehensive list of CIK firms that submit Form MA filings to [the SEC](https://www.sec.gov/data-research/statistics-data-visualizations/municipal-advisors). To obtain this, we download the monthly filings on the SEC webpage using [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step1_getCIKma_SEC.ipynb). The output data from this step is saved [here](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Data/sec_cik_ma.csv).

Next, we use the unique values of the CIK firms to obtain the Form MA filings from the SEC EDGAR using [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step2_getSEC_maFilings.ipynb).The code will obtain both .txt and .xml versions of the filings.

Having downloaded the filings (Form MA; Form MA-W; and Form MA-I), we now proceed to construct a tabular dataframe by parsing each of the (txt) types. The following code is used to extract:
  - Form MA data (Data/output_step3k.csv) with [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step3_getDF_formMA_Txt.ipynb).
  - Form MA-W data (Data/sec_form_ma_w.csv) with [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step4_getDF_formMA_W.ipynb).
  - Form MA-I data (Data/sec_form_ma_i.csv) with [this code](https://github.com/baridhi/muniAdvisors_pbf_public/blob/main/Code/Step5_getDF_formMA_I.ipynb).

For reference, we also provide the snapshot of data files (Form MA; Form MA-W; and Form MA-I) downloaded at the time of writing this paper. These files are included in the [.\Data](https://github.com/baridhi/muniAdvisors_pbf_public/tree/main/Data) subfolder of this repository.

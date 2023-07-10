# Stock CB Conversion Analyzer

This project is a tool that analyzes the stock issuance data from the Korea Exchange (KRX) and selects domestic CB conversion stocks. The program is written in Python and utilizes libraries such as FinanceDataReader and BeautifulSoup.

## Features

- Downloads the latest stock issuance data from KRX and performs data analysis.
- Extracts stocks with the reason for issuance being "국내CB전환" (domestic CB conversion).
- Retrieves the previous day's stock prices for each stock to be used in the analysis.
- Retrieves the price and issued stock quantity of CBs.
- Calculates the total number of issued CB stocks and the average price.
- Retrieves the total number of issued stocks.
- Filters and selects stocks based on specific conditions.

## Installation and Usage

1. Download the project code.
```
git clone https://github.com/hgnx/stock-cb-analyzer.git
```

2. Install the required libraries.
```
pip install -r requirements.txt
```

3. Run the program.
```
python main.py
```

## Future Improvements

- Improve Performance: Currently, the program searches the page like `date+000000` which takes a long time to complete. To enhance performance, consider implementing a mechanism to only search for existing items in the future. This would require a detailed examination of the web page structure of KRX.

## Disclaimer
This script is for informational purposes only and should not be used as the basis for any financial decisions. I take no responsibility for any personal financial loss. Use this script at your own risk.
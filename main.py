import pandas as pd
import requests
import datetime
import re
import os
import FinanceDataReader as fdr
import contextlib
import time
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from html_table_parser import parser_functions

# Days option for searching
days                            = 15

thisyear                        = str(datetime.datetime.now().year)
today                           = datetime.date.today()
from_date                       = str(today - datetime.timedelta(days=days))

ua                              = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36"

URL                             = f"https://kind.krx.co.kr/corpgeneral/stockissuelist.do?method=searchStockIssueList&pageIndex=1&currentPageSize=3000&searchCodeType=&searchCorpName=&orderMode=1&orderStat=D&repIsuSrtCd=&repIsuCd=&forward=download&searchMode=&bzProcsNo=&isurCd=&paxreq=&outsvcno=&marketType=all&comAbbrv=&listingType=2&fromDate={from_date}&toDate={today}"
file                            = requests.get(URL, headers={"User-Agent": ua}, allow_redirects=True)
open("주식발행내역.xls", "wb").write(file.content)

# Read "주식발행내역.xls" and convert to DataFrame
stock_temp                      = pd.read_html('주식발행내역.xls')
stock_temp                      = pd.DataFrame(stock_temp[0])
stock_temp["종목코드"]            = stock_temp["종목코드"].apply(lambda x: str(x).zfill(6))
if os.path.isfile("주식발행내역.xls"):
    os.remove("주식발행내역.xls")

# Extract only DataFrames whose "발행사유" is "국내CB전환"
cb_conversion                   = stock_temp[stock_temp['발행사유'] == '국내CB전환']

# Create dictionary for company name and stock code
cb_stock                        = cb_conversion.groupby('회사명')['회사명'].count().to_dict()
cb_stock                        = {k: [{'CB발행가': []}, {'발행주식수': []}] for k in cb_stock}
company_dict                    = cb_conversion.set_index('회사명')['종목코드'].to_dict()

# Create date and search range then merge
date_range                      = [(today + pd.Timedelta(days=1) - pd.Timedelta(days=i)).strftime("%Y%m%d")
                                  for i in range(1, days+2)]
code_range                      = [str(i).zfill(6) for i in range(1001)]
search_list                     = [date + code for date in date_range for code in code_range]

# Fetch stock price of yesterday
for company_name, company_code in company_dict.items():
    df                          = fdr.DataReader(company_code, start=thisyear)
    cb_stock[company_name].extend([
                                    {"종목코드": company_code},
                                    {"1일전주가": df['Close'].iloc[-2] if len(df['Close']) > 1 else None}
                                 ])

# Fetch CB price and issued CB
def fetch_url(url):
    with contextlib.suppress(Exception):
        stock_req               = requests.get(url, headers={"User-Agent": ua})
        stock_soup              = BeautifulSoup(stock_req.text, "html.parser")
        stock_name              = stock_soup.find("table", {"class": "detail type-02 chain-head"})
        stock_method            = stock_soup.find("table", {"class": "detail type-02 mt5 tdr chain-foot"})

        if stock_name is not None and stock_method is not None:
            table_subject       = parser_functions.make2d(stock_name)
            table_content       = parser_functions.make2d(stock_method)

            if table_content[0][2] == "국내CB전환":
                key             = table_subject[0][3]
                if key in cb_stock:
                    cb_stock[key][0]["CB발행가"].append(table_content[1][3])
                    cb_stock[key][1]["발행주식수"].append(table_content[2][2])
        time.sleep(0.05)
urls                            = [f"https://kind.krx.co.kr/corpgeneral/stockissuelist.do?method=searchStockIssueDetail&pageIndex=1&currentPageSize=3000&searchCodeType=&searchCorpName=&orderMode=1&orderStat=D&repIsuSrtCd=&repIsuCd=&forward=searchStockIssueDetail&searchMode=&bzProcsNo={i}&isurCd=&paxreq=&outsvcno=&marketType=all&comAbbrv=&listingType=2&fromDate={from_date}&toDate={today}" for i in search_list]

# Max_workers is 2. More than 2 will cause IP blocking for a while.
with ThreadPoolExecutor(max_workers=2) as executor:
    executor.map(fetch_url, urls)

pattern                         = re.compile("\D")

# Convert string to integer and calculate total number of issued CB
for company_name, company_data in cb_stock.items():
    company_data[1]["발행주식수"] = [int(pattern.sub("", num)) for num in company_data[1]["발행주식수"]]
    company_data[0]["CB발행가"]  = [int(pattern.sub("", price)) for price in company_data[0]["CB발행가"]]
    company_data.append({"발행주식수합계": sum(company_data[1]["발행주식수"])})

# Calculate average price of issued CB price
for company_name, company_data in cb_stock.items():
    cb_sum                      = sum(cb_price * issued_stocks / company_data[4]["발행주식수합계"] for cb_price, issued_stocks
                                  in zip(company_data[0]["CB발행가"], company_data[1]["발행주식수"]))
    company_data.append({"CB발행가평균": round(cb_sum)})

# Fetch total issued stock numbers
for company_name, company_data in cb_stock.items():
    stock_info_url              = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={company_data[2]['종목코드']}"
    company_data_req            = requests.get(stock_info_url, headers={"User-Agent": ua})
    company_data_soup           = BeautifulSoup(company_data_req.text, "html.parser")

    stock_table                 = company_data_soup.find("table", {"class": "gHead"})
    table_total_num             = parser_functions.make2d(stock_table)
    total_num_temp              = table_total_num[6][1].split("/")[0]
    total_num_result            = int(pattern.sub("", total_num_temp))
    company_data.append({"총주식수": total_num_result})

# Filter by condition
filtered_ticker                 = [company_name for company_name, company_data in cb_stock.items()
                                   if (company_data[3].get("1일전주가") <= company_data[5].get("CB발행가평균") * 1.05
                                       and round((company_data[4].get("발행주식수합계") / company_data[6].get("총주식수")) * 100, 2) >= 1.0)
                                   ]

print(filtered_ticker)
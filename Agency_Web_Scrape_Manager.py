from bs4 import BeautifulSoup
from requests import get
import pandas as pd
import re

# Extract gage URLs from csv and convert to a list
url_csv = pd.read_csv ('USGS_Funders_Temp_URLS.csv')
url_csv_list = url_csv.values.T[2].tolist()
STA_csv_list = url_csv.values.T[0].tolist()

# Lists to store scraped data in
manage_station_IDs = []
manage_names = []

for url in url_csv_list:
  # Extract text content from website
  soup = BeautifulSoup(get(url).text, "html.parser")
  for i in soup.find_all('div', attrs={'class':"stationContainer"}):
    manager = (str(i).split('</form>')[1].split('<br/><br/>')[0].strip())

    # Append managing agency information to list
    manage_names.append(manager) 

    # Append STA
    STA = soup.find_all ('title')
    STA_clean_a = STA[0].text.strip()
    STA_clean_b = re.sub('[^0-9]','', STA_clean_a)
    if STA_clean_b.startswith('0'):
      STA_clean_c = STA_clean_b[:8]
    elif STA_clean_b.startswith('1'):
      STA_clean_c = STA_clean_b[:8]
    else:
      STA_clean_c = STA_clean_b[:15]

    manage_station_IDs.append(STA_clean_c) 

# Store data in a dataframe
managesheet = pd.DataFrame.from_dict({
      "STA": manage_station_IDs,
      "manager":manage_names
      }, orient ='index')
managesheet = managesheet.transpose()

# Export dataframe to a csv file
managesheet.to_csv ('Manager_Result.csv')

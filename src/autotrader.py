import bs4
import requests
import multiprocessing
import datetime
import math
import json
from multiprocessing.pool import ThreadPool
from config import auth_to_sheet, get_proxy, send_mail, HEADERS, AUTO_TRADE_TABLE, CRITERIES_TABLE


class AutoTraderScraper():
    def __init__(self):
        super().__init__()
        self.criteries_sheet = auth_to_sheet().worksheet_by_title(CRITERIES_TABLE)
        self.result_sheet = auth_to_sheet().worksheet_by_title(AUTO_TRADE_TABLE)
        self.search_radius = self.criteries_sheet.get_value("B6")
        self.post_code = self.criteries_sheet.get_value("B7")
        self.base_url = "https://www.autotrader.ca/cars"

    def get_cars(self, start_year, end_year, maker, model, seller_type, condition, keywords=''):
        links = []
        item_on_page = 1000
        url = f'{self.base_url}/{maker}/{model}/on/milton/'
        payload = {
            'rcp': f'{item_on_page}',
            'rsc': str(0), #page number
            'srt': str(3),
            'yRng': f'{start_year},{end_year}',
            'prx': f'{self.search_radius}',
            'prv': 'Ontario',
            'loc': f'{self.post_code}',
            'hprc': True,
            'wcp': True,
            'sts': f'{condition}',
            'adtype': f'{seller_type}',
            'showcpo': str(1),
            'inMarket': 'advancedSearchs'
        }
        if keywords != '':
            payload['kwd'] = keywords

        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.proxies.update(get_proxy())
        response = session.get(url, headers=HEADERS, params=payload)
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        cars_count = soup.find('div', {'class': 'results-count-wrapper'}).find('span', {'id': 'sbCount'}).text
        page_count = math.ceil(int(cars_count)/15)
        j_data = soup.find('div', {'class': 'col-xs-12 disable-on-search'}).find('script', {'type': 'application/ld+json'})
        json_data = json.loads(str(j_data).replace('</script>', '').replace('<script type="application/ld+json">', '').strip())
        for data in json_data['offers']['offers']:
            links.append('https://www.autotrader.ca'+ data['url'])

        return links

    def get_search_settings(self):
        data = self.criteries_sheet.get_values(start='A10', end='G10000')
        return data

    def main(self):
        data = []
        new_links = []
        pool = ThreadPool(multiprocessing.cpu_count())
        result = pool.starmap(self.get_cars, self.get_search_settings())
        for link_list in result:
            for link in link_list:
                if link not in data:
                    data.append(link)

        if len(data):
            current_data = self.result_sheet.get_values(start='A2', end='A10000')
            current_data_list = []
            for d in current_data:
                current_data_list.append(d[0])
            if current_data_list != data:
                for link in data:
                    if link not in current_data_list:
                        new_links.append(link)
                
                now = datetime.datetime.now()
                if len(current_data_list) == 1:
                    self.result_sheet.update_col(index=1, values=new_links, row_offset=1)
                    self.result_sheet.update_col(index=2, values=[f'{now.year}/{now.month}/{now.day}-{now.hour}:{now.minute}' for i in range(len(new_links))], row_offset=1)
                else:
                    link_for_mail = []
                    for link in new_links:
                        if link not in current_data_list:
                            self.result_sheet.insert_rows(1, values=[link, f'{now.year}/{now.month}/{now.day}-{now.hour}:{now.minute}'], inherit=True)
                            link_for_mail.append(link)
                    if link_for_mail:
                        mail_text = 'New links have been added to the table, please check out:\n' + '\n'.join([f'{ref}\n' for ref in link_for_mail])
                        send_mail(mail_text)

            else:
                print("nothing new")


if __name__ == "__main__":
    scraper = AutoTraderScraper()
    scraper.main()

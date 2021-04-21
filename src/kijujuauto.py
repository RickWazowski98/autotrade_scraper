import bs4
import requests
import multiprocessing
import datetime
import json
from multiprocessing.pool import ThreadPool
from config import auth_to_sheet, get_proxy, send_mail, KJ_HEADERS, KIJIJI_AUTO_TABLE, CRITERIES_TABLE


class KijijiAutoScraper():
    def __init__(self):
        super().__init__()
        self.criteries_sheet = auth_to_sheet().worksheet_by_title(CRITERIES_TABLE)
        self.result_sheet = auth_to_sheet().worksheet_by_title(KIJIJI_AUTO_TABLE)
        self.search_radius = self.criteries_sheet.get_value("B6")
        self.post_code = self.criteries_sheet.get_value("B7")
        self.base_url = 'www.kijijiautos.ca'
        self.base_search_url = 'https://www.kijijiautos.ca/cars'

    def get_cars(self, start_year, end_year, maker, model, seller_type, condition, keywords=''):
        links = []
        if seller_type == 'Private':
            transform_seller_type = 'FSBO'
        elif seller_type == 'Diller':
            transform_seller_type = 'DILLER'
        else:
            transform_seller_type = ''
        """
        if keywords == '':
            url = f'{self.base_search_url}/{str(maker).lower()}/{model}/{str(condition).lower()}/#con={str(condition).upper()}&od=down&sb=relv3&st={str(transform_seller_type)}&yc={start_year}%3A{end_year}'
        else:
            url = f'{self.base_search_url}/{str(maker).lower()}/{model}/{str(condition).lower()}/#con={str(condition).upper()}&od=down&q={str(keywords).lower()}&sb=relv3&st={str(transform_seller_type)}&yc={start_year}%3A{end_year}'
        """
        url = 'https://www.kijijiautos.ca/consumer/srp/by-params'
        payload = {
            # 'url': f'/cars/{str(maker).lower()}/{str(model).lower()}/{str(condition).lower()}/',
            'sb': 'relv3',
            'od': 'down',
            # 'ms': f'{str(maker).lower()};{str(model).lower()}',
            'yc': f'{start_year}:{end_year}',
            'st': transform_seller_type,
            'ps': '0',
            'psz': '20',
            'vc': 'Car',
            # 'con': f'{str(condition).upper()}',
            'll': '43.52318260000001,-79.8547073',
            'rd': self.search_radius
        }
        if keywords != '':
            payload['q'] = keywords
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        session.proxies.update(get_proxy())
        url2 = 'https://www.kijijiautos.ca/consumer/srp/by-params?sb=relv3&od=down&ms=9000%3B16&yc=2015%3A2019&st=FSBO&ps=0&psz=20&vc=Car&ll=43.52318260000001%2C-79.8547073&rd=500'
        resp = session.get(url, headers=KJ_HEADERS, params=payload)
        print(resp.url)
        print(url2)
        print(resp)
        # print(str(maker).encode('ascii'))
        """
        response = session.get(url, headers=KJ_HEADERS)
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        car_blocks = soup.find('head').find_all('script', {'type': 'application/ld+json'})
        for car in car_blocks[1:]:
            j_car_info = json.loads(str(car).replace('<script data-rh="true" type="application/ld+json">', '').replace('</script>', ''))
            sku = j_car_info['sku']
            link = f'{self.base_search_url}/{str(maker).lower()}/{model}/{str(condition).lower()}/#vip={sku}'
            links.append(link)
        """
        
        return links

        


    def get_search_settings(self):
        data = self.criteries_sheet.get_values(start='A10', end='G10000')
        return data

    def main(self):
        one_car = self.get_search_settings()[0]
        result = self.get_cars(one_car[0], one_car[1], one_car[2], one_car[3], one_car[4], one_car[5], one_car[6])
        print(len(result))



if __name__ == "__main__":
    scraper = KijijiAutoScraper()
    scraper.main()
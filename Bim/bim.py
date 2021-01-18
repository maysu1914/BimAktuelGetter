from concurrent.futures.thread import ThreadPoolExecutor
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from Bim import helpers


class Bim:
    url = 'https://www.bim.com.tr/default.aspx'
    campaign_query = '?Bim_AktuelTarihKey='

    def __init__(self, campaign_id):
        self.campaign_id = campaign_id
        self.products = {}  # '1':{'brand':'', 'name':'', 'features':[], 'price': '', 'image':'', 'url':''}
        self.kiyasla_products = []
        self.product_names = []  # for a special need

    @staticmethod
    def get_content(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        counter = 3
        while counter != 0:  # bim bazen anasayfaya yönlendirme yapiyor
            try:
                page = requests.get(url, timeout=3, headers=headers)
                _url = page.url
                if _url != url:
                    print(counter, end='')
                    counter -= 1  # try 'counter' times if site redirecting to somewhere
                    continue
                counter = 0
                return BeautifulSoup(page.content, "lxml")
            except requests.exceptions.RequestException as e:  # try always if some connection error occurred
                print('-', end='')
        print('')
        return BeautifulSoup('', "lxml")

    def get_all_products(self):
        page_content = self.get_content(self.url + self.campaign_query + self.campaign_id)
        product_contents = page_content.select(".product:not(.justImage)")
        campaign_name = page_content.select("a.active.subButton")[0].text.strip() \
            if page_content.select("a.active.subButton") else 'Campaign name not found.'
        print(campaign_name)
        print(len(product_contents), 'products found!\n')

        threads = []
        for product_id, product_content in zip(range(len(product_contents)), product_contents):
            threads.append(ThreadPoolExecutor().submit(Bim.get_product, product_id, str(product_content)))

        for thread in threads:
            product_id, product = thread.result()
            self.products[product_id] = product

            # for some special usages
            kiyasla_style = {"u": helpers.get_product_name(product, 120),
                             "f": product['price'],
                             "k": product['image']}
            self.kiyasla_products.append(kiyasla_style)

            if product['name'].strip() not in self.product_names:
                self.product_names.append(product['name'].strip())
            print(kiyasla_style['u'], kiyasla_style['f'])

        return self.products

    @staticmethod
    def get_product(product_id, product_content):
        product_content = BeautifulSoup(product_content, "lxml")
        product = Bim.get_features_from_list(product_content)
        product = Bim.add_features_from_detail(product)
        product['features'] = helpers.get_optimized_list(product['features'])

        return product_id, product

    @staticmethod
    def get_features_from_list(product_content):
        try:
            product_brand = product_content.find("div", "descArea").find("h2", "subTitle").text \
                if product_content.find("div", "descArea").find("h2", "subTitle") else ''
            product_name = product_content.find("div", "descArea").find("h2", "title").text \
                if product_content.find("div", "descArea").find("h2", "title") else ''
            product_price_left = product_content.find("div", "quantify").text.replace(".", '').replace(",", ".").strip() \
                if product_content.find("div", "quantify") else ''
            product_price_right = product_content.find("div", "kusurArea").find("span", "number").text.strip() \
                if product_content.find("div", "kusurArea").find("span", "number") else ''
            product_price = product_price_left + product_price_right
            product_link = urljoin(Bim.url, product_content.find("div", "imageArea").find("a")['href'])
            features = []

            for feature in product_content.find("div", "textArea").select('span.text'):
                feature = feature.text
                if feature.find(',') > -1 and \
                        feature.find(',') + 1 < len(feature) and \
                        not feature[feature.find(',') + 1].isdigit():
                    mini_features = feature.split(',')
                    for mini_feature in mini_features:
                        mini_feature = helpers.get_optimized_text(
                            mini_feature.replace('•', '').replace('’', "'"))
                        if mini_feature.lower() in product_name.lower():
                            continue
                        else:
                            features.append(mini_feature)
                else:
                    feature = helpers.get_optimized_text(
                        feature.replace('•', '').replace('’', "'"))
                    if feature.lower() in product_name.lower():
                        continue
                    else:
                        features.append(feature)

            return {'brand': product_brand, 'name': product_name, 'features': features,
                    'price': product_price, 'image': '', 'url': product_link}
        except Exception as e:
            print("add_features_from_list", e)
            raise

    @staticmethod
    def add_features_from_detail(product):
        try:
            page_content = Bim.get_content(product['url'])
            product_detail = page_content.find("div", "detailArea")
            product_image = urljoin(Bim.url, quote(product_detail.find("a", "fotoZoom")['data-src']))
            features = []

            for feature in product_detail.find("div", 'textArea').text.split('\n'):  # ÜRÜN ÖZELLIKLERINI ÇEKMEK
                if feature.find(',') > -1 and \
                        feature.find(',') + 1 < len(feature) and \
                        not feature[feature.find(',') + 1].isdigit():
                    mini_features = feature.split(',')
                    for mini_feature in mini_features:
                        mini_feature = helpers.get_optimized_text(
                            mini_feature.replace('•', '').replace('’', "'"))
                        if mini_feature.lower() in product['name'].lower():
                            continue
                        else:
                            features.append(mini_feature)
                else:
                    feature = helpers.get_optimized_text(
                        feature.replace('•', '').replace('’', "'"))
                    if feature.lower() in product['name'].lower():
                        continue
                    else:
                        features.append(feature)

            product['image'] = product_image
            product['features'] += features

            return product
        except Exception as e:
            print("add_features_from_detail", e)
            raise

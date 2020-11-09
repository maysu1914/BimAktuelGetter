import json
import re
from multiprocessing import Pool
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class File:
    filename = 'file'

    def __init__(self, filename=filename):
        self.filename = filename
        self.append_to_filename()

    def append_to_filename(self):
        self.filename += input('Filename: {}'.format(self.filename))

    def export(self, data):
        with open('{name}.txt'.format(name=self.filename), 'w', encoding='utf-8') as file:
            file.write(data)
        print('\n{name}.txt created.'.format(name=self.filename))


class Bim:
    url = 'https://www.bim.com.tr/default.aspx'
    campaign_query = '?Bim_AktuelTarihKey='

    def __init__(self):
        self.campaign_id = self.input_campaign_id()
        self.products = {}  # '1':{'brand':'', 'name':'', 'features':[], 'price': '', 'image':'', 'url':''}
        self.kiyasla_products = []
        self.product_names = []  # for a special need
        self.product_operations = self.Product()

    @staticmethod
    def input_campaign_id():
        return input('Campaign ID: ')

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

        with Pool() as pool:
            processes = []
            for product_id, product_content in zip(range(len(product_contents)), product_contents):
                processes.append(pool.apply_async(Bim.get_product, (product_id, str(product_content))))

            for process in processes:
                product_id, product = process.get()
                self.products[product_id] = product

                # for some special usages
                kiyasla_style = {"u": Bim.Product.get_product_name(product, 120),
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
        product = Bim.add_features_from_list(product_content)
        product = Bim.add_features_from_detail(product)
        product['features'] = Bim.Product.get_optimized_list(product['features'])

        return product_id, product

    @staticmethod
    def add_features_from_list(product_content):
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
                        mini_feature = Bim.Product.get_optimized_text(
                            mini_feature.replace('•', '').replace('’', "'"))
                        if mini_feature.lower() in product_name.lower():
                            continue
                        else:
                            features.append(mini_feature)
                else:
                    feature = Bim.Product.get_optimized_text(
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
            product_image = urljoin(Bim.url, product_detail.find("a", "fotoZoom")['data-src'])
            features = []

            for feature in product_detail.find("div", 'textArea').text.split('\n'):  # ÜRÜN ÖZELLIKLERINI ÇEKMEK
                if feature.find(',') > -1 and \
                        feature.find(',') + 1 < len(feature) and \
                        not feature[feature.find(',') + 1].isdigit():
                    mini_features = feature.split(',')
                    for mini_feature in mini_features:
                        mini_feature = Bim.Product.get_optimized_text(
                            mini_feature.replace('•', '').replace('’', "'"))
                        if mini_feature.lower() in product['name'].lower():
                            continue
                        else:
                            features.append(mini_feature)
                else:
                    feature = Bim.Product.get_optimized_text(
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

    class Product:

        @staticmethod
        def is_quantity(text):
            volumes = ['ml', 'kg', 'l', 'lt', 'g', 'gr', 'cc', 'cm', 'mah', 'w', 'db', 'mm', 'watt', 'gb']
            quantities = ["'lı", "'li", "'lu", "'lü", "kapsül", "in 1", "numara", "yaş", "adet", "yıkama",
                          "yaprak", "çeşit"]
            words = ["beden"]
            for feature_types in [volumes, quantities]:
                for feature in feature_types:
                    occurrences = [m.start() for m in re.finditer(feature, text)]
                    for occurrence in occurrences:
                        if feature in text and occurrence - 1 > -1 and \
                                (
                                        (
                                                text[occurrence - 1].isdigit() and
                                                (
                                                        occurrence + len(feature) == len(text) or
                                                        text[occurrence + len(feature)] == ' '
                                                )
                                        ) or
                                        (
                                                text[occurrence - 1] == ' ' and
                                                occurrence - 2 > -1 and
                                                text[occurrence - 2].isdigit() and
                                                (
                                                        occurrence + len(feature) == len(text) or
                                                        text[occurrence + len(feature)] == ' '
                                                )
                                        )
                                ):
                            return True

            for word in words:
                if word in text and text.find(word) - 1 > -1 and text[text.find(word) - 1] == ' ' and \
                        (
                                text.find(word) + len(word) == len(text) or text[text.find(word) + len(word)] == ' '
                        ):
                    return True
            return False

        @staticmethod
        def get_product_name(product, char_limit):
            brand = product['brand']
            name = product['name']
            features = product['features']

            final_name = Bim.Product.get_optimized_text(brand + ' ' + name)
            features_to_add = []
            char_counter = len(
                final_name) + 3  # else durumunda eklenen ' - ' karakterleri için +3 yapildi, diger durumlarda sayac gecersiz zaten

            if not features:
                return final_name

            elif len(features) == 1:
                return final_name + ' ' + features[0].strip()

            else:
                for feature in features:
                    if char_counter + len(feature) + 2 <= char_limit:
                        char_counter = char_counter + len(feature) + 2
                        features_to_add.append(feature)
                    else:
                        break
                return final_name + ' - ' + ', '.join(features_to_add)

        @staticmethod
        def get_optimized_list(_list):
            # print('in', _list)
            new_list = []

            for element in _list:
                if element.lower() not in [el.lower() for el in new_list] and not any(
                        element != el and element in el for el in _list):
                    if Bim.Product.is_quantity(element.lower()):
                        new_list.insert(0, element)
                    else:
                        new_list.append(element)
            # print('out', new_list)
            return new_list

        @staticmethod
        def get_optimized_text(string):
            cleaned_string = ' '.join(string.split())
            return cleaned_string


if __name__ == "__main__":
    bim_aktuels = Bim()
    bim_aktuels.get_all_products()

    kiyasla_datas = bim_aktuels.kiyasla_products
    final_output = bim_aktuels.product_names
    if kiyasla_datas:
        print('\n{}\n'.format(', '.join(final_output)))
        File('bim_ready_').export(str(json.dumps(kiyasla_datas)).replace('"u": ', '"u":ur'))

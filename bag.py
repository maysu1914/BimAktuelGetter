import json
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class File:

    @staticmethod
    def export(filename, data):
        with open('{name}.txt'.format(name=filename), 'w', encoding='utf-8') as file:
            file.write(data)
        print('\n{name}.txt olusturuldu.'.format(name=filename))


class Bim:
    url = 'https://www.bim.com.tr/default.aspx'
    aktuel_query = '?Bim_AktuelTarihKey='

    def __init__(self):
        self.aktuel_key = self.input_aktuel_key()
        self.aktuel_name = self.input_aktuel_name()
        self.products = {}  # '1':{'brand':'', 'name':'', 'features':[], 'price': '', 'image':'', 'url':''}
        self.kiyasla_products = []
        self.product_names = []  # for a special need
        self.product_operations = self.Product()

    def input_aktuel_key(self):
        return input('AktuelTarihKey= ')

    def input_aktuel_name(self):
        return input('AktuelTarih= ')

    def get_content(self, url):
        _url = ''
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        try:
            counter = 0
            while _url != url:  # bim bazen anasayfaya yönlendirme yapiyor
                counter += 1
                page = requests.get(url, timeout=10, headers=headers)
                _url = page.url
                if counter == 3:
                    if _url != url:
                        return BeautifulSoup('', "lxml")
                    break
            page_content = BeautifulSoup(page.content, "lxml")
            return page_content
        except requests.exceptions.ConnectionError as e:
            raise

    def get_all_products(self):
        page_content = self.get_content(self.url + self.aktuel_query + self.aktuel_key)
        product_contents = page_content.select(".product:not(.justImage)")
        print(len(product_contents), 'aktuels found!\n')

        for product_id, product_content in zip(range(len(product_contents)), product_contents):
            self.add_features_from_list(product_id, product_content)
            self.add_features_from_detail(product_id)

            self.products[product_id]['features'] = self.product_operations.get_optimized_list(
                self.products[product_id]['features'])

            # print(self.products[product_id])

            # for some special usages
            kiyasla_style = {"u": self.product_operations.get_product_name(self.products[product_id], 120),
                             "f": self.products[product_id]['price'],
                             "k": self.products[product_id]['image']}
            self.kiyasla_products.append(kiyasla_style)
            if self.products[product_id]['name'].strip() not in self.product_names:
                self.product_names.append(self.products[product_id]['name'].strip())
            print(kiyasla_style['u'], kiyasla_style['f'])

        return self.products

    def add_features_from_list(self, product_id, product_content):

        product_brand = product_content.find("div", "descArea").find("h2", "subTitle").text \
            if product_content.find("div", "descArea").find("h2", "subTitle") else ''
        product_name = product_content.find("div", "descArea").find("h2", "title").text \
            if product_content.find("div", "descArea").find("h2", "title") else ''
        product_price_left = product_content.find("div", "quantify").text.replace(".", '').replace(",", ".").strip() \
            if product_content.find("div", "quantify") else ''
        product_price_right = product_content.find("div", "kusurArea").find("span", "number").text.strip() \
            if product_content.find("div", "kusurArea").find("span", "number") else ''
        product_price = product_price_left + product_price_right
        product_link = urljoin(self.url, product_content.find("div", "imageArea").find("a")['href'])
        features = []

        for feature in product_content.find("div", "textArea").select('span.text'):
            feature = feature.text
            if feature.find(',') > -1 and \
                    feature.find(',') + 1 < len(feature) and \
                    not feature[feature.find(',') + 1].isdigit():
                mini_features = feature.split(',')
                for mini_feature in mini_features:
                    mini_feature = self.product_operations.get_optimized_text(
                        mini_feature.replace('•', '').replace('’', "'"))
                    if mini_feature.lower() in product_name.lower():
                        continue
                    else:
                        features.append(mini_feature)
            else:
                feature = self.product_operations.get_optimized_text(feature.replace('•', '').replace('’', "'"))
                if feature.lower() in product_name.lower():
                    continue
                else:
                    features.append(feature)

        self.products[product_id] = {'brand': product_brand, 'name': product_name, 'features': features,
                                     'price': product_price, 'image': '', 'url': product_link}

    def add_features_from_detail(self, product_id):
        page_content = self.get_content(self.products[product_id]['url'])
        product_detail = page_content.find("div", "detailArea")
        product_image = urljoin(self.url, product_detail.find("a", "fotoZoom")['data-src'])
        features = []

        for feature in product_detail.find("div", 'textArea').text.split('\n'):  # ÜRÜN ÖZELLIKLERINI ÇEKMEK
            if feature.find(',') > -1 and \
                    feature.find(',') + 1 < len(feature) and \
                    not feature[feature.find(',') + 1].isdigit():
                mini_features = feature.split(',')
                for mini_feature in mini_features:
                    mini_feature = self.product_operations.get_optimized_text(
                        mini_feature.replace('•', '').replace('’', "'"))
                    if mini_feature.lower() in self.products[product_id]['name'].lower():
                        continue
                    else:
                        features.append(mini_feature)
            else:
                feature = self.product_operations.get_optimized_text(feature.replace('•', '').replace('’', "'"))
                if feature.lower() in self.products[product_id]['name'].lower():
                    continue
                else:
                    features.append(feature)

        self.products[product_id]['image'] = product_image
        self.products[product_id]['features'] += features

    class Product:

        def is_quantity(self, text):
            volumes = ['ml', 'kg', 'l', 'lt', 'g', 'gr', 'cc', 'cm', 'mah', 'mah', 'w', 'db', 'mm', 'watt', 'gb']
            quantities = ["'lı", "'li", "'lu", "'lü", "kapsül", "in 1", "in 1", "numara", "yaş", "adet", "yıkama",
                          "yaprak", "çeşit"]
            words = ["beden"]

            for volume in volumes:
                occurrences = [m.start() for m in re.finditer(volume, text)]
                for occurrence in occurrences:
                    if volume in text and occurrence - 1 > -1 and \
                            (
                                    (
                                            text[occurrence - 1].isdigit() and
                                            (
                                                    occurrence + len(volume) == len(text) or
                                                    text[occurrence + len(volume)] == ' '
                                            )
                                    ) or
                                    (
                                            text[occurrence - 1] == ' ' and
                                            occurrence - 2 > -1 and
                                            text[occurrence - 2].isdigit() and
                                            (
                                                    occurrence + len(volume) == len(text) or
                                                    text[occurrence + len(volume)] == ' '
                                            )
                                    )
                            ):
                        return True
            for quantity in quantities:
                occurrences = [m.start() for m in re.finditer(quantity, text)]
                for occurrence in occurrences:
                    if quantity in text and occurrence - 1 > -1 and \
                            (
                                    (
                                            text[occurrence - 1].isdigit() and
                                            (
                                                    occurrence + len(quantity) == len(text) or
                                                    text[occurrence + len(quantity)] == ' '
                                            )
                                    ) or
                                    (
                                            text[occurrence - 1] == ' ' and
                                            occurrence - 2 > -1 and
                                            text[occurrence - 2].isdigit() and
                                            (
                                                    occurrence + len(quantity) == len(text) or
                                                    text[occurrence + len(quantity)] == ' '
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

        def get_product_name(self, product, char_limit):
            brand = product['brand']
            name = product['name']
            features = product['features']

            final_name = self.get_optimized_text(brand + ' ' + name)
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

        def get_optimized_list(self, _list):
            # print('in', _list)
            new_list = []

            for element in _list:
                if element.lower() not in [el.lower() for el in new_list] and not any(
                        element != el and element in el for el in _list):
                    if self.is_quantity(element.lower()):
                        new_list.insert(0, element)
                    else:
                        new_list.append(element)
            # print('out', new_list)
            return new_list

        def get_optimized_text(self, string):
            cleaned_string = ' '.join(string.split())
            return cleaned_string


if __name__ == "__main__":
    bim_aktuels = Bim()
    bim_aktuels.get_all_products()

    kiyasla_datas = bim_aktuels.kiyasla_products
    final_output = bim_aktuels.product_names

    print('\n' + ', '.join(final_output))
    input('\nKaydetmek için bir tusa basin...')
    File.export('bim_hazir_' + bim_aktuels.aktuel_name, str(json.dumps(kiyasla_datas)).replace('"u": ', '"u":ur'))

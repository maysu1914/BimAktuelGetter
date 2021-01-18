import re


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


def get_product_name(product, char_limit):
    brand = product['brand']
    name = product['name']
    features = product['features']

    final_name = get_optimized_text(brand + ' ' + name)
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
                continue
        return final_name + ' - ' + ', '.join(features_to_add)


def get_optimized_list(_list):
    # print('in', _list)
    new_list = []

    for element in _list:
        if element.lower() not in [el.lower() for el in new_list] and not any(
                element != el and element in el for el in _list):
            if is_quantity(element.lower()):
                new_list.insert(0, element)
            else:
                new_list.append(element)
    # print('out', new_list)
    return new_list


def get_optimized_text(string):
    cleaned_string = ' '.join(string.split())
    return cleaned_string

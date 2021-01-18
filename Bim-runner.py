import json

from Bim.bim import Bim
from File.file import File

if __name__ == "__main__":
    campaign = input('Campaign ID: ')
    bim_aktuels = Bim(campaign)
    bim_aktuels.get_all_products()

    kiyasla_datas = bim_aktuels.kiyasla_products
    final_output = bim_aktuels.product_names
    if kiyasla_datas:
        print('\n{}\n'.format(', '.join(final_output)))
        File('bim_ready_').export(str(json.dumps(kiyasla_datas)).replace('"u": ', '"u":ur'))

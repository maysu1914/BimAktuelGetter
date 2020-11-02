from urllib.parse import urlparse
from requests.utils import requote_uri
import requests
from bs4 import BeautifulSoup
from lxml import html
import json
import re

AktuelTarihKey = input('AktuelTarihKey=')
AktuelTarih = input('AktuelTarih=')
url='https://www.bim.com.tr/default.aspx?Bim_AktuelTarihKey='+AktuelTarihKey
base_url='https://www.bim.com.tr'

def createTextFile_raw(filename,data):
    with open('{name}.txt'.format(name=filename),'w',encoding='utf-8') as file:
        file.write(data)
    print('\n{name}.txt olusturuldu.'.format(name=filename))

def cleanExtraSpaces(string):
    cleanedString = ' '.join(string.split())
    return cleanedString

def ozellikListDuzenleyici(_list):
    newList = []

##    print(_list)
    for element in sorted(_list, key=len):
        if element.lower() not in [el.lower() for el in newList] and not any(element != el and element in el for el in _list):
##            print(newList)
##            print(element,'listede yok')
##            print(element,"isquantity:",isquantity(element.lower()))
            if isquantity(element.lower()):
                newList.insert(0,element)
            else:
                newList.append(element)
##    print(newList)
    return newList

def urunAdiOlusturucu(marka,urun_ad,ozellikList,karakterlimiti):
    yeni_urun_ad = cleanExtraSpaces(marka + ' ' + urun_ad)
    eklenecekOzellikler = []
    karakterSayaci = len(yeni_urun_ad) + 3 #else durumunda eklenen ' - ' karakterleri için +3 yapildi, diger durumlarda sayac gecersiz zaten
    
    if not ozellikList:
        return yeni_urun_ad
    
    elif len(ozellikList) == 1:
        return yeni_urun_ad + ' ' + ozellikList[0].strip()
    
    else:
        for ozellik in ozellikList:
            if karakterSayaci + len(ozellik) + 2 <= karakterlimiti:
                karakterSayaci = karakterSayaci + len(ozellik) + 2
                eklenecekOzellikler.append(ozellik)
            else: break
        return yeni_urun_ad + ' - ' + ', '.join(eklenecekOzellikler)
    
def isquantity(text):
##    print(text)
    birimler = ['ml','kg','l','lt','g','gr','cc', 'cm', 'mah', 'mah','w','db','mm','watt','gb']
    adetler = ["'lı","'li","'lu","'lü","kapsül", "in 1", "in 1", "numara", "yaş", "adet","yıkama", "yaprak","çeşit"]
    kelimeler = ["beden"]

    for birim in birimler:
        karsilasmalar = [m.start() for m in re.finditer(birim, text)]
        for karsilasma in karsilasmalar:
##            print(karsilasma)
            if birim in text and karsilasma-1 > -1 and ((text[karsilasma-1].isdigit() and (karsilasma+len(birim) == len(text) or text[karsilasma+len(birim)] ==' ')) or (text[karsilasma-1] == ' ' and karsilasma-2 > -1 and text[karsilasma-2].isdigit() and (karsilasma+len(birim) == len(text) or text[karsilasma+len(birim)] ==' '))):
                return True
    for adet in adetler:
        karsilasmalar = [m.start() for m in re.finditer(adet, text)]
        for karsilasma in karsilasmalar:
            if adet in text and karsilasma-1 > -1 and ((text[karsilasma-1].isdigit() and (karsilasma+len(adet) == len(text) or text[karsilasma+len(adet)] ==' ')) or (text[karsilasma-1] == ' ' and karsilasma-2 > -1 and text[karsilasma-2].isdigit() and (karsilasma+len(adet) == len(text) or text[karsilasma+len(adet)] ==' '))):
                return True
    for kelime in kelimeler:
        if kelime in text and text.find(kelime)-1 > -1 and text[text.find(kelime)-1] == ' ' and (text.find(kelime)+len(kelime) == len(text) or text[text.find(kelime)+len(kelime)] ==' '):
            return True
    return False
                        
def getAllUrls():
    _link =''
    while(_link != url): #bim bazen anasayfaya yönlendirme yapiyor
        response = requests.get(url)
        _link = response.url
    _html=response.text
    soup = BeautifulSoup(_html,"lxml")
    link_list=[]
    for link in soup.find(class_='container content white no-pb').find(class_='row').find_all('a'):
        link = base_url+link['href'].strip()
        if 'aktuel-urunler' not in link or link in link_list:
            continue
        else:
            link_list.append(link)
##            print(link)
    return link_list

def getAllDatas(links):
    all_datas=[]
    cikti=[]
    for i in links:
        count = 10
        link = ''
        while count > 0: #bim bazen anasayfaya yönlendirme yapiyor
            page = requests.get(i)
            link = page.url
            print(count,'',end='') if count <= 3 else ''
            if link == i:
                break
            count -= 1
        if count == 0:
            print(i,'baglanti kurulamadi.')
            continue
        tree = html.fromstring(page.content.decode(page.encoding)) #https://stackoverflow.com/a/29057244
        resim = requote_uri(base_url+tree.xpath("""//*[@id="form1"]/div[2]/div[2]/div[1]/div/div/div[1]/a/img/@src""")[0])
        fiyat_buyuk = tree.xpath("""//*[@id="form1"]/div[2]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/a/div[1]/text()""")[0].strip().replace(".",'').replace(",",".")
        fiyat_kusurat = tree.xpath("""//*[@id="form1"]/div[2]/div[2]/div[1]/div/div/div[2]/div[2]/div/div/a/div[2]/span/text()""")[0].strip()
        fiyat_tam = fiyat_buyuk.strip() + fiyat_kusurat.strip()
        urun_ad = tree.xpath("""//*[@id="form1"]/div[2]/div[2]/div[1]/div/div/div[2]/div[1]/h2/text()""")[0]
        if urun_ad.strip() not in cikti:
            cikti.append(urun_ad.strip())
        
        soup = BeautifulSoup(page.text,"lxml")
        miktar = [] #miktar veya özelliklerin bulundugu dizi
        marka = ''

        for ozellik in soup.find(class_='rightSide col-md-6').find(class_='textArea').text.split('\n'): #ÜRÜN ÖZELLIKLERINI ÇEKMEK
            if ozellik.find(',')>-1 and ozellik.find(',')+1 < len(ozellik) and not ozellik[ozellik.find(',')+1].isdigit():
                ozellikler3 = ozellik.split(',')
                for ozellik3 in ozellikler3:
                    ozellik3 = cleanExtraSpaces(ozellik3.replace('•','').replace('’',"'"))
                    if ozellik3.lower() in urun_ad.lower():
                        continue
                    else: miktar.append(ozellik3)
            else:
                ozellik = cleanExtraSpaces(ozellik.replace('•','').replace('’',"'"))
                if ozellik.lower() in urun_ad.lower():
                    continue
                else: miktar.append(ozellik)

        for urun in soup.find(class_='container content white no-pb').find_all(class_='inner'): #ÜRÜN ÖZELLIKLERINI CEKMEK 2 - bazen ürün sayfasinda özellik yazmiyor ama listede yaziyor
            if urlparse(link).path in [a['href'] for a in urun.find_all('a', href=True)]:
                ozellikler2 = urun.find(class_='textArea')
                for ozellik in ozellikler2.text.split('•'):
                    if ozellik.find(',')>-1 and ozellik.find(',')+1 < len(ozellik) and not ozellik[ozellik.find(',')+1].isdigit():
                        ozellikler3 = ozellik.split(',')
                        for ozellik3 in ozellikler3:
                            ozellik3 = cleanExtraSpaces(ozellik3.replace('’',"'"))
                            if ozellik3.lower() in urun_ad.lower():
                                continue
                            else: miktar.append(ozellik3)
                    else:
                        ozellik = cleanExtraSpaces(ozellik.replace('’',"'"))
                        if ozellik.lower() in urun_ad.lower():
                            continue
                        else: miktar.append(ozellik)
                break
            else: continue

        for urun in soup.find(class_='container content white no-pb').find_all(class_='inner'): #ÜRÜN MARKASINI BULMAK
            if urlparse(link).path in [a['href'] for a in urun.find_all('a', href=True)]:
                marka = urun.find("h2","subTitle")
                if marka:
                    marka = marka.text
                else:
                    marka = ' ' #bazi aktuellerin ilk urunlerinin sayfasinin altinda bir onceki aktüellerin listesi bulunuyor, bu da urun markasini listeden cekemememiz anlamina geliyr, genelde bu ürünlerin zaten markasi yok, ama subtitle blokuda olmadigi icin marka'nin False ya da None ya da bos olmamasi gerekiyor
                break
            else: continue
            
        urun_tam_ad = urunAdiOlusturucu(marka,urun_ad,ozellikListDuzenleyici(miktar),120)
        all_datas.append({"u":urun_tam_ad, "f":fiyat_tam, "k":resim})
        print(urun_tam_ad, fiyat_tam)
##        print('_________________________________________________________________________________________')
    return all_datas,cikti

if __name__ == "__main__":
    links=getAllUrls()
    for i in links:
        print(i)
    print(len(links),'ÜRÜN VAR.')
    print("-------------------------")
    datas,cikti=getAllDatas(links)
    aa=str(json.dumps(datas)).replace('"u": ','"u":ur')
    print('\n' + ', '.join(cikti))
    input('\nKaydetmek için bir tusa basin...')
    createTextFile_raw('bim_hazir_'+AktuelTarih, aa)
##    print(aa)
##    getAllDatas(['https://www.bim.com.tr/aktuel-urunler/dondurulmus-baget-ekmek/aktuel.aspx'])
##    text = 'mustafa'
##    print(text.find('fa'),text.find('fa')+len('fa'),len(text))
####    print("1ml".find('ml'))
######    print(isquantity("4w"))
######    print("S Watt değeri: 4W".lower())

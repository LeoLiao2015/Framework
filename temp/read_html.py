# -*- coding: utf-8 -*-
import os
import sys
import shutil

from bs4 import BeautifulSoup
from lxml import etree
# chcp 936
# chcp 65001
print(sys.getdefaultencoding())

with open('中港台電視 TVB - Google Play.html', 'r', encoding='utf-8') as f:
    html = f.read(4096*1024*1024)
    tree = etree.HTML(html, etree.HTMLParser())
    items_1 = tree.xpath('//div[@class="ZmHEEd "]')
    for item_1_x in items_1:
        items_2 = item_1_x.xpath(
            '//div[@class="Ktdaqe  "]/div[@class="ZmHEEd "]//div[@class="Vpfmgd"]')
        for item_2_x in items_2:
            item_2_x = etree.fromstring(etree.tostring(item_2_x))
            image = item_2_x.xpath(
                '//span[@class="kJ9uy K3IMke buPxGf"]/img/@src')  # div[@class="uzcko"]/div[@class="N9c7d eJxoSc"]
            if len(image) == 0:
                image = item_2_x.xpath(
                    '//span[@class="kJ9uy K3IMke buPxGf"]/img/@data-src')  # div[@class="uzcko"]/div[@class="N9c7d eJxoSc"]
            if len(image) == 0:
                image.append("")
            name = item_2_x.xpath(
                '//div[@class="b8cIId ReQCgd Q9MA7b"]/a/div[@class="WsMG1c nnK0zc"]/text()')
            if len(name) == 0:
                name.append("")
            company = item_2_x.xpath(
                '//div[@class="b8cIId ReQCgd KoLSrc"]/a/div[@class="KoLSrc"]/text()')
            if len(company) == 0:
                company.append("")
            star = item_2_x.xpath(
                '//div[@class="vU6FJ p63iDd"]//div[@class="pf5lIe"]/div/@aria-label')
            if len(star) > 0:
                star = star[0].split(" ")[1]
            else:
                star = ""
            print("name:{} company:{} star:{} image:{}".format(
                name[0], company[0], star, image[0]))


# etree.HTML()
# tree = etree.parse('./TV BOX TVB - Google Play.html', etree.HTMLParser())
# items = tree.xpath(
#     '//div[contains(@id, "ImZGtf") and contains(@id, "ImZGtf")]')
# for item in items:
#     item_tree = etree.HTML(item)

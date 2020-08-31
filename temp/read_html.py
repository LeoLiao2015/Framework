# -*- coding: utf-8 -*-
import os
import sys
import shutil

from bs4 import BeautifulSoup
from lxml import etree
import xlwt
# chcp 936
# chcp 65001
print(sys.getdefaultencoding())



def write_data_to_excel():

    # 将sql作为参数传递调用get_data并将结果赋值给result,(result为一个嵌套元组)
    # result = get_data(sql)
    # 实例化一个Workbook()对象(即excel文件)
    wbk = xlwt.Workbook(encoding='utf-8')
    # 新建一个名为Sheet1的excel sheet。此处的cell_overwrite_ok =True是为了能对同一个单元格重复操作。
    sheet = wbk.add_sheet('Sheet1',cell_overwrite_ok=True)

    # 遍历result中的没个元素。
    # for i in xrange(len(result)):
    #     #对result的每个子元素作遍历，
    #     for j in xrange(len(result[i])):
    #         #将每一行的每个元素按行号i,列号j,写入到excel中。
    #         sheet.write(i,j,result[i][j])
    sheet.write(0, 0, "0.0")
    sheet.write(0, 1, "0.1")

    sheet.write(1, 0, "1.0")
    sheet.write(1, 1, "1.1")

    sheet.write(10, 10, "10.10")

    # 以传递的name+当前日期作为excel名称保存。
    wbk.save('123.xls')

write_data_to_excel()
write_data_to_excel()
write_data_to_excel()

with open('TV BOX APP TVB_百度搜索1.html', 'r', encoding='utf-8') as f:
    html = f.read(4096*1024*1024)
    items_weburl = []
    items_name = []
    items_desc = []

    tree = etree.HTML(html, etree.HTMLParser())
    res = tree.xpath('//div[@class="result c-container "]')
    for re in res:
        search_item = etree.fromstring(etree.tostring(re))
        name = search_item.xpath('//h3[contains(@class, "t")]/a')
        name_response = etree.HTML(text=etree.tostring(name[0]))
        # name_response.xpath('string(.)')

        desc = search_item.xpath('//div[contains(@class, "c-abstract")]')
        desc_response = etree.HTML(text=etree.tostring(desc[0]))
        # desc_response.xpath('string(.)')

        weburl = search_item.xpath('//h3[contains(@class, "t")]/a/@href')

        items_name.append(name_response.xpath('string(.)'))
        items_desc.append(desc_response.xpath('string(.)'))
        items_weburl.append(weburl[0])

        print("name:{} desc:{} weburl:{}".format(
            name_response.xpath('string(.)'), desc_response.xpath('string(.)'), weburl[0]))




with open('中港台電視 TVB - Google 搜索1.html', 'r', encoding='utf-8') as f:
    html = f.read(4096*1024*1024)
    tree = etree.HTML(html, etree.HTMLParser())
    res = tree.xpath('//div[@id="rso"]/div[@class="g"]/div[@class="rc"]')
    items_weburl = []
    items_name = []
    items_desc = []
    for re in res:
        search_item = etree.fromstring(etree.tostring(re))
        weburl = search_item.xpath('//div[@class="TbwUpd NJjxre"]/cite[contains(@class, "iUh30") and contains(@class, "tjvcx")]/text()')
        name = search_item.xpath('//div[@class="rc"]//h3[@class="LC20lb DKV0Md"]/text()')
        desc = search_item.xpath('//div[@class="s"]//span[@class="st"]')
        response = etree.HTML(text=etree.tostring(desc[0]))
        # print(response.xpath('string(.)'))
        # soup = BeautifulSoup(etree.tostring(desc[0]),'html.parser')
        # print(soup.get_text())
        items_weburl.append(weburl[0])
        items_name.append(name[0])
        items_desc.append(response.xpath('string(.)'))

        print("name:{} desc:{} weburl:{}".format(
            name[0], response.xpath('string(.)'), weburl[0]))
    # weburl_items = tree.xpath('//div[@class="TbwUpd NJjxre"]/cite[@class="iUh30 bc tjvcx"]/text()')
    # name_items = tree.xpath('//div[@class="rc"]//h3[@class="LC20lb DKV0Md"]/text()')

    weburl
    name
    desc

    



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

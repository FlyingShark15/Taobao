#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Will  2018/8/9


import re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo

# MONGODB的创建
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

# 声明浏览器对象
browser = webdriver.Chrome()
# 显式等待
wait = WebDriverWait(browser, 10)


def search():
    try:
        browser.get('https://www.taobao.com')
        # 搜索框
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#q')))
        # 搜索按钮
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > '
                                                                         'div.search-button > button')))
        # 经过测试，‘美食’可以换成其他宝贝，到2018年8月9日前未发现问题
        input.send_keys('美食')
        submit.click()
        # 总页数
        total = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div '
                                                                            '> div > div > div.total')))
        return total.text
        # 调用get_products()方法
        get_products()
    except TimeoutException:
        return search()

# 如何翻页
def next_page(page_number):
    try:
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div'
                                                                            ' > div > div.form > input')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mainsrp-pager > div > div '
                                                                         '> div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        # 验证是否跳转成功
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)
        ))
        get_products()
    except TimeoutException:
        next_page(page_number)

# 获取商品信息
def get_products():
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = browser.page_source
    doc = pq(html)
    items = doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product = {
            'name': item.find(' .title').text().replace('\n', ' 、'),
            'image': item.find(' .pic .img').attr('src'),
            'price': item.find(' .price').text().replace('\n', ' '),
            'deal': item.find(' .deal-cnt').text()[:-3],
            'shop': item.find(' .shop').text(),
            'location': item.find(' .location').text()
        }
        save_to_mongo(product)


def save_to_mongo(Result):
    try:
        db[MONGO_TABLE].insert_one(Result)
        '''
        # 这是测试用的
        if db[MONGO_TABLE].insert_one(Result):
            print('插入到MONGO成功', Result)
        '''
    except Exception:
        print('插入失败', Result)


def main():
    total = search()
    total = int(re.compile('(\d+)').search(total).group(1))
    for i in range(2, total+1):
        next_page(i)


if __name__ == '__main__':
    main()

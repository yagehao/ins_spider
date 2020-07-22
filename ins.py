#目标网站：ins
#====================================================================
#准备工作
#====================================================================
# -*- encoding: utf-8 -*-

#导入module
import requests
import random
import json
import time
from openpyxl import Workbook
from pyquery import PyQuery as pq
import re

#====================================================================
#下载html网页数据
#====================================================================
#设置requests请求的headers
headers = {
    'accept': '*/*',
    #'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,ja;q=0.6,zh-TW;q=0.5',
    'referer': 'https://www.instagram.com/oedo.kuipers/',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'cookie': 'ig_cb=1; ig_did=EE977BF7-AFF1-4152-8ED5-2ED8DF7C0E09; mid=Xwu73QAEAAGZ0ef2EUtflrQNTiyN; csrftoken=WAVw0EPAkTB4x45icMizmOXbR2pNiFHF; ds_user_id=3593692569; sessionid=3593692569%3A7KlEpJRAFH1wVW%3A20; shbid=2363; shbts=1595221828.7090933; rur=PRN; urlgen="{\"89.187.161.206\": 60068\054 \"89.187.161.191\": 60068}:1jxQYJ:juhvk-HP2VWJCwDwjfWKmaH4Ugs"' #使用cookie模拟登陆
}

#设置url
url = 'https://www.instagram.com/oedo.kuipers/'
uri = 'https://www.instagram.com/graphql/query/?query_hash=15bf78a4ad24e33cbd838fdb31353ac1&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'

#获取网页
def get_html(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print('请求错误状态码：', response.status_code)
    except Exception as e:
        print(e)
        return None

html = get_html(url)
#print(html)

#获取网页中json script
def get_json(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print('请求网页json错误, 错误状态码：', response.status_code)
    except Exception as e:
        print(e)
        time.sleep(60 + float(random.randint(1, 4000))/100)
        return get_json(url)

#====================================================================
#解析动态js得到真实地址，实现自动翻页爬取
#====================================================================
def get_urls(html):
    urls = []

    user_id = re.findall('"profilePage_([0-9]+)"', html, re.S)[0]
    print('user_id:' + user_id)

    doc = pq(html)
    items = doc('script[type="text/javascript"]').items()

    #解析得到图片地址与文字信息
    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1], encoding='utf-8')
            edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]

            #判断自动翻页所需信息
            page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']

            for edge in edges:
                #time.sleep(random.uniform(0,1))

                if edge['node']['display_url']:
                    id = edge["node"]["id"] #用于确认唯一性、查重
                    pic_url = edge["node"]["display_url"]
                    if len(edge["node"]["edge_media_to_caption"]["edges"])>0:
                        text = edge["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                    else:
                        text = ""
                    print([id, pic_url, text])
                    #urls.append(pic_url)
            print(cursor, flag)

    while flag:
        url = uri.format(user_id=user_id, cursor=cursor)
        js_data = get_json(url)

        infos = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        cursor = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        flag = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']

        for info in infos:
            #time.sleep(random.uniform(0,1))

            if info['node']['display_url']:
                id = info["node"]["id"] #用于确认唯一性、查重
                pic_url = info["node"]["display_url"]
                if len(info["node"]["edge_media_to_caption"]["edges"])>0:
                    text = info["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                else:
                    text = ""
                print([id, pic_url, text])
                #urls.append(pic_url)
        print(cursor, flag)

        time.sleep(random.uniform(0,1))
    return None

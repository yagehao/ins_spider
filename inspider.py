# https://github.com/pinggin/Instagram_crawler

# 运行 python inspider.py user_name
# 这里的user_name写上要爬的博主账号名称

import os
import re
import sys
import json
import time
import random
import requests
from hashlib import md5
from pyquery import PyQuery as pq

url_base = 'https://www.instagram.com/'
uri = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'


headers = {
    'Connection': 'keep-alive',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    'cookie': 'ig_cb=1; ig_did=EE977BF7-AFF1-4152-8ED5-2ED8DF7C0E09; mid=Xwu73QAEAAGZ0ef2EUtflrQNTiyN; csrftoken=WAVw0EPAkTB4x45icMizmOXbR2pNiFHF; ds_user_id=3593692569; sessionid=3593692569%3A7KlEpJRAFH1wVW%3A20; shbid=2363; shbts=1595221828.7090933; rur=PRN; urlgen="{\"89.187.161.206\": 60068\054 \"89.187.161.191\": 60068}:1jxQYJ:juhvk-HP2VWJCwDwjfWKmaH4Ugs"'
}


def get_html(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print('请求网页源代码错误, 错误状态码：', response.status_code)
    except Exception as e:
        print(e)
        return None


def get_json(url):
    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print('请求网页json错误, 错误状态码：', response.status_code)
    except Exception as e:
        print(e)
        time.sleep(60 + float(random.randint(1, 4000))/100)
        return get_json(url)


def get_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.content
        else:
            print('请求照片二进制流错误, 错误状态码：', response.status_code)
    except Exception as e:
        print(e)
        return None


def get_urls(html):
    urls = []
    data = []
    user_id = re.findall('"profilePage_([0-9]+)"', html, re.S)[0]
    print('user_id：' + user_id)
    doc = pq(html)
    items = doc('script[type="text/javascript"]').items()
    for item in items:
        if item.text().strip().startswith('window._sharedData'):
            js_data = json.loads(item.text()[21:-1], encoding='utf-8')
            edges = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
            page_info = js_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']
            cursor = page_info['end_cursor']
            flag = page_info['has_next_page']
            for edge in edges:
                if edge['node']['display_url']:
                    id = edge["node"]["id"] #用于确认唯一性、查重
                    display_url = edge['node']['display_url']
                    if len(edge["node"]["edge_media_to_caption"]["edges"])>0:
                        text = edge["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                    else:
                        text = ""
                    print([id, display_url, text])
                    urls.append(display_url)
                    data.append([id, display_url, text])
            print(cursor, flag)
    while flag:
        url = uri.format(user_id=user_id, cursor=cursor)
        js_data = get_json(url)
        infos = js_data['data']['user']['edge_owner_to_timeline_media']['edges']
        cursor = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']
        flag = js_data['data']['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
        for info in infos:
            if info['node']['is_video']:
                id = info["node"]["id"]
                video_url = info['node']['video_url']
                if len(info["node"]["edge_media_to_caption"]["edges"])>0:
                    text = info["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                else:
                    text = ""
                if video_url:
                    print([id, video_url, text])
                    urls.append(video_url)
                    data.append([id, video_url, text])
            else:
                if info['node']['display_url']:
                    id = info["node"]["id"]
                    display_url = info['node']['display_url']
                    if len(info["node"]["edge_media_to_caption"]["edges"])>0:
                        text = info["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
                    else:
                        text = ""
                    print([id, display_url, text])
                    urls.append(display_url)
                    data.append([id, display_url, text])
        print(cursor, flag)
        # time.sleep(4 + float(random.randint(1, 800))/200)    # if count > 2000, turn on
    return urls


def main(user):
    url = url_base + user + '/'
    html = get_html(url)
    urls = get_urls(html)
    dirpath = r'.\{0}'.format(user)
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    for i in range(len(urls)):
        #print(urls)
        print('\n正在下载第{0}张： '.format(i) + urls[i], ' 还剩{0}张'.format(len(urls)-i-1))
        try:
            content = get_content(urls[i])
            endw = 'mp4' if r'mp4?_nc_ht=scontent' in urls[i] else 'jpg'
            file_path = r'.\{0}\{1}.{2}'.format(user, md5(content).hexdigest(), endw)
            if not os.path.exists(file_path):
                with open(file_path, 'wb') as f:
                    print('第{0}张下载完成： '.format(i) + urls[i])
                    f.write(content)
                    f.close()
            else:
                print('第{0}张照片已下载'.format(i))
        except Exception as e:
            print(e)
            print('这张图片or视频下载失败')


if __name__ == '__main__':
    user_name = sys.argv[1]
    start = time.time()
    main(user_name)
    print('Complete!!!!!!!!!!')
    end = time.time()
    spend = end - start
    hour = spend // 3600
    minu = (spend - 3600 * hour) // 60
    sec = spend - 3600 * hour - 60 * minu
    print(f'一共花费了{hour}小时{minu}分钟{sec}秒')

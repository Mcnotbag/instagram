import hashlib
import json
import random
import re
from pprint import pprint
from time import sleep
import requests
from lxml.etree import HTML
# 翻墙用的是Shadowsocks,全局模式无须设置代理

headers = {
    'Connection': 'keep-alive',
    'Host': 'www.instagram.com',
    'Referer': 'https://www.instagram.com/instagram/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

url = "https://www.instagram.com/instagram/"
next_page_url = 'https://www.instagram.com/graphql/query/?query_hash=a5164aed103f24b03e7b7747a2d94e3c&variables=%7B%22id%22%3A%22{user_id}%22%2C%22first%22%3A12%2C%22after%22%3A%22{cursor}%22%7D'
detail_url = "https://www.instagram.com/p/{shortcode}/?__a=1"
page = 1

def get_data(url):
    global page
    html = requests.get(url,headers=headers,timeout=15).content.decode()

    index = re.search(r"window._sharedData = (.*);</script>",html).group(1)
    Data = json.loads(index)
    # rhx_gis 加密算法组成
    rhx_gis = Data["rhx_gis"]
    user_id = Data["entry_data"]["ProfilePage"][0]["logging_page_id"][12:]
    first_info = Data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]
    for data in first_info:
        img_url = data["node"]["display_url"]
        comments = data['node']['edge_media_to_comment']["count"]
        likes = data["node"]["edge_media_preview_like"]["count"]
        shortcode = data["node"]["shortcode"]
        sleep(random.uniform(3,6))
        text = request_detail(shortcode)
        write_json(dict_date(img_url=img_url, text=text, likes=likes, comments=comments))
    # 下一页的必要b64值
    after = Data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']["end_cursor"]
    # 是否有下一页
    next_page = Data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]['page_info']["has_next_page"]
    # 翻页
    while next_page:
        # 每页加载12条，请求10页就够
        page += 1
        print("当前页数--%s" %page)
        if page > 10:
            break
        # 下一页请求参数
        queryVariables = '{"id":"' + user_id + '","first":12,"after":"' + after + '"}'
        # md5加密，生成headers必须x-instagram-gis值
        header_gis = hash_gis(rhx_gis + ":" + queryVariables)
        headers["x-instagram-gis"] = header_gis
        Data = json.loads(requests.get(next_page_url.format(cursor=after,user_id=user_id),headers=headers,timeout=15).content.decode())
        next_info = Data["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
        for data in next_info:
            comments = data["node"]["edge_media_to_comment"]["count"]
            likes = data["node"]["edge_media_preview_like"]["count"]
            img_url = data["node"]["display_url"]
            text = data["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
            write_json(dict_date(img_url=img_url,text=text,likes=likes,comments=comments))
        page_info = Data["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]
        after = page_info["end_cursor"]
        next_page = page_info["has_next_page"]
        sleep(random.uniform(2, 5))

def request_detail(shortcode):
    detail = json.loads(requests.get(detail_url.format(shortcode=shortcode),headers=headers,timeout=15).content.decode())
    text = detail["graphql"]["shortcode_media"]["edge_media_to_caption"]["edges"][0]["node"]["text"]
    return text

def hash_gis(string):
    h = hashlib.md5()
    h.update(string.encode("utf-8"))
    return h.hexdigest()

def write_json(date):
    str_date = json.dumps(date)
    print(str_date)
    with open('instagram.json',"a",encoding="utf-8") as f:
        f.write(str_date+","+'\n')

def dict_date(img_url,comments,likes,text):
    need_date = {}
    need_date["image_url"] = img_url
    need_date["comments"] = comments
    need_date["likes"] = likes
    need_date["text"] = text
    return need_date
if __name__ == '__main__':
    get_data(url)

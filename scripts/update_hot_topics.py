#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热点榜单自动更新脚本
每小时自动抓取微博、百度热搜数据，生成 hot_data.json
"""

import json
import re
import time
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4")
    exit(1)

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

# 分类关键词映射
CATEGORY_KEYWORDS = {
    'politics': ['特朗普', '普京', '外交部', '中美', '会晤', '访问', '政治', '外交', '军事', '战争', '伊朗', '以色列', '日本', '抗议'],
    'tech': ['微信', 'AI', '人工智能', '芯片', '华为', '苹果', '三星', '科技', '数码', '手机', '电脑', '互联网', '耳机', '机甲', '宇树'],
    'entertainment': ['明星', '演员', '电影', '电视剧', '综艺', '演唱会', '娱乐', '艺人', '导演'],
    'sports': ['世界杯', '足球', '篮球', 'NBA', '乒乓球', '体育', '比赛', '冠军', '运动员', '湖人', '雷霆'],
    'finance': ['股价', '股市', '经济', '金融', '银行', '存款', '油价', '房价', '企业', '公司', 'A股', '芯片', '市值'],
    'health': ['疫情', '病毒', '疫苗', '医院', '医生', '健康', '疾病', '药品', '医疗'],
    'life': ['机票', '旅游', '酒店', '美食', '购物', '价格', '生活', '日常', '家庭'],
    'social': ['地震', '火灾', '事故', '灾难', '救援', '警察', '法院', '法律', '社会', '民生', '网红']
}

def classify_topic(title, summary=''):
    """根据标题自动分类"""
    text = title + summary
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return 'social'

def fetch_weibo_hot():
    """抓取微博热搜"""
    topics = []
    try:
        url = 'https://weibo.com/a/hot/realtime'
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 微博热搜条目
        items = soup.find_all('div', class_=['UG_list_b', 'UG_list_a'])
        for i, item in enumerate(items[:20]):
            title_elem = item.find('h3') or item.find('a')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            heat = max(500, 5500 - i * 250)

            topics.append({
                'title': title,
                'heat': heat,
                'rank': i + 1,
                'url': 'https://weibo.com/a/hot/realtime'
            })
    except Exception as e:
        print(f"微博抓取失败: {e}")

    return topics

def fetch_baidu_hot():
    """抓取百度热搜"""
    topics = []
    try:
        url = 'https://top.baidu.com/board?tab=realtime&platform=pc'
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all('div', class_='category-wrap_iQLoo')
        for i, item in enumerate(items[:20]):
            title_elem = item.find('div', class_='c-single-text-ellipsis')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)

            heat_elem = item.find('div', class_='hot-index_1Bl1a')
            heat = 5000000
            if heat_elem:
                heat_text = heat_elem.get_text(strip=True)
                heat_match = re.search(r'(\d+)', heat_text)
                if heat_match:
                    heat = int(heat_match.group(1))

            summary_elem = item.find('div', class_='content_1YWBm')
            summary = ''
            if summary_elem:
                summary = summary_elem.get_text(strip=True)[:100]

            topics.append({
                'title': title,
                'heat': heat,
                'rank': i + 1,
                'summary': summary,
                'url': 'https://top.baidu.com/board?tab=realtime&platform=pc'
            })
    except Exception as e:
        print(f"百度抓取失败: {e}")

    return topics

def merge_topics(weibo_data, baidu_data):
    """合并各平台数据，去重并计算综合热度"""
    topic_map = {}

    # 处理微博数据
    for item in weibo_data:
        key = item['title'][:15]
        if key not in topic_map:
            topic_map[key] = {
                'title': item['title'],
                'heat': {'weibo': item['heat'] / 10000, 'baidu': 0, 'douyin': 0, 'bilibili': 0, 'zhihu': 0},
                'sources': [{'name': '微博', 'url': item['url']}],
                'summary': '',
            }

    # 处理百度数据
    for item in baidu_data:
        key = item['title'][:15]
        if key in topic_map:
            topic_map[key]['heat']['baidu'] = item['heat'] / 10000
            topic_map[key]['sources'].append({'name': '百度', 'url': item['url']})
            if item.get('summary'):
                topic_map[key]['summary'] = item['summary']
        else:
            topic_map[key] = {
                'title': item['title'],
                'heat': {'weibo': 0, 'baidu': item['heat'] / 10000, 'douyin': 0, 'bilibili': 0, 'zhihu': 0},
                'sources': [{'name': '百度', 'url': item['url']}],
                'summary': item.get('summary', ''),
            }

    # 转换为列表并计算综合热度
    topics = []
    for key, data in topic_map.items():
        total_heat = sum(data['heat'].values())
        category = classify_topic(data['title'], data['summary'])

        topics.append({
            'title': data['title'],
            'category': category,
            'summary': data['summary'] or data['title'],
            'heat': data['heat'],
            'trend': 'hot',
            'trendVal': 0,
            'sources': data['sources']
        })

    # 按综合热度排序
    topics.sort(key=lambda x: sum(x['heat'].values()), reverse=True)

    # 重新编号
    for i, topic in enumerate(topics[:30]):
        topic['rank'] = i + 1

    return topics[:30]

def generate_data():
    """主函数：抓取数据并生成 JSON"""
    print(f"[{datetime.now()}] 开始抓取热点数据...")

    weibo_data = fetch_weibo_hot()
    print(f"  微博: {len(weibo_data)} 条")

    baidu_data = fetch_baidu_hot()
    print(f"  百度: {len(baidu_data)} 条")

    topics = merge_topics(weibo_data, baidu_data)
    print(f"  合并后: {len(topics)} 条")

    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'topics': topics
    }

    with open('data/hot_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[{datetime.now()}] 数据已更新，共 {len(topics)} 条热点")
    return output

if __name__ == '__main__':
    generate_data()

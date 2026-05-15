#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热点榜单自动更新脚本 (v8.1 热度拉齐版)
特点：
- 综合排名时各平台热度拉齐（归一化）
- 显示时保留各平台原始热度值
- 排名算法：平台覆盖数 * 10000 + 归一化热度总和
"""

import json
import sys
import time
import random
import re
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

CATEGORY_KEYWORDS = {
    'politics': ['特朗普', '普京', '外交部', '中美', '会晤', '访问', '政治', '外交', '军事', '战争', '伊朗', '以色列', '日本', '抗议', '台湾', '香港', '澳门', '两会', '人大', '政协', '总书记', '主席', '总理', '部长'],
    'tech': ['微信', 'AI', '人工智能', '芯片', '华为', '苹果', '三星', '科技', '数码', '手机', '电脑', '互联网', '耳机', '机甲', '宇树', '大模型', 'GPT', 'ChatGPT', 'OpenAI', '马斯克', '特斯拉', '电动车', '新能源', '5G', '6G', '云计算', '区块链'],
    'entertainment': ['明星', '演员', '电影', '电视剧', '综艺', '演唱会', '娱乐', '艺人', '导演', '票房', '戛纳', '奥斯卡', '金马', '金像', '百花', '飞天', '白玉兰', '金鹰', '红毯', '恋情', '离婚', '结婚', '出轨', '爆料'],
    'sports': ['世界杯', '足球', '篮球', 'NBA', '乒乓球', '体育', '比赛', '冠军', '运动员', '湖人', '雷霆', 'CBA', '中超', '亚冠', '欧冠', '英超', '西甲', '意甲', '德甲', '法网', '温网', '澳网', '美网', '奥运', '亚运会', '全运会', '世乒赛', '苏迪曼杯', '汤尤杯'],
    'finance': ['股价', '股市', '经济', '金融', '银行', '存款', '油价', '房价', '企业', '公司', 'A股', '芯片', '市值', '基金', '理财', '保险', '债券', '汇率', '人民币', '美元', '黄金', '比特币', '以太坊', '期货', 'IPO', '上市', '退市', '涨停', '跌停', '大盘', '指数', '创业板', '科创板', '北交所'],
    'health': ['疫情', '病毒', '疫苗', '医院', '医生', '健康', '疾病', '药品', '医疗', '癌症', '肿瘤', '手术', '体检', '医保', '卫健委', '疾控', '传染病', '流感', '新冠', '甲流', '乙流', '支原体', '登革热', '疟疾', '艾滋病'],
    'life': ['机票', '旅游', '酒店', '美食', '购物', '价格', '生活', '日常', '家庭', '装修', '家具', '家电', '汽车', '油价', '天气', '气候', '环保', '垃圾分类', '宠物', '猫', '狗', '养花', '种菜', '钓鱼', '露营', '徒步', '骑行', '自驾'],
    'social': ['地震', '火灾', '事故', '灾难', '救援', '警察', '法院', '法律', '社会', '民生', '网红', '直播', '短视频', '抖音', '快手', 'B站', '小红书', '微博', '知乎', '豆瓣', '贴吧', '论坛', '社区', '公益', '慈善', '志愿者', '见义勇为', '失踪', '寻亲', '拐卖', '诈骗', '电信诈骗', '网络诈骗']
}

def classify_topic(title, summary=''):
    text = title + summary
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score
    if scores:
        return max(scores, key=scores.get)
    return 'social'

def safe_request(url, headers=None, timeout=15, retries=3):
    headers = headers or HEADERS
    for i in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            print(f"  ⚠️ HTTP {resp.status_code} (尝试 {i+1}/{retries})")
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"  ⚠️ 请求异常: {str(e)[:50]} (尝试 {i+1}/{retries})")
            time.sleep(random.uniform(2, 4))
    return None

# ============ 归一化热度 ============
def normalize_heat(source, heat):
    """
    将各平台热度归一化到同一量级 (0-10000)
    用于综合排名计算
    """
    if heat <= 0:
        return 0

    if source == 'weibo':
        # 微博: 100-5000 → 保持不变
        return min(heat, 10000)
    elif source == 'baidu':
        # 百度: 10000-500000 → ÷10
        return min(heat / 10, 10000)
    elif source == 'zhihu':
        # 知乎: 100000-5000000 → ÷100
        return min(heat / 100, 10000)
    elif source == 'bilibili':
        # B站: 100-3000 → ×2
        return min(heat * 2, 10000)
    elif source == 'douyin':
        # 抖音: 1000-10000 → 保持不变
        return min(heat, 10000)
    else:
        return min(heat, 10000)

# ============ 微博 ============
def fetch_weibo_hot():
    topics = []
    try:
        print("  [微博] 尝试抓取...")
        url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            if data.get('ok') == 1:
                cards = data['data'].get('cards', [])
                for card in cards:
                    for item in card.get('card_group', []):
                        title = item.get('desc', '')
                        if not title or title in ['热搜', '实时上升热点']:
                            continue
                        heat = item.get('desc_extr', 0)
                        if isinstance(heat, str):
                            match = re.search(r'(\d+(?:\.\d+)?)', heat)
                            if match:
                                heat = float(match.group(1))
                                if '万' in heat:
                                    heat *= 10000
                            else:
                                heat = 0
                        if heat == 0:
                            heat = max(5000 - len(topics) * 200, 100)
                        topics.append({
                            'title': title,
                            'heat': int(heat),
                            'url': f'https://s.weibo.com/weibo?q={quote(title)}',
                            'source': 'weibo'
                        })
                if topics:
                    print(f"  ✅ 成功: {len(topics)} 条")
                    return topics
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("  ⚠️ 微博所有接口失败")
    return topics

# ============ 百度 ============
def fetch_baidu_hot():
    topics = []
    try:
        print("  [百度] 尝试第三方API...")
        url = 'https://v2.xxapi.cn/api/baiduhot'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            if data.get('code') == 200 and 'data' in data:
                items = data['data']
                for item in items[:30]:
                    title = item.get('title', '')
                    if not title:
                        continue
                    hot = item.get('hot', 0)
                    if isinstance(hot, str):
                        match = re.search(r'(\d+(?:\.\d+)?)', hot)
                        if match:
                            hot = float(match.group(1))
                            if '万' in hot or 'w' in hot.lower():
                                hot *= 10000
                            elif '亿' in hot:
                                hot *= 100000000
                        else:
                            hot = 0
                    if hot == 0:
                        hot = random.randint(10000, 500000)
                    topics.append({
                        'title': title,
                        'heat': int(hot),
                        'summary': item.get('desc', '')[:100],
                        'url': item.get('url', f'https://www.baidu.com/s?wd={quote(title)}'),
                        'source': 'baidu'
                    })
                if topics:
                    print(f"  ✅ 成功: {len(topics)} 条")
                    return topics
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("  ⚠️ 百度所有接口失败")
    return topics

# ============ 知乎 ============
def fetch_zhihu_hot():
    topics = []
    try:
        print("  [知乎] 尝试API...")
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-list-web?limit=20&desktop=true'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            items = data.get('data', [])
            for idx, item in enumerate(items):
                target = item.get('target', {})
                title_area = target.get('title_area', {})
                title = title_area.get('text', '')
                if not title:
                    continue
                link = target.get('link', {})
                url_zhihu = link.get('url', '')
                metrics = target.get('metrics_area', {})
                heat_text = metrics.get('text', '')
                heat = 0
                match = re.search(r'(\d+(?:\.\d+)?)', heat_text)
                if match:
                    heat = float(match.group(1))
                    if '万' in heat_text:
                        heat *= 10000
                if heat == 0:
                    heat = max(5000000 - idx * 250000, 100000)

                topics.append({
                    'title': title,
                    'heat': int(heat),
                    'url': url_zhihu,
                    'source': 'zhihu'
                })
            if topics:
                print(f"  ✅ 成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("  ⚠️ 知乎所有接口失败")
    return topics

# ============ B站 ============
def fetch_bilibili_hot():
    topics = []
    try:
        print("  [B站] 尝试搜索推荐API...")
        url = 'https://s.search.bilibili.com/main/hotword?limit=30'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            if data.get('code') == 0:
                items = data.get('list', [])
                for idx, item in enumerate(items):
                    title = item.get('show_name', '') or item.get('keyword', '')
                    if not title:
                        continue
                    heat = item.get('hot_id', 0)
                    if isinstance(heat, str):
                        match = re.search(r'(\d+(?:\.\d+)?)', heat)
                        if match:
                            heat = float(match.group(1))
                        else:
                            heat = 0
                    if heat == 0:
                        heat = max(3000 - idx * 100, 100)
                    topics.append({
                        'title': title,
                        'heat': int(heat),
                        'url': f'https://search.bilibili.com/all?keyword={quote(item.get("keyword", title))}',
                        'source': 'bilibili'
                    })
                if topics:
                    print(f"  ✅ 成功: {len(topics)} 条")
                    return topics
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("  ⚠️ B站所有接口失败")
    return topics

# ============ 抖音 ============
def fetch_douyin_hot():
    topics = []
    try:
        print("  [抖音] 尝试官方API...")
        headers_dy = {**HEADERS, 'Referer': 'https://www.douyin.com/'}
        resp = safe_request('https://www.douyin.com/aweme/v1/web/hot/search/list/', headers=headers_dy, timeout=10)
        if resp:
            data = resp.json()
            word_list = data.get('data', {}).get('word_list', [])
            for idx, item in enumerate(word_list):
                title = item.get('word', '')
                if not title:
                    continue
                heat = item.get('hot_value', 0)
                if isinstance(heat, str):
                    match = re.search(r'(\d+(?:\.\d+)?)', heat)
                    if match:
                        heat = float(match.group(1))
                    else:
                        heat = 0
                if heat == 0:
                    heat = max(10000 - idx * 300, 100)
                topics.append({
                    'title': title,
                    'heat': int(heat),
                    'url': f'https://www.douyin.com/search/{quote(title)}',
                    'source': 'douyin'
                })
            if topics:
                print(f"  ✅ 成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    print("  ⚠️ 抖音所有接口失败")
    return topics

# ============ 合并数据（新逻辑） ============
def merge_topics(all_data):
    """
    新的合并逻辑：
    1. 每个平台的数据独立保留
    2. 综合排名使用归一化后的热度
    3. 显示时保留原始热度值
    """
    topic_map = {}

    # 第一步：收集所有数据
    for source_name, topics in all_data.items():
        for item in topics:
            title = item['title']
            key = title

            if key not in topic_map:
                topic_map[key] = {
                    'title': title,
                    'heat': {'weibo': 0, 'baidu': 0, 'zhihu': 0, 'bilibili': 0, 'douyin': 0},
                    'normalized_heat': {'weibo': 0, 'baidu': 0, 'zhihu': 0, 'bilibili': 0, 'douyin': 0},
                    'sources': [],
                    'summary': item.get('summary', ''),
                    'categories': []
                }

            source = item.get('source', source_name)
            heat = item.get('heat', 0)
            if isinstance(heat, str):
                match = re.search(r'(\d+(?:\.\d+)?)', heat)
                if match:
                    heat = float(match.group(1))
                    if '万' in heat or 'w' in heat.lower():
                        heat *= 10000
                    elif '亿' in heat:
                        heat *= 100000000
                else:
                    heat = 0

            heat = int(heat)

            # 保存原始热度值
            topic_map[key]['heat'][source] = heat

            # 保存归一化热度值（用于排名）
            topic_map[key]['normalized_heat'][source] = normalize_heat(source, heat)

            # 添加来源（保留原始热度用于显示）
            source_url = item.get('url', '')
            existing = [s['name'] for s in topic_map[key]['sources']]
            source_display = {'weibo': '微博', 'baidu': '百度', 'zhihu': '知乎', 'bilibili': 'B站', 'douyin': '抖音'}.get(source, source)
            if source_display not in existing:
                topic_map[key]['sources'].append({
                    'name': source_display,
                    'url': source_url,
                    'heat': heat  # 原始热度值
                })

            # 更新摘要
            if item.get('summary') and len(item['summary']) > len(topic_map[key]['summary']):
                topic_map[key]['summary'] = item['summary']

            # 分类
            cat = classify_topic(title, topic_map[key]['summary'])
            topic_map[key]['categories'].append(cat)

    # 第二步：计算综合排名
    topics = []
    for key, data in topic_map.items():
        # 计算平台覆盖数
        source_count = len(data['sources'])

        # 计算归一化热度总和（用于排名）
        normalized_total = sum(data['normalized_heat'].values())

        # 计算原始热度总和（用于显示）
        original_total = sum(data['heat'].values())

        # 综合分数 = 平台覆盖数 * 10000 + 归一化热度总和
        composite_score = source_count * 10000 + normalized_total

        categories = data['categories']
        category = max(set(categories), key=categories.count) if categories else 'social'

        # 趋势判断
        if source_count >= 3:
            trend = 'hot'
            trend_val = 0
        elif source_count >= 2:
            trend = 'up'
            trend_val = random.randint(5, 15)
        else:
            trend = 'up'
            trend_val = random.randint(1, 10)

        topics.append({
            'rank': 0,
            'title': data['title'],
            'category': category,
            'summary': data['summary'] or data['title'],
            'heat': data['heat'],  # 各平台原始热度（用于显示）
            'normalized_heat': data['normalized_heat'],  # 归一化热度（用于排名）
            'total_heat': original_total,  # 原始热度总和
            'normalized_total': normalized_total,  # 归一化热度总和
            'source_count': source_count,
            'composite_score': composite_score,
            'trend': trend,
            'trendVal': trend_val,
            'sources': data['sources']  # 包含原始热度
        })

    # 按综合分数排序
    topics.sort(key=lambda x: x['composite_score'], reverse=True)

    # 重新编号，取前30
    for i, topic in enumerate(topics[:30]):
        topic['rank'] = i + 1

    return topics[:30]

# ============ 主函数 ============
def generate_data():
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)

    print(f"[{beijing_now}] 开始抓取热点数据...")

    all_data = {}
    print("[1/5] 抓取微博热搜...")
    all_data['weibo'] = fetch_weibo_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("[2/5] 抓取百度热搜...")
    all_data['baidu'] = fetch_baidu_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("[3/5] 抓取知乎热榜...")
    all_data['zhihu'] = fetch_zhihu_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("[4/5] 抓取B站热搜...")
    all_data['bilibili'] = fetch_bilibili_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("[5/5] 抓取抖音热榜...")
    all_data['douyin'] = fetch_douyin_hot()

    total_fetched = sum(len(v) for v in all_data.values())
    print("=" * 50)
    print("抓取统计:")
    for source, topics in all_data.items():
        status = "✅" if topics else "❌"
        print(f"  {status} {source}: {len(topics)} 条")
    print("=" * 50)

    if total_fetched == 0:
        print("所有数据源均抓取失败！")
        all_data = {
            'weibo': [],
            'baidu': [],
            'zhihu': [],
            'bilibili': [],
            'douyin': []
        }

    print("合并数据...")
    topics = merge_topics(all_data)
    print(f"合并后: {len(topics)} 条热点")

    # 统计各平台覆盖情况
    platform_counts = {'weibo': 0, 'baidu': 0, 'zhihu': 0, 'bilibili': 0, 'douyin': 0}
    for topic in topics:
        for source in topic['sources']:
            source_name = source['name']
            if source_name == '微博':
                platform_counts['weibo'] += 1
            elif source_name == '百度':
                platform_counts['baidu'] += 1
            elif source_name == '知乎':
                platform_counts['zhihu'] += 1
            elif source_name == 'B站':
                platform_counts['bilibili'] += 1
            elif source_name == '抖音':
                platform_counts['douyin'] += 1

    print("平台覆盖统计:")
    for platform, count in platform_counts.items():
        print(f"  {platform}: {count} 条")

    output = {
        'updateTime': beijing_now.strftime('%Y-%m-%d %H:%M'),
        'topics': topics
    }

    with open('data/hot_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[{beijing_now}] 数据已更新，共 {len(topics)} 条热点")
    print(f"更新时间: {output['updateTime']}")

    print("Top 5 热点:")
    for i, t in enumerate(topics[:5]):
        sources_str = ', '.join([f"{s['name']}({s['heat']})" for s in t['sources']])
        print(f"  {i+1}. {t['title'][:40]}...")
        print(f"     覆盖: {t['source_count']}平台, 综合: {t['composite_score']}")
        print(f"     原始热度: {t['total_heat']}, 归一化: {t['normalized_total']}")
        print(f"     来源: [{sources_str}]")

    return output

if __name__ == '__main__':
    generate_data()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热点榜单自动更新脚本 (v5.2 最终修复版)
修复: JSON解析问题，Rebang API返回字符串而不是字典
"""

import json
import sys
import time
import random
from datetime import datetime, timedelta
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests")
    sys.exit(1)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://rebang.today/',
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

def parse_json_response(resp):
    """解析响应，处理字符串JSON的情况"""
    try:
        data = resp.json()
        # 如果返回的是字符串，再次解析
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except Exception as e:
        print(f"  ❌ JSON解析失败: {e}")
        return None

def fetch_rebang_data(platform):
    """从 Rebang.Today 获取数据"""
    topics = []
    try:
        print(f"  [{platform}] 尝试 Rebang.Today API...")
        url = f'https://api.rebang.today/v1/items?tab={platform}&date_type=now&version=1'
        resp = safe_request(url, timeout=15)
        if resp:
            data = parse_json_response(resp)
            if data is None:
                return topics

            # 检查数据结构
            if isinstance(data, dict) and 'data' in data:
                data_inner = data['data']
                if isinstance(data_inner, dict) and 'list' in data_inner:
                    items = data_inner['list']
                    for idx, item in enumerate(items[:30]):
                        title = item.get('title', '')
                        if not title:
                            continue
                        # Rebang 返回的热度值
                        hot = item.get('hot', 0)
                        if isinstance(hot, str):
                            import re
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
                            hot = max(10000 - idx * 300, 100)

                        topics.append({
                            'title': title,
                            'heat': int(hot),
                            'url': item.get('www_url', item.get('url', '')),
                            'source': platform
                        })
                    if topics:
                        print(f"  ✅ Rebang成功: {len(topics)} 条")
                        return topics
                else:
                    print(f"  ⚠️ 数据结构不正确: {type(data_inner)}")
            else:
                print(f"  ⚠️ 返回数据格式不正确: {type(data)}")
    except Exception as e:
        print(f"  ❌ Rebang失败: {e}")

    return topics

# ============ 各平台抓取 ============
def fetch_weibo_hot():
    topics = fetch_rebang_data('weibo')
    if topics:
        return topics
    print("  ⚠️ 微博所有接口失败")
    return topics

def fetch_baidu_hot():
    topics = fetch_rebang_data('baidu')
    if topics:
        return topics
    print("  ⚠️ 百度所有接口失败")
    return topics

def fetch_zhihu_hot():
    topics = fetch_rebang_data('zhihu')
    if topics:
        return topics
    print("  ⚠️ 知乎所有接口失败")
    return topics

def fetch_bilibili_hot():
    topics = fetch_rebang_data('bilibili')
    if topics:
        return topics
    print("  ⚠️ B站所有接口失败")
    return topics

def fetch_douyin_hot():
    topics = fetch_rebang_data('douyin')
    if topics:
        return topics
    print("  ⚠️ 抖音所有接口失败")
    return topics

# ============ 合并数据 ============
def merge_topics(all_data):
    topic_map = {}
    for source_name, topics in all_data.items():
        for idx, item in enumerate(topics):
            title = item['title']
            key = title[:15]
            if key not in topic_map:
                topic_map[key] = {
                    'title': title,
                    'heat': {'weibo': 0, 'baidu': 0, 'zhihu': 0, 'bilibili': 0, 'douyin': 0},
                    'sources': [],
                    'summary': item.get('summary', ''),
                    'categories': []
                }
            source = item.get('source', source_name)
            heat = item.get('heat', 0)
            if isinstance(heat, str):
                import re
                match = re.search(r'(\d+(?:\.\d+)?)', heat)
                if match:
                    heat = float(match.group(1))
                    if '万' in heat or 'w' in heat.lower():
                        heat *= 10000
                    elif '亿' in heat:
                        heat *= 100000000
                else:
                    heat = 0

            if source == 'weibo':
                normalized_heat = min(heat, 10000)
            elif source == 'baidu':
                normalized_heat = min(heat / 10, 10000)
            elif source == 'zhihu':
                normalized_heat = min(heat / 100, 10000)
            elif source == 'bilibili':
                normalized_heat = min(heat * 2, 10000)
            elif source == 'douyin':
                normalized_heat = min(heat, 10000)
            else:
                normalized_heat = min(heat, 10000)

            topic_map[key]['heat'][source] = max(topic_map[key]['heat'][source], normalized_heat)
            source_url = item.get('url', '')
            existing = [s['name'] for s in topic_map[key]['sources']]
            source_display = {'weibo': '微博', 'baidu': '百度', 'zhihu': '知乎', 'bilibili': 'B站', 'douyin': '抖音'}.get(source, source)
            if source_display not in existing:
                topic_map[key]['sources'].append({'name': source_display, 'url': source_url})
            if item.get('summary') and len(item['summary']) > len(topic_map[key]['summary']):
                topic_map[key]['summary'] = item['summary']
            cat = classify_topic(title, topic_map[key]['summary'])
            topic_map[key]['categories'].append(cat)

    topics = []
    for key, data in topic_map.items():
        total_heat = sum(data['heat'].values())
        categories = data['categories']
        category = max(set(categories), key=categories.count) if categories else 'social'
        source_count = len(data['sources'])
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
            'heat': data['heat'],
            'trend': trend,
            'trendVal': trend_val,
            'sources': data['sources']
        })
    topics.sort(key=lambda x: sum(x['heat'].values()), reverse=True)
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
        # 使用空数据，不退出
        all_data = {
            'weibo': [],
            'baidu': [],
            'zhihu': [],
            'bilibili': [],
            'douyin': []
        }

    print("合并数据，去重并计算综合热度...")
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
        total = sum(t['heat'].values())
        sources = [s['name'] for s in t['sources']]
        print(f"  {i+1}. {t['title'][:40]}... (热度: {total:.0f}) [{', '.join(sources)}]")

    return output

if __name__ == '__main__':
    generate_data()

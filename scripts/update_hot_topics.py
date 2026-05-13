#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热点榜单自动更新脚本 (重构版)
每小时自动抓取多平台热搜数据，生成 hot_data.json
特点：多层容错、多源备份、失败告警
"""

import json
import re
import sys
import time
import random
from datetime import datetime
from urllib.parse import quote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4")
    sys.exit(1)

# ============ 配置 ============
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}

# 分类关键词映射
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

# ============ 工具函数 ============

def classify_topic(title, summary=''):
    """根据标题和摘要自动分类"""
    text = title + summary
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return 'social'


def safe_request(url, headers=None, timeout=15, retries=3, method='get', **kwargs):
    """带重试的安全请求"""
    headers = headers or HEADERS
    for i in range(retries):
        try:
            if method.lower() == 'post':
                resp = requests.post(url, headers=headers, timeout=timeout, **kwargs)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout, **kwargs)

            if resp.status_code == 200:
                return resp
            elif resp.status_code == 403:
                print(f"  ⚠️ 403 Forbidden (尝试 {i+1}/{retries})")
                time.sleep(random.uniform(1, 3))
            elif resp.status_code == 429:
                print(f"  ⚠️ 429 Too Many Requests (尝试 {i+1}/{retries})")
                time.sleep(random.uniform(3, 6))
            else:
                print(f"  ⚠️ HTTP {resp.status_code} (尝试 {i+1}/{retries})")
                time.sleep(random.uniform(1, 2))
        except requests.exceptions.Timeout:
            print(f"  ⚠️ 请求超时 (尝试 {i+1}/{retries})")
            time.sleep(random.uniform(2, 4))
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️ 连接错误 (尝试 {i+1}/{retries})")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"  ⚠️ 请求异常: {e} (尝试 {i+1}/{retries})")
            time.sleep(random.uniform(1, 2))

    return None


def extract_heat_value(text):
    """从文本中提取热度数值"""
    if not text:
        return 0
    # 匹配数字（支持万、亿等单位）
    match = re.search(r'(\d+(?:\.\d+)?)(?:万|亿|w|W)?', str(text))
    if match:
        val = float(match.group(1))
        if '亿' in str(text) or '万' in str(text) or 'w' in str(text).lower():
            val *= 10000
        return int(val)
    return 0


# ============ 数据源1: 微博热搜 ============

def fetch_weibo_hot():
    """抓取微博热搜 - 使用多个备用接口"""
    topics = []

    # 尝试1: 微博移动端API (通过m.weibo.cn)
    try:
        print("  [微博] 尝试接口1: m.weibo.cn...")
        url = 'https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            if data.get('ok') == 1 and 'data' in data:
                cards = data['data'].get('cards', [])
                for card in cards:
                    card_group = card.get('card_group', [])
                    for item in card_group:
                        title = item.get('desc', '')
                        if not title or title in ['热搜', '实时上升热点', '更多热搜']:
                            continue
                        heat = item.get('desc_extr', 0)
                        if isinstance(heat, str):
                            heat = extract_heat_value(heat)

                        topics.append({
                            'title': title,
                            'heat': max(heat, 100),
                            'url': f'https://s.weibo.com/weibo?q={quote(title)}',
                            'source': 'weibo'
                        })

                if topics:
                    print(f"  ✅ 微博接口1成功: {len(topics)} 条")
                    return topics
    except Exception as e:
        print(f"  ❌ 微博接口1失败: {e}")

    # 尝试2: 通过weibo.com的新版API (需要特殊header)
    try:
        print("  [微博] 尝试接口2: weibo.com API...")
        headers2 = {
            **HEADERS,
            'Referer': 'https://weibo.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        url = 'https://weibo.com/ajax/side/hotSearch'
        resp = safe_request(url, headers=headers2, timeout=10)
        if resp:
            data = resp.json()
            realtime = data.get('data', {}).get('realtime', [])
            for item in realtime:
                title = item.get('word', '')
                if not title:
                    continue
                raw_hot = item.get('raw_hot', 0)
                rank = item.get('rank', 0)

                topics.append({
                    'title': title,
                    'heat': max(raw_hot, 100),
                    'url': f'https://s.weibo.com/weibo?q={quote(title)}',
                    'source': 'weibo'
                })

            if topics:
                print(f"  ✅ 微博接口2成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 微博接口2失败: {e}")

    print("  ⚠️ 微博所有接口均失败")
    return topics


# ============ 数据源2: 百度热搜 ============

def fetch_baidu_hot():
    """抓取百度热搜 - 使用API和页面解析双重策略"""
    topics = []

    # 尝试1: 百度公开API
    try:
        print("  [百度] 尝试接口1: 百度API...")
        url = 'https://top.baidu.com/api/board?platform=wise&tab=realtime'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            cards = data.get('data', {}).get('cards', [])
            for card in cards:
                content = card.get('content', [])
                for item in content:
                    title = item.get('word', '')
                    if not title:
                        continue
                    raw_hot = item.get('raw_hot', 0)
                    desc = item.get('desc', '')

                    topics.append({
                        'title': title,
                        'heat': max(raw_hot, 100),
                        'summary': desc[:100] if desc else '',
                        'url': f'https://www.baidu.com/s?wd={quote(title)}',
                        'source': 'baidu'
                    })

            if topics:
                print(f"  ✅ 百度接口1成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 百度接口1失败: {e}")

    # 尝试2: 百度页面解析
    try:
        print("  [百度] 尝试接口2: 页面解析...")
        url = 'https://top.baidu.com/board?tab=realtime'
        resp = safe_request(url, timeout=10)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.find_all('div', class_=re.compile('category-wrap'))
            for item in items[:30]:
                title_elem = item.find('div', class_=re.compile('single-text'))
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                heat_elem = item.find('div', class_=re.compile('hot-index'))
                heat = 0
                if heat_elem:
                    heat = extract_heat_value(heat_elem.get_text())

                summary_elem = item.find('div', class_=re.compile('content_'))
                summary = summary_elem.get_text(strip=True)[:100] if summary_elem else ''

                topics.append({
                    'title': title,
                    'heat': max(heat, 100),
                    'summary': summary,
                    'url': f'https://www.baidu.com/s?wd={quote(title)}',
                    'source': 'baidu'
                })

            if topics:
                print(f"  ✅ 百度接口2成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 百度接口2失败: {e}")

    print("  ⚠️ 百度所有接口均失败")
    return topics


# ============ 数据源3: 知乎热榜 ============

def fetch_zhihu_hot():
    """抓取知乎热榜 - 使用公开API"""
    topics = []

    try:
        print("  [知乎] 尝试API接口...")
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50'
        headers_zhihu = {
            **HEADERS,
            'Referer': 'https://www.zhihu.com/hot',
            'x-api-version': '3.0.91',
            'x-app-za': 'OS=Web',
        }
        resp = safe_request(url, headers=headers_zhihu, timeout=10)
        if resp:
            data = resp.json()
            items = data.get('data', [])
            for item in items:
                target = item.get('target', {})
                title = target.get('title', '')
                if not title:
                    continue

                # 知乎热度计算: detail_text 如 "1234 万热度"
                detail = item.get('detail_text', '')
                heat = extract_heat_value(detail)

                # 如果没有热度值，用排名估算
                if heat == 0:
                    heat = max(5000000 - items.index(item) * 100000, 100000)

                answer_count = target.get('answer_count', 0)
                follower_count = target.get('follower_count', 0)

                topics.append({
                    'title': title,
                    'heat': heat,
                    'summary': target.get('excerpt', '')[:100],
                    'url': target.get('url', f'https://www.zhihu.com/question/{target.get("id", "")}'),
                    'source': 'zhihu'
                })

            if topics:
                print(f"  ✅ 知乎API成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 知乎API失败: {e}")

    print("  ⚠️ 知乎所有接口均失败")
    return topics


# ============ 数据源4: B站热搜 ============

def fetch_bilibili_hot():
    """抓取B站热搜"""
    topics = []

    try:
        print("  [B站] 尝试API接口...")
        url = 'https://api.bilibili.com/x/web-interface/search/square?limit=30'
        resp = safe_request(url, timeout=10)
        if resp:
            data = resp.json()
            if data.get('code') == 0:
                items = data.get('data', {}).get('trending', {}).get('list', [])
                for item in items:
                    title = item.get('keyword', '')
                    if not title:
                        continue
                    show_name = item.get('show_name', title)
                    heat = item.get('hot_id', 0)  # B站用hot_id表示热度

                    topics.append({
                        'title': show_name or title,
                        'heat': max(heat, 100),
                        'url': f'https://search.bilibili.com/all?keyword={quote(title)}',
                        'source': 'bilibili'
                    })

                if topics:
                    print(f"  ✅ B站API成功: {len(topics)} 条")
                    return topics
    except Exception as e:
        print(f"  ❌ B站API失败: {e}")

    print("  ⚠️ B站所有接口均失败")
    return topics


# ============ 数据源5: 抖音热榜 ============

def fetch_douyin_hot():
    """抓取抖音热榜"""
    topics = []

    try:
        print("  [抖音] 尝试API接口...")
        url = 'https://www.douyin.com/aweme/v1/web/hot/search/list/'
        headers_dy = {
            **HEADERS,
            'Referer': 'https://www.douyin.com/',
            'Cookie': 'msToken=; ttwid=;'
        }
        resp = safe_request(url, headers=headers_dy, timeout=10)
        if resp:
            data = resp.json()
            word_list = data.get('data', {}).get('word_list', [])
            for item in word_list:
                title = item.get('word', '')
                if not title:
                    continue
                heat = item.get('hot_value', 0)

                topics.append({
                    'title': title,
                    'heat': max(heat, 100),
                    'url': f'https://www.douyin.com/search/{quote(title)}',
                    'source': 'douyin'
                })

            if topics:
                print(f"  ✅ 抖音API成功: {len(topics)} 条")
                return topics
    except Exception as e:
        print(f"  ❌ 抖音API失败: {e}")

    print("  ⚠️ 抖音所有接口均失败")
    return topics


# ============ 数据合并 ============

def merge_topics(all_data):
    """合并各平台数据，去重并计算综合热度"""
    topic_map = {}

    for source_name, topics in all_data.items():
        for item in topics:
            title = item['title']
            # 使用标题前15字作为去重key
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

            # 归一化热度值 (不同平台数值范围差异很大)
            if source == 'weibo':
                normalized_heat = min(heat / 100, 10000)  # 微博热度通常较小
            elif source == 'baidu':
                normalized_heat = min(heat / 10000, 10000)  # 百度热度通常很大
            elif source == 'zhihu':
                normalized_heat = min(heat / 10000, 10000)
            elif source == 'bilibili':
                normalized_heat = min(heat / 100, 10000)
            elif source == 'douyin':
                normalized_heat = min(heat / 1000, 10000)
            else:
                normalized_heat = min(heat, 10000)

            topic_map[key]['heat'][source] = max(topic_map[key]['heat'][source], normalized_heat)

            # 添加来源（去重）
            source_url = item.get('url', '')
            existing = [s['name'] for s in topic_map[key]['sources']]
            source_display = {'weibo': '微博', 'baidu': '百度', 'zhihu': '知乎', 'bilibili': 'B站', 'douyin': '抖音'}.get(source, source)
            if source_display not in existing:
                topic_map[key]['sources'].append({
                    'name': source_display,
                    'url': source_url
                })

            # 更新摘要（优先用更长的）
            if item.get('summary') and len(item['summary']) > len(topic_map[key]['summary']):
                topic_map[key]['summary'] = item['summary']

            # 记录分类
            cat = classify_topic(title, topic_map[key]['summary'])
            topic_map[key]['categories'].append(cat)

    # 转换为列表
    topics = []
    for key, data in topic_map.items():
        total_heat = sum(data['heat'].values())

        # 使用出现最多的分类
        categories = data['categories']
        category = max(set(categories), key=categories.count) if categories else 'social'

        # 计算趋势 (简单规则：多平台出现=hot，单平台=up)
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
            'rank': 0,  # 稍后重新编号
            'title': data['title'],
            'category': category,
            'summary': data['summary'] or data['title'],
            'heat': data['heat'],
            'trend': trend,
            'trendVal': trend_val,
            'sources': data['sources']
        })

    # 按综合热度排序
    topics.sort(key=lambda x: sum(x['heat'].values()), reverse=True)

    # 重新编号，取前30
    for i, topic in enumerate(topics[:30]):
        topic['rank'] = i + 1

    return topics[:30]


# ============ 主函数 ============

def generate_data():
    """主函数：抓取数据并生成 JSON"""
    print(f"[{datetime.now()}] 开始抓取热点数据...")

    all_data = {}

    # 抓取各平台数据
    print("\n[1/5] 抓取微博热搜...")
    all_data['weibo'] = fetch_weibo_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("\n[2/5] 抓取百度热搜...")
    all_data['baidu'] = fetch_baidu_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("\n[3/5] 抓取知乎热榜...")
    all_data['zhihu'] = fetch_zhihu_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("\n[4/5] 抓取B站热搜...")
    all_data['bilibili'] = fetch_bilibili_hot()
    time.sleep(random.uniform(0.5, 1.5))

    print("\n[5/5] 抓取抖音热榜...")
    all_data['douyin'] = fetch_douyin_hot()

    # 统计
    total_fetched = sum(len(v) for v in all_data.values())
    print(f"\n{'='*50}")
    print(f"抓取统计:")
    for source, topics in all_data.items():
        status = "✅" if topics else "❌"
        print(f"  {status} {source}: {len(topics)} 条")
    print(f"{'='*50}")

    # 检查是否有数据
    if total_fetched == 0:
        print("\n❌ 错误：所有数据源均抓取失败，没有获取到任何数据！")
        print("可能原因：")
        print("  1. 网络连接问题")
        print("  2. 目标网站反爬机制升级")
        print("  3. API接口变更")
        sys.exit(1)  # 让 GitHub Actions 标记为失败

    # 合并数据
    print("\n[合并数据] 去重并计算综合热度...")
    topics = merge_topics(all_data)
    print(f"合并后: {len(topics)} 条热点")

    # 生成输出
    output = {
        'updateTime': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'topics': topics
    }

    # 写入文件
    with open('data/hot_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[{datetime.now()}] ✅ 数据已更新，共 {len(topics)} 条热点")
    print(f"更新时间: {output['updateTime']}")

    # 显示前5条
    print("\nTop 5 热点:")
    for i, t in enumerate(topics[:5]):
        total = sum(t['heat'].values())
        sources = [s['name'] for s in t['sources']]
        print(f"  {i+1}. {t['title'][:40]}... (热度: {total:.0f}) [{', '.join(sources)}]")

    return output


if __name__ == '__main__':
    generate_data()

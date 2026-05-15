#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全网热点榜单自动更新脚本 (v12)
修复:
1. 移除 politics 中单独的"韩国"关键词
2. sports 增加"赛场""啦啦队""饭拍"等词
3. 保留所有之前的防卡死和智能分类改进
"""

import json
import sys
import time
import random
import re
import os
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

# ============ 智能分类系统 (v3) ============
CATEGORY_KEYWORDS = {
    'politics': {
        'primary': [
            '特朗普', '普京', '拜登', '泽连斯基', '内塔尼亚胡', '哈梅内伊', '金正恩',
            '外交部', '国务院', '国防部', '发改委', '商务部', '教育部', '卫健委',
            '中美', '中俄', '中日', '中欧', '中印', '朝韩', '巴以', '俄乌',
            '会晤', '会谈', '谈判', '访问', '出访', '接待', '国事访问', '正式访问',
            '政治', '外交', '军事', '战争', '冲突', '制裁', '关税', '贸易战',
            '伊朗', '以色列', '巴勒斯坦', '乌克兰', '俄罗斯', '朝鲜', '韩朝', '日韩', '日美', '美韩', '韩美', '中日韩', '日本',
            '台湾', '香港', '澳门', '新疆', '西藏',
            '两会', '人大', '政协', '全会', '常委会', '代表大会',
            '总书记', '主席', '总理', '部长', '省长', '市长', '州长', '县长',
            '选举', '投票', '民意', '公投', '宪法', '法律', '法案', '政策',
            '北约', '欧盟', '联合国', '安理会', 'G7', 'G20', 'APEC', '金砖',
            '使馆', '领事馆', '大使', '领事', '外交官', '发言人',
            '访华', '访美', '访俄', '访日', '访欧', '出国', '外交部长', '国防部长'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员', '艺人', '导演'],
        'force': ['外交部发言人', '国防部', '国务院', '两会', '人大', '政协', '总书记', '主席', '总理']
    },
    'tech': {
        'primary': [
            '微信', '支付宝', '抖音', '快手', '小红书', 'B站', '知乎', '微博',
            'AI', '人工智能', '大模型', 'GPT', 'ChatGPT', 'OpenAI', 'Claude', 'Gemini',
            '芯片', '半导体', '光刻机', '台积电', '中芯国际', '华为', '苹果', '三星', '小米', 'OPPO', 'vivo',
            '科技', '数码', '手机', '电脑', '笔记本', '平板', '耳机', '手表', '手环',
            '互联网', '网络安全', '黑客', '漏洞', '勒索病毒',
            '宇树', '机器人', '人形机器人', '四足机器人', '无人机', '自动驾驶',
            '马斯克', '特斯拉', 'SpaceX', '星舰', '星链', '电动车', '新能源汽车', '比亚迪', '蔚来', '小鹏', '理想',
            '5G', '6G', 'WiFi', '蓝牙', '卫星通信', '量子', '云计算', '边缘计算',
            '区块链', '比特币', '以太坊', 'NFT', '元宇宙', 'VR', 'AR', 'MR',
            '编程', '代码', '开源', 'GitHub', '开发者', '程序员', '工程师',
            '发布会', '新品', '上市', '发售', '预售', '测评', '评测', '跑分',
            '系统更新', 'iOS', 'Android', '鸿蒙', 'Windows', 'macOS'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员', '艺人'],
        'force': ['GPT', 'ChatGPT', 'OpenAI', '芯片', '半导体', '光刻机', '大模型', '人工智能', '自动驾驶', '星舰', 'SpaceX']
    },
    'entertainment': {
        'primary': [
            '明星', '演员', '歌手', '偶像', '练习生', '女团', '男团', '乐队',
            '电影', '影片', '院线', '首映', '重映', '撤档', '定档', '票房', '影评',
            '电视剧', '网剧', '短剧', '剧集', '追剧', '番剧', '动漫', '动画',
            '综艺', '真人秀', '选秀', '脱口秀', '相声', '小品', '喜剧', '话剧',
            '演唱会', '音乐会', '音乐节', '巡演', 'Live', '现场',
            '娱乐', '八卦', '绯闻', '恋情', '分手', '复合', '离婚', '结婚', '求婚', '出轨', '爆料', '塌房', '封杀', '复出',
            '导演', '编剧', '制片人', '摄影师', '造型师', '经纪人',
            '戛纳', '奥斯卡', '金马', '金像', '百花', '飞天', '白玉兰', '金鹰', '金鸡', '华表', '金马奖', '金像奖',
            '红毯', '颁奖', '获奖', '提名', '入围', '影帝', '影后', '视帝', '视后',
            '网红', '主播', 'UP主', '博主', 'KOL', 'MCN',
            '配音', '声优', 'COS', '漫展', '同人', '二创', '鬼畜'
        ],
        'exclude': ['疫情', '病毒', '疫苗', '医院', '医生', '疾病', '癌症', '手术'],
        'force': ['票房', '首映', '定档', '撤档', '演唱会', '音乐节', '红毯', '颁奖', '影帝', '影后', '塌房', '封杀']
    },
    'sports': {
        'primary': [
            '世界杯', '欧洲杯', '美洲杯', '亚洲杯', '非洲杯',
            '足球', '英超', '西甲', '意甲', '德甲', '法甲', '中超', '中甲', '亚冠', '欧冠', '欧联', '世俱杯',
            '篮球', 'NBA', 'CBA', 'WNBA', 'NCAA', '全明星', '季后赛', '总决赛', '选秀', '状元',
            '乒乓球', '羽毛球', '网球', '排球', '棒球', '橄榄球', '冰球', '曲棍球', '手球',
            '高尔夫', '台球', '斯诺克', '九球',
            '游泳', '跳水', '花游', '水球',
            '田径', '短跑', '长跑', '马拉松', '跨栏', '跳远', '跳高', '铅球', '铁饼',
            '体操', '艺术体操', '蹦床', '技巧',
            '举重', '拳击', '跆拳道', '柔道', '摔跤', '空手道', '散打', '搏击', '格斗', 'UFC', 'MMA',
            '击剑', '射箭', '射击', '马术', '赛艇', '皮划艇', '帆船', '帆板',
            '自行车', '公路赛', '山地车', 'BMX',
            '滑雪', '单板', '双板', '滑冰', '花滑', '速滑', '冰壶', '雪车', '雪橇',
            '攀岩', '滑板', '冲浪', '轮滑', '街舞', '霹雳舞',
            '体育', '比赛', '赛事', '联赛', '锦标赛', '大奖赛', '公开赛', '冠军赛',
            '冠军', '亚军', '季军', '金牌', '银牌', '铜牌', '奖牌榜', '积分榜', '排行榜',
            '运动员', '选手', '球员', '球星',
            '湖人', '勇士', '凯尔特人', '热火', '掘金', '雷霆', '独行侠', '快船', '太阳', '雄鹿',
            '皇马', '巴萨', '曼城', '利物浦', '阿森纳', '切尔西', '曼联', '拜仁', '巴黎', '国米', '米兰', '尤文',
            '法网', '温网', '澳网', '美网', '大满贯',
            '奥运', '亚运会', '全运会', '世乒赛', '苏迪曼杯', '汤尤杯', '汤姆斯杯', '尤伯杯',
            'F1', '赛车', 'NASCAR', '拉力赛', '达喀尔',
            '转会', '续约', '签约', '加盟', '离队', '退役', '复出', '伤停', '禁赛', '红牌', '黄牌',
            '裁判', 'VAR', '点球', '任意球', '角球', '越位', '犯规', '绝杀', '逆转', '平局', '加时', '点球大战',
            '国足', '男足', '女足', '国青', '国奥', '国少', '国家队',
            '赛场', '球场', '体育场', '体育馆', '啦啦队', '啦啦操', '饭拍', '直拍', '应援', '球迷', '观众', '主场', '客场'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员'],
        'force': ['NBA', 'CBA', '英超', '欧冠', '世界杯', '奥运', '法网', '温网', '大满贯', 'F1', 'UFC', 'MMA', '转会', '退役', '国足']
    },
    'finance': {
        'primary': [
            '股价', '股票', '股市', 'A股', '港股', '美股', '沪深', '创业板', '科创板', '北交所', '新三板',
            '牛市', '熊市', '涨停', '跌停', '停牌', '复牌', '破发',
            '大盘', '沪指', '深指', '成指', '恒生', '纳斯达克', '道琼斯', '标普',
            '指数', 'ETF', 'LOF', '股指期货', '期权', '权证',
            '经济', '宏观经济', 'GDP', 'CPI', 'PPI', 'PMI', '通胀', '通缩', '衰退', '复苏',
            '金融', '银行', '央行', '降准', '降息', '加息', 'MLF', 'LPR', '逆回购',
            '存款', '贷款', '房贷', '车贷', '消费贷', '经营贷', '信用贷',
            '油价', '房价',
            '企业', '公司', '集团', '市值', '估值', '营收', '利润', '财报', '年报', '季报', '中报',
            '基金', '公募', '私募', '货币基金', '债券基金', '股票基金', '混合基金', '指数基金',
            '理财', '保险', '寿险', '财险', '健康险', '意外险', '分红险', '万能险',
            '债券', '国债', '地方债', '企业债', '可转债', '城投债',
            '汇率', '人民币', '美元', '欧元', '日元', '英镑', '港币', '离岸人民币',
            '黄金', '白银', '原油', '大宗商品', '期货', '现货',
            '比特币', '以太坊', '加密货币', '数字货币', '稳定币', 'DeFi', '挖矿',
            'IPO', '上市', '退市', '借壳', '重组', '并购', '收购', '分拆', '借壳上市',
            '破产', '清算', '债务', '违约', '暴雷', '跑路', 'P2P', '非法集资',
            '税务', '税收', '个税', '增值税', '消费税', '关税', '减税降费',
            '就业', '失业', '招聘', '裁员', '降薪', '社保', '公积金', '养老金'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员', '艺人', '体育', '比赛', '冠军'],
        'force': ['A股', '港股', '美股', '涨停', '跌停', '大盘', '沪指', 'GDP', 'CPI', '降准', '降息', 'IPO', '上市', '退市', '财报']
    },
    'health': {
        'primary': [
            '疫情', '病毒', '毒株', '变异', '变异株', '传播', '传染', '感染', '确诊', '无症状', '密接', '次密接', '隔离', '封控', '解封',
            '疫苗', '接种', '加强针', '辉瑞', '莫德纳', '科兴', '国药', '康希诺',
            '医院', '医生', '护士', '医师', '专家', '院士', '主任', '副主任',
            '健康', '养生', '保健', '体检', '筛查', '早筛',
            '疾病', '病症', '症状', '诊断', '治疗', '治愈', '康复', '复发', '并发症',
            '药品', '药物', '用药', '服药', '处方药', '非处方药', 'OTC', '仿制药', '原研药', '特效药', '靶向药', '免疫疗法',
            '医疗', '医保', '新农合', '医保局', '卫健委', '疾控', '疾控中心', '传染病', '发热门诊',
            '流感', '新冠', '甲流', '乙流', '支原体', '登革热', '疟疾', '艾滋病', 'HIV', '结核', '乙肝', '丙肝', '手足口', '诺如', '猴痘', '埃博拉', '非典', 'SARS', 'MERS',
            '癌症', '肿瘤', '肺癌', '肝癌', '胃癌', '肠癌', '乳腺癌', '宫颈癌', '前列腺癌', '白血病', '淋巴瘤', '黑色素瘤',
            '手术', '开刀', '微创', '介入', '移植', '器官移植', '骨髓移植', '肾移植', '肝移植', '心脏移植',
            '血压', '血糖', '血脂', '尿酸', '胆固醇', '甘油三酯',
            '失眠', '抑郁', '焦虑', '自闭症', '多动症', '阿尔茨海默', '帕金森', '痴呆',
            '近视', '远视', '散光', '白内障', '青光眼', '视网膜',
            '中医', '中药', '针灸', '推拿', '拔罐', '艾灸', '把脉', '方剂',
            '急救', '抢救', 'ICU', '重症监护', '急诊', '120', '救护车',
            '食品安全', '药品安全', '医疗器械', '医美', '整容', '整形', '植发', '正畸'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员', '体育', '比赛', '冠军', '经济', '股市', '金融'],
        'force': ['疫情', '病毒', '疫苗', '医院', '医生', '癌症', '肿瘤', '手术', '医保', '卫健委', '疾控', '流感', '新冠', '甲流', '支原体']
    },
    'life': {
        'primary': [
            '机票', '航班', '航线', '机场', '航空公司', '值机', '登机', '延误', '取消', '改签', '退票',
            '旅游', '旅行', '出游', '度假', '自由行', '跟团', '签证', '护照', '出入境', '海关',
            '酒店', '民宿', '客栈', '青旅', '度假村', '星级酒店', '快捷酒店',
            '美食', '餐厅', '饭店', '小吃', '特产', '米其林', '黑珍珠', '探店', '打卡', '网红店',
            '购物', '消费', '促销', '打折', '优惠', '满减', '秒杀', '抢购', '预售', '尾款', '定金',
            '价格', '涨价', '降价', '调价', '涨价潮', '降价潮', '物价', '菜价', '肉价', '蛋价', '奶价',
            '生活', '日常', '居家', '家务', '收纳', '整理',
            '家庭', '亲子', '育儿', '母婴', '孕妇', '产假', '育儿假', '托育', '早教', '幼儿园',
            '装修', '家装', '软装', '硬装', '全屋定制', '智能家居', '家具', '家电', '厨具', '卫浴', '灯具', '地板', '瓷砖', '壁纸', '涂料',
            '汽车', '买车', '卖车', '二手车', '新车', '试驾', '提车', '保养', '维修', '年检', '驾照', '驾考', '科目', '充电桩', '换电站',
            '油价', '汽油', '柴油', '92号', '95号', '98号', '油价上调', '油价下调', '成品油',
            '天气', '气候', '气温', '降雨', '降雪', '台风', '暴雨', '高温', '寒潮', '雾霾', '沙尘暴', '冰雹', '龙卷风', '厄尔尼诺', '拉尼娜',
            '环保', '低碳', '碳中和', '碳达峰', '节能减排', '垃圾分类', '限塑令', '禁塑令',
            '宠物', '猫', '狗', '犬', '喵', '汪', '流浪动物', '领养', '绝育', '宠物医院', '猫粮', '狗粮',
            '养花', '种菜', '园艺', '多肉', '绿植', '盆栽', '阳台', '庭院',
            '钓鱼', '露营', '徒步', '骑行', '自驾', '摩旅', '房车', '越野', '探险', '登山', '攀岩', '潜水', '滑雪', '冲浪',
            '穿搭', '时尚', '潮流', 'OOTD', '街拍', '时装周',
            '美妆', '护肤', '化妆', '口红', '眼影', '香水', '面膜', '精华', '防晒', '卸妆',
            '发型', '理发', '烫发', '染发', '接发', '护发', '脱发', '秃头', '发际线',
            '快递', '物流', '顺丰', '京东物流', '菜鸟', '驿站', '代收点', '送货上门',
            '外卖', '美团', '饿了么', '骑手', '配送', '准时达',
            '租房', '买房', '卖房', '二手房', '新房', '楼盘', '开发商', '中介', '链家', '贝壳', '安居客',
            '物业', '业委会', '停车位', '停车费', '物业费', '水电费', '燃气费', '暖气费',
            '故宫', '天坛', '颐和园', '圆明园', '长城', '兵马俑', '敦煌', '布达拉宫', '黄山', '泰山', '华山', '张家界', '桂林', '西湖', '九寨沟', '丽江', '大理', '三亚', '厦门', '成都', '西安', '南京', '苏州', '杭州',
            '景点', '景区', '博物馆', '美术馆', '展览', '文物', '古迹', '遗址', '文化遗产', '历史建筑', '古建筑', '园林', '寺庙', '道观', '教堂',
            '文化', '历史', '传统', '民俗', '非遗', '文旅'
        ],
        'exclude': ['电影', '电视剧', '综艺', '演唱会', '票房', '明星', '演员', '体育', '比赛', '冠军', '经济', '股市', '政治', '外交'],
        'force': ['机票', '旅游', '酒店', '美食', '购物', '装修', '汽车', '油价', '天气', '宠物', '租房', '买房', '外卖', '快递', '故宫', '天坛', '颐和园', '景点', '景区', '博物馆', '展览', '文旅']
    },
    'social': {
        'primary': [
            '地震', '火山', '海啸', '台风', '龙卷风', '洪水', '泥石流', '滑坡', '塌方', '崩塌',
            '火灾', '爆炸', '燃爆', '爆燃', '泄漏', '污染', '中毒', '窒息',
            '事故', '车祸', '空难', '海难', '矿难', '坍塌', '坠落', '溺水', '触电',
            '灾难', '灾害', '险情', '危机', '紧急', '应急', '救援', '搜救', '抢险', '救灾', '赈灾', '募捐', '捐助',
            '警察', '公安', '民警', '刑警', '交警', '特警', '武警', 'FBI', 'CIA',
            '法院', '法庭', '审判', '判决', '裁定', '宣判', '开庭', '休庭', '再审', '二审', '终审', '死刑', '无期徒刑', '有期徒刑', '缓刑', '保释', '假释',
            '法律', '法规', '条例', '规章', '司法解释', '宪法', '民法', '刑法', '行政法', '劳动法', '合同法', '婚姻法', '继承法',
            '社会', '民生', '民情', '民意', '舆论', '舆情', '热点', '焦点', '关注', '热议', '讨论', '争议', '辩论', '声讨', '抗议', '游行', '示威', '集会',
            '网红', '主播', 'UP主', '博主', '大V', '素人',
            '直播', '带货', '直播间', '打赏', '礼物', '连麦', 'PK', '封禁', '封号', '限流', '降权',
            '短视频', '抖音', '快手', 'B站', '小红书', '微博', '知乎', '豆瓣', '贴吧', '虎扑', 'NGA', 'V2EX',
            '论坛', '社区', '社群', '圈子', '群组', '频道', '超话',
            '公益', '慈善', '捐赠', '捐款', '捐物', '志愿服务', '志愿者', '义工', '社工',
            '见义勇为', '好人好事', '道德模范', '感动中国', '最美人物',
            '失踪', '寻人', '寻亲', '寻子', '拐卖', '拐卖儿童', '人贩子', '买家', '卖家', '解救',
            '诈骗', '电信诈骗', '网络诈骗', '杀猪盘', '刷单', '冒充', '假冒', '伪造', '传销', '非法集资', '套路贷', '校园贷', '裸贷',
            '盗窃', '抢劫', '抢夺', '强奸', '猥亵', '性骚扰', '性侵', '虐待', '家暴', '暴力', '斗殴', '打架', '持刀', '持枪', '枪击', '枪击案',
            '自杀', '跳楼', '跳桥', '投河', '自焚', '服毒',
            '谣言', '辟谣', '传谣', '造谣', '信谣', '不实信息', '虚假信息', '假新闻', '假消息',
            '隐私', '个人信息', '数据泄露', '信息泄露', '黑客攻击', '勒索软件',
            '就业', '失业', '招聘', '求职', '面试', '简历', '跳槽', '离职', '辞职', '被裁', '裁员', '优化', '毕业', 'N+1', '赔偿金',
            '教育', '学校', '大学', '中学', '小学', '幼儿园', '高考', '中考', '考研', '考公', '考编', '教资', '雅思', '托福', 'GRE', 'SAT',
            '学术', '论文', '期刊', 'SCI', 'Nature', '影响因子', '引用', '查重', '知网', '万方', '维普',
            '交通', '地铁', '公交', '高铁', '动车', '火车', '轻轨', '磁悬浮', '有轨电车', 'BRT',
            '拥堵', '限行', '限号', '单双号', '尾号限行', '交通管制', '封路', '绕行',
            '食品安全', '食品', '添加剂', '防腐剂', '农药残留', '重金属', '地沟油', '瘦肉精', '三聚氰胺',
            '消费维权', '315', '打假', '维权', '投诉', '举报', '曝光', '黑幕', '内幕', '潜规则'
        ],
        'exclude': [],
        'force': ['地震', '火灾', '爆炸', '事故', '灾难', '救援', '法院', '审判', '判决', '诈骗', '拐卖', '自杀', '谣言', '辟谣', '315', '维权', '投诉']
    }
}

CATEGORY_PRIORITY = {
    'politics': 10,
    'health': 9,
    'finance': 8,
    'sports': 7,
    'tech': 6,
    'entertainment': 5,
    'life': 4,
    'social': 3
}

def classify_topic(title, summary=''):
    text_title = title
    text_summary = summary
    text_full = title + summary

    scores = {}

    for category, config in CATEGORY_KEYWORDS.items():
        score = 0

        for force_word in config.get('force', []):
            if force_word in text_full:
                score += 100

        for kw in config['primary']:
            if kw in text_title:
                score += 3

        for kw in config['primary']:
            if kw in text_summary:
                score += 1

        for exclude_word in config.get('exclude', []):
            if exclude_word in text_full:
                score = max(score // 2, 0)
                break

        if score > 0:
            scores[category] = score

    # 检查是否有politics强制词命中
    politics_force = ['中美元首', '外交部', '国防部', '国务院', '两会', '人大', '政协', '总书记', '主席', '总理', '会晤', '会谈', '访问', '访华', '外交']
    if any(w in text_full for w in politics_force):
        if 'politics' in scores and scores['politics'] > 0:
            return 'politics'

    # 文化/旅游/历史类内容优先归到 life（但优先级低于politics强制词）
    cultural_words = ['故宫', '天坛', '颐和园', '圆明园', '长城', '兵马俑', '敦煌', '布达拉宫', '黄山', '泰山', '华山', '张家界', '桂林', '西湖', '九寨沟', '丽江', '大理', '三亚', '厦门', '成都', '西安', '南京', '苏州', '杭州', '景点', '景区', '博物馆', '美术馆', '展览', '文物', '古迹', '遗址', '文化遗产', '历史建筑', '古建筑', '园林', '寺庙', '道观', '教堂', '文化', '历史', '传统', '民俗', '非遗']
    if any(w in text_full for w in cultural_words):
        politics_score = scores.get('politics', 0)
        life_score = scores.get('life', 0)
        if life_score > 0 and politics_score <= life_score + 3:
            return 'life'
        elif politics_score <= 3 and life_score == 0:
            return 'life'

    if not scores:
        return 'social'

    max_score = max(scores.values())
    top_categories = [cat for cat, s in scores.items() if s == max_score]

    if len(top_categories) > 1:
        top_categories.sort(key=lambda c: CATEGORY_PRIORITY.get(c, 0), reverse=True)

    return top_categories[0]

# ============ 防卡死请求函数 ============
def safe_request(url, headers=None, timeout=10, retries=2):
    headers = headers or HEADERS
    for i in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            print(f"  ⚠️ HTTP {resp.status_code} (尝试 {i+1}/{retries})")
            time.sleep(1)
        except requests.exceptions.Timeout:
            print(f"  ⚠️ 请求超时 (尝试 {i+1}/{retries})")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ 请求异常: {str(e)[:50]} (尝试 {i+1}/{retries})")
            time.sleep(1)
    return None

# ============ 归一化热度 (v2) ============
PLATFORM_WEIGHTS = {
    'weibo': 1.2,
    'baidu': 1.0,
    'zhihu': 0.9,
    'bilibili': 0.7,
    'douyin': 0.8
}

COVERAGE_MULTIPLIER = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.5,
    5: 3.0
}

def normalize_heat(source, heat):
    if heat <= 0:
        return 0

    if source == 'weibo':
        base = heat
    elif source == 'baidu':
        base = heat / 50
    elif source == 'zhihu':
        base = heat / 500
    elif source == 'bilibili':
        base = heat
    elif source == 'douyin':
        base = heat / 10
    else:
        base = heat

    weight = PLATFORM_WEIGHTS.get(source, 1.0)
    normalized = base * weight

    return min(normalized, 100000)

# ============ 微博 (多API备用) ============
def fetch_weibo_hot():
    topics = []

    apis = [
        ('https://api.vvhan.com/api/hotlist?type=wbHot', 'vvhan'),
        ('https://www.coderutil.com/api/v1/weibo/hot', 'coderutil'),
        ('https://weibo.com/ajax/side/hotSearch', 'weibo_official'),
    ]

    for api_url, api_name in apis:
        try:
            print(f" [微博] 尝试 {api_name}...")
            headers_api = HEADERS.copy()
            if api_name == 'weibo_official':
                headers_api.update({
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://weibo.com/',
                    'X-Requested-With': 'XMLHttpRequest'
                })

            resp = safe_request(api_url, headers=headers_api, timeout=8, retries=1)
            if not resp:
                continue

            try:
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ JSON解析失败: {e}")
                continue

            items = []
            if api_name == 'vvhan':
                items = data.get('data', [])
            elif api_name == 'coderutil':
                items = data.get('data', []) if data.get('code') == 200 else []
            elif api_name == 'weibo_official':
                realtime = data.get('data', {}).get('realtime', [])
                for item in realtime:
                    items.append({
                        'title': item.get('word', ''),
                        'hot': item.get('raw_hot', 0) or item.get('num', 0),
                        'url': f"https://s.weibo.com/weibo?q={quote(item.get('word_scheme', item.get('word', '')))}"
                    })

            for idx, item in enumerate(items[:50]):
                title = item.get('title', '') or item.get('word', '')
                if not title or len(title) < 2:
                    continue

                heat = item.get('hot', 0) or item.get('hotnum', 0) or item.get('raw_hot', 0)
                if isinstance(heat, str):
                    match = re.search(r'(\d+(?:\.\d+)?)', heat)
                    if match:
                        heat = float(match.group(1))
                        if '万' in heat:
                            heat *= 10000
                    else:
                        heat = 0

                if heat == 0:
                    heat = max(500000 - idx * 10000, 10000)

                url_link = item.get('url', '')
                if not url_link:
                    url_link = f'https://s.weibo.com/weibo?q={quote(title)}'

                topics.append({
                    'title': title,
                    'heat': int(heat),
                    'url': url_link,
                    'source': 'weibo'
                })

            if topics:
                print(f"  ✅ {api_name} 成功: {len(topics)} 条")
                return topics

        except Exception as e:
            print(f"  ❌ {api_name} 失败: {e}")
            continue

    print("  ⚠️ 微博所有接口失败")
    return topics

# ============ 百度 ============
def fetch_baidu_hot():
    topics = []
    try:
        print(" [百度] 尝试API...")
        url = 'https://v2.xxapi.cn/api/baiduhot'
        resp = safe_request(url, timeout=8, retries=1)
        if resp:
            try:
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ JSON解析失败: {e}")
                return topics
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
                            if '万' in str(item.get('hot', '')) or 'w' in str(item.get('hot', '')).lower():
                                hot *= 10000
                            elif '亿' in str(item.get('hot', '')):
                                hot *= 100000000
                        else:
                            hot = 0
                    elif isinstance(hot, (int, float)):
                        hot = float(hot)
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
        print(" [知乎] 尝试API...")
        url = 'https://www.zhihu.com/api/v3/feed/topstory/hot-list-web?limit=20&desktop=true'
        resp = safe_request(url, timeout=8, retries=1)
        if resp:
            try:
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ JSON解析失败: {e}")
                return topics
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
        print(" [B站] 尝试API...")
        url = 'https://s.search.bilibili.com/main/hotword?limit=30'
        resp = safe_request(url, timeout=8, retries=1)
        if resp:
            try:
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ JSON解析失败: {e}")
                return topics
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
        print(" [抖音] 尝试API...")
        headers_dy = {**HEADERS, 'Referer': 'https://www.douyin.com/'}
        resp = safe_request('https://www.douyin.com/aweme/v1/web/hot/search/list/', headers=headers_dy, timeout=8, retries=1)
        if resp:
            try:
                data = resp.json()
            except Exception as e:
                print(f"  ⚠️ JSON解析失败: {e}")
                return topics
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

# ============ 合并数据 ============
def merge_topics(all_data):
    topic_map = {}

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

            topic_map[key]['heat'][source] = heat
            topic_map[key]['normalized_heat'][source] = normalize_heat(source, heat)

            source_url = item.get('url', '')
            existing = [s['name'] for s in topic_map[key]['sources']]
            source_display = {'weibo': '微博', 'baidu': '百度', 'zhihu': '知乎', 'bilibili': 'B站', 'douyin': '抖音'}.get(source, source)
            if source_display not in existing:
                topic_map[key]['sources'].append({
                    'name': source_display,
                    'url': source_url,
                    'heat': heat
                })

            if item.get('summary') and len(item['summary']) > len(topic_map[key]['summary']):
                topic_map[key]['summary'] = item['summary']

            cat = classify_topic(title, topic_map[key]['summary'])
            topic_map[key]['categories'].append(cat)

    topics = []
    for key, data in topic_map.items():
        source_count = len(data['sources'])
        normalized_total = sum(data['normalized_heat'].values())
        original_total = sum(data['heat'].values())

        coverage_bonus = COVERAGE_MULTIPLIER.get(source_count, 1.0)
        coverage_base = source_count * 50000

        composite_score = coverage_base + (normalized_total * coverage_bonus)

        categories = data['categories']
        category = max(set(categories), key=categories.count) if categories else 'social'

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
            'normalized_heat': data['normalized_heat'],
            'total_heat': original_total,
            'normalized_total': normalized_total,
            'source_count': source_count,
            'composite_score': composite_score,
            'trend': trend,
            'trendVal': trend_val,
            'sources': data['sources']
        })

    topics.sort(key=lambda x: x['composite_score'], reverse=True)

    for i, topic in enumerate(topics[:50]):
        topic['rank'] = i + 1

    return topics[:50]

# ============ 主函数 ============
def generate_data():
    utc_now = datetime.utcnow()
    beijing_now = utc_now + timedelta(hours=8)

    print(f"[{beijing_now}] 开始抓取热点数据...")

    all_data = {}
    print("[1/5] 抓取微博热搜...")
    all_data['weibo'] = fetch_weibo_hot()
    time.sleep(0.5)

    print("[2/5] 抓取百度热搜...")
    all_data['baidu'] = fetch_baidu_hot()
    time.sleep(0.5)

    print("[3/5] 抓取知乎热榜...")
    all_data['zhihu'] = fetch_zhihu_hot()
    time.sleep(0.5)

    print("[4/5] 抓取B站热搜...")
    all_data['bilibili'] = fetch_bilibili_hot()
    time.sleep(0.5)

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

    print("合并数据生成综合榜...")
    merged_topics = merge_topics(all_data)
    print(f"综合榜: {len(merged_topics)} 条热点")

    platform_counts = {'weibo': 0, 'baidu': 0, 'zhihu': 0, 'bilibili': 0, 'douyin': 0}
    for topic in merged_topics:
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

    platform_rankings = {}
    for source, topics in all_data.items():
        ranked = []
        for i, t in enumerate(topics):
            ranked.append({
                'rank': i + 1,
                'title': t['title'],
                'heat': t['heat'],
                'url': t.get('url', ''),
                'summary': t.get('summary', ''),
                'source': t['source'],
                'category': classify_topic(t['title'], t.get('summary', ''))
            })
        platform_rankings[source] = ranked

    output = {
        'updateTime': beijing_now.strftime('%Y-%m-%d %H:%M'),
        'topics': merged_topics,
        'platforms': platform_rankings
    }

    with open('data/hot_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[{beijing_now}] 数据已更新")
    print(f"更新时间: {output['updateTime']}")
    print(f"综合榜: {len(merged_topics)} 条")
    print("Top 5 综合热点:")
    for i, t in enumerate(merged_topics[:5]):
        sources_str = ', '.join([f"{s['name']}({s['heat']})" for s in t['sources']])
        print(f"  {i+1}. {t['title'][:40]}...")
        print(f"     覆盖: {t['source_count']}平台, 综合分: {t['composite_score']}")
        print(f"     来源: [{sources_str}]")

    return output

if __name__ == '__main__':
    generate_data()

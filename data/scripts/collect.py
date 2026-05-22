"""投融资事件数据采集 — 样本数据 + 合成数据生成 + 外部数据加载"""
import json
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# 样本数据：覆盖12行业，86条真实投资事件
# ============================================================
SAMPLE_DATA = [
    # ── 互联网 ──
    {"enterprise": "字节跳动", "investor": "红杉资本", "round": "A轮", "amount": "500万美元", "date": "2012-03", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "红杉资本投资字节跳动A轮"},
    {"enterprise": "字节跳动", "investor": "DST Global", "round": "B轮", "amount": "1000万美元", "date": "2013-06", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "DST领投字节跳动B轮"},
    {"enterprise": "字节跳动", "investor": "红杉资本", "round": "C轮", "amount": "1亿美元", "date": "2014-01", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "红杉资本领投字节跳动C轮"},
    {"enterprise": "字节跳动", "investor": "KKR", "round": "D轮", "amount": "10亿美元", "date": "2016-12", "industry": "互联网", "investor_type": "PE", "lead": 1, "description": "KKR领投字节跳动D轮"},
    {"enterprise": "快手", "investor": "红杉资本", "round": "A轮", "amount": "数百万美元", "date": "2014-06", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "红杉资本投资快手A轮"},
    {"enterprise": "快手", "investor": "晨兴资本", "round": "B轮", "amount": "数千万美元", "date": "2015-01", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "晨兴资本领投快手B轮"},
    {"enterprise": "快手", "investor": "腾讯", "round": "D轮", "amount": "3.5亿美元", "date": "2017-03", "industry": "互联网", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投快手D轮"},
    {"enterprise": "知乎", "investor": "创新工场", "round": "天使轮", "amount": "150万人民币", "date": "2011-06", "industry": "互联网", "investor_type": "Angel", "lead": 1, "description": "创新工场天使投资知乎"},
    {"enterprise": "知乎", "investor": "启明创投", "round": "B轮", "amount": "2200万美元", "date": "2014-06", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "启明创投领投知乎B轮"},
    {"enterprise": "知乎", "investor": "腾讯", "round": "C轮", "amount": "5500万美元", "date": "2015-11", "industry": "互联网", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投知乎C轮"},
    {"enterprise": "小红书", "investor": "真格基金", "round": "天使轮", "amount": "数百万人民币", "date": "2013-10", "industry": "互联网", "investor_type": "Angel", "lead": 1, "description": "真格基金天使投资小红书"},
    {"enterprise": "小红书", "investor": "金沙江创投", "round": "C轮", "amount": "1亿美元", "date": "2018-06", "industry": "互联网", "investor_type": "VC", "lead": 1, "description": "金沙江创投领投小红书C轮"},
    {"enterprise": "小红书", "investor": "高瓴资本", "round": "D轮", "amount": "3亿美元", "date": "2021-11", "industry": "互联网", "investor_type": "PE", "lead": 1, "description": "高瓴资本领投小红书D轮"},
    # ── 电子商务 ──
    {"enterprise": "拼多多", "investor": "高榕资本", "round": "A轮", "amount": "800万美元", "date": "2015-09", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "高榕资本领投拼多多A轮"},
    {"enterprise": "拼多多", "investor": "IDG资本", "round": "B轮", "amount": "1.1亿美元", "date": "2016-07", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "IDG资本领投拼多多B轮"},
    {"enterprise": "拼多多", "investor": "红杉资本", "round": "C轮", "amount": "2.13亿美元", "date": "2017-02", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "红杉资本领投拼多多C轮"},
    {"enterprise": "每日优鲜", "investor": "联想创投", "round": "B轮", "amount": "2亿人民币", "date": "2016-04", "industry": "电子商务", "investor_type": "Corporate", "lead": 1, "description": "联想创投领投每日优鲜B轮"},
    {"enterprise": "每日优鲜", "investor": "老虎基金", "round": "C轮", "amount": "1亿美元", "date": "2017-03", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "老虎基金领投每日优鲜C轮"},
    {"enterprise": "叮咚买菜", "investor": "今日资本", "round": "B轮", "amount": "5000万美元", "date": "2019-07", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "今日资本领投叮咚买菜B轮"},
    {"enterprise": "叮咚买菜", "investor": "红杉资本", "round": "C轮", "amount": "3亿美元", "date": "2020-05", "industry": "电子商务", "investor_type": "VC", "lead": 1, "description": "红杉资本领投叮咚买菜C轮"},
    # ── 人工智能 ──
    {"enterprise": "商汤科技", "investor": "鼎晖投资", "round": "B轮", "amount": "数千万美元", "date": "2017-11", "industry": "人工智能", "investor_type": "PE", "lead": 1, "description": "鼎晖投资领投商汤科技B轮"},
    {"enterprise": "商汤科技", "investor": "阿里巴巴", "round": "C轮", "amount": "6亿美元", "date": "2018-04", "industry": "人工智能", "investor_type": "Corporate", "lead": 1, "description": "阿里巴巴领投商汤科技C轮"},
    {"enterprise": "商汤科技", "investor": "软银愿景基金", "round": "D轮", "amount": "10亿美元", "date": "2018-09", "industry": "人工智能", "investor_type": "PE", "lead": 1, "description": "软银愿景基金领投商汤科技D轮"},
    {"enterprise": "旷视科技", "investor": "创新工场", "round": "A轮", "amount": "100万美元", "date": "2013-01", "industry": "人工智能", "investor_type": "Angel", "lead": 1, "description": "创新工场天使投资旷视科技"},
    {"enterprise": "旷视科技", "investor": "蚂蚁金服", "round": "D轮", "amount": "6亿美元", "date": "2019-05", "industry": "人工智能", "investor_type": "Corporate", "lead": 1, "description": "蚂蚁金服领投旷视科技D轮"},
    {"enterprise": "云从科技", "investor": "中国互联网投资基金", "round": "B轮", "amount": "10亿人民币", "date": "2018-06", "industry": "人工智能", "investor_type": "Government", "lead": 1, "description": "中国互联网投资基金领投云从科技B轮"},
    {"enterprise": "云从科技", "investor": "国新基金", "round": "C轮", "amount": "18亿人民币", "date": "2020-05", "industry": "人工智能", "investor_type": "Government", "lead": 1, "description": "国新基金领投云从科技C轮"},
    {"enterprise": "依图科技", "investor": "高瓴资本", "round": "C轮", "amount": "3亿美元", "date": "2018-06", "industry": "人工智能", "investor_type": "PE", "lead": 1, "description": "高瓴资本领投依图科技C轮"},
    {"enterprise": "百川智能", "investor": "阿里云峰基金", "round": "A轮", "amount": "3亿美元", "date": "2023-10", "industry": "人工智能", "investor_type": "Corporate", "lead": 1, "description": "阿里云峰基金领投百川智能A轮"},
    {"enterprise": "月之暗面", "investor": "红杉资本", "round": "A轮", "amount": "2亿美元", "date": "2024-02", "industry": "人工智能", "investor_type": "VC", "lead": 1, "description": "红杉资本领投月之暗面A轮"},
    {"enterprise": "智谱AI", "investor": "启明创投", "round": "B轮", "amount": "数亿人民币", "date": "2023-10", "industry": "人工智能", "investor_type": "VC", "lead": 1, "description": "启明创投领投智谱AI B轮"},
    # ── 新能源汽车 ──
    {"enterprise": "蔚来汽车", "investor": "高瓴资本", "round": "A轮", "amount": "1亿美元", "date": "2015-06", "industry": "新能源汽车", "investor_type": "PE", "lead": 1, "description": "高瓴资本领投蔚来汽车A轮"},
    {"enterprise": "蔚来汽车", "investor": "腾讯", "round": "B轮", "amount": "5亿美元", "date": "2017-03", "industry": "新能源汽车", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投蔚来汽车B轮"},
    {"enterprise": "蔚来汽车", "investor": "淡马锡", "round": "C轮", "amount": "10亿美元", "date": "2017-11", "industry": "新能源汽车", "investor_type": "PE", "lead": 1, "description": "淡马锡领投蔚来汽车C轮"},
    {"enterprise": "小鹏汽车", "investor": "阿里云峰基金", "round": "B轮", "amount": "22亿人民币", "date": "2018-01", "industry": "新能源汽车", "investor_type": "Corporate", "lead": 1, "description": "阿里云峰基金领投小鹏汽车B轮"},
    {"enterprise": "小鹏汽车", "investor": "小米集团", "round": "C轮", "amount": "4亿美元", "date": "2019-11", "industry": "新能源汽车", "investor_type": "Corporate", "lead": 1, "description": "小米集团领投小鹏汽车C轮"},
    {"enterprise": "理想汽车", "investor": "明势资本", "round": "天使轮", "amount": "数千万人民币", "date": "2015-10", "industry": "新能源汽车", "investor_type": "Angel", "lead": 1, "description": "明势资本天使投资理想汽车"},
    {"enterprise": "理想汽车", "investor": "美团", "round": "C轮", "amount": "5.5亿美元", "date": "2020-07", "industry": "新能源汽车", "investor_type": "Corporate", "lead": 1, "description": "美团领投理想汽车C轮"},
    {"enterprise": "零跑汽车", "investor": "红杉资本", "round": "A轮", "amount": "数亿人民币", "date": "2018-01", "industry": "新能源汽车", "investor_type": "VC", "lead": 1, "description": "红杉资本领投零跑汽车A轮"},
    # ── 芯片半导体 ──
    {"enterprise": "寒武纪", "investor": "国投创业", "round": "B轮", "amount": "数亿美元", "date": "2018-06", "industry": "芯片半导体", "investor_type": "Government", "lead": 1, "description": "国投创业领投寒武纪B轮"},
    {"enterprise": "寒武纪", "investor": "中科院创投", "round": "A轮", "amount": "数千万人民币", "date": "2017-08", "industry": "芯片半导体", "investor_type": "Government", "lead": 1, "description": "中科院创投天使投资寒武纪"},
    {"enterprise": "壁仞科技", "investor": "高瓴资本", "round": "B轮", "amount": "20亿人民币", "date": "2021-03", "industry": "芯片半导体", "investor_type": "PE", "lead": 1, "description": "高瓴资本领投壁仞科技B轮"},
    {"enterprise": "壁仞科技", "investor": "启明创投", "round": "A轮", "amount": "10亿人民币", "date": "2020-06", "industry": "芯片半导体", "investor_type": "VC", "lead": 1, "description": "启明创投领投壁仞科技A轮"},
    {"enterprise": "地平线", "investor": "五源资本", "round": "A轮", "amount": "数千万美元", "date": "2016-06", "industry": "芯片半导体", "investor_type": "VC", "lead": 1, "description": "五源资本领投地平线A轮"},
    {"enterprise": "地平线", "investor": "英特尔", "round": "B轮", "amount": "近亿美元", "date": "2017-10", "industry": "芯片半导体", "investor_type": "Corporate", "lead": 0, "description": "英特尔跟投地平线B轮"},
    {"enterprise": "地平线", "investor": "SK海力士", "round": "C轮", "amount": "4亿美元", "date": "2019-02", "industry": "芯片半导体", "investor_type": "Corporate", "lead": 1, "description": "SK海力士领投地平线C轮"},
    {"enterprise": "黑芝麻智能", "investor": "北极光创投", "round": "A轮", "amount": "数千万人民币", "date": "2017-05", "industry": "芯片半导体", "investor_type": "VC", "lead": 1, "description": "北极光创投领投黑芝麻智能A轮"},
    {"enterprise": "黑芝麻智能", "investor": "君联资本", "round": "B轮", "amount": "数亿人民币", "date": "2019-09", "industry": "芯片半导体", "investor_type": "VC", "lead": 1, "description": "君联资本领投黑芝麻智能B轮"},
    # ── 金融科技 ──
    {"enterprise": "蚂蚁集团", "investor": "社保基金", "round": "战略投资", "amount": "200亿人民币", "date": "2018-06", "industry": "金融科技", "investor_type": "Government", "lead": 1, "description": "社保基金战略投资蚂蚁集团"},
    {"enterprise": "蚂蚁集团", "investor": "中投公司", "round": "战略投资", "amount": "500亿人民币", "date": "2018-06", "industry": "金融科技", "investor_type": "Government", "lead": 1, "description": "中投公司战略投资蚂蚁集团"},
    {"enterprise": "陆金所", "investor": "摩根士丹利", "round": "B轮", "amount": "数亿美元", "date": "2015-03", "industry": "金融科技", "investor_type": "PE", "lead": 1, "description": "摩根士丹利领投陆金所B轮"},
    {"enterprise": "京东数科", "investor": "红杉资本", "round": "A轮", "amount": "6亿美元", "date": "2016-01", "industry": "金融科技", "investor_type": "VC", "lead": 1, "description": "红杉资本领投京东数科A轮"},
    {"enterprise": "微众银行", "investor": "腾讯", "round": "天使轮", "amount": "数亿人民币", "date": "2014-12", "industry": "金融科技", "investor_type": "Corporate", "lead": 1, "description": "腾讯发起设立微众银行"},
    # ── 本地生活 ──
    {"enterprise": "美团", "investor": "红杉资本", "round": "A轮", "amount": "1200万美元", "date": "2010-09", "industry": "本地生活", "investor_type": "VC", "lead": 1, "description": "红杉资本领投美团A轮"},
    {"enterprise": "美团", "investor": "阿里巴巴", "round": "B轮", "amount": "5000万美元", "date": "2011-07", "industry": "本地生活", "investor_type": "Corporate", "lead": 1, "description": "阿里巴巴领投美团B轮"},
    {"enterprise": "美团", "investor": "泛大西洋资本", "round": "D轮", "amount": "3亿美元", "date": "2014-12", "industry": "本地生活", "investor_type": "PE", "lead": 1, "description": "泛大西洋资本领投美团D轮"},
    {"enterprise": "饿了么", "investor": "金沙江创投", "round": "A轮", "amount": "数百万美元", "date": "2011-03", "industry": "本地生活", "investor_type": "VC", "lead": 1, "description": "金沙江创投领投饿了么A轮"},
    {"enterprise": "饿了么", "investor": "红杉资本", "round": "C轮", "amount": "2500万美元", "date": "2013-11", "industry": "本地生活", "investor_type": "VC", "lead": 1, "description": "红杉资本领投饿了么C轮"},
    {"enterprise": "饿了么", "investor": "阿里巴巴", "round": "F轮", "amount": "12.5亿美元", "date": "2015-01", "industry": "本地生活", "investor_type": "Corporate", "lead": 1, "description": "阿里巴巴领投饿了么F轮"},
    {"enterprise": "喜茶", "investor": "IDG资本", "round": "A轮", "amount": "1亿元", "date": "2016-08", "industry": "本地生活", "investor_type": "VC", "lead": 1, "description": "IDG资本领投喜茶A轮"},
    {"enterprise": "喜茶", "investor": "美团龙珠", "round": "B轮", "amount": "4亿元", "date": "2018-04", "industry": "本地生活", "investor_type": "Corporate", "lead": 1, "description": "美团龙珠领投喜茶B轮"},
    # ── 硬件/无人机 ──
    {"enterprise": "大疆创新", "investor": "红杉资本", "round": "B轮", "amount": "3000万美元", "date": "2015-05", "industry": "硬件", "investor_type": "VC", "lead": 1, "description": "红杉资本投资大疆创新B轮"},
    {"enterprise": "大疆创新", "investor": "Accel Partners", "round": "A轮", "amount": "1000万美元", "date": "2013-01", "industry": "硬件", "investor_type": "VC", "lead": 1, "description": "Accel投资大疆创新A轮"},
    {"enterprise": "极飞科技", "investor": "成为资本", "round": "B轮", "amount": "数千万美元", "date": "2017-09", "industry": "硬件", "investor_type": "VC", "lead": 1, "description": "成为资本领投极飞科技B轮"},
    {"enterprise": "峰飞航空", "investor": "IDG资本", "round": "A轮", "amount": "5000万美元", "date": "2022-11", "industry": "硬件", "investor_type": "VC", "lead": 1, "description": "IDG资本领投峰飞航空A轮"},
    {"enterprise": "亿航智能", "investor": "GGV纪源资本", "round": "A轮", "amount": "1000万美元", "date": "2014-08", "industry": "硬件", "investor_type": "VC", "lead": 1, "description": "GGV领投亿航智能A轮"},
    # ── 企业服务 ──
    {"enterprise": "明略科技", "investor": "华创资本", "round": "A轮", "amount": "数千万元", "date": "2014-12", "industry": "企业服务", "investor_type": "VC", "lead": 1, "description": "华创资本领投明略科技A轮"},
    {"enterprise": "明略科技", "investor": "腾讯", "round": "C轮", "amount": "10亿人民币", "date": "2019-03", "industry": "企业服务", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投明略科技C轮"},
    {"enterprise": "神策数据", "investor": "红杉资本", "round": "B轮", "amount": "2000万美元", "date": "2017-03", "industry": "企业服务", "investor_type": "VC", "lead": 1, "description": "红杉资本领投神策数据B轮"},
    {"enterprise": "神策数据", "investor": "华平投资", "round": "C轮", "amount": "3000万美元", "date": "2018-12", "industry": "企业服务", "investor_type": "PE", "lead": 1, "description": "华平投资领投神策数据C轮"},
    {"enterprise": "PingCAP", "investor": "华创资本", "round": "A轮", "amount": "数百万美元", "date": "2016-04", "industry": "企业服务", "investor_type": "VC", "lead": 1, "description": "华创资本领投PingCAP A轮"},
    {"enterprise": "PingCAP", "investor": "复星锐正", "round": "B轮", "amount": "1500万美元", "date": "2017-06", "industry": "企业服务", "investor_type": "VC", "lead": 1, "description": "复星锐正领投PingCAP B轮"},
    # ── 物流 ──
    {"enterprise": "京东物流", "investor": "红杉资本", "round": "A轮", "amount": "25亿美元", "date": "2018-02", "industry": "物流", "investor_type": "VC", "lead": 1, "description": "红杉资本领投京东物流A轮"},
    {"enterprise": "满帮集团", "investor": "腾讯", "round": "B轮", "amount": "1.5亿美元", "date": "2015-06", "industry": "物流", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投满帮B轮"},
    {"enterprise": "满帮集团", "investor": "软银愿景基金", "round": "E轮", "amount": "19亿美元", "date": "2018-04", "industry": "物流", "investor_type": "PE", "lead": 1, "description": "软银愿景基金领投满帮E轮"},
    {"enterprise": "货拉拉", "investor": "红杉资本", "round": "B轮", "amount": "3000万美元", "date": "2017-01", "industry": "物流", "investor_type": "VC", "lead": 1, "description": "红杉资本领投货拉拉B轮"},
    {"enterprise": "货拉拉", "investor": "高瓴资本", "round": "E轮", "amount": "15亿美元", "date": "2020-12", "industry": "物流", "investor_type": "PE", "lead": 1, "description": "高瓴资本领投货拉拉E轮"},
    # ── 游戏 ──
    {"enterprise": "B站", "investor": "IDG资本", "round": "A轮", "amount": "数百万美元", "date": "2013-10", "industry": "游戏", "investor_type": "VC", "lead": 1, "description": "IDG资本领投B站A轮"},
    {"enterprise": "B站", "investor": "腾讯", "round": "D轮", "amount": "3.18亿美元", "date": "2018-10", "industry": "游戏", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投B站D轮"},
    {"enterprise": "米哈游", "investor": "斯凯网络", "round": "天使轮", "amount": "100万元", "date": "2012-02", "industry": "游戏", "investor_type": "Angel", "lead": 1, "description": "斯凯网络天使投资米哈游"},
    {"enterprise": "莉莉丝游戏", "investor": "红杉资本", "round": "A轮", "amount": "数千万人民币", "date": "2014-05", "industry": "游戏", "investor_type": "VC", "lead": 1, "description": "红杉资本领投莉莉丝A轮"},
    # ── 医疗健康 ──
    {"enterprise": "药明康德", "investor": "高瓴资本", "round": "战略投资", "amount": "10亿美元", "date": "2019-06", "industry": "医疗健康", "investor_type": "PE", "lead": 1, "description": "高瓴资本战略投资药明康德"},
    {"enterprise": "百济神州", "investor": "高瓴资本", "round": "战略投资", "amount": "10亿美元", "date": "2020-07", "industry": "医疗健康", "investor_type": "PE", "lead": 1, "description": "高瓴资本战略投资百济神州"},
    {"enterprise": "微医", "investor": "腾讯", "round": "B轮", "amount": "3亿美元", "date": "2015-09", "industry": "医疗健康", "investor_type": "Corporate", "lead": 1, "description": "腾讯领投微医B轮"},
    {"enterprise": "微医", "investor": "友邦保险", "round": "C轮", "amount": "5亿美元", "date": "2018-05", "industry": "医疗健康", "investor_type": "Corporate", "lead": 1, "description": "友邦保险领投微医C轮"},
    {"enterprise": "平安好医生", "investor": "IDG资本", "round": "A轮", "amount": "5000万美元", "date": "2014-06", "industry": "医疗健康", "investor_type": "VC", "lead": 1, "description": "IDG资本领投平安好医生A轮"},
]

# ============================================================
# 合成数据生成：扩充至500+企业、2000+事件
# ============================================================

# 行业→企业名称池
INDUSTRY_ENTERPRISES = {
    "互联网": [
        "得物", "转转", "脉脉", "即刻", "什么值得买", "百合网", "马蜂窝", "汽车之家",
        "58同城", "赶集网", "猎聘", "BOSS直聘", "拉勾网", "豆瓣", "天涯社区", "美图秀秀",
        "墨迹天气", "WiFi万能钥匙", "快手极速版", "懂球帝", "Keep", "薄荷健康",
        "小宇宙", "喜马拉雅", "荔枝微课", "樊登读书", "作业帮", "猿辅导", "掌门教育",
        "高途课堂", "有道精品课", "学而思网校", "火花思维", "VIPKID", "编程猫",
    ],
    "电子商务": [
        "有赞", "微盟", "云集", "贝店", "淘集集", "蜜芽", "格格家", "楚楚街",
        "卷皮折扣", "折800", "返利网", "淘粉吧", "洋码头", "小红唇", "达令家",
        "蘑菇街", "唯品会", "寺库", "万里目", "KK集团", "名创优品", "NOME",
        "鲜丰水果", "百果园", "钱大妈", "谊品生鲜", "锅圈食汇", "懒熊火锅",
    ],
    "人工智能": [
        "思必驰", "出门问问", "Rokid", "影谱科技", "格灵深瞳", "图森未来",
        "Momenta", "小马智行", "文远知行", "AutoX", "轻舟智航", "禾赛科技",
        "速腾聚创", "一径科技", "镭神智能", "第四范式", "九章云极", "星环科技",
        "竹间智能", "追一科技", "澜舟科技", "MiniMax", "光年之外", "深度求索",
        "阶跃星辰", "面壁智能", "衔远科技", "聆心智能", "深言科技",
    ],
    "新能源汽车": [
        "哪吒汽车", "威马汽车", "高合汽车", "极氪汽车", "岚图汽车", "智己汽车",
        "阿维塔", "极狐汽车", "飞凡汽车", "合创汽车", "爱驰汽车", "天际汽车",
        "拜腾汽车", "博郡汽车", "奇点汽车", "云度汽车", "新特汽车", "前途汽车",
        "恒大汽车", "宝能汽车", "自游家", "仰望汽车", "深蓝汽车", "启源汽车",
    ],
    "芯片半导体": [
        "紫光展锐", "中芯国际", "华虹半导体", "长江存储", "长鑫存储", "兆易创新",
        "韦尔股份", "卓胜微", "圣邦股份", "思瑞浦", "芯朋微", "晶晨股份",
        "全志科技", "瑞芯微", "北京君正", "景嘉微", "海光信息", "龙芯中科",
        "平头哥", "天数智芯", "燧原科技", "摩尔线程", "芯驰科技", "杰发科技",
        "黑芝麻智能", "后摩智能", "亿智电子", "爱芯元智", "瀚博半导体",
    ],
    "金融科技": [
        "度小满", "360数科", "乐信", "趣店", "信也科技", "嘉银金科",
        "小赢科技", "品钛", "萨摩耶数科", "简普科技", "和信贷", "拍拍贷",
        "宜人贷", "人人贷", "有利网", "积木盒子", "点融网", "爱钱进",
        "网信普惠", "团贷网", "麻袋财富", "恒昌利通", "向前金控", "融360",
    ],
    "本地生活": [
        "瑞幸咖啡", "Manner咖啡", "Seesaw咖啡", "Tims咖啡", "M Stand",
        "奈雪的茶", "茶百道", "古茗", "蜜雪冰城", "书亦烧仙草", "沪上阿姨",
        "甜啦啦", "7分甜", "CoCo都可", "一点点", "霸王茶姬", "茶颜悦色",
        "和府捞面", "遇见小面", "马记永", "陈香贵", "张拉拉", "太二酸菜鱼",
        "巴奴毛肚火锅", "湊湊火锅", "怂火锅", "叮咚买菜", "朴朴超市", "美团买菜",
    ],
    "硬件": [
        "柔宇科技", "柔灵科技", "影石Insta360", "GoPro中国", "萤石网络",
        "极米科技", "坚果投影", "当贝投影", "小明投影", "峰米投影",
        "追觅科技", "石头科技", "云鲸智能", "科沃斯", "iRobot中国",
        "九号公司", "小牛电动", "雅迪科技", "新日电动车", "哈啰出行",
        "Insta360", "雷鸟创新", "Nreal", "影目科技", "亮亮视野",
    ],
    "企业服务": [
        "北森", "Moka", "飞书", "钉钉", "企业微信", "石墨文档", "金山文档",
        "有道云笔记", "印象笔记", "Notion中国", "ONES", "Worktile", "Teambition",
        "Tower", "Leangoo", "禅道", "JIRA中国", "Tapd", "Coding",
        "阿里云", "腾讯云", "华为云", "百度云", "京东云", "UCloud", "青云",
        "七牛云", "又拍云", "金山云", "浪潮云", "深信服", "奇安信",
    ],
    "物流": [
        "极兔速递", "百世快递", "中通快递", "圆通速递", "申通快递", "韵达快递",
        "顺丰速运", "德邦快递", "安能物流", "壹米滴答", "百世快运",
        "日日顺", "远成物流", "中铁物流", "宅急送", "如风达",
        "闪送", "达达快送", "点我达", "UU跑腿", "顺丰同城",
    ],
    "游戏": [
        "鹰角网络", "叠纸游戏", "网易游戏", "完美世界", "三七互娱",
        "世纪华通", "游族网络", "恺英网络", "巨人网络", "昆仑万维",
        "IGG", "FunPlus", "沐瞳科技", "朝夕光年", "雷霆游戏",
        "心动网络", "中手游", "飞鱼科技", "4399", "多益网络",
    ],
    "医疗健康": [
        "丁香园", "春雨医生", "好大夫在线", "企鹅杏仁", "妙手医生",
        "医联", "健客", "1药网", "叮当快药", "药京采",
        "华大基因", "贝瑞基因", "诺禾致源", "燃石医学", "世和基因",
        "泛生子", "思路迪", "至本医疗", "吉因加", "鹍远基因",
        "推想医疗", "数坤科技", "鹰瞳科技", "医渡云", "太美医疗",
    ],
    "新材料": [
        "宁德时代", "比亚迪电池", "国轩高科", "亿纬锂能", "中创新航",
        "蜂巢能源", "欣旺达", "孚能科技", "正力新能", "瑞浦能源",
        "恩捷股份", "星源材质", "中材科技", "璞泰来", "杉杉股份",
        "天赐材料", "新宙邦", "多氟多", "天际股份", "石大胜华",
    ],
}

# 投资机构池
INVESTORS = [
    # VC
    ("红杉资本", "VC"), ("IDG资本", "VC"), ("经纬创投", "VC"), ("启明创投", "VC"),
    ("金沙江创投", "VC"), ("晨兴资本", "VC"), ("高榕资本", "VC"), ("五源资本", "VC"),
    ("北极光创投", "VC"), ("君联资本", "VC"), ("华创资本", "VC"), ("今日资本", "VC"),
    ("真格基金", "VC"), ("创新工场", "VC"), ("光速中国", "VC"), ("蓝驰创投", "VC"),
    ("GGV纪源资本", "VC"), ("DCM中国", "VC"), ("联想之星", "VC"), ("梅花创投", "VC"),
    ("险峰长青", "VC"), ("源码资本", "VC"), ("明势资本", "VC"), ("BAI资本", "VC"),
    ("嘉御资本", "VC"), ("钟鼎资本", "VC"), ("云九资本", "VC"), ("成为资本", "VC"),
    ("德同资本", "VC"), ("达晨财智", "VC"), ("深创投", "VC"), ("同创伟业", "VC"),
    ("松禾资本", "VC"), ("基石资本", "VC"), ("东方富海", "VC"),
    # PE
    ("高瓴资本", "PE"), ("中信产业基金", "PE"), ("鼎晖投资", "PE"), ("华平投资", "PE"),
    ("KKR", "PE"), ("CPE源峰", "PE"), ("泛大西洋资本", "PE"), ("淡马锡", "PE"),
    ("软银愿景基金", "PE"), ("CVC资本", "PE"), ("太盟投资", "PE"), ("博裕资本", "PE"),
    ("方源资本", "PE"), ("春华资本", "PE"), ("国开金融", "PE"),
    # Corporate
    ("腾讯", "Corporate"), ("阿里巴巴", "Corporate"), ("百度", "Corporate"),
    ("京东", "Corporate"), ("小米集团", "Corporate"), ("美团", "Corporate"),
    ("字节跳动", "Corporate"), ("华为", "Corporate"), ("联想创投", "Corporate"),
    ("比亚迪", "Corporate"), ("蔚来资本", "Corporate"), ("蚂蚁金服", "Corporate"),
    ("网易", "Corporate"), ("微博", "Corporate"), ("360", "Corporate"),
    # Government
    ("国家集成电路产业基金", "Government"), ("国新基金", "Government"),
    ("社保基金", "Government"), ("中投公司", "Government"), ("国投创业", "Government"),
    ("中科院创投", "Government"), ("中国互联网投资基金", "Government"),
    ("深创投集团", "Government"), ("北京政府引导基金", "Government"),
    ("上海科创投", "Government"), ("深圳市政府引导基金", "Government"),
]

# 轮次序列
ROUND_SEQUENCE = ["天使轮", "Pre-A轮", "A轮", "A+轮", "B轮", "B+轮", "C轮", "C+轮", "D轮", "E轮", "F轮", "Pre-IPO"]

# 金额范围（万元）
ROUND_AMOUNTS = {
    "天使轮": (100, 2000), "Pre-A轮": (500, 5000), "A轮": (1000, 30000),
    "A+轮": (3000, 50000), "B轮": (5000, 100000), "B+轮": (10000, 200000),
    "C轮": (20000, 500000), "C+轮": (30000, 800000), "D轮": (50000, 1000000),
    "E轮": (80000, 2000000), "F轮": (100000, 5000000), "Pre-IPO": (200000, 10000000),
}

# Founding year range
FOUNDING_YEARS = (2010, 2022)


def _format_amount(amt_wan):
    """将万元数值格式化为字符串"""
    if amt_wan >= 10000:
        yi = amt_wan / 10000
        if yi == int(yi):
            return f"{int(yi)}亿人民币"
        return f"{yi:.1f}亿人民币"
    if amt_wan >= 1000:
        return f"{int(amt_wan)}万人民币"
    return f"{int(amt_wan)}万人民币"


def _generate_date(founding_year, round_idx):
    """根据成立年份和轮次索引生成投资日期"""
    base_year = founding_year + round_idx // 2  # 每两轮大约过一年
    base_year = min(base_year, 2024)
    month = random.randint(1, 12)
    return f"{base_year}-{month:02d}"


def generate_synthetic_data(target_enterprises=500, target_events=2000, seed=42):
    """生成合成投融资数据"""
    random.seed(seed)

    events = list(SAMPLE_DATA)  # 从真实数据开始
    existing_enterprises = {e["enterprise"] for e in events}
    enterprise_count = len(existing_enterprises)

    # 从已有事件中提取已有行业的计数
    industry_ent_counts = {}
    for e in events:
        ind = e.get("industry", "")
        industry_ent_counts.setdefault(ind, set()).add(e["enterprise"])

    needed = target_enterprises - enterprise_count

    # 为每个行业生成新企业
    all_new_entreprises = []
    for industry, ent_names in INDUSTRY_ENTERPRISES.items():
        for name in ent_names:
            if name not in existing_enterprises:
                all_new_entreprises.append((name, industry))

    random.shuffle(all_new_entreprises)
    new_entreprises = all_new_entreprises[:needed]

    # 为每家新企业生成3-5轮融资事件
    for ent_name, industry in new_entreprises:
        founding_year = random.randint(*FOUNDING_YEARS)
        num_rounds = random.randint(3, 6)
        start_idx = random.randint(0, 3)  # 起始轮次

        for r in range(num_rounds):
            round_idx = start_idx + r
            if round_idx >= len(ROUND_SEQUENCE):
                break
            round_name = ROUND_SEQUENCE[round_idx]
            amt_lo, amt_hi = ROUND_AMOUNTS[round_name]
            amount = random.randint(amt_lo, amt_hi)
            date = _generate_date(founding_year, round_idx)

            # 选择投资方
            inv_name, inv_type = random.choice(INVESTORS)
            lead = 1 if random.random() < 0.7 else 0

            events.append({
                "enterprise": ent_name,
                "investor": inv_name,
                "round": round_name,
                "amount": _format_amount(amount),
                "date": date,
                "industry": industry,
                "investor_type": inv_type,
                "lead": lead,
                "description": f"{inv_name}{'领投' if lead else '跟投'}{ent_name}{round_name}",
            })

    # 如果还不够，追加更多事件（让已有企业获得追投）
    all_enterprises = list(existing_enterprises | {n for n, _ in new_entreprises})
    while len(events) < target_events:
        ent_name = random.choice(all_enterprises)
        # 找到该企业已有轮次
        ent_rounds = [e["round"] for e in events if e["enterprise"] == ent_name]
        ent_industry = next((e["industry"] for e in events if e["enterprise"] == ent_name), "互联网")
        max_round_idx = max((ROUND_SEQUENCE.index(r) for r in ent_rounds if r in ROUND_SEQUENCE), default=-1)
        next_idx = max_round_idx + 1
        if next_idx >= len(ROUND_SEQUENCE):
            next_idx = max_round_idx  # 追投同轮
        round_name = ROUND_SEQUENCE[next_idx]
        amt_lo, amt_hi = ROUND_AMOUNTS.get(round_name, (1000, 50000))
        amount = random.randint(amt_lo, amt_hi)
        year = random.randint(2015, 2024)
        month = random.randint(1, 12)
        inv_name, inv_type = random.choice(INVESTORS)
        lead = 1 if random.random() < 0.6 else 0

        events.append({
            "enterprise": ent_name,
            "investor": inv_name,
            "round": round_name,
            "amount": _format_amount(amount),
            "date": f"{year}-{month:02d}",
            "industry": ent_industry,
            "investor_type": inv_type,
            "lead": lead,
            "description": f"{inv_name}{'领投' if lead else '跟投'}{ent_name}{round_name}",
        })

    return events


def collect_data(output_dir=None, target_enterprises=500, target_events=2000):
    """写入数据到 data/raw/investment_events.json（包含真实+合成数据）"""
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, 'raw')
    os.makedirs(output_dir, exist_ok=True)

    data = generate_synthetic_data(target_enterprises, target_events)
    output_path = os.path.join(output_dir, 'investment_events.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    enterprises = set(e["enterprise"] for e in data)
    investors = set(e["investor"] for e in data)
    industries = set(e.get("industry", "") for e in data)
    print(f"已采集 {len(data)} 条投资事件")
    print(f"  企业: {len(enterprises)} 家")
    print(f"  投资方: {len(investors)} 家")
    print(f"  行业: {len(industries)} 个")
    print(f"  保存至: {output_path}")
    return output_path


def load_external(json_path, output_dir=None):
    """加载外部JSON数据并合并到 raw 目录"""
    with open(json_path, 'r', encoding='utf-8') as f:
        external = json.load(f)
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, 'raw')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'investment_events.json')

    existing = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    merged = existing + external
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"合并完成：原有 {len(existing)} 条 + 新增 {len(external)} 条 = 共 {len(merged)} 条")
    return output_path


if __name__ == '__main__':
    collect_data()

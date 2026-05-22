"""投融资时序知识图谱 — 三级本体定义

Industry (行业)
  └── Enterprise (企业) — BELONGS_TO
       └── Investor (投资机构) — INVEST/LEAD/FOLLOW
"""

# ========== 实体类型 ==========
ENTITY_TYPES = {
    "Enterprise": {
        "label_cn": "企业",
        "attributes": ["name", "founding_date", "industry", "valuation", "status", "description"],
        "required": ["name"],
    },
    "Investor": {
        "label_cn": "投资机构",
        "attributes": ["name", "type", "aum", "focus_industry", "description"],
        "required": ["name"],
    },
    "Round": {
        "label_cn": "融资轮次",
        "attributes": ["name", "sequence"],
        "required": ["name"],
    },
    "Industry": {
        "label_cn": "行业分类",
        "attributes": ["name", "policy_date", "hotness_score"],
        "required": ["name"],
    },
}

# 投资机构子类型
INVESTOR_SUBTYPES = {
    "VC": "风险投资",
    "PE": "私募股权",
    "Angel": "天使投资",
    "Government": "政府引导基金",
    "Corporate": "企业战投",
}

# 融资轮次（按递进顺序）
ROUND_ORDER = [
    "种子轮", "天使轮", "Pre-A轮", "A轮", "A+轮",
    "Pre-B轮", "B轮", "B+轮", "C轮", "C+轮",
    "D轮", "E轮", "F轮", "G轮",
    "Pre-IPO", "IPO",
]

# 融资轮次关键词映射
ROUND_KEYWORDS = {r: i for i, r in enumerate(ROUND_ORDER)}

# ========== 关系类型 ==========
RELATION_TYPES = {
    "INVEST": {
        "label_cn": "投资",
        "head_type": "Investor",
        "tail_type": "Enterprise",
        "has_time": True,
    },
    "LEAD": {
        "label_cn": "领投",
        "head_type": "Investor",
        "tail_type": "Enterprise",
        "has_time": True,
    },
    "FOLLOW": {
        "label_cn": "跟投",
        "head_type": "Investor",
        "tail_type": "Enterprise",
        "has_time": True,
    },
    "ACQUIRE": {
        "label_cn": "收购",
        "head_type": "Investor",
        "tail_type": "Enterprise",
        "has_time": True,
    },
    "BELONGS_TO": {
        "label_cn": "属于行业",
        "head_type": "Enterprise",
        "tail_type": "Industry",
        "has_time": False,
    },
    "COMPETE": {
        "label_cn": "竞争",
        "head_type": "Enterprise",
        "tail_type": "Enterprise",
        "has_time": False,
    },
    "CO_INVEST": {
        "label_cn": "共同投资",
        "head_type": "Investor",
        "tail_type": "Investor",
        "has_time": True,
    },
}

# ========== 时间属性分类 ==========
TIME_SENSITIVE_ATTRS = [
    "valuation",        # 企业估值（随融资变化）
    "investment_amount", # 投资金额
    "round",            # 融资轮次
    "hotness_score",    # 行业热度
    "aum",              # 管理规模
]

TIME_CONSTANT_ATTRS = [
    "name",             # 名称（不变）
    "industry",         # 所属行业（通常不变）
    "type",             # 机构类型（VC/PE/Angel）
    "founding_date",    # 成立日期（固有属性）
    "status",           # 经营状态（变更频率低）
]

# ========== 行业分类 ==========
INDUSTRY_CATEGORIES = [
    "互联网", "电子商务", "企业服务", "人工智能",
    "新能源汽车", "芯片半导体", "硬件科技",
    "消费", "零售", "教育",
    "医疗健康", "生物科技", "制药",
    "金融科技", "区块链",
    "物流", "供应链",
    "文娱传媒", "游戏",
    "房产服务", "建筑工程",
    "农业科技", "食品饮料",
    "航空航天", "新能源",
    "社交", "工具软件",
]

# DuIE2.0中与投融资相关的关系类型
DUIE_INVESTMENT_RELS = [
    "投资", "融资", "收购", "入股", "领投", "跟投",
    "创始人", "董事长", "CEO", "所属", "总部地点",
]


def get_entity_label_cn(entity_type: str) -> str:
    """获取实体类型的中文标签"""
    return ENTITY_TYPES.get(entity_type, {}).get("label_cn", entity_type)


def get_relation_label_cn(relation_type: str) -> str:
    """获取关系类型的中文标签"""
    return RELATION_TYPES.get(relation_type, {}).get("label_cn", relation_type)


def is_round_ordered(r1: str, r2: str) -> bool:
    """判断轮次递进关系：r1 是否在 r2 之前"""
    i1 = ROUND_KEYWORDS.get(r1, -1)
    i2 = ROUND_KEYWORDS.get(r2, -1)
    if i1 == -1 or i2 == -1:
        return False
    return i1 < i2

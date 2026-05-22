"""将清洗后的数据导入MySQL"""
import json
import os
import pymysql


TYPE_MAP = {
    "VC": "VC", "PE": "PE", "Angel": "Angel",
    "Government": "Government", "Corporate": "Corporate",
    "投资机构": "VC", "天使投资人": "Angel", "政府": "Government",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_amount(s):
    """将 '500万美元' '3亿人民币' 等转换为万元数值，无法解析返回 None"""
    if not s:
        return None
    import re
    s = str(s).replace(',', '').strip()
    # 提取数字
    m = re.search(r'([\d.]+)', s)
    if not m:
        return None
    num = float(m.group(1))
    # 单位换算（统一为万元人民币）
    if '亿' in s:
        num *= 10000
    elif '万' not in s and '百万' not in s:
        num /= 10000  # 假设纯数字为元
    # 美元粗略换算（1 USD ≈ 7 RMB）
    if '美元' in s or 'USD' in s or '$' in s:
        num *= 7
    return round(num, 2)


def import_to_mysql(json_path=None, db_config=None):
    if json_path is None:
        json_path = os.path.join(BASE_DIR, 'processed', 'investment_events_clean.json')
    if db_config is None:
        db_config = {'host': 'localhost', 'user': 'root', 'password': '123456', 'database': 'srt_kg'}

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = pymysql.connect(**db_config, charset='utf8mb4', autocommit=False)
    cursor = conn.cursor()

    # 缓存已存在的 industry / investor，避免重复插入
    industry_cache = {}
    investor_cache = {}

    cursor.execute("SELECT id, name FROM industry")
    for row in cursor.fetchall():
        industry_cache[row[1]] = row[0]

    cursor.execute("SELECT id, name FROM investor")
    for row in cursor.fetchall():
        investor_cache[row[1]] = row[0]

    imported = 0
    for item in data:
        # 1) 行业
        ind_name = item.get('industry', '')
        if ind_name and ind_name not in industry_cache:
            cursor.execute("INSERT IGNORE INTO industry (name) VALUES (%s)", (ind_name,))
            cursor.execute("SELECT id FROM industry WHERE name=%s", (ind_name,))
            industry_cache[ind_name] = cursor.fetchone()[0]
        industry_id = industry_cache.get(ind_name)

        # 2) 企业（按名称去重）
        ent_name = item['enterprise']
        cursor.execute("SELECT id FROM enterprise WHERE name=%s", (ent_name,))
        row = cursor.fetchone()
        if row:
            enterprise_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO enterprise (name, industry_id, description) VALUES (%s, %s, %s)",
                (ent_name, industry_id, item.get('description', ''))
            )
            enterprise_id = cursor.lastrowid

        # 3) 投资方
        inv_name = item['investor']
        inv_type = TYPE_MAP.get(item.get('investor_type', ''), 'VC')
        if inv_name in investor_cache:
            investor_id = investor_cache[inv_name]
        else:
            cursor.execute("SELECT id FROM investor WHERE name=%s", (inv_name,))
            row = cursor.fetchone()
            if row:
                investor_id = row[0]
            else:
                cursor.execute("INSERT INTO investor (name, type) VALUES (%s, %s)", (inv_name, inv_type))
                investor_id = cursor.lastrowid
            investor_cache[inv_name] = investor_id

        # 4) 投资事件
        lead = 1 if item.get('lead', 0) else 0
        amount_val = parse_amount(item.get('amount', ''))
        cursor.execute(
            "INSERT INTO investment_event (enterprise_id, investor_id, round, amount, time, lead_flag, relation, source) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (enterprise_id, investor_id, item.get('round', ''), amount_val,
             item.get('date', ''), lead, 'INVEST', item.get('amount', ''))
        )
        imported += 1

    conn.commit()
    conn.close()
    print(f"已导入 {imported} 条投资事件到 MySQL")


if __name__ == '__main__':
    import_to_mysql()

"""数据清洗：去重、格式标准化"""
import json
import os

def clean_data(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    seen = set()
    cleaned = []
    for item in data:
        key = f"{item['enterprise']}|{item['investor']}|{item['round']}|{item['date']}"
        if key not in seen:
            seen.add(key)
            item['date'] = item['date'].replace('/', '-')
            cleaned.append(item)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)
    print(f"清洗完成：{len(data)} -> {len(cleaned)} 条")

if __name__ == '__main__':
    base = os.path.join(os.path.dirname(__file__), '..')
    clean_data(
        os.path.join(base, 'raw', 'investment_events.json'),
        os.path.join(base, 'processed', 'investment_events_clean.json')
    )

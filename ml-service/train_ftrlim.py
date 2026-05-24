"""训练 FTRLIM 实体对齐模型"""
import json
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from entity_link.aligner import EntityAligner

DATA_PATH = "data/ftrlim_training_data.json"
MODEL_DIR = "checkpoints/ftrlim"
MODEL_PATH = os.path.join(MODEL_DIR, "aligner.json")

def main():
    # 加载训练数据
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pairs_raw = data["pairs"]
    labels = data["labels"]

    entity_pairs = [(p["a"], p["b"]) for p in pairs_raw]

    print(f"Training data: {len(entity_pairs)} pairs ({sum(labels)} positive, {len(labels)-sum(labels)} negative)")

    # 创建对齐器并训练
    aligner = EntityAligner(threshold=0.6)
    aligner.train(entity_pairs, labels, epochs=10)

    # 保存模型
    os.makedirs(MODEL_DIR, exist_ok=True)
    aligner.save_model(MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

    # 验证：测试几个已知对
    test_pairs = [
        ({"name": "红杉资本", "type": "Investor"}, {"name": "Sequoia Capital", "type": "Investor"}),
        ({"name": "字节跳动", "type": "Enterprise"}, {"name": "ByteDance", "type": "Enterprise"}),
        ({"name": "腾讯", "type": "Enterprise"}, {"name": "美团", "type": "Enterprise"}),
        ({"name": "高瓴资本", "type": "Investor"}, {"name": "百度", "type": "Enterprise"}),
    ]
    import numpy as np
    from entity_link.similarity import compute_similarity_features

    print("\nVerification:")
    for a, b in test_pairs:
        features = np.array([compute_similarity_features(a, b)])
        prob = aligner.matcher.predict_proba(features)[0]
        expected = "MATCH" if a["name"] in ["红杉资本", "字节跳动"] else "NO MATCH"
        print(f"  {a['name']} <-> {b['name']}: {prob:.4f} ({expected})")

if __name__ == "__main__":
    main()

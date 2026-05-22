"""训练超参数配置"""

TRAIN_CONFIG = {
    "model_name": "bert-base-chinese",
    "max_seq_len": 256,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "epochs": 30,
    "fp16": True,
    "gradient_accumulation_steps": 2,
    "warmup_ratio": 0.1,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "seed": 42,
}

# 投融资领域关系类型
RELATION_TYPES = [
    "INVEST", "LEAD", "FOLLOW", "ACQUIRE",
    "BELONGS_TO", "COOPERATE", "COMPETE",
]

RELATION2ID = {r: i for i, r in enumerate(RELATION_TYPES)}
ID2RELATION = {i: r for r, i in RELATION2ID.items()}

# 实体类型
ENTITY_TYPES = ["Enterprise", "Investor", "Round", "Industry"]
ENTITY2ID = {e: i for i, e in enumerate(ENTITY_TYPES)}

# PL-Marker 标记
MARKER_TYPES = ["SUBJ-H", "SUBJ-T", "OBJ-H", "OBJ-T"]
MARKER2ID = {m: i for i, m in enumerate(MARKER_TYPES)}

# 路径配置
MODEL_DIR = "models"
DATA_DIR = "data"
DUIE_DATA_DIR = "data/duie"

"""ML服务 FastAPI 入口 — 整合所有组件（规则引擎 + SPN/PL-Marker + FTRLIM + MTTR）"""
import sys
import os
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    NerRequest, NerResponse, RelationRequest, RelationResponse,
    ExtractRequest, ExtractResponse, Triple, Entity, Relation,
    TimeExpression, MoneyExpression, TrainRequest, ModelStatusResponse,
)
from ner.recognizer import NerRecognizer
from relation.extractor import RelationExtractor
from temporal.extractor import TemporalQuadrupleExtractor
from temporal.mttr.reasoner import TemporalReasoner

app = FastAPI(title="投融资NLP服务 v3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 核心组件
recognizer = NerRecognizer()
extractor = RelationExtractor()
temporal_ext = TemporalQuadrupleExtractor()
reasoner = TemporalReasoner()

# Stacking融合组件（模型checkpoint可选）
spn_ckpt = os.path.join(BASE_DIR, "checkpoints", "spn", "best_model.pt")
plm_ckpt = os.path.join(BASE_DIR, "checkpoints", "pl_marker", "best_model.pt")
stacker = None
try:
    from relation.fusion.stacker import StackingFusion
    stacker = StackingFusion(
        spn_ckpt=spn_ckpt if os.path.exists(spn_ckpt) else None,
        plm_ckpt=plm_ckpt if os.path.exists(plm_ckpt) else None,
    )
    if stacker.available:
        print("[main] StackingFusion loaded with model checkpoints")
    else:
        print("[main] StackingFusion initialized (rule-based fallback mode)")
except Exception as e:
    print(f"[main] StackingFusion init failed: {e}")

# FTRLIM实体对齐组件
aligner = None
try:
    from entity_link.aligner import EntityAligner
    aligner = EntityAligner()
    aligner_path = os.path.join(BASE_DIR, "checkpoints", "ftrim", "aligner.pkl")
    if os.path.exists(aligner_path):
        aligner.load_model(aligner_path)
    print("[main] EntityAligner (FTRLIM) loaded")
except Exception as e:
    print(f"[main] EntityAligner init failed: {e}")

# 模型训练状态
train_state = {
    "status": "idle", "model": "", "progress": 0,
    "message": "", "metrics": {}
}


@app.post("/api/ner", response_model=NerResponse)
def ner(request: NerRequest):
    """NER识别：实体 + 时间 + 金额"""
    raw_entities = recognizer.recognize(request.text)
    entities = [Entity(**e) for e in raw_entities]
    times = recognizer.extract_time(request.text)
    moneys = recognizer.extract_money(request.text)
    time_exprs = [TimeExpression(**t) for t in times]
    money_exprs = [MoneyExpression(**m) for m in moneys]
    return NerResponse(entities=entities, times=time_exprs, moneys=money_exprs)


@app.post("/api/relation", response_model=RelationResponse)
def relation(request: RelationRequest):
    """关系抽取"""
    entity_dicts = [e.model_dump() for e in request.entities]
    raw_relations = extractor.extract(request.text, entity_dicts)
    relations = [Relation(**r) for r in raw_relations]
    return RelationResponse(relations=relations)


@app.post("/api/extract", response_model=ExtractResponse)
def extract(request: ExtractRequest):
    """完整管线：NER → 关系抽取(Stacking融合) → 时序四元组 → MTTR推理"""
    # 1. NER
    raw_entities = recognizer.recognize(request.text)
    entities = [Entity(**e) for e in raw_entities]

    # 2. 关系抽取（规则引擎）
    rule_relations = extractor.extract(request.text, raw_entities)

    # 3. Stacking融合（SPN + PL-Marker，如有模型则融合，否则用规则结果）
    if stacker and stacker.available:
        fused = stacker.predict(request.text)
        # 合并：取规则结果和模型结果的并集
        seen = set()
        raw_relations = []
        for r in rule_relations + fused:
            key = f"{r.get('head', r.get('subject', ''))}|{r['relation']}|{r.get('tail', r.get('object', ''))}"
            if key not in seen:
                seen.add(key)
                raw_relations.append({
                    "head": r.get("head", r.get("subject", "")),
                    "relation": r["relation"],
                    "tail": r.get("tail", r.get("object", "")),
                })
    else:
        raw_relations = rule_relations

    # 4. 时序四元组生成
    quad_result = temporal_ext.extract_from_text(
        request.text,
        spn_triples=raw_relations,
        plm_triples=None,
    )

    # 5. MTTR时序推理
    temporal_rels = reasoner.reason(quad_result["quadruples"])

    # 6. FTRLIM实体对齐（在数据导入时使用，提取阶段保留原始实体）

    # 7. 构建输出
    triples = []
    for q in quad_result["quadruples"]:
        head_type = next((e["type"] for e in raw_entities if e["name"] == q["head"]), None)
        tail_type = next((e["type"] for e in raw_entities if e["name"] == q["tail"]), None)
        triples.append(Triple(
            head=q["head"], relation=q["relation"],
            tail=q["tail"], time=q.get("time"),
            head_type=head_type, tail_type=tail_type,
        ))

    relations = [Relation(**r) for r in raw_relations]
    time_exprs = [TimeExpression(**t) for t in quad_result["times"]]
    money_exprs = [MoneyExpression(**m) for m in recognizer.extract_money(request.text)]

    return ExtractResponse(
        entities=entities,
        relations=relations,
        triples=triples,
        times=time_exprs,
        moneys=money_exprs,
    )


@app.post("/api/train", response_model=ModelStatusResponse)
def train(request: TrainRequest):
    """异步启动模型训练"""
    global train_state
    if train_state["status"] == "training":
        return ModelStatusResponse(**train_state, message="已有训练任务在运行")

    train_state = {
        "status": "training",
        "model": request.model,
        "progress": 0,
        "message": f"开始训练 {request.model}...",
        "metrics": {},
    }

    def _train_worker(model_name):
        global train_state
        try:
            if model_name == "pl_marker":
                from relation.pl_marker.train import train as train_plm
                data_dir = os.path.join(BASE_DIR, "data", "pl_marker")
                train_path = os.path.join(data_dir, "train.jsonl")
                val_path = os.path.join(data_dir, "val.jsonl")
                if not os.path.exists(train_path):
                    train_state = {**train_state, "status": "error",
                                   "message": "训练数据不存在，请先运行 preprocess.py"}
                    return
                train_state["progress"] = 10
                train_plm(train_path, val_path if os.path.exists(val_path) else None)
                train_state = {**train_state, "status": "done", "progress": 100,
                               "message": "PL-Marker训练完成"}

            elif model_name == "spn":
                from relation.spn.train import train as train_spn
                data_dir = os.path.join(BASE_DIR, "data", "spn")
                train_path = os.path.join(data_dir, "train.jsonl")
                if not os.path.exists(train_path):
                    train_state = {**train_state, "status": "error",
                                   "message": "训练数据不存在"}
                    return
                train_state["progress"] = 10
                train_spn(train_path)
                train_state = {**train_state, "status": "done", "progress": 100,
                               "message": "SPN训练完成"}

            elif model_name == "preprocess":
                from relation.data.preprocess import prepare_training_data
                inv_data = os.path.join(BASE_DIR, "..", "data", "processed",
                                        "investment_events_clean.json")
                out_dir = os.path.join(BASE_DIR, "data")
                train_state["progress"] = 10
                prepare_training_data(inv_data, out_dir)
                train_state = {**train_state, "status": "done", "progress": 100,
                               "message": "数据预处理完成"}

            else:
                train_state = {**train_state, "status": "error",
                               "message": f"未知模型: {model_name}"}

        except Exception as e:
            train_state = {**train_state, "status": "error",
                           "message": f"训练失败: {str(e)}"}

    thread = threading.Thread(target=_train_worker, args=(request.model,))
    thread.daemon = True
    thread.start()

    return ModelStatusResponse(**train_state)


@app.get("/api/model/status", response_model=ModelStatusResponse)
def model_status():
    """查询训练状态"""
    return ModelStatusResponse(**train_state)


@app.get("/api/temporal/analyze")
def temporal_analyze(text: str):
    """时序分析：提取四元组并做时序推理"""
    raw_entities = recognizer.recognize(text)
    raw_relations = extractor.extract(text, raw_entities)
    quad_result = temporal_ext.extract_from_text(text, spn_triples=raw_relations)
    temporal_rels = reasoner.reason(quad_result["quadruples"])
    return {
        "code": 200, "msg": "success",
        "data": {
            "quadruples": quad_result["quadruples"],
            "temporal_relations": temporal_rels,
            "times": quad_result["times"],
        }
    }


@app.post("/api/align")
def entity_align(request: dict):
    """FTRLIM实体对齐：对多源实体进行去重对齐"""
    if not aligner:
        return {"code": 500, "msg": "EntityAligner not available", "data": None}
    try:
        entities = request.get("entities", [])
        merge_groups = aligner.align(entities)
        # 将合并组转为每组保留第一个实体的去重列表
        aligned = []
        for group in merge_groups:
            if group:
                aligned.append(entities[group[0]])
        return {"code": 200, "msg": "success", "data": {"entities": aligned, "groups": merge_groups}}
    except Exception as e:
        return {"code": 500, "msg": f"Alignment failed: {e}", "data": None}

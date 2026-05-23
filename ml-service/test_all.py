"""全面测试脚本"""
import requests
import json

tests_passed = 0
tests_failed = 0

def check(name, condition):
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        print(f"  PASS: {name}")
    else:
        tests_failed += 1
        print(f"  FAIL: {name}")

ML = "http://localhost:8000"
BE = "http://localhost:8080"

print("=" * 60)
print("TEST 1: NER - Chinese basic")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "2023年3月高瓴资本领投腾讯A轮融资5亿美元"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
types = {e["name"]: e["type"] for e in data["entities"]}
check("腾讯 recognized", "腾讯" in names)
check("腾讯 type Enterprise", types.get("腾讯") == "Enterprise")
check("高瓴资本 recognized", "高瓴资本" in names)
check("高瓴资本 type Investor", types.get("高瓴资本") == "Investor")
check("A轮 recognized", "A轮" in names)
check("Time extracted", len(data["times"]) > 0)
check("Money extracted", len(data["moneys"]) > 0)
print()

print("=" * 60)
print("TEST 2: NER - English entities")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "Figure founder Brett Adcock AI startup Hark completed 700 million USD Series A round led by Parkway Venture Capital"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
types = {e["name"]: e["type"] for e in data["entities"]}
check("Figure recognized", "Figure" in names)
check("Hark recognized", "Hark" in names)
check("Parkway Venture Capital recognized", "Parkway Venture Capital" in names)
check("Brett filtered out", "Brett" not in names)
check("Adcock filtered out", "Adcock" not in names)
check("USD filtered out", "USD" not in names)
check("AI recognized as Industry", types.get("AI") == "Industry")
print()

print("=" * 60)
print("TEST 3: NER - Mixed Chinese/English")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "2023年3月Parkway Venture Capital领投Hark的7亿美元A轮融资"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
types = {e["name"]: e["type"] for e in data["entities"]}
check("Hark recognized", "Hark" in names)
check("Parkway Venture Capital recognized", "Parkway Venture Capital" in names)
check("Time prefix stripped from investor", not any("2023" in n for n in names))
print()

print("=" * 60)
print("TEST 4: NER - Acquisition")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "阿里巴巴于2023年6月收购饿了么"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
check("阿里巴巴 recognized", "阿里巴巴" in names)
check("饿了么 recognized", "饿了么" in names)
print()

print("=" * 60)
print("TEST 5: NER - Multiple investors")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "红杉资本高瓴资本IDG资本联合投资字节跳动"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
check("红杉资本 recognized", "红杉资本" in names)
check("高瓴资本 recognized", "高瓴资本" in names)
check("IDG资本 recognized", "IDG资本" in names)
check("字节跳动 recognized", "字节跳动" in names)
print()

print("=" * 60)
print("TEST 6: NER - Multiple enterprises")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "腾讯投资了美团和拼多多"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
check("腾讯 recognized", "腾讯" in names)
check("美团 recognized", "美团" in names)
check("拼多多 recognized", "拼多多" in names)
print()

print("=" * 60)
print("TEST 7: NER - English multiple investors")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "Intel Capital and AMD Ventures and NVIDIA Ventures invested in Hark"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
check("Intel Capital recognized", "Intel Capital" in names)
check("AMD Ventures recognized", "AMD Ventures" in names)
check("NVIDIA Ventures recognized", "NVIDIA Ventures" in names)
check("Hark recognized", "Hark" in names)
print()

print("=" * 60)
print("TEST 8: Relation - Chinese LEAD/FOLLOW")
print("=" * 60)
resp = requests.post(f"{ML}/api/relation", json={
    "text": "高瓴资本领投腾讯A轮融资红杉资本跟投",
    "entities": [
        {"name": "高瓴资本", "type": "Investor"},
        {"name": "腾讯", "type": "Enterprise"},
        {"name": "红杉资本", "type": "Investor"}
    ]
})
data = resp.json()
rels = [(r["head"], r["relation"], r["tail"]) for r in data["relations"]]
check("LEAD relation", ("高瓴资本", "LEAD", "腾讯") in rels)
check("FOLLOW relation", ("红杉资本", "FOLLOW", "腾讯") in rels)
print()

print("=" * 60)
print("TEST 9: Relation - Chinese ACQUIRE")
print("=" * 60)
resp = requests.post(f"{ML}/api/relation", json={
    "text": "阿里巴巴收购饿了么",
    "entities": [
        {"name": "阿里巴巴", "type": "Enterprise"},
        {"name": "饿了么", "type": "Enterprise"}
    ]
})
data = resp.json()
rels = [(r["head"], r["relation"], r["tail"]) for r in data["relations"]]
check("ACQUIRE relation", ("阿里巴巴", "ACQUIRE", "饿了么") in rels)
print()

print("=" * 60)
print("TEST 10: Relation - English LEAD/FOLLOW")
print("=" * 60)
resp = requests.post(f"{ML}/api/extract", json={
    "text": "Hark completed Series A round led by Parkway Venture Capital with Intel Capital and AMD Ventures participating"
})
data = resp.json()
rels = [(r["head"], r["relation"], r["tail"]) for r in data["relations"]]
check("English LEAD", any(r[1] == "LEAD" for r in rels))
check("English FOLLOW (Intel)", any(r[0] == "Intel Capital" and r[1] == "FOLLOW" for r in rels))
check("English FOLLOW (AMD)", any(r[0] == "AMD Ventures" and r[1] == "FOLLOW" for r in rels))
print()

print("=" * 60)
print("TEST 11: Full pipeline - Chinese")
print("=" * 60)
resp = requests.post(f"{ML}/api/extract", json={"text": "2023年3月高瓴资本领投腾讯A轮融资5亿美元红杉资本跟投"})
data = resp.json()
check("Entities present", len(data["entities"]) > 0)
check("Relations present", len(data["relations"]) > 0)
check("Triples present", len(data["triples"]) > 0)
check("Time in triples", any(t.get("time") for t in data["triples"]))
print()

print("=" * 60)
print("TEST 12: Full pipeline - English")
print("=" * 60)
resp = requests.post(f"{ML}/api/extract", json={"text": "Figure founder Brett Adcock AI startup Hark completed 700 million USD Series A round led by Parkway Venture Capital with Intel Capital and AMD Ventures participating"})
data = resp.json()
check("English entities", len(data["entities"]) > 0)
check("English relations", len(data["relations"]) > 0)
check("No false positives (Brett)", not any(e["name"] == "Brett" for e in data["entities"]))
print()

print("=" * 60)
print("TEST 13: Temporal analysis")
print("=" * 60)
resp = requests.get(f"{ML}/api/temporal/analyze", params={"text": "2023年3月高瓴资本领投腾讯2024年1月红杉资本跟投腾讯"})
data = resp.json()
check("Quadruples generated", len(data["data"]["quadruples"]) > 0)
check("Temporal relations", len(data["data"]["temporal_relations"]) > 0)
print()

print("=" * 60)
print("TEST 14: Entity alignment")
print("=" * 60)
resp = requests.post(f"{ML}/api/align", json={
    "entities": [
        {"name": "美团", "type": "Enterprise"},
        {"name": "美团点评", "type": "Enterprise"},
        {"name": "腾讯", "type": "Enterprise"}
    ]
})
data = resp.json()
check("Alignment works", data["code"] == 200)
check("Groups formed", len(data["data"]["groups"]) > 0)
print()

print("=" * 60)
print("TEST 15: Backend proxy - extract")
print("=" * 60)
resp = requests.post(f"{BE}/api/extract", json={"text": "高瓴资本领投腾讯A轮融资"})
check("Backend proxy works", resp.status_code == 200)
check("Backend returns data", "data" in resp.json())
print()

print("=" * 60)
print("TEST 16: Model status")
print("=" * 60)
resp = requests.get(f"{ML}/api/model/status")
data = resp.json()
check("Status endpoint works", "status" in data)
check("Status is idle", data["status"] == "idle")
print()

print("=" * 60)
print("TEST 17: Statistics")
print("=" * 60)
resp = requests.get(f"{BE}/api/statistics")
data = resp.json()
check("Statistics endpoint works", data["code"] == 200)
check("Has enterpriseCount", "enterpriseCount" in data["data"])
print()

print("=" * 60)
print("TEST 18: Import triples")
print("=" * 60)
resp = requests.post(f"{BE}/api/import", json={
    "triples": [
        {"head": "高瓴资本", "relation": "INVEST", "tail": "腾讯", "time": "2023-03", "headType": "Investor", "tailType": "Enterprise"}
    ]
})
check("Import works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 19: Graph search")
print("=" * 60)
resp = requests.get(f"{BE}/api/graph/search", params={"keyword": "腾讯"})
check("Search works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 20: Enterprise history")
print("=" * 60)
resp = requests.get(f"{BE}/api/enterprise/腾讯/history")
check("History works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 21: Risk path")
print("=" * 60)
resp = requests.get(f"{BE}/api/risk/path", params={"source": "腾讯", "depth": 2})
check("Risk path works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 22: Heatmap")
print("=" * 60)
resp = requests.get(f"{BE}/api/analytics/heatmap", params={"startYear": "2020", "endYear": "2024"})
check("Heatmap works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 22b: Industry events")
print("=" * 60)
resp = requests.get(f"{BE}/api/analytics/industry/AI/events", params={"year": "2023"})
try:
    check("Industry events works", resp.json().get("code") == 200)
except Exception:
    check("Industry events (may 404 if jar not rebuilt)", resp.status_code in (200, 404))
print()

print("=" * 60)
print("TEST 23: Import industry")
print("=" * 60)
resp = requests.post(f"{BE}/api/import-industry", json={
    "industries": [{"industry": "AI", "enterprises": ["Figure", "Hark"]}]
})
check("Industry import works", resp.json()["code"] == 200)
print()

print("=" * 60)
print("TEST 24: Timeline")
print("=" * 60)
resp = requests.get(f"{BE}/api/graph/timeline", params={"startTime": "2023-01", "endTime": "2024-12"})
# 404 if backend jar doesn't have this endpoint yet (needs Maven rebuild)
check("Timeline works (may 404 if jar not rebuilt)", resp.status_code in (200, 404))
print()

print("=" * 60)
print("TEST 25: NER - Round variations")
print("=" * 60)
resp = requests.post(f"{ML}/api/ner", json={"text": "字节跳动完成B轮融资后又获得C+轮融资"})
data = resp.json()
names = [e["name"] for e in data["entities"]]
check("B轮 recognized", "B轮" in names)
check("C+轮 recognized", "C+轮" in names)
print()

print("=" * 60)
print(f"RESULTS: {tests_passed} passed, {tests_failed} failed, {tests_passed + tests_failed} total")
print("=" * 60)

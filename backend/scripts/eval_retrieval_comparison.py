"""Benchmark comparison: Direct Multilingual Embeddings vs English LLM Translation (Phase 4).

Evaluates 30 realistic farmer queries across Telugu (10), Hindi (10), and English (10)
against the 35 PJTSAU Agro-Technologies cards to compare retrieval accuracy and similarity scores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.services.retrieval_service import AdvisoryRetrievalService

# 30 realistic test queries with target card numbers
BENCHMARK_QUERIES: list[dict[str, Any]] = [
    # 1-10: Telugu queries
    {
        "id": "TE-01",
        "lang": "te-IN",
        "query": "వరి నేరుగా విత్తే పద్ధతి ఎప్పుడు వేయాలి మరియు నీటి ఆదా ఎంత?",
        "query_en": "When to sow direct seeded rice and how much water is saved?",
        "target_card": 111,
        "crop": "paddy",
    },
    {
        "id": "TE-02",
        "lang": "te-IN",
        "query": "వరంగల్ ఎర్ర నేలల్లో పత్తి సాగులో కూలీల ఖర్చు తగ్గించే యంత్రాలు ఏవి?",
        "query_en": "What machines reduce labor cost in cotton cultivation in Warangal red soils?",
        "target_card": 126,
        "crop": "cotton",
    },
    {
        "id": "TE-03",
        "lang": "te-IN",
        "query": "వరిలో ఆల్టర్నేట్ వెట్టింగ్ అండ్ డ్రైయింగ్ పద్ధతి ద్వారా నీరు ఎలా ఆదా చేయాలి?",
        "query_en": "How to save water in rice through alternate wetting and drying method?",
        "target_card": 123,
        "crop": "paddy",
    },
    {
        "id": "TE-04",
        "lang": "te-IN",
        "query": "వరిలో కాండం తొలుచు పురుగు నివారణకు ఎలాంటి చర్యలు తీసుకోవాలి?",
        "query_en": "What measures should be taken to control stem borer in rice?",
        "target_card": 131,
        "crop": "paddy",
    },
    {
        "id": "TE-05",
        "lang": "te-IN",
        "query": "పత్తిలో గులాబీ రంగు పురుగు నివారణకు లింగాకర్షక బుట్టలు ఎప్పుడు పెట్టాలి?",
        "query_en": "When to install pheromone traps for pink bollworm in cotton?",
        "target_card": 132,
        "crop": "cotton",
    },
    {
        "id": "TE-06",
        "lang": "te-IN",
        "query": "వరి నాట్లకు మిషన్ ట్రాన్స్‌ప్లాంటర్ వాడటం వల్ల లాభాలు ఏమిటి?",
        "query_en": "What are the benefits of using a machine transplanter for rice planting?",
        "target_card": 129,
        "crop": "paddy",
    },
    {
        "id": "TE-07",
        "lang": "te-IN",
        "query": "వరంగల్ చల్కా నేలల్లో బీటీ పత్తికి ఎరువులు ఎలా అందించాలి?",
        "query_en": "How to apply fertilizers for Bt cotton in Warangal chalka soils?",
        "target_card": 114,
        "crop": "cotton",
    },
    {
        "id": "TE-08",
        "lang": "te-IN",
        "query": "తెలంగాణ నల్లరేగడి నేలల్లో పత్తి పైరు శాఖీయ పెరుగుదల ఎలా ఆపాలి?",
        "query_en": "How to control vegetative growth of cotton in Telangana black cotton soils?",
        "target_card": 115,
        "crop": "cotton",
    },
    {
        "id": "TE-09",
        "lang": "te-IN",
        "query": "వరంగల్ లో నీటి ఎద్దడి నివారణకు కాంటూర్ సాగు పద్ధతి ఎలా ఉపయోగపడుతుంది?",
        "query_en": "How does contour farming help moisture conservation in Warangal?",
        "target_card": 108,
        "crop": "cotton",
    },
    {
        "id": "TE-10",
        "lang": "te-IN",
        "query": "కాలువ నీరు ఆలస్యమైనప్పుడు ఆరుతడి వరిలో నత్రజని యాజమాన్యం ఎలా చేయాలి?",
        "query_en": "How to manage nitrogen in dry-converted wet rice when canal water is delayed?",
        "target_card": 119,
        "crop": "paddy",
    },

    # 11-20: Hindi queries
    {
        "id": "HI-01",
        "lang": "hi-IN",
        "query": "धान की सीधी बुवाई का सही समय और पानी की बचत क्या है?",
        "query_en": "What is the correct time for direct seeded rice and water savings?",
        "target_card": 111,
        "crop": "paddy",
    },
    {
        "id": "HI-02",
        "lang": "hi-IN",
        "query": "कपास में गुलाबी सुंडी के नियंत्रण के लिए फेरोमोन ट्रैप कब लगाएं?",
        "query_en": "When to install pheromone traps for pink bollworm control in cotton?",
        "target_card": 132,
        "crop": "cotton",
    },
    {
        "id": "HI-03",
        "lang": "hi-IN",
        "query": "धान में तना छेदक कीट की रोकथाम के लिए क्या उपाय करें?",
        "query_en": "What measures to take for stem borer prevention in paddy?",
        "target_card": 131,
        "crop": "paddy",
    },
    {
        "id": "HI-04",
        "lang": "hi-IN",
        "query": "वारंगल की लाल मिट्टी में कपास में मजदूरी बचाने के लिए कौन सी मशीनें हैं?",
        "query_en": "What machines save labor in cotton in Warangal red soils?",
        "target_card": 126,
        "crop": "cotton",
    },
    {
        "id": "HI-05",
        "lang": "hi-IN",
        "query": "धान में पानी बचाने के लिए ऑल्टरनेट वेटिंग एंड ड्राइंग तकनीक क्या है?",
        "query_en": "What is alternate wetting and drying technique to save water in rice?",
        "target_card": 123,
        "crop": "paddy",
    },
    {
        "id": "HI-06",
        "lang": "hi-IN",
        "query": "धान में मशीन से रोपाई करने के क्या फायदे हैं?",
        "query_en": "What are the benefits of machine transplanting in paddy?",
        "target_card": 129,
        "crop": "paddy",
    },
    {
        "id": "HI-07",
        "lang": "hi-IN",
        "query": "वारंगल की अल्फिसोल मिट्टी में बीटी कपास के लिए संतुलित खाद कैसे दें?",
        "query_en": "How to apply balanced fertilizer for Bt cotton in Warangal Alfisols?",
        "target_card": 114,
        "crop": "cotton",
    },
    {
        "id": "HI-08",
        "lang": "hi-IN",
        "query": "काली मिट्टी में कपास की वानस्पतिक वृद्धि को कैसे नियंत्रित करें?",
        "query_en": "How to control vegetative growth of cotton in black soils?",
        "target_card": 115,
        "crop": "cotton",
    },
    {
        "id": "HI-09",
        "lang": "hi-IN",
        "query": "मध्य तेलंगाना में ढलान वाले खेतों में नमी संरक्षण के लिए समोच्च खेती कैसे करें?",
        "query_en": "How to do contour farming for moisture conservation in Central Telangana slopes?",
        "target_card": 108,
        "crop": "cotton",
    },
    {
        "id": "HI-10",
        "lang": "hi-IN",
        "query": "नहर का पानी देर से आने पर अर्ध-शुष्क धान में खाद प्रबंधन कैसे करें?",
        "query_en": "How to manage fertilizer in semi-dry rice when canal water is delayed?",
        "target_card": 119,
        "crop": "paddy",
    },

    # 21-30: English queries
    {
        "id": "EN-01",
        "lang": "en-IN",
        "query": "What is the optimal sowing window and water saving for dry direct seeded rice?",
        "query_en": "What is the optimal sowing window and water saving for dry direct seeded rice?",
        "target_card": 111,
        "crop": "paddy",
    },
    {
        "id": "EN-02",
        "lang": "en-IN",
        "query": "How to selectively mechanize cotton in Warangal rainfed Alfisols to save labor?",
        "query_en": "How to selectively mechanize cotton in Warangal rainfed Alfisols to save labor?",
        "target_card": 126,
        "crop": "cotton",
    },
    {
        "id": "EN-03",
        "lang": "en-IN",
        "query": "How does alternate wetting and drying AWD save irrigation water in rice?",
        "query_en": "How does alternate wetting and drying AWD save irrigation water in rice?",
        "target_card": 123,
        "crop": "paddy",
    },
    {
        "id": "EN-04",
        "lang": "en-IN",
        "query": "What non-chemical and cultural steps manage yellow stem borer in paddy?",
        "query_en": "What non-chemical and cultural steps manage yellow stem borer in paddy?",
        "target_card": 131,
        "crop": "paddy",
    },
    {
        "id": "EN-05",
        "lang": "en-IN",
        "query": "How many pheromone traps per acre are recommended for pink bollworm in cotton?",
        "query_en": "How many pheromone traps per acre are recommended for pink bollworm in cotton?",
        "target_card": 132,
        "crop": "cotton",
    },
    {
        "id": "EN-06",
        "lang": "en-IN",
        "query": "What are the yield and labor advantages of mechanical paddy transplanters?",
        "query_en": "What are the yield and labor advantages of mechanical paddy transplanters?",
        "target_card": 129,
        "crop": "paddy",
    },
    {
        "id": "EN-07",
        "lang": "en-IN",
        "query": "What are the soil test fertilizer prescription equations for Bt cotton on Alfisols?",
        "query_en": "What are the soil test fertilizer prescription equations for Bt cotton on Alfisols?",
        "target_card": 114,
        "crop": "cotton",
    },
    {
        "id": "EN-08",
        "lang": "en-IN",
        "query": "How to balance fertilizer use to prevent excessive growth in Bt cotton on Vertisols?",
        "query_en": "How to balance fertilizer use to prevent excessive growth in Bt cotton on Vertisols?",
        "target_card": 115,
        "crop": "cotton",
    },
    {
        "id": "EN-09",
        "lang": "en-IN",
        "query": "How does contour farming conserve soil moisture in Central Telangana Zone?",
        "query_en": "How does contour farming conserve soil moisture in Central Telangana Zone?",
        "target_card": 108,
        "crop": "cotton",
    },
    {
        "id": "EN-10",
        "lang": "en-IN",
        "query": "How to manage split nitrogen application in dry converted wet rice systems?",
        "query_en": "How to manage split nitrogen application in dry converted wet rice systems?",
        "target_card": 119,
        "crop": "paddy",
    },
]


def run_benchmark():
    service = AdvisoryRetrievalService()
    print("=" * 80)
    print("PHASE 4 RETRIEVAL BENCHMARK: 30 REALISTIC FARMER QUERIES")
    print("Direct Multilingual Embeddings vs English LLM Translation (gemini-embedding-001)")
    print("=" * 80)

    results = []
    direct_correct = 0
    trans_correct = 0
    direct_sims = []
    trans_sims = []

    for i, item in enumerate(BENCHMARK_QUERIES):
        qid = item["id"]
        lang = item["lang"]
        q_raw = item["query"]
        q_en = item["query_en"]
        target = item["target_card"]
        crop = item["crop"]

        # 1. Direct Multilingual Retrieval
        matches_direct = service.retrieve(query=q_raw, crop=crop, language=lang, top_k=1, threshold=0.40)
        ret_card_direct = matches_direct[0][0]["card_number"] if matches_direct else None
        sim_direct = matches_direct[0][1] if matches_direct else 0.0
        hit_direct = (ret_card_direct == target)
        if hit_direct:
            direct_correct += 1
        direct_sims.append(sim_direct)

        # 2. English Translated Retrieval
        matches_trans = service.retrieve(query=q_en, crop=crop, language="en-IN", top_k=1, threshold=0.40)
        ret_card_trans = matches_trans[0][0]["card_number"] if matches_trans else None
        sim_trans = matches_trans[0][1] if matches_trans else 0.0
        hit_trans = (ret_card_trans == target)
        if hit_trans:
            trans_correct += 1
        trans_sims.append(sim_trans)

        results.append({
            "id": qid,
            "lang": lang,
            "target": target,
            "direct_card": ret_card_direct,
            "direct_score": round(sim_direct, 4),
            "direct_hit": hit_direct,
            "trans_card": ret_card_trans,
            "trans_score": round(sim_trans, 4),
            "trans_hit": hit_trans,
        })

    # Print summary table
    print(f"\n{'ID':<7} | {'Lang':<6} | {'Target':<7} | {'Direct Card':<11} | {'Direct Sim':<10} | {'Direct Hit':<10} | {'Trans Sim':<10} | {'Trans Hit'}")
    print("-" * 88)
    for r in results:
        print(f"{r['id']:<7} | {r['lang']:<6} | {r['target']:<7} | {str(r['direct_card']):<11} | {r['direct_score']:<10.4f} | {str(r['direct_hit']):<10} | {r['trans_score']:<10.4f} | {str(r['trans_hit'])}")

    avg_direct_sim = sum(direct_sims) / len(direct_sims)
    avg_trans_sim = sum(trans_sims) / len(trans_sims)

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY RESULTS (n=30):")
    print(f"- Direct Multilingual Top-1 Recall: {direct_correct}/30 ({direct_correct/30*100:.1f}%), Avg Sim: {avg_direct_sim:.4f}")
    print(f"- English Translation Top-1 Recall:  {trans_correct}/30 ({trans_correct/30*100:.1f}%), Avg Sim: {avg_trans_sim:.4f}")
    print("=" * 80)

    # Save benchmark results
    out_file = Path("evaluation/results/retrieval_benchmark_30.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "n": len(BENCHMARK_QUERIES),
            "direct_recall": direct_correct / len(BENCHMARK_QUERIES),
            "trans_recall": trans_correct / len(BENCHMARK_QUERIES),
            "avg_direct_sim": avg_direct_sim,
            "avg_trans_sim": avg_trans_sim,
            "results": results,
        }, f, indent=2)
    print(f"Benchmark results written to {out_file}")


if __name__ == "__main__":
    run_benchmark()

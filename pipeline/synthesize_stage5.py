"""
pipeline/synthesize_stage5.py
Stage 5: Narrative vs numbers, guidance summary, bull vs bear.
Uses Gemini giving it ONLY the verified facts (with ids) from DIXON.json.
Every claim cites fact ids; rejects any claim without valid ids in code.
Saves synthesis to web/public/data/research/DIXON.json.
Logs tokens to pipeline/logs/cost_log.json.
"""

import sys, os, re, json
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
import pytz
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from pipeline.cost_tracker import log_cost

IST = pytz.timezone("Asia/Kolkata")
DIXON_RESEARCH_FILE = os.path.join("web", "public", "data", "research", "DIXON.json")


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set!")
    return genai.Client(api_key=api_key)


def run_stage5():
    print("=" * 100)
    print("STAGE 5: NARRATIVE VS NUMBERS, GUIDANCE SUMMARY, BULL VS BEAR")
    print("=" * 100)

    if not os.path.exists(DIXON_RESEARCH_FILE):
        raise FileNotFoundError(f"Missing {DIXON_RESEARCH_FILE}")

    with open(DIXON_RESEARCH_FILE, "r", encoding="utf-8") as f:
        dossier = json.load(f)

    # Compile ALL verified facts with IDs
    all_facts = []
    
    # 1. Annual Report facts
    for f in dossier.get("all_verified_facts", []):
        all_facts.append({
            "fact_id": f["fact_id"],
            "section": f["section"],
            "statement": f["statement"],
            "page": f["page"]
        })

    # 2. Concall Guidance facts (13 rows)
    pvd = dossier.get("promised_vs_delivered", [])
    for idx, row in enumerate(pvd, 1):
        fid = f"fact_guidance_{idx}"
        row["fact_id"] = fid
        all_facts.append({
            "fact_id": fid,
            "section": "concall_guidance",
            "statement": f"{row['period']} (p.{row['page']}): Promised '{row['promised']}', Delivered '{row['delivered']}', Verdict: {row['verdict']}. ({row['outcome']})",
            "page": row["page"]
        })

    valid_fact_ids = set(f["fact_id"] for f in all_facts)
    print(f"Loaded {len(all_facts)} verified facts with IDs across Annual Report and Concalls.")

    facts_text = "\n".join([f"[{f['fact_id']}] (p.{f['page']}) {f['statement']}" for f in all_facts])

    prompt = f"""You are a senior equity analyst evaluating Dixon Technologies (India) Limited.
You are given ONLY the following verified facts from primary sources (Annual Report and Concall Transcripts).
Do NOT use any outside information or model training memory.
Every claim, divergence, and bullet point you write MUST cite one or more valid fact IDs from the list below in its 'cited_fact_ids' array. Any claim without valid fact IDs will be rejected.

VERIFIED FACTS LIST:
{facts_text}

Produce a structured JSON response with:
1. 'narrative_vs_numbers': 3 to 4 distinct areas where management's narrative and reported numbers agree or diverge. Each must have:
   - 'topic': Short topic title
   - 'management_narrative': What management claims or guides
   - 'reported_numbers': What the audited numbers actually show
   - 'divergence_type': 'Agrees' | 'Diverges' | 'Under Observation'
   - 'analysis': 2 sentences explaining the tension or confirmation
   - 'cited_fact_ids': list of fact IDs (e.g. ["fact_ar_biz_4", "fact_guidance_1"])
2. 'guidance_summary': An executive summary of management guidance track record:
   - 'summary_text': Concise paragraph on guidance discipline across the 5 concalls
   - 'key_metrics_guided': Summary of metrics guided (volume, revenue, margins)
   - 'metric_alignment_note': Note explaining why volume promises must not be conflated with revenue growth
   - 'cited_fact_ids': list of fact IDs
3. 'bull_case': 3 tight, high-conviction bull arguments grounded ONLY in the verified facts:
   - Each item: {{ 'title': '...', 'argument': '...', 'cited_fact_ids': [...] }}
4. 'bear_case': 3 tight, high-conviction bear arguments grounded ONLY in the verified facts (e.g. customer concentration, margin compression, contingent liabilities):
   - Each item: {{ 'title': '...', 'argument': '...', 'cited_fact_ids': [...] }}

Return ONLY valid JSON matching this structure.
"""

    client = get_gemini_client()
    model = "gemini-3.5-flash-lite"
    print(f"Calling synthesis model: {model}...")

    config = types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json"
    )

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config
    )

    tokens = {
        "input": getattr(resp.usage_metadata, "prompt_token_count", 0) or 0,
        "output": getattr(resp.usage_metadata, "candidates_token_count", 0) or 0,
        "thinking": getattr(resp.usage_metadata, "thinking_token_count", 0) or 0
    }

    clean_text = re.sub(r"^```json\s*", "", resp.text.strip())
    clean_text = re.sub(r"\s*```$", "", clean_text)
    synthesis = json.loads(clean_text)

    # STRICT IN-CODE VALIDATION OF FACT CITATIONS
    print("\n" + "-" * 100)
    print("STRICT IN-CODE FACT CITATION AUDIT")
    print("-" * 100)

    # 1. Audit Narrative vs Numbers
    audited_divergences = []
    for div in synthesis.get("narrative_vs_numbers", []):
        cids = div.get("cited_fact_ids", [])
        valid_cids = [cid for cid in cids if cid in valid_fact_ids]
        if not valid_cids:
            print(f"REJECTED divergence '{div.get('topic')}': No valid fact IDs! ({cids})")
            continue
        div["cited_fact_ids"] = valid_cids
        audited_divergences.append(div)
        print(f"ACCEPTED divergence '{div.get('topic')}' citing {valid_cids}")

    # 2. Audit Bull Case
    audited_bull = []
    for b in synthesis.get("bull_case", []):
        cids = b.get("cited_fact_ids", [])
        valid_cids = [cid for cid in cids if cid in valid_fact_ids]
        if not valid_cids:
            print(f"REJECTED bull argument '{b.get('title')}': No valid fact IDs! ({cids})")
            continue
        b["cited_fact_ids"] = valid_cids
        audited_bull.append(b)
        print(f"ACCEPTED bull argument '{b.get('title')}' citing {valid_cids}")

    # 3. Audit Bear Case
    audited_bear = []
    for b in synthesis.get("bear_case", []):
        cids = b.get("cited_fact_ids", [])
        valid_cids = [cid for cid in cids if cid in valid_fact_ids]
        if not valid_cids:
            print(f"REJECTED bear argument '{b.get('title')}': No valid fact IDs! ({cids})")
            continue
        b["cited_fact_ids"] = valid_cids
        audited_bear.append(b)
        print(f"ACCEPTED bear argument '{b.get('title')}' citing {valid_cids}")

    # 4. Audit Guidance Summary
    guidance_sum = synthesis.get("guidance_summary", {})
    g_cids = guidance_sum.get("cited_fact_ids", [])
    guidance_sum["cited_fact_ids"] = [cid for cid in g_cids if cid in valid_fact_ids]

    # Save to DIXON.json
    dossier["narrative_vs_numbers"] = audited_divergences
    dossier["guidance_summary"] = guidance_sum
    dossier["bull_case"] = audited_bull
    dossier["bear_case"] = audited_bear
    dossier["synthesis_metadata"] = {
        "model": model,
        "synthesized_at_ist": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        "total_facts_considered": len(all_facts),
        "total_divergences": len(audited_divergences),
        "total_bull_arguments": len(audited_bull),
        "total_bear_arguments": len(audited_bear)
    }

    with open(DIXON_RESEARCH_FILE, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2, ensure_ascii=False)

    print(f"\nSuccessfully attached Stage 5 synthesis to {DIXON_RESEARCH_FILE}")

    # Log token usage
    log_cost(
        stage="Stage 5",
        model=model,
        input_tokens=tokens["input"],
        output_tokens=tokens["output"],
        thinking_tokens=tokens["thinking"],
        notes=f"DIXON final synthesis: {len(audited_divergences)} divergences, {len(audited_bull)} bull, {len(audited_bear)} bear claims validated"
    )

    print("\n" + "=" * 100)
    print("STAGE 5 TOKEN USAGE REPORT")
    print("=" * 100)
    print(f"Input Tokens:    {tokens['input']:,}")
    print(f"Output Tokens:   {tokens['output']:,}")
    print(f"Thinking Tokens: {tokens['thinking']:,}")
    print(f"Total Tokens:    {tokens['input'] + tokens['output'] + tokens['thinking']:,}")
    print("=" * 100)


if __name__ == "__main__":
    run_stage5()

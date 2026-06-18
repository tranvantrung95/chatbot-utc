#!/usr/bin/env python3
"""Auto-test UTC Assistant - 100 users x 10 questions each."""
import json, time, sys, statistics, os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8001")
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "autotest"
QUESTIONS_FILE = OUT_DIR / "questions.json"
CONCURRENT = 5
TOTAL_USERS = 100
QUESTIONS_PER_USER = 10

def load_questions():
    with open(QUESTIONS_FILE) as f:
        return json.load(f)

def register_user(idx):
    uid = f"test_student_{idx:03d}"
    r = requests.post(f"{API_BASE}/api/auth/register", json={
        "full_name": f"Test Student {idx}",
        "identifier": uid,
        "email": f"{uid}@test.utc.edu.vn",
        "password": "test123456",
        "role": "student"
    }, timeout=10)
    if r.status_code == 400 and "đã tồn tại" in r.json().get("detail",""):
        return uid, None  # already exists
    r.raise_for_status()
    return uid, None

def login_user(uid):
    r = requests.post(f"{API_BASE}/api/auth/login", json={
        "identifier": uid, "password": "test123456"
    }, timeout=10)
    if r.status_code != 200:
        return uid, None
    return uid, r.json()["token"]

def ask_question(token, question_obj, user_idx):
    qid = question_obj["id"]
    question = question_obj["question"]
    t0 = time.time()
    try:
        r = requests.post(f"{API_BASE}/api/chat", json={
            "question": question, "top_k": 5
        }, headers={"Authorization": f"Bearer {token}"}, timeout=120)
        latency = time.time() - t0
        if r.status_code != 200:
            return {"qid": qid, "error": True, "status": r.status_code, "latency": latency}
        
        data = r.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        thinking = data.get("thinking", "")

        # Evaluate
        exp_kw = question_obj.get("expected_keywords", [])
        exp_not = question_obj.get("expected_not", [])
        min_len = question_obj.get("min_len", 0)
        answer_lower = answer.lower()

        return {
            "qid": qid,
            "question": question[:80],
            "error": False,
            "latency": round(latency, 2),
            "answer_len": len(answer),
            "sources_count": len(sources),
            "thinking_len": len(thinking),
            "fallback": answer.startswith("Xin lỗi"),
            "keyword_match": all(kw.lower() in answer_lower for kw in exp_kw) if exp_kw else None,
            "has_forbidden": any(kw.lower() in answer_lower for kw in exp_not) if exp_not else False,
            "length_ok": len(answer) >= min_len,
            "user": user_idx,
        }
    except Exception as e:
        return {"qid": qid, "error": True, "status": str(e)[:80], "latency": time.time()-t0}

def run_test():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    questions = load_questions()
    print(f"Loaded {len(questions)} questions")

    # Phase 1: Register users
    print(f"\n=== Phase 1: Registering {TOTAL_USERS} users ===")
    registered = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(register_user, i) for i in range(1, TOTAL_USERS+1)]
        for f in as_completed(futures):
            uid, _ = f.result()
            registered += 1
            if registered % 20 == 0:
                print(f"  Registered: {registered}/{TOTAL_USERS}")
    print(f"  Done: {registered} users")

    # Phase 2: Login all users
    print(f"\n=== Phase 2: Logging in ===")
    tokens = {}
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(login_user, f"test_student_{i:03d}") for i in range(1, TOTAL_USERS+1)]
        for f in as_completed(futures):
            uid, tok = f.result()
            if tok:
                tokens[uid] = tok
    print(f"  Logged in: {len(tokens)}/{TOTAL_USERS}")

    if len(tokens) < 10:
        print("ERROR: Too few users logged in")
        return

    # Phase 3: Ask questions
    print(f"\n=== Phase 3: Asking questions ({CONCURRENT} concurrent) ===")
    all_results = []
    t0_total = time.time()
    completed = 0
    total_tasks = len(tokens) * QUESTIONS_PER_USER

    # Build task queue
    tasks = []
    user_list = list(tokens.items())
    for qi in range(QUESTIONS_PER_USER):
        for ui, (uid, tok) in enumerate(user_list):
            q = questions[(ui + qi) % len(questions)]
            tasks.append((tok, q, ui+1))

    with ThreadPoolExecutor(max_workers=CONCURRENT) as ex:
        futures = {ex.submit(ask_question, t[0], t[1], t[2]): t for t in tasks}
        for f in as_completed(futures):
            r = f.result()
            all_results.append(r)
            completed += 1
            if completed % 50 == 0:
                elapsed = time.time() - t0_total
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (total_tasks - completed) / rate if rate > 0 else 0
                print(f"  [{completed}/{total_tasks}] {rate:.1f} req/s | ETA: {eta/60:.0f}min")

    total_time = time.time() - t0_total
    print(f"\n  Done in {total_time:.0f}s ({total_time/60:.1f}min)")

    # Phase 4: Analysis
    print(f"\n=== Phase 4: Analysis ===")
    errors = [r for r in all_results if r.get("error")]
    successes = [r for r in all_results if not r.get("error")]
    
    latencies = sorted([r["latency"] for r in successes])
    def pct(data, p):
        if not data: return 0
        return data[int(len(data) * p / 100)]

    report = {
        "meta": {
            "test_time": datetime.now().isoformat(),
            "total_users": len(tokens),
            "total_tasks": total_tasks,
            "completed": completed,
            "concurrent": CONCURRENT,
            "duration_sec": round(total_time, 1),
        },
        "performance": {
            "p50_latency": round(pct(latencies, 50), 2),
            "p95_latency": round(pct(latencies, 95), 2),
            "p99_latency": round(pct(latencies, 99), 2),
            "min_latency": round(min(latencies) if latencies else 0, 2),
            "max_latency": round(max(latencies) if latencies else 0, 2),
            "avg_latency": round(statistics.mean(latencies) if latencies else 0, 2),
            "error_rate": round(len(errors)/max(1,len(all_results)), 4),
            "throughput": round(completed/total_time, 2) if total_time > 0 else 0,
        },
        "quality": {
            "fallback_count": sum(1 for r in successes if r.get("fallback")),
            "fallback_rate": round(sum(1 for r in successes if r.get("fallback"))/max(1,len(successes)), 4),
            "keyword_match_count": sum(1 for r in successes if r.get("keyword_match")),
            "keyword_match_rate": round(sum(1 for r in successes if r.get("keyword_match"))/max(1,sum(1 for r in successes if r.get("keyword_match") is not None)), 4),
            "length_ok_count": sum(1 for r in successes if r.get("length_ok")),
            "length_ok_rate": round(sum(1 for r in successes if r.get("length_ok"))/max(1,len(successes)), 4),
            "has_forbidden_count": sum(1 for r in successes if r.get("has_forbidden")),
            "avg_sources": round(statistics.mean([r.get("sources_count",0) for r in successes]) if successes else 0, 1),
            "avg_answer_len": round(statistics.mean([r.get("answer_len",0) for r in successes]) if successes else 0, 0),
        },
        "stability": {
            "rate_limit_429": sum(1 for r in errors if r.get("status") == 429),
            "server_errors_5xx": sum(1 for r in errors if isinstance(r.get("status"), int) and r["status"] >= 500),
        },
    }

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = OUT_DIR / f"report_{ts}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Per-question stats
    per_q = {}
    for r in successes:
        qid = r.get("qid","?")
        if qid not in per_q:
            per_q[qid] = {"count":0, "latencies":[], "fallback":0, "match":0, "match_n":0}
        per_q[qid]["count"] += 1
        per_q[qid]["latencies"].append(r["latency"])
        if r.get("fallback"): per_q[qid]["fallback"] += 1
        if r.get("keyword_match") is not None:
            per_q[qid]["match_n"] += 1
            if r["keyword_match"]: per_q[qid]["match"] += 1

    # HTML report
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>UTC Autotest {ts}</title>
<style>body{{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;background:#f8fafc;color:#0f172a}}
h1{{color:#0f294a}}h2{{color:#00828a;margin-top:2rem}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem}}
.card{{background:#fff;border-radius:8px;padding:1rem;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
.card .label{{font-size:.8rem;color:#64748b}}.card .value{{font-size:1.5rem;font-weight:bold}}
.good{{color:#059669}}.warn{{color:#f59e0b}}.bad{{color:#dc2626}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
th,td{{padding:.5rem .75rem;text-align:left;font-size:.85rem}}th{{background:#0f294a;color:#fff}}
tr:nth-child(even){{background:#f1f5f9}}
</style></head><body>
<h1>🧪 UTC Assistant Autotest Report</h1>
<p>{datetime.now().strftime('%d/%m/%Y %H:%M')} | {len(tokens)} users × {QUESTIONS_PER_USER} questions | {CONCURRENT} concurrent | {total_time:.0f}s</p>

<h2>📊 Performance</h2>
<div class="metrics">
<div class="card"><div class="label">P50 Latency</div><div class="value">{report['performance']['p50_latency']}s</div></div>
<div class="card"><div class="label">P95 Latency</div><div class="value">{report['performance']['p95_latency']}s</div></div>
<div class="card"><div class="label">Avg Latency</div><div class="value">{report['performance']['avg_latency']}s</div></div>
<div class="card"><div class="label">Error Rate</div><div class="value {'good' if report['performance']['error_rate']<.05 else 'warn'}">{report['performance']['error_rate']*100:.1f}%</div></div>
<div class="card"><div class="label">Throughput</div><div class="value">{report['performance']['throughput']} req/s</div></div>
<div class="card"><div class="label">Min/Max</div><div class="value">{report['performance']['min_latency']}/{report['performance']['max_latency']}s</div></div>
</div>

<h2>🎯 Quality</h2>
<div class="metrics">
<div class="card"><div class="label">Fallback Rate</div><div class="value {'good' if report['quality']['fallback_rate']<.15 else 'warn'}">{report['quality']['fallback_rate']*100:.1f}%</div></div>
<div class="card"><div class="label">Keyword Match</div><div class="value {'good' if report['quality']['keyword_match_rate']>.7 else 'warn'}">{report['quality']['keyword_match_rate']*100:.1f}%</div></div>
<div class="card"><div class="label">Length OK</div><div class="value">{report['quality']['length_ok_rate']*100:.1f}%</div></div>
<div class="card"><div class="label">Avg Sources</div><div class="value">{report['quality']['avg_sources']}</div></div>
<div class="card"><div class="label">Avg Answer Len</div><div class="value">{report['quality']['avg_answer_len']}c</div></div>
<div class="card"><div class="label">Forbidden Words</div><div class="value {'bad' if report['quality']['has_forbidden_count']>0 else 'good'}">{report['quality']['has_forbidden_count']}</div></div>
</div>

<h2>🔧 Stability</h2>
<div class="metrics">
<div class="card"><div class="label">Rate Limit 429</div><div class="value">{report['stability']['rate_limit_429']}</div></div>
<div class="card"><div class="label">Server 5xx</div><div class="value">{report['stability']['server_errors_5xx']}</div></div>
</div>

<h2>📋 Per-Question</h2>
<table><tr><th>ID</th><th>Topic</th><th>Question</th><th>Count</th><th>Avg Lat</th><th>Fallback%</th><th>Match%</th></tr>
"""
    for q in questions:
        qid = q["id"]
        stats = per_q.get(qid, {})
        c = stats.get("count", 0)
        avg_l = statistics.mean(stats["latencies"]) if stats.get("latencies") else 0
        fb = stats.get("fallback", 0)
        m = stats.get("match", 0)
        mn = stats.get("match_n", 1)
        html += f"<tr><td>{qid}</td><td>{q['topic']}</td><td>{q['question'][:60]}</td><td>{c}</td><td>{avg_l:.1f}s</td><td>{fb/max(1,c)*100:.0f}%</td><td>{m/max(1,mn)*100:.0f}%</td></tr>\n"
    html += "</table></body></html>"

    html_path = OUT_DIR / f"report_{ts}.html"
    with open(html_path, "w") as f:
        f.write(html)

    # Summary
    p = report["performance"]
    q = report["quality"]
    print(f"""
{'='*60}
SUMMARY
{'='*60}
Users: {len(tokens)} | Tasks: {completed} | Duration: {total_time:.0f}s
P50: {p['p50_latency']}s | P95: {p['p95_latency']}s | Avg: {p['avg_latency']}s
Error: {p['error_rate']*100:.1f}% | Throughput: {p['throughput']} req/s
Fallback: {q['fallback_rate']*100:.1f}% | Match: {q['keyword_match_rate']*100:.1f}% | LengthOK: {q['length_ok_rate']*100:.1f}%

Report: {report_path}
HTML:    {html_path}
""")

if __name__ == "__main__":
    run_test()

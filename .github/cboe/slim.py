# Lädt die verzögerten Optionsketten von CBOE und speichert eine schlanke Fassung für das TQI Terminal.
import json, os, re, time, urllib.request
SYMS = os.environ.get("SYMS", "IBIT SPY QQQ IWM _SPX _NDX MSTR COIN").split()
os.makedirs("out", exist_ok=True)
idx = {}
pat = re.compile(r"^([A-Z0-9]+?)(\d{6})([CP])(\d{8})$")
for s in SYMS:
    url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{s}.json"
    raw = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TQI Terminal data job)"})
            raw = json.load(urllib.request.urlopen(req, timeout=90))
            break
        except Exception as e:
            print("Fehler", s, attempt, e); time.sleep(5)
    if not raw:
        continue
    d = raw.get("data", {}) or {}
    spot = d.get("current_price") or d.get("close")
    rows = []
    for o in d.get("options", []) or []:
        m = pat.match(o.get("option", ""))
        if not m:
            continue
        root, ymd, cp, k = m.groups()
        K = int(k) / 1000
        if spot and not (0.5 * spot <= K <= 1.5 * spot):
            continue
        oi = int(o.get("open_interest") or 0); vol = int(o.get("volume") or 0)
        if not oi and not vol:
            continue
        r = lambda v, n: round(float(v or 0), n)
        rows.append([ymd, cp, K, oi, vol, r(o.get("iv"), 4), r(o.get("delta"), 4), r(o.get("gamma"), 6), r(o.get("vega"), 4),
                     r(o.get("theta"), 4), r(o.get("last_trade_price"), 2), r(o.get("bid"), 2), r(o.get("ask"), 2), root])
    name = s.strip("_")
    out = {"sym": name, "t": raw.get("timestamp"), "spot": spot, "chg": d.get("price_change"), "pct": d.get("price_change_percent"),
           "iv30": d.get("iv30"), "cols": ["exp", "cp", "k", "oi", "vol", "iv", "delta", "gamma", "vega", "theta", "last", "bid", "ask", "root"], "rows": rows}
    with open(f"out/{name}.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))
    idx[name] = {"t": out["t"], "spot": spot, "n": len(rows)}
    print(name, len(rows), "Optionen")
with open("out/index.json", "w") as f:
    json.dump({"t": int(time.time()), "syms": idx}, f, separators=(",", ":"))

# Lädt die verzögerten Optionsketten von CBOE und speichert eine schlanke Fassung für das TQI Terminal.
# Format: {"sym","t","spot","meta",{...},"exps":{"YYMMDD[A]":[[call(1/0), strike, oi, volumen, iv, delta, gamma, preis], ...]}}
# "A" am Verfall = AM-Abrechnung (SPX/NDX-Monatsoptionen), sonst Abrechnung zum Handelsschluss.
import json, os, re, time, urllib.request
SYMS = os.environ.get("SYMS", "IBIT SPY QQQ IWM _SPX _NDX MSTR COIN").split()
os.makedirs("out", exist_ok=True)
pat = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")
idx = {}
def num(v, n):
    try:
        x = round(float(v or 0), n)
        return int(x) if x == int(x) else x
    except Exception:
        return 0
for s in SYMS:
    name = s.strip("_")
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
    roots = {name: 0, name + "W": 0, name + "P": 0}
    am_roots = {"SPX", "NDX", "RUT", "XSP"} & {name}
    exps = {}
    n = 0
    for o in d.get("options", []) or []:
        m = pat.match(o.get("option", ""))
        if not m:
            continue
        root, ymd, cp, k = m.groups()
        if root not in roots:
            continue  # angepasste Kontrakte (z. B. nach Splits) auslassen
        K = int(k) / 1000
        if spot and not (0.6 * spot <= K <= 1.4 * spot):
            continue
        oi = int(o.get("open_interest") or 0); vol = int(o.get("volume") or 0)
        if not oi and not vol:
            continue
        bid, ask, last = float(o.get("bid") or 0), float(o.get("ask") or 0), float(o.get("last_trade_price") or 0)
        px = (bid + ask) / 2 if bid > 0 and ask > 0 else last
        key = ymd + ("A" if root in am_roots else "")
        exps.setdefault(key, []).append([1 if cp == "C" else 0, num(K, 3), oi, vol, num(o.get("iv"), 4), num(o.get("delta"), 4), num(o.get("gamma"), 6), num(px, 2)])
        n += 1
    meta = {k: v for k, v in d.items() if not isinstance(v, (list, dict))}
    out = {"sym": name, "t": raw.get("timestamp"), "spot": spot, "meta": meta, "exps": dict(sorted(exps.items()))}
    with open(f"out/{name}.json", "w") as f:
        json.dump(out, f, separators=(",", ":"))
    idx[name] = {"t": out["t"], "spot": spot, "n": n}
    print(name, n, "Optionen", len(exps), "Verfälle")
with open("out/index.json", "w") as f:
    json.dump({"t": int(time.time()), "syms": idx}, f, separators=(",", ":"))

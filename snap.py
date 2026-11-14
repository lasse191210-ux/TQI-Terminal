# Einmaliger Schnappschuss echter Deribit-Daten (BTC) für Screenshots des TQI Terminals
import json, time, urllib.request, os
B="https://www.deribit.com/api/v2/public/"
def get(m, **p):
    q="&".join(f"{k}={v}" for k,v in p.items())
    for a in range(3):
        try:
            r=json.load(urllib.request.urlopen(urllib.request.Request(B+m+"?"+q, headers={"User-Agent":"Mozilla/5.0"}), timeout=60))
            return r.get("result")
        except Exception as e:
            print("Fehler", m, e); time.sleep(2)
    return None
os.makedirs("out", exist_ok=True)
now=int(time.time()*1000); D=86400000; res={"t":now}
res["book_option"]=get("get_book_summary_by_currency",currency="BTC",kind="option")
res["book_future"]=get("get_book_summary_by_currency",currency="BTC",kind="future")
res["index"]=get("get_index_price",index_name="btc_usd")
T=[]; seen=set(); start=now-30*3600*1000
for g in range(120):
    r=get("get_last_trades_by_currency_and_time",currency="BTC",kind="option",start_timestamp=start,end_timestamp=now,count=1000,sorting="asc")
    if not r or not r.get("trades"): break
    for t in r["trades"]:
        if t["trade_id"] in seen: continue
        seen.add(t["trade_id"]); T.append({k:t.get(k) for k in ["trade_id","timestamp","instrument_name","direction","amount","price","index_price","iv","mark_price","block_trade_id","combo_id"]})
    if not r.get("has_more"): break
    last=r["trades"][-1]["timestamp"]; start= last+1 if last==start else last
res["trades"]=T
for rs,span in [("1",1000*60e3),("5",1000*5*60e3),("15",1000*15*60e3),("60",1000*60*60e3),("1D",1500*D)]:
    res["tv_"+rs]=get("get_tradingview_chart_data",instrument_name="BTC-PERPETUAL",start_timestamp=int(now-span),end_timestamp=now,resolution=rs)
res["dvol"]=get("get_volatility_index_data",currency="BTC",start_timestamp=now-365*D,end_timestamp=now,resolution="1D")
res["funding"]=get("get_funding_rate_history",instrument_name="BTC-PERPETUAL",start_timestamp=now-30*D,end_timestamp=now)
res["rfq"]=get("get_block_rfq_trades",currency="BTC",count=50)
try:
    res["bn_5m"]=json.load(urllib.request.urlopen("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=1500",timeout=30))
except Exception as e:
    print("Binance", e)
json.dump(res, open("out/deribit.json","w"), separators=(",",":"))
print("Trades", len(T), "Optionen", len(res["book_option"] or []))

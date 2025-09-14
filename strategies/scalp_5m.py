# shortened version: see previous message for full details
from __future__ import annotations
import math, pandas as pd, numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Literal, Tuple
try:
    from logging_setup import logger
except Exception:
    import logging; logging.basicConfig(level=logging.INFO); logger = logging.getLogger("5m-scalp")
Direction = Literal["long","short"]
@dataclass
class StrategyConfig:
    htf_ema_period:int=50; ema_fast:int=9; ema_slow:int=21; rsi_period:int=14; rsi_overbought:int=70; rsi_oversold:int=30
    vol_ma_period:int=20; swing_lookback:int=5; enable_session_filter:bool=True
    sessions_local:Tuple[Tuple[pd.Timestamp.time,pd.Timestamp.time],...]=((pd.Timestamp('2000-01-01T08:00').time(),pd.Timestamp('2000-01-01T11:30').time()),(pd.Timestamp('2000-01-01T14:30').time(),pd.Timestamp('2000-01-01T16:00').time()),)
    max_trades_per_day:int=10; account_balance:float=10000.0; risk_per_trade:float=0.01; rr:float=2.0; tick_size:float=0.0; min_pos_size:float=0.0; max_pos_size:float=float('inf')
def ema(s:pd.Series,p:int)->pd.Series: return s.ewm(span=p,adjust=False).mean()
def rsi(s:pd.Series,p:int=14)->pd.Series:
    d=s.diff(); g=(d.where(d>0,0.0)).rolling(p).mean(); l=(-d.where(d<0,0.0)).rolling(p).mean(); rs=g/(l.replace({0:np.nan})); r=100-(100/(1+rs)); return r.fillna(50.0)
def within_sessions(ts:pd.Timestamp,sessions)->bool:
    t=ts.time()
    for start,end in sessions:
        if start<=end:
            if start<=t<=end: return True
        else:
            if t>=start or t<=end: return True
    return False
def rolling_min(s:pd.Series,w:int)->pd.Series: return s.rolling(w).min()
def rolling_max(s:pd.Series,w:int)->pd.Series: return s.rolling(w).max()
def is_bull(df,i): 
    if i<1: return False
    c=df.iloc[i]; p=df.iloc[i-1]; return (c.close>c.open and p.close<p.open and c.close>=p.open and c.open<=p.close)
def is_bear(df,i):
    if i<1: return False
    c=df.iloc[i]; p=df.iloc[i-1]; return (c.close<c.open and p.close>p.open and c.close<=p.open and c.open>=p.close)
class Scalp5M:
    def __init__(self,cfg:StrategyConfig=StrategyConfig()): self.cfg=cfg
    def generate_signals(self,df_5m:pd.DataFrame,df_1h:pd.DataFrame)->List[Dict[str,Any]]:
        df5=df_5m.copy(); df1=df_1h.copy()
        df1["ema_htf"]=ema(df1["close"],self.cfg.htf_ema_period); df1["bias"]=np.where(df1["close"]>=df1["ema_htf"],"long","short")
        bias=df1["bias"].reindex(df5.index,method="ffill")
        df5["ema_fast"]=ema(df5["close"],self.cfg.ema_fast); df5["ema_slow"]=ema(df5["close"],self.cfg.ema_slow); df5["rsi"]=rsi(df5["close"],self.cfg.rsi_period); df5["vol_ma"]=df5["volume"].rolling(20).mean()
        df5["swing_low"]=rolling_min(df5["low"],self.cfg.swing_lookback); df5["swing_high"]=rolling_max(df5["high"],self.cfg.swing_lookback)
        out=[]; per_day={}
        for i in range(1,len(df5)):
            row=df5.iloc[i]; ts=df5.index[i]; dk=ts.strftime("%Y-%m-%d")
            if per_day.get(dk,0)>=self.cfg.max_trades_per_day: continue
            if self.cfg.enable_session_filter and not within_sessions(ts,self.cfg.sessions_local): continue
            b=bias.iloc[i]; vol_ok=True
            if not np.isnan(row["vol_ma"]): vol_ok=row["volume"]>=row["vol_ma"]
            ema_bull=row["ema_fast"]>=row["ema_slow"]; ema_bear=row["ema_fast"]<=row["ema_slow"]
            ema_cross_up=(df5["ema_fast"].iloc[i-1]<df5["ema_slow"].iloc[i-1]) and ema_bull
            ema_cross_dn=(df5["ema_fast"].iloc[i-1]>df5["ema_slow"].iloc[i-1]) and ema_bear
            rsi_long=(df5["rsi"].iloc[i-1]<=self.cfg.rsi_oversold) and (row["rsi"]>self.cfg.rsi_oversold)
            rsi_short=(df5["rsi"].iloc[i-1]>=self.cfg.rsi_overbought) and (row["rsi"]<self.cfg.rsi_overbought)
            price_above=row["close"]>=row["ema_slow"]; price_below=row["close"]<=row["ema_slow"]
            if b=="long" and vol_ok and (ema_cross_up or ema_bull) and rsi_long and is_bull(df5,i) and price_above:
                entry=float(row["close"]); sl=float(row["swing_low"] if not math.isnan(row["swing_low"]) else df5['low'].iloc[i-1]); 
                if sl>=entry: sl=min(sl,float(df5['low'].iloc[i-1]),entry-1e-8)
                tp=entry+self.cfg.rr*max(entry-sl,1e-8); size=self._pos(entry,sl)
                if size>0: out.append({"time":ts,"direction":"long","entry":entry,"sl":sl,"tp":tp,"size":size,"meta":{"bias":b,"rsi":float(row['rsi'])}}); per_day[dk]=per_day.get(dk,0)+1
            if b=="short" and vol_ok and (ema_cross_dn or ema_bear) and rsi_short and is_bear(df5,i) and price_below:
                entry=float(row["close"]); sl=float(row["swing_high"] if not math.isnan(row["swing_high"]) else df5['high'].iloc[i-1]); 
                if sl<=entry: sl=max(sl,float(df5['high'].iloc[i-1]),entry+1e-8)
                tp=entry-self.cfg.rr*max(sl-entry,1e-8); size=self._pos(entry,sl)
                if size>0: out.append({"time":ts,"direction":"short","entry":entry,"sl":sl,"tp":tp,"size":size,"meta":{"bias":b,"rsi":float(row['rsi'])}}); per_day[dk]=per_day.get(dk,0)+1
        return out
    def _pos(self,entry:float,sl:float)->float:
        risk=self.cfg.account_balance*self.cfg.risk_per_trade; stop=abs(entry-sl)
        if stop<=0: return 0.0
        size=risk/stop
        if self.cfg.tick_size>0:
            import math as m; size=m.floor(size/self.cfg.tick_size)*self.cfg.tick_size
        size=max(self.cfg.min_pos_size,min(size,self.cfg.max_pos_size))
        return float(size)

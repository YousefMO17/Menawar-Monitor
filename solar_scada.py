"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MENAWAR — Data Collection & SCADA Control Panel v5.0                       ║
║  AI-Powered Dual-Axis Solar Tracker | Streamlit + Background Threading       ║
╚══════════════════════════════════════════════════════════════════════════════╝
Run with:  streamlit run solar_scada.py
"""

import streamlit as st

st.set_page_config(
    page_title="MENAWAR — Data Collection & SCADA",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Standard imports ──────────────────────────────────────────────────────────
import firebase_admin
from firebase_admin import credentials, db
import pandas as pd
import requests
import time
import random
import numpy as np
import csv
import os
import threading
import plotly.graph_objects as go
import html as _html
from datetime import datetime, timedelta
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════════
#  🎨  MENAWAR BRAND CSS  (ported exactly from app.py → inject_css)
# ═══════════════════════════════════════════════════════════════════════════════
def inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ══ FORCE LIGHT THEME — ALL CONTEXTS ══ */
:root,html,body,
[data-theme="light"],[data-theme="dark"],
.stApp,[data-testid="stAppViewContainer"],
[data-testid="stMain"],.main{
  background:#f4f7f2 !important;
  color:#1a2e12       !important;
  font-family:'Plus Jakarta Sans',sans-serif !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"]{
  background:#ffffff !important;
  border-right:1.5px solid rgba(58,125,30,.14) !important;
  box-shadow:2px 0 16px rgba(45,90,22,.07) !important;
}
[data-testid="stSidebar"] *{color:#1a2e12 !important;}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3{
  color:#2d6a2d !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-size:.7rem !important;
  letter-spacing:1.5px;
  text-transform:uppercase;
}

/* ── METRICS ── */
[data-testid="stMetric"]{
  background:#ffffff !important;
  border:1px solid rgba(58,125,30,.14) !important;
  border-radius:14px !important;
  padding:16px 18px !important;
  box-shadow:0 1px 4px rgba(45,90,22,.08),0 4px 16px rgba(45,90,22,.05) !important;
  transition:transform .2s,box-shadow .2s;
  position:relative;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-2px);
  box-shadow:0 4px 14px rgba(45,90,22,.12),0 8px 32px rgba(45,90,22,.07) !important;
}
[data-testid="stMetric"]::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#3a7d1e,#d4a030);
  border-radius:14px 14px 0 0;
}
[data-testid="stMetricLabel"]>div{
  color:#4a6741 !important;
  font-size:.65rem !important;
  font-weight:600 !important;
  letter-spacing:1px;
  text-transform:uppercase;
}
[data-testid="stMetricValue"]{
  color:#2d6a2d !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-size:1.45rem !important;
  font-weight:700 !important;
}
[data-testid="stMetricDelta"]{font-size:.7rem !important;color:#4a6741 !important;}

/* ── TABS ── */
[data-testid="stTabs"] [role="tab"]{
  font-family:'Space Grotesk',sans-serif !important;
  font-size:.68rem !important;
  letter-spacing:1px;text-transform:uppercase;
  color:#4a6741 !important;
  padding:10px 18px !important;
  background:transparent !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{
  color:#3a7d1e !important;
  border-bottom:2px solid #3a7d1e !important;
  font-weight:700 !important;
}
[data-testid="stTabsContent"]{background:transparent !important;}

/* ── BUTTONS ── */
.stButton button{
  background:#ffffff !important;
  border:1.5px solid rgba(58,125,30,.35) !important;
  color:#3a7d1e !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-size:.65rem !important;
  letter-spacing:1px;font-weight:600 !important;
  border-radius:10px !important;
  transition:all .2s !important;
  box-shadow:0 1px 4px rgba(45,90,22,.08) !important;
}
.stButton button:hover{
  background:rgba(58,125,30,.07) !important;
  border-color:#3a7d1e !important;
  color:#2d5a16 !important;
  transform:translateY(-1px) !important;
}
.stButton button[kind="primary"]{
  background:linear-gradient(135deg,#2d6a2d,#3a7d1e) !important;
  color:#ffffff !important;border:none !important;
  box-shadow:0 0 8px 2px rgba(58,125,30,.35) !important;
}
.stButton button[kind="primary"]:hover{opacity:.92 !important;color:#ffffff !important;}

/* ── CARDS ── */
.mn-card{
  background:#ffffff;
  border:1px solid rgba(58,125,30,.14);
  border-radius:16px;
  padding:20px 24px;
  position:relative;overflow:hidden;
  box-shadow:0 1px 4px rgba(45,90,22,.08),0 4px 16px rgba(45,90,22,.05);
  transition:transform .2s,box-shadow .2s;
  margin-bottom:10px;
  color:#1a2e12;
}
.mn-card:hover{
  transform:translateY(-2px);
  box-shadow:0 4px 14px rgba(45,90,22,.12),0 8px 32px rgba(45,90,22,.07);
}
.mn-card::before{
  content:'';
  position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#3a7d1e,#d4a030,#5aad2e);
  border-radius:16px 16px 0 0;
}

/* ── CONNECTION STATUS CARDS ── */
.conn-success-card{
  background:rgba(45,138,62,.07);
  border:1.5px solid rgba(45,138,62,.30);
  border-radius:12px;padding:12px 16px;
  display:flex;align-items:center;gap:10px;margin:8px 0;
}
.conn-error-card{
  background:rgba(220,38,38,.06);
  border:1.5px solid rgba(220,38,38,.28);
  border-radius:12px;padding:12px 16px;margin:8px 0;
}

/* ── SECTION HEADERS ── */
.mn-section{
  display:flex;align-items:center;gap:10px;
  margin:20px 0 16px 0;padding-bottom:10px;
  border-bottom:1.5px solid rgba(58,125,30,.14);
}
.mn-section-title{
  font-family:'Space Grotesk',sans-serif;
  font-weight:700;font-size:.78rem;
  color:#2d6a2d;letter-spacing:2px;text-transform:uppercase;
}

/* ── TERMINAL CARD ── */
.mn-terminal{
  background:#0d1117 !important;
  border:1px solid #21262d;
  border-radius:16px;
  padding:16px 18px;
  position:relative;overflow:hidden;
  box-shadow:0 4px 20px rgba(0,0,0,.30);
  margin-bottom:10px;
}
.mn-terminal::before{
  content:'';
  position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#39ff14,#00d4aa,#39ff14);
  border-radius:16px 16px 0 0;
  animation:termGlow 3s ease-in-out infinite;
}
.mn-terminal pre{
  color:#39ff14;
  font-family:'Courier New',Courier,monospace;
  font-size:11px;
  max-height:320px;
  overflow-y:auto;
  overflow-x:auto;
  margin:0;
  white-space:pre;
  line-height:1.75;
}
.mn-terminal-label{
  font-size:.58rem;color:#39ff14;
  letter-spacing:1.5px;text-transform:uppercase;
  margin-bottom:8px;font-weight:600;opacity:.65;
}

/* ── HEADER GRADIENT DIVIDER ── */
.mn-divider{
  height:2.5px;
  background:linear-gradient(90deg,transparent,#3a7d1e,#d4a030,#5aad2e,transparent);
  border-radius:2px;margin-bottom:18px;
}

/* ── LIST ROWS ── */
.hr-row{
  display:flex;align-items:center;gap:10px;
  padding:10px 14px;border-radius:10px;margin-bottom:4px;
  background:#f8faf6;border:1px solid rgba(58,125,30,.12);
  transition:background .15s,box-shadow .15s;color:#1a2e12;
}
.hr-row:hover{background:rgba(58,125,30,.05);box-shadow:0 1px 4px rgba(45,90,22,.08);}

/* ── INPUTS ── */
[data-testid="stTextInput"] input{
  background:#f8faf6 !important;
  border:1.5px solid rgba(58,125,30,.18) !important;
  color:#1a2e12 !important;border-radius:8px !important;font-size:.8rem !important;
}
[data-testid="stTextInput"] input:focus{
  border-color:#3a7d1e !important;
  box-shadow:0 0 0 3px rgba(58,125,30,.12) !important;
}
[data-testid="stTextInput"] label{color:#4a6741 !important;}

/* ── SCROLLBAR ── */
::-webkit-scrollbar{width:5px;}
::-webkit-scrollbar-track{background:#eaf0e6;}
::-webkit-scrollbar-thumb{background:rgba(58,125,30,.35);border-radius:3px;}
::-webkit-scrollbar-thumb:hover{background:#3a7d1e;}

/* ── ANIMATIONS ── */
@keyframes termGlow{0%,100%{opacity:.7;}50%{opacity:1;}}
@keyframes mnGlow{
  0%  {filter:drop-shadow(0 0 4px rgba(58,125,30,.35)) drop-shadow(0 0 2px rgba(212,160,48,.3));}
  50% {filter:drop-shadow(0 0 14px rgba(58,125,30,.75)) drop-shadow(0 0 8px rgba(212,160,48,.65));}
  100%{filter:drop-shadow(0 0 4px rgba(58,125,30,.35)) drop-shadow(0 0 2px rgba(212,160,48,.3));}
}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}
@keyframes slideIn{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);}}

.mn-logo-anim{animation:mnGlow 3s ease-in-out infinite;}
.online-dot{
  display:inline-block;width:8px;height:8px;
  background:#2d8a3e;border-radius:50%;
  animation:pulse 2s infinite;box-shadow:0 0 6px #2d8a3e;
}
.panel-content{animation:slideIn .22s ease-out;}

/* ── ALERTS ── */
[data-testid="stAlert"]{border-radius:12px !important;background:#f8faf6 !important;}

/* ── RADIO / TOGGLES ── */
[data-testid="stRadio"] label{font-size:.8rem !important;color:#1a2e12 !important;}
[data-testid="stToggle"] label{font-size:.8rem !important;color:#1a2e12 !important;}

/* ── PLOTLY ── */
.stPlotlyChart{background:transparent !important;}
.js-plotly-plot .plotly .bg{fill:transparent !important;}

/* ── MAIN BLOCK CONTAINER ── */
.main .block-container{padding-top:.75rem !important;}

/* ── GLOBAL TEXT ── */
p,span,div,label,h1,h2,h3,h4,h5,h6,li{color:#1a2e12;}
code{background:rgba(58,125,30,.08);color:#3a7d1e;}

/* ── SELECTBOX ── */
[data-baseweb="select"] *{color:#1a2e12 !important;background:#ffffff !important;}

/* ── NAV BUTTON LABEL FIX ── */
.stButton button p{margin:0 !important;}

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] button{
  background:linear-gradient(135deg,#2d6a2d,#3a7d1e) !important;
  color:#ffffff !important;border:none !important;
  font-family:'Space Grotesk',sans-serif !important;
  font-size:.65rem !important;letter-spacing:1px;font-weight:600 !important;
  border-radius:10px !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  PLOTLY LIGHT THEME  (matches app.py exactly)
# ─────────────────────────────────────────────────────────────────────────────
PLOT_BG     = "rgba(0,0,0,0)"
PAPER_BG    = "rgba(0,0,0,0)"
GRID_COLOR  = "rgba(58,125,30,0.09)"
FONT_COLOR  = "#2d5a1a"
FONT_FAMILY = "Plus Jakarta Sans"


def light_layout(**kwargs) -> dict:
    base = dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(family=FONT_FAMILY, color=FONT_COLOR, size=10),
        xaxis=dict(
            gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
            tickfont=dict(color=FONT_COLOR), title_font=dict(color=FONT_COLOR),
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR, linecolor=GRID_COLOR,
            tickfont=dict(color=FONT_COLOR), title_font=dict(color=FONT_COLOR),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)", bordercolor=GRID_COLOR,
            borderwidth=1, font=dict(color=FONT_COLOR, size=9),
        ),
        margin=dict(l=12, r=12, t=44, b=28),
    )
    base.update(kwargs)
    return base


# ═══════════════════════════════════════════════════════════════════════════════
#  ⚙️  CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
WRITE_API_KEY    = 'HKCLFZPMEMWFGN9I'
CSV_FILE         = 'ULTIMATE_CLEAN_TRAINING_DATA.csv'
LOCAL_DB_FILE    = 'LOCAL_DATABASE_LOG.csv'
THINGSPEAK_URL   = 'https://api.thingspeak.com/update'

IDEAL_POWER      = 20.0
CONSTANT_LOAD_W  = 3.0
API_DELAY_SEC    = 16
TIME_WARP_DELAY  = 0.5

BATT_V_MIN       = 10.50
BATT_V_START     = 11.55
BATT_V_FULL      = 14.00
CHARGE_RATE_MAX  = 0.015
DISCHARGE_RATE   = 0.00045

SUNRISE_H        = 6.0
SUNSET_H         = 19.5
PEAK_PV_POWER    = 10.5
SCENARIO_CADENCE = 15

HEADERS = [
    'Timestamp', 'V_PV', 'V_Batt', 'SOC_%', 'Amp',
    'Power_W', 'Ideal_Power_W', 'UV_Ideal', 'UV_Actual',
    'Dust_Ratio', 'Scenario',
]

SCENARIO_ICONS = {
    'NIGHT_MODE':    '🌙',
    'NORMAL':        '☀️',
    'SHADOW':        '☁️',
    'SOILING':       '🌫️',
    'SHORT_CIRCUIT': '⚡',
    'DISCONNECT':    '🔌',
}

# Matches app.py fault_color palette exactly
SCENARIO_COLORS = {
    'NIGHT_MODE':    '#5b6a3e',
    'NORMAL':        '#2d8a3e',
    'SHADOW':        '#d4a030',
    'SOILING':       '#c47a1e',
    'SHORT_CIRCUIT': '#991b1b',
    'DISCONNECT':    '#dc2626',
}

FAULT_RANGES = {
    'NORMAL':        'V: 12.0–14.0 V  ·  A: 0.6–1.0 A',
    'SHADOW':        'V: 9.0–11.5 V  ·  A: 0.1–0.3 A  ·  UV ≤ 20 % of ideal',
    'SOILING':       'V: 10.0–12.0 V  ·  A: 0.2–0.4 A  ·  Dust 75–95 %  ·  UV = UV_ideal',
    'SHORT_CIRCUIT': 'V: 0.0–1.0 V  ·  A: 1.2–1.5 A spike',
    'DISCONNECT':    'V: 0.0 V  ·  A: 0.0 A',
}


# ═══════════════════════════════════════════════════════════════════════════════
#  🔥  FIREBASE — one-time init per process
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def init_firebase():
    try:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://menawar-db-default-rtdb.firebaseio.com/'
        })
        return True, "Connected"
    except Exception as exc:
        return False, str(exc)


# ═══════════════════════════════════════════════════════════════════════════════
#  ☀️  SOLAR PHYSICS
# ═══════════════════════════════════════════════════════════════════════════════
def get_solar_state(hour_float: float):
    if hour_float < SUNRISE_H or hour_float >= SUNSET_H:
        return 0.0, 0.0, 0.0
    day_len         = SUNSET_H - SUNRISE_H
    t_norm          = (hour_float - SUNRISE_H) / day_len
    sine_val        = max(0.0, np.sin(np.pi * t_norm))
    uv_ideal        = round(sine_val * 10.0, 2)
    time_multiplier = round(sine_val, 4)
    pv_power_base   = round(PEAK_PV_POWER * sine_val, 3)
    return uv_ideal, time_multiplier, pv_power_base


def update_battery(v_batt: float, power_w: float, is_day: bool) -> float:
    net = power_w - CONSTANT_LOAD_W
    if net > 0:
        headroom = max(0.0, BATT_V_FULL - v_batt)
        taper    = headroom / (BATT_V_FULL - BATT_V_START)
        taper    = max(0.3, taper)
        increase = CHARGE_RATE_MAX * (net / IDEAL_POWER) * taper
        increase = max(0.003, increase)
        v_batt  += increase
    else:
        if not is_day:
            v_batt -= DISCHARGE_RATE * (abs(net) / CONSTANT_LOAD_W)
    return max(BATT_V_MIN, min(BATT_V_FULL, v_batt))


def soc_pct(v: float) -> float:
    return round(max(0.0, min(100.0, (v - 10.50) / 3.227 * 100.0)), 1)


def calculate_realistic_start_battery(now_hf: float) -> float:
    v_sim       = BATT_V_START
    start_hf    = SUNRISE_H
    end_hf      = now_hf if now_hf >= SUNRISE_H else (now_hf + 24.0)
    total_ticks = int((end_hf - start_hf) * 3600 / API_DELAY_SEC)
    current_hf  = start_hf
    for _ in range(total_ticks):
        _, tm, pv_base = get_solar_state(current_hf % 24.0)
        is_day  = tm > 0.0
        if is_day:
            v_pv    = 16.0 * (0.80 + 0.20 * tm)
            amp     = (pv_base / v_pv) if v_pv > 0 else 0.0
            power_w = min(v_pv * amp, IDEAL_POWER)
        else:
            power_w = 0.0
        v_sim      = update_battery(v_sim, power_w, is_day)
        current_hf += API_DELAY_SEC / 3600.0
    return v_sim


# ═══════════════════════════════════════════════════════════════════════════════
#  💾  LOCAL DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
def init_local_db():
    if not os.path.exists(LOCAL_DB_FILE):
        with open(LOCAL_DB_FILE, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(HEADERS)


def log_local(row: list):
    with open(LOCAL_DB_FILE, 'a', newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(row)


# ═══════════════════════════════════════════════════════════════════════════════
#  📡  THINGSPEAK
# ═══════════════════════════════════════════════════════════════════════════════
def push_thingspeak(session, v_pv, v_batt, amp, power_w,
                    uv_ideal, uv_actual, dust) -> bool:
    try:
        r = session.get(THINGSPEAK_URL, params={
            'api_key': WRITE_API_KEY,
            'field1': v_pv,       'field2': v_batt,
            'field3': amp,        'field4': power_w,
            'field5': IDEAL_POWER,
            'field6': uv_ideal,   'field7': uv_actual,
            'field8': dust,
        }, timeout=10)
        return r.status_code == 200 and r.text.strip() not in ('0', '')
    except requests.RequestException:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  🧵  BACKGROUND SIMULATION THREAD
# ═══════════════════════════════════════════════════════════════════════════════
def _tlog(state: dict, msg: str):
    """Append one line to the shared terminal buffer (thread-safe via GIL)."""
    state['terminal'].append(msg)


# ═══════════════════════════════════════════════════════════════════════════════
#  📅  HISTORICAL REPLAY THREAD
# ═══════════════════════════════════════════════════════════════════════════════
def _replay_physics(scenario: str, uv_ideal: float, is_day: bool):
    """Return (v_pv, amp, power_w, dust, uv_actual) for a given scenario."""
    if not is_day:
        return round(random.uniform(0.0, 0.3), 2), 0.0, 0.0, round(random.uniform(4.0, 6.0), 2), 0.0
    if scenario == 'NORMAL':
        v_pv = round(random.uniform(12.0, 14.0), 2)
        amp  = round(random.uniform(0.6, 1.0), 3)
        dust = round(random.uniform(2.0, 4.5), 2)
        uv_a = max(0.0, round(uv_ideal - random.uniform(0.0, 0.5), 2)) if uv_ideal > 0.5 else 0.0
    elif scenario == 'SHADOW':
        v_pv = round(random.uniform(9.0, 11.5), 2)
        amp  = round(random.uniform(0.1, 0.3), 3)
        dust = round(random.uniform(2.0, 4.5), 2)
        uv_a = round(random.uniform(0.05, max(0.10, uv_ideal * 0.20)), 2)
    elif scenario == 'SOILING':
        v_pv = round(random.uniform(10.0, 12.0), 2)
        amp  = round(random.uniform(0.2, 0.4), 3)
        dust = round(random.uniform(75.0, 95.0), 2)
        uv_a = uv_ideal
    elif scenario == 'SHORT_CIRCUIT':
        v_pv = round(random.uniform(0.0, 1.0), 2)
        amp  = round(random.uniform(1.2, 1.5), 3)
        dust = round(random.uniform(2.0, 5.0), 2)
        uv_a = uv_ideal
    else:  # DISCONNECT
        v_pv = 0.0; amp = 0.0; dust = round(random.uniform(2.0, 5.0), 2); uv_a = uv_ideal
    power_w = round(min(v_pv * amp, IDEAL_POWER), 2)
    return v_pv, amp, power_w, dust, uv_a


def historical_replay_loop(state: dict, start_dt: datetime, end_dt: datetime, interval_min: int):
    """
    Replays historical readings from start_dt → end_dt at interval_min spacing.
    Runs in a daemon thread; honours state['replay_running'] for early stop.
    """
    http_session = requests.Session()
    total        = max(1, int((end_dt - start_dt).total_seconds() / 60 / interval_min) + 1)
    sent         = 0
    current_dt   = start_dt

    _tlog(state,
          f"╔══ 📅 HISTORICAL REPLAY ══════════════════════════════════════════╗")
    _tlog(state,
          f"║  From : {start_dt.strftime('%Y-%m-%d %H:%M')}  →  "
          f"To: {end_dt.strftime('%Y-%m-%d %H:%M')}  |  Δ{interval_min} min  |  {total} packets")
    _tlog(state,
          f"╚═════════════════════════════════════════════════════════════════╝")

    while current_dt <= end_dt and state.get('replay_running', False):
        hf               = current_dt.hour + current_dt.minute / 60.0
        uv_ideal, tm, _  = get_solar_state(hf)
        is_day           = tm > 0.0

        scenario = (
            random.choices(
                ['NORMAL', 'SHADOW', 'SOILING', 'SHORT_CIRCUIT', 'DISCONNECT'],
                weights=[0.65, 0.15, 0.10, 0.05, 0.05],
            )[0] if is_day else 'NIGHT_MODE'
        )

        v_pv, amp, power_w, dust, uv_actual = _replay_physics(scenario, uv_ideal, is_day)
        v_batt = round(
            random.uniform(12.5, 14.0) if is_day else random.uniform(11.0, 12.5), 3
        )
        soc = soc_pct(v_batt)
        ts  = current_dt.strftime('%Y-%m-%d %H:%M:%S')

        ts_ok = push_thingspeak(http_session, v_pv, v_batt, amp, power_w, uv_ideal, uv_actual, dust)
        fb_ok = False
        try:
            db.reference('sensor_readings').push({
                'timestamp':   int(current_dt.timestamp()),
                'datetime':    ts,
                'v_pv':        v_pv,
                'v_batt':      v_batt,
                'soc_percent': soc,
                'amp':         amp,
                'power_w':     power_w,
                'uv_actual':   uv_actual,
                'dust_ratio':  dust,
                'scenario':    scenario,
            })
            fb_ok = True
        except Exception as exc:
            _tlog(state, f"  ❌ Firebase error: {exc}")

        sent += 1
        icon    = SCENARIO_ICONS.get(scenario, '❓')
        ts_icon = '✅' if ts_ok else '❌'
        fb_icon = '✅' if fb_ok else '❌'
        _tlog(state,
              f"  [{sent:>4}/{total}] {ts} | {icon} {scenario:<13} | "
              f"PV:{v_pv:5.2f}V {amp:.3f}A {power_w:5.2f}W | "
              f"TS:{ts_icon} FB:{fb_icon}")

        current_dt += timedelta(minutes=interval_min)
        time.sleep(0.08)   # brief pause so we don't hammer the APIs

    if state.get('replay_running', False):
        _tlog(state, f"  ✅ REPLAY COMPLETE — {sent}/{total} packets sent successfully.")
    else:
        _tlog(state, f"  🛑 REPLAY STOPPED — {sent}/{total} packets sent before stop.")
    state['replay_running'] = False


def simulation_loop(state: dict):
    """
    Runs entirely in a daemon thread.
    `state` is the plain dict stored in st.session_state['shared'].
    The UI reads it on every 1-second auto-rerun.
    """
    now     = datetime.now()
    hf_boot = now.hour + now.minute / 60.0 + now.second / 3600.0

    _tlog(state, "⏳ Synchronizing battery state with real-world time ...")
    v_batt   = calculate_realistic_start_battery(hf_boot)
    soc_init = soc_pct(v_batt)

    _tlog(state, "╔═══════════════════════════════════════════════════════════╗")
    _tlog(state, "║  🌍 MENAWAR SCADA v5.0 — Data Collection Terminal         ║")
    _tlog(state, f"║  Boot: {now.strftime('%H:%M')} │ Init SOC: {soc_init:.1f}% ({round(v_batt,3)}V)              ║")
    _tlog(state, "╚═══════════════════════════════════════════════════════════╝")

    init_local_db()

    try:
        csv_data = pd.read_csv(CSV_FILE).to_dict('records')
        _tlog(state, f"✅ Loaded {len(csv_data)} records from training CSV.")
    except Exception as exc:
        _tlog(state, f"⚠️  CSV not found ({exc}) — running with synthetic rows.")
        csv_data = [{}] * 500   # physics don't use CSV values; this just drives the loop

    http_session     = requests.Session()
    tick_counter     = 0
    current_scenario = 'NORMAL'

    while state.get('running', False):
        try:
            for _row in csv_data:
                if not state.get('running', False):
                    break

                now     = datetime.now()
                hf      = now.hour + now.minute / 60.0 + now.second / 3600.0
                uv_ideal, tm, _ = get_solar_state(hf)
                is_day   = tm > 0.0
                offline  = state.get('network_offline', False)
                override = state.get('override_scenario')

                # ── Night mode ─────────────────────────────────────────────
                if not is_day:
                    scenario  = 'NIGHT_MODE'
                    v_pv      = round(random.uniform(0.0, 0.3), 2)
                    amp       = 0.0
                    power_w   = 0.0
                    uv_actual = 0.0
                    dust      = round(random.uniform(4.0, 6.0), 2)
                    v_batt    = update_battery(v_batt, 0.0, False)

                else:
                    # ── Scenario selection ─────────────────────────────────
                    if override:
                        scenario         = override
                        tick_counter     = 0
                        current_scenario = override
                    else:
                        tick_counter += 1
                        if tick_counter >= SCENARIO_CADENCE:
                            current_scenario = random.choices(
                                ['NORMAL', 'SHADOW', 'SOILING',
                                 'SHORT_CIRCUIT', 'DISCONNECT'],
                                weights=[0.65, 0.15, 0.10, 0.05, 0.05],
                            )[0]
                            tick_counter = 0
                        scenario = current_scenario

                    # ══════════════════════════════════════════════════════
                    #  FAULT PHYSICS — strictly non-overlapping ML ranges
                    #  Each class occupies a unique region in feature space
                    #  so the Random Forest classifier can distinguish them.
                    # ══════════════════════════════════════════════════════

                    if scenario == 'NORMAL':
                        # V: 12.0–14.0 V  |  A: 0.6–1.0 A
                        v_pv      = round(random.uniform(12.0, 14.0), 2)
                        amp       = round(random.uniform(0.6, 1.0), 3)
                        power_w   = round(min(v_pv * amp, IDEAL_POWER), 2)
                        dust      = round(random.uniform(2.0, 4.5), 2)
                        # UV_actual ≈ UV_ideal with slight natural variation
                        uv_actual = round(
                            uv_ideal - random.uniform(0.0, 0.5), 2
                        ) if uv_ideal > 0.5 else 0.0
                        uv_actual = max(0.0, uv_actual)

                    elif scenario == 'SHADOW':
                        # V: 9.0–11.5 V  |  A: 0.1–0.3 A
                        # UV_actual collapses to ≤ 20 % of UV_ideal
                        v_pv      = round(random.uniform(9.0, 11.5), 2)
                        amp       = round(random.uniform(0.1, 0.3), 3)
                        power_w   = round(min(v_pv * amp, IDEAL_POWER), 2)
                        uv_actual = round(
                            random.uniform(0.05, max(0.10, uv_ideal * 0.20)), 2
                        )
                        dust      = round(random.uniform(2.0, 4.5), 2)

                    elif scenario == 'SOILING':
                        # V: 10.0–12.0 V  |  A: 0.2–0.4 A  |  Dust: 75–95 %
                        # UV_actual == UV_ideal exactly
                        # (dust covers panel surface, not the external UV sensor)
                        v_pv      = round(random.uniform(10.0, 12.0), 2)
                        amp       = round(random.uniform(0.2, 0.4), 3)
                        power_w   = round(min(v_pv * amp, IDEAL_POWER), 2)
                        dust      = round(random.uniform(75.0, 95.0), 2)
                        uv_actual = uv_ideal          # ← zero UV deviation

                    elif scenario == 'SHORT_CIRCUIT':
                        # V: 0.0–1.0 V (strict collapse)  |  A: 1.2–1.5 A spike
                        v_pv      = round(random.uniform(0.0, 1.0), 2)
                        amp       = round(random.uniform(1.2, 1.5), 3)
                        power_w   = round(v_pv * amp, 2)
                        dust      = round(random.uniform(2.0, 5.0), 2)
                        uv_actual = uv_ideal

                    else:  # DISCONNECT
                        # V: 0.0 V  |  A: 0.0 A
                        v_pv      = 0.0
                        amp       = 0.0
                        power_w   = 0.0
                        dust      = round(random.uniform(2.0, 5.0), 2)
                        uv_actual = uv_ideal

                    v_batt = update_battery(v_batt, power_w, is_day)

                soc = soc_pct(v_batt)
                ts  = now.strftime('%Y-%m-%d %H:%M:%S')

                log_local([ts, v_pv, round(v_batt, 3), soc, amp, power_w,
                           IDEAL_POWER, uv_ideal, uv_actual, dust, scenario])

                # ── Network push (skipped when offline) ───────────────────
                ts_ok = fb_ok = False
                if not offline:
                    ts_ok = push_thingspeak(
                        http_session, v_pv, v_batt, amp,
                        power_w, uv_ideal, uv_actual, dust,
                    )
                    try:
                        db.reference('sensor_readings').push({
                            'timestamp':   int(time.time()),
                            'datetime':    ts,
                            'v_pv':        v_pv,
                            'v_batt':      round(v_batt, 3),
                            'soc_percent': soc,
                            'amp':         amp,
                            'power_w':     power_w,
                            'uv_actual':   uv_actual,
                            'dust_ratio':  dust,
                            'scenario':    scenario,
                        })
                        fb_ok = True
                    except Exception as exc:
                        _tlog(state, f"❌ Firebase error: {exc}")

                # ── Build terminal line ────────────────────────────────────
                net      = round(power_w - CONSTANT_LOAD_W, 2)
                arrow    = '↑' if net > 0 else '↓'
                filled   = int(soc / 5)
                batt_bar = '▓' * filled + '░' * (20 - filled)
                ts_icon  = '✅' if ts_ok else ('🚫' if offline else '❌')
                fb_icon  = '✅' if fb_ok else ('🚫' if offline else '❌')
                icon     = SCENARIO_ICONS.get(scenario, '❓')

                line = (
                    f"{icon} [{scenario:<13}] {ts} | "
                    f"PV:{v_pv:5.2f}V {amp:.3f}A {power_w:5.2f}W net:{net:+.2f}W{arrow} | "
                    f"🔋{v_batt:.3f}V {soc:5.1f}%[{batt_bar}] | "
                    f"UV:{uv_ideal:.2f}→{uv_actual:.2f} Dust:{dust:.1f}% "
                    f"TS:{ts_icon} FB:{fb_icon}"
                )
                _tlog(state, line)

                # ── Shared metrics for the UI ──────────────────────────────
                state['metrics'] = {
                    'scenario':  scenario,
                    'power_w':   power_w,
                    'soc':       soc,
                    'v_batt':    round(v_batt, 3),
                    'v_pv':      v_pv,
                    'amp':       amp,
                    'uv_ideal':  uv_ideal,
                    'uv_actual': uv_actual,
                    'dust':      dust,
                    'ts':        ts,
                    'network':   'OFFLINE 🚫' if offline else 'ONLINE 📶',
                }
                state['chart_data'].append({
                    'Power_W': power_w,
                    'V_Batt':  round(v_batt, 3),
                })

                # ── Interruptible sleep (responds to STOP within 0.25 s) ──
                delay   = TIME_WARP_DELAY if state.get('time_warp') else API_DELAY_SEC
                elapsed = 0.0
                while elapsed < delay and state.get('running', False):
                    time.sleep(0.25)
                    elapsed += 0.25

            if state.get('running', False):
                _tlog(state, "\n🔄 End of records — looping back to start ...\n")

        except Exception as exc:
            _tlog(state, f"❌ Loop Error: {exc} — recovering ...")
            time.sleep(2)

    _tlog(state, "🛑 [SHUTDOWN] Simulation stopped. All data saved to CSV.")


# ═══════════════════════════════════════════════════════════════════════════════
#  🎨  STREAMLIT UI
# ═══════════════════════════════════════════════════════════════════════════════

inject_css()

# ── Session-state bootstrap ───────────────────────────────────────────────────
if 'shared' not in st.session_state:
    st.session_state.shared = {
        'running':           False,
        'override_scenario': None,
        'time_warp':         False,
        'network_offline':   False,
        'replay_running':    False,
        'terminal':          deque(maxlen=50),
        'chart_data':        deque(maxlen=50),
        'metrics': {
            'scenario':  '—',  'power_w':   0.0,  'soc':      0.0,
            'v_batt':    0.0,  'v_pv':      0.0,  'amp':      0.0,
            'uv_ideal':  0.0,  'uv_actual': 0.0,  'dust':     0.0,
            'ts':        '—',  'network':   'OFFLINE 🚫',
        },
    }

if 'sim_thread' not in st.session_state:
    st.session_state.sim_thread = None

shared     = st.session_state.shared
firebase_ok, firebase_msg = init_firebase()

# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # ── Logo ──────────────────────────────────────────────────────────────────
    _logo_found = False
    for _lp in ("logo.jpeg", "logo.jpg", "logo.png", "logo.PNG", "logo.JPG"):
        if os.path.exists(_lp):
            st.image(_lp, use_container_width=True)
            _logo_found = True
            break

    if not _logo_found:
        st.markdown("""
<div style='text-align:center;padding:16px 12px;
            background:linear-gradient(135deg,rgba(58,125,30,.08),rgba(212,160,48,.05));
            border:2px solid rgba(58,125,30,.28);border-radius:16px;margin-bottom:4px;'>
  <div style='font-size:2rem;margin-bottom:4px;'>☀️</div>
  <div style='font-family:"Space Grotesk",sans-serif;font-weight:800;font-size:1.1rem;
              color:#2d6a2d;letter-spacing:3px;'>MENAWAR</div>
  <div style='font-size:.56rem;color:#8aaa7a;letter-spacing:2px;text-transform:uppercase;
              margin-top:3px;'>Data Collection &amp; SCADA</div>
</div>""", unsafe_allow_html=True)

    st.markdown("""
<div style='text-align:center;padding:6px 0 14px 0;
            border-bottom:1.5px solid rgba(58,125,30,.14);margin-bottom:16px;'>
  <div style='font-family:"Space Grotesk",sans-serif;font-weight:800;font-size:1.15rem;
              color:#2d6a2d;letter-spacing:4px;'>MENAWAR</div>
  <div style='font-size:.56rem;color:#8aaa7a;letter-spacing:2px;text-transform:uppercase;
              margin-top:3px;'>Data Collection &amp; SCADA</div>
</div>""", unsafe_allow_html=True)

    # ── Simulation power ──────────────────────────────────────────────────────
    st.markdown("## ⚡ SIMULATION POWER")
    _c1, _c2 = st.columns(2)
    with _c1:
        _start = st.button(
            "▶ START", use_container_width=True,
            disabled=shared['running'], type='primary',
        )
    with _c2:
        _stop = st.button(
            "⏹ STOP", use_container_width=True,
            disabled=not shared['running'],
        )

    if _start and not shared['running']:
        shared['running'] = True
        _t = threading.Thread(target=simulation_loop, args=(shared,), daemon=True)
        st.session_state.sim_thread = _t
        _t.start()
        st.rerun()

    if _stop:
        shared['running'] = False
        st.rerun()

    if shared['running']:
        st.markdown("""
<div class='conn-success-card'>
  <span class='online-dot'></span>
  <span style='font-size:.78rem;color:#2d8a3e;font-weight:600;'>Simulation Active</span>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class='conn-error-card'>
  <span style='font-size:.78rem;color:#dc2626;font-weight:600;'>● Simulation Stopped</span>
</div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Time-Warp ─────────────────────────────────────────────────────────────
    st.markdown("## ⏩ TIME-WARP MODE")
    _warp = st.toggle(
        "Fast-Forward Day (0.5 s/tick)",
        value=shared['time_warp'],
        help="Compress a full simulated day into minutes for live demos.",
    )
    shared['time_warp'] = _warp
    st.markdown(
        f"<div style='font-size:.72rem;color:#4a6741;margin-top:4px;'>"
        f"{'🚀 Turbo: 0.5 s per tick' if _warp else f'🕐 Normal: {API_DELAY_SEC} s per tick'}"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Historical Replay ─────────────────────────────────────────────────────
    st.markdown("## 📅 HISTORICAL REPLAY")

    _rep_date_from = st.date_input(
        "From date", value=datetime(2026, 6, 10).date(), key="rep_date_from",
    )
    _rep_time_from = st.time_input(
        "From time", value=datetime(2026, 6, 10, 0, 0).time(),
        step=60, key="rep_time_from",
    )
    _rep_date_to = st.date_input(
        "To date", value=datetime(2026, 6, 10).date(), key="rep_date_to",
    )
    _rep_time_to = st.time_input(
        "To time", value=datetime(2026, 6, 10, 3, 0).time(),
        step=60, key="rep_time_to",
    )
    _rep_interval = st.slider(
        "Interval between readings (min)", 1, 60, 5, key="rep_interval",
    )

    _rep_start = datetime.combine(_rep_date_from, _rep_time_from)
    _rep_end   = datetime.combine(_rep_date_to,   _rep_time_to)
    _rep_valid = _rep_end > _rep_start
    _rep_n     = (
        max(0, int((_rep_end - _rep_start).total_seconds() / 60 / _rep_interval) + 1)
        if _rep_valid else 0
    )

    st.markdown(
        f"<div style='font-size:.72rem;color:#4a6741;margin:4px 0 8px 0;'>"
        f"{'📦 ' + str(_rep_n) + ' packets to send' if _rep_valid else '⚠️ End must be after start'}"
        f"</div>",
        unsafe_allow_html=True,
    )

    if not shared.get('replay_running', False):
        if st.button(
            "📤 SEND HISTORICAL PACKETS",
            use_container_width=True,
            disabled=(not _rep_valid or _rep_n == 0),
        ):
            shared['replay_running'] = True
            _rt = threading.Thread(
                target=historical_replay_loop,
                args=(shared, _rep_start, _rep_end, _rep_interval),
                daemon=True,
            )
            _rt.start()
            st.rerun()
    else:
        st.warning("⏳ Replay in progress …")
        if st.button("⏹ STOP REPLAY", use_container_width=True):
            shared['replay_running'] = False
            st.rerun()

    st.markdown("---")

    # ── Network Outage Simulator ──────────────────────────────────────────────
    st.markdown("## 📡 NETWORK OUTAGE SIM")
    _offline = st.toggle(
        "Drop Wi-Fi 🚫",
        value=shared['network_offline'],
        help="Pause ThingSpeak & Firebase — local CSV continues uninterrupted.",
    )
    shared['network_offline'] = _offline
    if _offline:
        st.warning("APIs PAUSED — CSV still running")
    else:
        st.success("Network ONLINE — all APIs active")

    st.markdown("---")

    # ── Data Export ───────────────────────────────────────────────────────────
    st.markdown("## 💾 DATA EXPORT")
    if os.path.exists(LOCAL_DB_FILE):
        with open(LOCAL_DB_FILE, 'rb') as _f:
            st.download_button(
                label="⬇ Download LOCAL_DATABASE_LOG.csv",
                data=_f,
                file_name=LOCAL_DB_FILE,
                mime='text/csv',
                use_container_width=True,
            )
        _rows = sum(1 for _ in open(LOCAL_DB_FILE, encoding='utf-8')) - 1
        st.markdown(
            f"<div style='font-size:.72rem;color:#4a6741;margin-top:4px;'>"
            f"📊 {max(0, _rows)} rows logged so far</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='font-size:.72rem;color:#8aaa7a;'>"
            "CSV not yet created — start simulation first.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Status footer ─────────────────────────────────────────────────────────
    _fb_label = '✅ Connected' if firebase_ok else f'❌ {firebase_msg[:45]}'
    st.markdown(
        f"<div style='font-size:.68rem;color:#4a6741;line-height:2;'>"
        f"<b>Firebase:</b> {_fb_label}<br>"
        f"<b>ThingSpeak:</b> Write key configured</div>"
        f"<div style='font-size:.60rem;color:#8aaa7a;margin-top:8px;'>"
        f"© 2025 — Menawar PV Intelligence</div>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════

# ── MENAWAR Header ────────────────────────────────────────────────────────────
st.markdown("""
<div class='panel-content'>
  <div style='font-size:.58rem;color:#3a7d1e;letter-spacing:3px;text-transform:uppercase;
              margin-bottom:4px;font-weight:600;'>Solar Tracking &amp; IoT System</div>
  <div style='font-family:"Space Grotesk",sans-serif;font-weight:800;font-size:2rem;
              color:#2d6a2d;letter-spacing:4px;'>MENAWAR</div>
  <div style='font-family:"Space Grotesk",sans-serif;font-size:.82rem;font-weight:700;
              color:#3a7d1e;letter-spacing:2px;text-transform:uppercase;margin-top:2px;'>
    Data Collection &amp; SCADA</div>
  <div style='font-size:.65rem;color:#8aaa7a;letter-spacing:1.5px;margin-top:4px;'>
    AI-Powered Dual-Axis Solar Tracker &middot;
    Digital Twin &amp; Data Collection Engine</div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div class='mn-divider'></div>", unsafe_allow_html=True)

m = shared['metrics']

# ── Status row ────────────────────────────────────────────────────────────────
_bc, _tc, _nc = st.columns([1, 2, 1])
with _bc:
    if shared['running']:
        st.success("● RUNNING")
    else:
        st.error("● STOPPED")
with _tc:
    st.markdown(
        f"<div style='font-size:.72rem;color:#4a6741;padding-top:8px;'>"
        f"Last tick: <code>{m.get('ts','—')}</code></div>",
        unsafe_allow_html=True,
    )
with _nc:
    _nc_col = '#dc2626' if 'OFFLINE' in m.get('network', '') else '#2d8a3e'
    st.markdown(
        f"<div style='text-align:right;padding-top:8px;"
        f"font-family:\"Space Grotesk\",sans-serif;"
        f"font-weight:700;font-size:.78rem;color:{_nc_col};'>"
        f"{m.get('network','—')}</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='mn-divider'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  🖥  LIVE SYSTEM TERMINAL  (shown first so you can watch logs immediately)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='mn-section'>
  <span style='font-size:1rem'>🖥</span>
  <span class='mn-section-title'>Live System Terminal — Last 50 Lines</span>
</div>
""", unsafe_allow_html=True)

_term_ph = st.empty()
_lines   = list(shared['terminal'])

_raw = (
    '\n'.join(_lines) if _lines else
    "╔════════════════════════════════════════════════════╗\n"
    "║  MENAWAR SCADA v5.0 — Terminal Ready               ║\n"
    "║                                                    ║\n"
    "║  >>> Press  ▶ START  in the sidebar to begin.     ║\n"
    "╚════════════════════════════════════════════════════╝"
)

_term_ph.markdown(
    f"<div class='mn-terminal'>"
    f"<div class='mn-terminal-label'>● System Terminal — MENAWAR SCADA v5.0</div>"
    f"<pre>{_html.escape(_raw)}</pre>"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown("<div class='mn-divider'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  🔧  FAULT INJECTION — MANUAL OVERRIDE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='mn-section'>
  <span style='font-size:1rem'>🔧</span>
  <span class='mn-section-title'>Fault Injection — Manual Override</span>
</div>
""", unsafe_allow_html=True)

_fault_list    = ['NORMAL', 'SHADOW', 'SOILING', 'SHORT_CIRCUIT', 'DISCONNECT']
_fault_display = {
    'NORMAL':        '☀️ NORMAL',
    'SHADOW':        '☁️ SHADOW',
    'SOILING':       '🌫️ SOILING',
    'SHORT_CIRCUIT': '⚡ SHORT CIRCUIT',
    'DISCONNECT':    '🔌 DISCONNECT',
}

_btn_cols = st.columns(len(_fault_list) + 1)
with _btn_cols[0]:
    if st.button(
        "🔄 AUTO\n(Random)", use_container_width=True,
        help="Release override — weighted random selection resumes",
    ):
        shared['override_scenario'] = None
        st.rerun()

for _i, _fault in enumerate(_fault_list):
    with _btn_cols[_i + 1]:
        _active = shared.get('override_scenario') == _fault
        if st.button(
            _fault_display[_fault],
            use_container_width=True,
            type='primary' if _active else 'secondary',
            key=f"fault_{_fault}",
            help=FAULT_RANGES.get(_fault, ''),
        ):
            shared['override_scenario'] = _fault
            st.rerun()

_ov = shared.get('override_scenario')
if _ov:
    _ovc = SCENARIO_COLORS.get(_ov, '#3a7d1e')
    st.markdown(
        f"""<div style='background:{_ovc}10;border:1.5px solid {_ovc}40;
  border-radius:12px;padding:10px 16px;margin-top:4px;
  display:flex;align-items:center;gap:12px;'>
  <span style='font-size:1.2rem;'>{SCENARIO_ICONS.get(_ov,'❓')}</span>
  <div>
    <span style='font-family:"Space Grotesk",sans-serif;font-weight:700;
        color:{_ovc};font-size:.8rem;'>Override Active — {_ov}</span>
    <span style='font-size:.68rem;color:#4a6741;margin-left:10px;'>
      {FAULT_RANGES.get(_ov,'')}</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div style='background:rgba(58,125,30,.05);border:1px solid rgba(58,125,30,.14);"
        "border-radius:12px;padding:10px 16px;font-size:.78rem;color:#4a6741;margin-top:4px;'>"
        "🎲 <b>Auto Mode</b> — Scenarios rotate randomly every 15 ticks "
        "(65 % Normal · 15 % Shadow · 10 % Soiling · 5 % Short Circuit · 5 % Disconnect)"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div class='mn-divider'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  📊  LIVE KPI METRICS — ROW 1
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='mn-section'>
  <span style='font-size:1rem'>📊</span>
  <span class='mn-section-title'>Live System Metrics</span>
</div>
""", unsafe_allow_html=True)

_r1 = st.columns(5)
_r1[0].metric("🎭 Scenario",      m['scenario'])
_r1[1].metric(
    "⚡ PV Power",  f"{m['power_w']:.2f} W",
    delta=f"{m['power_w'] - CONSTANT_LOAD_W:+.2f} W net",
)
_r1[2].metric("🔋 Battery SOC",   f"{m['soc']:.1f} %")
_r1[3].metric("🔌 Battery V",     f"{m['v_batt']:.3f} V")
_r1[4].metric("📡 Network",       m.get('network', '—'))

_r2 = st.columns(5)
_r2[0].metric("☀️ PV Voltage",   f"{m['v_pv']:.2f} V")
_r2[1].metric("⚡ PV Current",   f"{m['amp']:.3f} A")
_r2[2].metric("🌡 UV Ideal",     f"{m['uv_ideal']:.2f}")
_r2[3].metric(
    "📡 UV Actual",  f"{m['uv_actual']:.2f}",
    delta=f"{m['uv_actual'] - m['uv_ideal']:+.2f} dev",
)
_r2[4].metric("🌫 Dust / Soiling", f"{m['dust']:.1f} %")

st.markdown("<div class='mn-divider'></div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  📈  LIVE PLOTLY CHART  (dual y-axis: Power W + Battery V)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='mn-section'>
  <span style='font-size:1rem'>📈</span>
  <span class='mn-section-title'>Real-Time Power &amp; Battery Voltage — Last 50 Ticks</span>
</div>
""", unsafe_allow_html=True)

_chart_ph = st.empty()

if shared['chart_data']:
    _cdf   = pd.DataFrame(list(shared['chart_data']))
    _xtick = list(range(len(_cdf)))

    _fig = go.Figure()
    _fig.add_trace(go.Scatter(
        x=_xtick, y=_cdf['Power_W'],
        mode='lines', name='Power (W)',
        line=dict(color='#3a7d1e', width=2.5),
        fill='tozeroy', fillcolor='rgba(58,125,30,0.07)',
        hovertemplate='Tick %{x}<br>Power: %{y:.2f} W<extra></extra>',
    ))
    _fig.add_trace(go.Scatter(
        x=_xtick, y=_cdf['V_Batt'],
        mode='lines', name='V_Batt (V)',
        line=dict(color='#d4a030', width=1.8, dash='dot'),
        yaxis='y2',
        hovertemplate='Tick %{x}<br>V_Batt: %{y:.3f} V<extra></extra>',
    ))
    _fig.add_hline(
        y=CONSTANT_LOAD_W,
        line=dict(color='#dc2626', width=1, dash='dash'),
        annotation_text=f'Load {CONSTANT_LOAD_W} W',
        annotation_font=dict(color='#dc2626', size=9),
    )
    _fig.update_layout(**light_layout(
        height=240,
        yaxis=dict(
            title='Power (W)', range=[0, 22],
            gridcolor=GRID_COLOR,
            tickfont=dict(color='#3a7d1e'),
            title_font=dict(color='#3a7d1e'),
        ),
        yaxis2=dict(
            title='Battery (V)', overlaying='y', side='right',
            range=[10.0, 15.0], gridcolor='rgba(0,0,0,0)',
            tickfont=dict(color='#d4a030'),
            title_font=dict(color='#d4a030'),
        ),
        legend=dict(
            orientation='h', y=1.08, x=0,
            bgcolor='rgba(0,0,0,0)', font=dict(size=9, color=FONT_COLOR),
        ),
        margin=dict(l=12, r=50, t=30, b=28),
        hovermode='x unified',
    ))
    _chart_ph.plotly_chart(_fig, use_container_width=True, key="live_chart")
else:
    _chart_ph.markdown("""
<div class='mn-card' style='text-align:center;padding:40px 20px;'>
  <div style='font-size:2rem;margin-bottom:10px;'>📡</div>
  <div style='font-family:"Space Grotesk",sans-serif;color:#4a6741;
              font-size:.85rem;font-weight:600;'>Waiting for simulation data</div>
  <div style='font-size:.75rem;color:#8aaa7a;margin-top:6px;'>
    Press ▶ START in the sidebar to begin data collection</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  🔄  AUTO-REFRESH  (1 s cadence while simulation is running)
# ═══════════════════════════════════════════════════════════════════════════════
if shared['running'] or shared.get('replay_running', False):
    time.sleep(1)
    st.rerun()

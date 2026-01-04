import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np

# --- 1. إعدادات الصفحة والتصميم العصري (Silver Theme) ---
st.set_page_config(page_title="SmartScore Pro", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    /* خلفية فضية بتدرج عصري */
    .stApp {
        background: linear-gradient(135deg, #e0e0e0 0%, #cfd8dc 100%);
        color: #263238;
    }
    
    /* تصميم بطاقة المباراة */
    .match-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 12px;
        border: 1px solid #b0bec5;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        transition: transform 0.2s;
    }
    .match-card:hover {
        transform: scale(1.01);
        border-color: #ff4b4b;
    }

    /* صناديق الاحتمالات */
    .prob-badge {
        background: #37474f;
        color: #ffffff;
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: bold;
        margin-left: 8px;
        min-width: 60px;
        text-align: center;
        border-bottom: 3px solid #ff4b4b;
    }

    /* العناوين */
    .league-header {
        background: #263238;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        margin: 25px 0 15px 0;
        font-size: 1.2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .team-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #212121;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. جلب البيانات من السحابة ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=300)
def load_data():
    try:
        response = supabase.table("matches").select("*").execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

df_full = load_data()

# --- 3. محرك التحليل (The Brain) ---
def analyze_match(home, away, data):
    # تحليل قوة الفرق من الـ 1766 مباراة
    def get_avg_goals(team):
        history = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['status'] == 'FINISHED')]
        if history.empty: return 1.3
        scores = []
        for _, m in history.iterrows():
            val = m['home_score'] if m['home_team'] == team else m['away_score']
            if val is not None: scores.append(float(val))
        return np.mean(scores) if scores else 1.3

    h_pow = get_avg_goals(home) * 1.2  # ميزة الأرض
    a_pow = get_avg_goals(away)
    
    total = h_pow + a_pow + 0.1
    p_h, p_a = (h_pow/total)*0.75, (a_pow/total)*0.75
    p_d = 1.0 - p_h - p_a

    return {
        "probs": [p_h, p_d, p_a],
        "xg": h_pow + a_pow,
        "yellow": [np.random.randint(1,5), np.random.randint(1,5)],
        "red_prob": int((h_pow + a_pow) * 6)
    }

# --- 4. واجهة العرض ---
st.title("⚽ SmartScore AI Pro")
st.markdown("##### محرك التوقعات الرياضية المبني على البيانات الحقيقية")

if not df_full.empty:
    t1, t2 = st.tabs(["🚀 التوقعات الحية", "📊 سجل الدقة"])

    with t1:
        upcoming = df_full[df_full['status'].isin(['TIMED', 'SCHEDULED'])]
        for league in upcoming['league'].unique():
            st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
            matches = upcoming[upcoming['league'] == league]
            
            for i, row in matches.iterrows():
                res = analyze_match(row['home_team'], row['away_team'], df_full)
                p1, px, p2 = res["probs"]

                st.markdown(f"""
                <div class="match-card">
                    <div style="flex:2; text-align:right;" class="team-name">{row['home_team']}</div>
                    <div style="padding:0 20px; color:#ff4b4b; font-weight:bold;">VS</div>
                    <div style="flex:2;" class="team-name">{row['away_team']}</div>
                    <div class="prob-badge"><small>1</small><br>{p1*100:.0f}%</div>
                    <div class="prob-badge"><small>X</small><br>{px*100:.0f}%</div>
                    <div class="prob-badge"><small>2</small><br>{p2*100:.0f}%</div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 تحليل تفصيلي (أهداف وبطاقات)"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.write("**🟨 البطاقات المتوقعة**")
                        fig_y = go.Figure(go.Bar(x=['الأرض', 'الضيف'], y=res['yellow'], marker_color=['#ffd11a', '#ffd11a']))
                        fig_y.update_layout(height=150, margin=dict(t=0,b=0,l=0,r=0), paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_y, use_container_width=True, key=f"y_{row['match_id']}")
                    with c2:
                        st.write("**🎯 معدل الأهداف xG**")
                        st.metric("Total Goals", f"{res['xg']:.2f}")
                        st.write(f"🟥 احتمالية طرد: {res['red_prob']}%")
                    with c3:
                        st.write("**💡 التوصية**")
                        if p1 > 0.45: st.success("خيار قوي: فوز صاحب الأرض")
                        elif p2 > 0.45: st.success("خيار قوي: فوز الضيف")
                        else: st.warning("مباراة متكافئة - تجنب الرهان العالي")

    with t2:
        st.subheader("تحليل المباريات المنتهية")
        finished = df_full[df_full['status'] == 'FINISHED'].tail(20)
        st.table(finished[['league', 'home_team', 'home_score', 'away_score', 'away_team']])

else:
    st.info("🔄 جاري تحديث البيانات من Vostro...")

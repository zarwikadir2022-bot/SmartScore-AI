import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات الصفحة والتصميم العصري (Silver Theme) ---
st.set_page_config(page_title="SmartScore Pro AI", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #e0e0e0 0%, #cfd8dc 100%);
        color: #263238;
    }
    .match-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 12px;
        border: 1px solid #b0bec5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .prob-badge {
        background: #37474f;
        color: #ffffff;
        padding: 8px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        min-width: 65px;
        border-bottom: 3px solid #ff4b4b;
    }
    .league-header {
        background: #263238;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط بالسحابة ---
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

# --- 3. محرك التحليل الإحصائي (Poisson Distribution) ---
def get_advanced_analysis(home, away, data):
    def get_avg(team):
        hist = data[((data['home_team'] == team) | (data['away_team'] == team)) & (data['status'] == 'FINISHED')]
        if hist.empty: return 1.2
        scores = [m['home_score'] if m['home_team'] == team else m['away_score'] for _, m in hist.iterrows() if m['home_score'] is not None]
        return np.mean(scores) if scores else 1.2

    h_exp = get_avg(home) * 1.10 # ميزة الأرض
    a_exp = get_avg(away)
    
    # حساب احتمالات عدد الأهداف (0, 1, 2, 3, 4+) باستخدام توزيع بواسون
    def goal_dist(lambda_val):
        dist = [poisson.pmf(i, lambda_val) for i in range(4)]
        dist.append(1 - sum(dist)) # احتمالية 4 أهداف أو أكثر
        return [round(p * 100, 1) for p in dist]

    h_goals_prob = goal_dist(h_exp)
    a_goals_prob = goal_dist(a_exp)
    
    # احتمالات الفوز
    total = h_exp + a_exp + 0.1
    p1, p2 = (h_exp/total)*0.78, (a_exp/total)*0.78
    px = 1.0 - p1 - p2

    return {
        "win_probs": [p1, px, p2],
        "h_dist": h_goals_prob,
        "a_dist": a_goals_prob,
        "xg": h_exp + a_exp,
        "yellow": [np.random.randint(1,5), np.random.randint(1,5)],
        "red_prob": int((h_exp + a_exp) * 7)
    }

# --- 4. واجهة العرض ---
st.title("⚽ SmartScore AI Pro")

if not df_full.empty:
    tab1, tab2 = st.tabs(["🎯 التوقعات الذكية", "🕰️ السجل التاريخي"])

    with tab1:
        upcoming = df_full[df_full['status'].isin(['TIMED', 'SCHEDULED'])]
        for league in upcoming['league'].unique():
            st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
            for i, row in upcoming[upcoming['league'] == league].iterrows():
                res = get_advanced_analysis(row['home_team'], row['away_team'], df_full)
                p1, px, p2 = res["win_probs"]

                # بطاقة المباراة الرئيسية
                st.markdown(f"""
                <div class="match-card">
                    <div style="display:flex; align-items:center; justify-content:space-between;">
                        <div style="flex:2; text-align:right; font-size:1.2rem;"><b>{row['home_team']}</b></div>
                        <div style="flex:1; text-align:center; color:#ff4b4b; font-weight:bold;">VS</div>
                        <div style="flex:2; text-align:left; font-size:1.2rem;"><b>{row['away_team']}</b></div>
                        <div style="display:flex; gap:5px;">
                            <div class="prob-badge"><small>1</small><br>{p1*100:.0f}%</div>
                            <div class="prob-badge"><small>X</small><br>{px*100:.0f}%</div>
                            <div class="prob-badge"><small>2</small><br>{p2*100:.0f}%</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # التحليل المعمق (الأهداف، البطاقات، الطرد)
                with st.expander(f"📊 تفاصيل التوقع: {row['home_team']} vs {row['away_team']}"):
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.write("**⚽ أهداف الفريقين (%)**")
                        categories = ['0', '1', '2', '3', '4+']
                        fig_goals = go.Figure(data=[
                            go.Bar(name=row['home_team'], x=categories, y=res['h_dist'], marker_color='#37474f'),
                            go.Bar(name=row['away_team'], x=categories, y=res['a_dist'], marker_color='#ff4b4b')
                        ])
                        fig_goals.update_layout(barmode='group', height=200, margin=dict(t=0,b=0,l=0,r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig_goals, use_container_width=True, key=f"goals_{row['match_id']}")

                    with c2:
                        st.write("**🟨 البطاقات الصفراء**")
                        fig_y = go.Figure(go.Bar(x=['الأرض', 'الضيف'], y=res['yellow'], marker_color='#ffd11a'))
                        fig_y.update_layout(height=180, margin=dict(t=0,b=0,l=0,r=0))
                        st.plotly_chart(fig_y, use_container_width=True, key=f"y_{row['match_id']}")

                    with c3:
                        st.write("**🛡️ احتمالية الطرد (🟥)**")
                        st.markdown(f"<h2 style='text-align:center; color:#d32f2f;'>{res['red_prob']}%</h2>", unsafe_allow_html=True)
                        st.write(f"**إجمالي الأهداف المتوقع:** {res['xg']:.2f}")
                        st.info("💡 نصيحة: " + ("فوز الأرض" if p1 > p2 else "فوز الضيف"))

    with tab2:
        finished = df_full[df_full['status'] == 'FINISHED'].tail(50)
        st.dataframe(finished[['league', 'home_team', 'home_score', 'away_score', 'away_team']], use_container_width=True)

else:
    st.warning("⚠️ لا توجد بيانات حالياً. تأكد من تشغيل سكريبت الرفع.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات التصميم الفضي العصري ---
st.set_page_config(page_title="SmartScore Pro AI", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #e0e0e0 0%, #bdc3c7 100%); color: #2c3e50; }
    .match-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #95a5a6; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .prob-badge { background: #34495e; color: #ffffff; padding: 8px; border-radius: 8px; font-weight: bold; text-align: center; min-width: 60px; border-bottom: 3px solid #e74c3c; line-height: 1.2; }
    .match-tag { font-weight: bold; padding: 4px 10px; border-radius: 5px; font-size: 14px; }
    .tag-success { background: #e8f5e9; color: #2e7d32; border: 1px solid #2e7d32; }
    .tag-fail { background: #ffebee; color: #c62828; border: 1px solid #c62828; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الاتصال بـ Supabase ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=300)
def load_data():
    try:
        response = supabase.table("matches").select("*").execute()
        data = pd.DataFrame(response.data)
        if not data.empty: data['status_upper'] = data['status'].str.upper()
        return data
    except: return pd.DataFrame()

df_full = load_data()

# --- 3. محرك التحليل والمقارنة ---
def get_analysis(home, away, data):
    def get_avg(team):
        hist = data[((data['home_team'] == team) | (data['away_team'] == team)) & 
                    ((data['status_upper'] == 'FINISHED') | (data['home_score'].notnull()))]
        if hist.empty: return 1.25
        scores = [m['home_score'] if m['home_team'] == team else m['away_score'] for _, m in hist.iterrows() if m['home_score'] is not None]
        return np.mean(scores) if scores else 1.25

    h_exp = get_avg(home) * 1.15
    a_exp = get_avg(away)
    
    # حساب الاحتمالات
    total = h_exp + a_exp + 0.1
    p1, p2 = (h_exp/total)*0.78, (a_exp/total)*0.78
    px = 1.0 - p1 - p2
    
    # تحديد التوقع
    if p1 > px and p1 > p2: pred = "فوز الأرض"
    elif p2 > px and p2 > p1: pred = "فوز الضيف"
    else: pred = "تعادل"

    return {
        "win_probs": [p1, px, p2],
        "prediction": pred,
        "xg": h_exp + a_exp,
        "h_dist": [round(poisson.pmf(i, h_exp)*100, 1) for i in range(4)] + [round((1-poisson.cdf(3, h_exp))*100, 1)],
        "a_dist": [round(poisson.pmf(i, a_exp)*100, 1) for i in range(4)] + [round((1-poisson.cdf(3, a_exp))*100, 1)],
        "yellow": [np.random.randint(1,5), np.random.randint(1,5)],
        "red_prob": int((h_exp + a_exp) * 6.5)
    }

# --- 4. العرض الرئيسي ---
st.title("⚽ SmartScore Pro AI")

if not df_full.empty:
    tab1, tab2 = st.tabs(["🚀 التوقعات الحية", "🕰️ سجل الدقة التاريخي"])

    with tab1:
        upcoming = df_full[df_full['status_upper'].isin(['TIMED', 'SCHEDULED', 'POSTPONED', 'IN_PLAY'])]
        if upcoming.empty:
            st.info("🔄 لا توجد مباريات قادمة. تفقد سجل النتائج.")
        else:
            leagues = sorted(upcoming['league'].unique())
            sel_leagues = st.sidebar.multiselect("🌍 اختر الدوري:", leagues, default=leagues[:2])
            for league in upcoming[upcoming['league'].isin(sel_leagues)]['league'].unique():
                st.markdown(f'<div style="background:#2c3e50; color:white; padding:10px; border-radius:10px; margin:15px 0;">🏆 {league}</div>', unsafe_allow_html=True)
                for i, row in upcoming[upcoming['league'] == league].iterrows():
                    res = get_analysis(row['home_team'], row['away_team'], df_full)
                    p1, px, p2 = res["win_probs"]
                    
                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:2; text-align:right;"><b>{row['home_team']}</b></div>
                            <div style="flex:1; text-align:center; color:#e74c3c;">VS</div>
                            <div style="flex:2; text-align:left;"><b>{row['away_team']}</b></div>
                            <div style="display:flex; gap:5px;">
                                <div class="prob-badge"><small>1</small><br>{p1*100:.0f}%</div>
                                <div class="prob-badge"><small>X</small><br>{px*100:.0f}%</div>
                                <div class="prob-badge"><small>2</small><br>{p2*100:.0f}%</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📊 تفاصيل التوقع"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write("**⚽ توزيع الأهداف (%)**")
                            fig = go.Figure(data=[go.Bar(name='الأرض', x=['0','1','2','3','4+'], y=res['h_dist'], marker_color='#34495e'),
                                                  go.Bar(name='الضيف', x=['0','1','2','3','4+'], y=res['a_dist'], marker_color='#e74c3c')])
                            fig.update_layout(barmode='group', height=180, margin=dict(t=0,b=0,l=0,r=0), legend=dict(orientation="h", y=1.2))
                            st.plotly_chart(fig, use_container_width=True, key=f"g_{row['match_id']}")
                        with c2:
                            st.write("**🟨 البطاقات والـ xG**")
                            st.metric("إجمالي الأهداف xG", f"{res['xg']:.2f}")
                            st.write(f"نسبة الطرد 🟥: {res['red_prob']}%")
                        with c3:
                            st.write("**💡 التوصية**")
                            st.info(f"النتيجة المرجحة: {res['prediction']}")

    with tab2:
        st.subheader("📊 مقارنة دقة الخوارزمية مع الواقع")
        finished = df_full[(df_full['status_upper'] == 'FINISHED') | (df_full['home_score'].notnull())].tail(40)
        for _, row in finished.iterrows():
            res = get_analysis(row['home_team'], row['away_team'], df_full)
            # النتيجة الحقيقية
            if row['home_score'] > row['away_score']: actual = "فوز الأرض"
            elif row['away_score'] > row['home_score']: actual = "فوز الضيف"
            else: actual = "تعادل"
            
            is_match = res['prediction'] == actual
            tag_class = "tag-success" if is_match else "tag-fail"
            tag_text = "✅ مطابق" if is_match else "❌ غير مطابق"

            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; margin-bottom:8px; border-left:5px solid {'#2e7d32' if is_match else '#c62828'};">
                <b>{row['league']}</b>: {row['home_team']} {row['home_score']} - {row['away_score']} {row['away_team']} 
                <br> <small>توقع الخوارزمية: {res['prediction']} | </small> <span class="match-tag {tag_class}">{tag_text}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("⚠️ فشل في تحميل البيانات.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np
from scipy.stats import poisson

# --- 1. إعدادات التصميم الاحترافي (Silver UI) ---
st.set_page_config(page_title="SmartScore Pro AI", layout="wide", page_icon="⚽")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #e0e0e0 0%, #bdc3c7 100%); color: #2c3e50; }
    .match-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #95a5a6; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    .prob-badge { background: #34495e; color: #ffffff; padding: 8px; border-radius: 8px; font-weight: bold; text-align: center; min-width: 65px; border-bottom: 3px solid #e74c3c; }
    .league-header { background: #2c3e50; color: #ecf0f1; padding: 12px 20px; border-radius: 10px; margin: 25px 0 10px 0; font-weight: bold; }
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
        if not data.empty:
            data['status_upper'] = data['status'].str.upper()
            data['home_score'] = pd.to_numeric(data['home_score'], errors='coerce')
            data['away_score'] = pd.to_numeric(data['away_score'], errors='coerce')
        return data
    except:
        return pd.DataFrame()

df_full = load_data()

# --- 3. محرك التوقعات المطور (Algorithm v2.0 - Accuracy Focus) ---
def get_analysis(home, away, data):
    finished = data[(data['status_upper'] == 'FINISHED') & (data['home_score'].notnull())]
    
    if finished.empty:
        return {"win_probs": [0.33, 0.34, 0.33], "prediction": "تعادل", "xg": 0, "h_dist": [0]*5, "a_dist": [0]*5, "yellow": [2,2], "red_prob": 5}

    # حساب معايير الدوري
    avg_h_g = finished['home_score'].mean()
    avg_a_g = finished['away_score'].mean()

    def get_team_metrics(team):
        team_data = finished[(finished['home_team'] == team) | (finished['away_team'] == team)].head(15)
        if team_data.empty: return 1.0, 1.0
        
        # قوة الهجوم: أهداف الفريق مقارنة بمتوسط الدوري
        goals_scored = team_data.apply(lambda x: x['home_score'] if x['home_team'] == team else x['away_score'], axis=1).mean()
        offense = goals_scored / ((avg_h_g + avg_a_g) / 2)
        
        # قوة الدفاع: الأهداف التي استقبلها مقارنة بمتوسط الدوري (كلما قل الرقم كان أفضل)
        goals_conceded = team_data.apply(lambda x: x['away_score'] if x['home_team'] == team else x['home_score'], axis=1).mean()
        defense = goals_conceded / ((avg_h_g + avg_a_g) / 2)
        
        return offense, defense

    h_off, h_def = get_team_metrics(home)
    a_off, a_def = get_team_metrics(away)

    # حساب الأهداف المتوقعة (xG) بناءً على تضارب القوى
    h_exp = h_off * a_def * avg_h_g * 1.12 # +12% ميزة الأرض
    a_exp = a_off * h_def * avg_a_g

    # مصفوفة الاحتمالات لنتائج دقيقة
    max_g = 6
    h_probs = [poisson.pmf(i, h_exp) for i in range(max_g)]
    a_probs = [poisson.pmf(i, a_exp) for i in range(max_g)]
    prob_matrix = np.outer(h_probs, a_probs)

    p1 = np.sum(np.tril(prob_matrix, -1)) # فوز الأرض
    px = np.sum(np.diag(prob_matrix))    # تعادل
    p2 = np.sum(np.triu(prob_matrix, 1))  # فوز الضيف

    # تطبيع النسب لتساوي 100%
    total = p1 + px + p2
    p1, px, p2 = p1/total, px/total, p2/total

    if p1 > px and p1 > p2: pred = "فوز الأرض"
    elif p2 > px and p2 > p1: pred = "فوز الضيف"
    else: pred = "تعادل"

    return {
        "win_probs": [p1, px, p2],
        "prediction": pred,
        "xg": h_exp + a_exp,
        "h_dist": [round(p*100, 1) for p in h_probs[:5]],
        "a_dist": [round(p*100, 1) for p in a_probs[:5]],
        "yellow": [np.random.randint(1,5), np.random.randint(1,5)],
        "red_prob": int((h_exp + a_exp) * 5.2)
    }

# --- 4. واجهة المستخدم ---
st.title("⚽ SmartScore Pro AI")

if not df_full.empty:
    tab1, tab2 = st.tabs(["🚀 التوقعات الذكية", "📊 سجل الدقة"])

    with tab1:
        upcoming = df_full[df_full['status_upper'].isin(['TIMED', 'SCHEDULED', 'IN_PLAY'])]
        if upcoming.empty:
            st.info("🔄 لا توجد مباريات قادمة حالياً.")
        else:
            for league in sorted(upcoming['league'].unique()):
                st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
                for _, row in upcoming[upcoming['league'] == league].iterrows():
                    res = get_analysis(row['home_team'], row['away_team'], df_full)
                    p1, px, p2 = res["win_probs"]

                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:2; text-align:right; font-weight:bold;">{row['home_team']}</div>
                            <div style="flex:1; text-align:center; color:#e74c3c; font-weight:bold;">VS</div>
                            <div style="flex:2; text-align:left; font-weight:bold;">{row['away_team']}</div>
                            <div style="display:flex; gap:5px;">
                                <div class="prob-badge">1<br>{p1*100:.0f}%</div>
                                <div class="prob-badge">X<br>{px*100:.0f}%</div>
                                <div class="prob-badge">2<br>{p2*100:.0f}%</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("📊 تحليل البيانات العميقة"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write("**⚽ احتمالية الأهداف**")
                            fig = go.Figure(data=[go.Bar(name='الأرض', x=['0','1','2','3','4+'], y=res['h_dist'], marker_color='#34495e'),
                                                  go.Bar(name='الضيف', x=['0','1','2','3','4+'], y=res['a_dist'], marker_color='#e74c3c')])
                            fig.update_layout(barmode='group', height=160, margin=dict(t=0,b=0,l=0,r=0), showlegend=False)
                            st.plotly_chart(fig, use_container_width=True)
                        with c2:
                            st.write("**🟨 البطاقات المتوقعة**")
                            st.write(f"الأرض: {'🟡' * res['yellow'][0]}")
                            st.write(f"الضيف: {'🟡' * res['yellow'][1]}")
                            st.write(f"نسبة الطرد 🟥: **{res['red_prob']}%**")
                        with c3:
                            st.write("**🎯 ملخص التوقع**")
                            st.metric("Total xG", f"{res['xg']:.2f}")
                            st.success(f"التوقع النهائي: {res['prediction']}")

    with tab2:
        st.subheader("📊 فحص جودة التوقعات")
        # عرض المباريات المنتهية التي تم تحديثها من السيرفر
        history = df_full[(df_full['status_upper'] == 'FINISHED') & 
                          (df_full['home_score'] + df_full['away_score'] >= 0)].sort_values('id', ascending=False).head(50)
        
        for _, row in history.iterrows():
            res = get_analysis(row['home_team'], row['away_team'], df_full)
            if row['home_score'] > row['away_score']: actual = "فوز الأرض"
            elif row['away_score'] > row['home_score']: actual = "فوز الضيف"
            else: actual = "تعادل"
            
            is_match = (res['prediction'] == actual)
            color = "#27ae60" if is_match else "#e74c3c"

            st.markdown(f"""
            <div style="background:white; padding:12px; border-radius:10px; margin-bottom:10px; border-right: 10px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <div style="font-size:0.8rem; color:gray;">{row['league']}</div>
                <div style="text-align:center; font-weight:bold;">
                    {row['home_team']} {int(row['home_score'])} - {int(row['away_score'])} {row['away_team']}
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:0.9rem;">
                    <span>توقعنا: <b>{res['prediction']}</b></span>
                    <span style="color:{color}; font-weight:bold;">{'✅ مطابق' if is_match else '❌ غير مطابق'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.error("⚠️ خطأ في الاتصال بقاعدة البيانات.")

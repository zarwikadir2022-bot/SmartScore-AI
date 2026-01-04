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
    /* خلفية فضية لؤلؤية */
    .stApp { background: linear-gradient(135deg, #e0e0e0 0%, #bdc3c7 100%); color: #2c3e50; }
    
    /* بطاقة المباراة القادمة */
    .match-card { background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #95a5a6; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    
    /* صناديق الاحتمالات */
    .prob-badge { background: #34495e; color: #ffffff; padding: 8px; border-radius: 8px; font-weight: bold; text-align: center; min-width: 60px; border-bottom: 3px solid #e74c3c; line-height: 1.2; }
    
    /* عناوين الدوريات */
    .league-header { background: #2c3e50; color: #ecf0f1; padding: 12px 20px; border-radius: 10px; margin: 20px 0 10px 0; font-weight: bold; }
    
    /* بطاقات السجل التاريخي */
    .history-card { padding:15px; border-radius:12px; margin-bottom:10px; border-width: 2px; border-style: solid; }
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
        return data
    except:
        return pd.DataFrame()

df_full = load_data()

# --- 3. محرك التحليل الإحصائي (توزيع بواسون والمقارنة) ---
def get_analysis(home, away, data):
    def get_avg(team):
        hist = data[((data['home_team'] == team) | (data['away_team'] == team)) & 
                    ((data['status_upper'] == 'FINISHED') | (data['home_score'].notnull()))]
        if hist.empty: return 1.25
        scores = [m['home_score'] if m['home_team'] == team else m['away_score'] for _, m in hist.iterrows() if m['home_score'] is not None]
        return np.mean(scores) if scores else 1.25

    h_exp = get_avg(home) * 1.15 # ميزة الأرض
    a_exp = get_avg(away)
    
    # احتمالات الفوز
    total = h_exp + a_exp + 0.1
    p1, p2 = (h_exp / total) * 0.78, (a_exp / total) * 0.78
    px = 1.0 - p1 - p2
    
    # التوقع النهائي
    if p1 > px and p1 > p2: prediction = "فوز الأرض"
    elif p2 > px and p2 > p1: prediction = "فوز الضيف"
    else: prediction = "تعادل"

    return {
        "win_probs": [p1, px, p2],
        "prediction": prediction,
        "xg": h_exp + a_exp,
        "h_dist": [round(poisson.pmf(i, h_exp)*100, 1) for i in range(4)] + [round((1-poisson.cdf(3, h_exp))*100, 1)],
        "a_dist": [round(poisson.pmf(i, a_exp)*100, 1) for i in range(4)] + [round((1-poisson.cdf(3, a_exp))*100, 1)],
        "yellow": [np.random.randint(1,5), np.random.randint(1,5)],
        "red_prob": int((h_exp + a_exp) * 6.5)
    }

# --- 4. واجهة العرض الرئيسية ---
st.title("⚽ SmartScore Pro AI")

if not df_full.empty:
    tab1, tab2 = st.tabs(["🚀 التوقعات الحية", "📊 سجل الدقة التاريخي"])

    with tab1:
        # فلاتر الدوريات
        upcoming_statuses = ['TIMED', 'SCHEDULED', 'POSTPONED', 'IN_PLAY']
        upcoming = df_full[df_full['status_upper'].isin(upcoming_statuses)]
        
        if upcoming.empty:
            st.info("🔄 لا توجد مباريات قادمة حالياً.")
        else:
            leagues = sorted(upcoming['league'].unique())
            sel_leagues = st.sidebar.multiselect("🌍 اختر الدوريات:", leagues, default=leagues[:2])
            
            for league in upcoming[upcoming['league'].isin(sel_leagues)]['league'].unique():
                st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
                for i, row in upcoming[upcoming['league'] == league].iterrows():
                    res = get_analysis(row['home_team'], row['away_team'], df_full)
                    p1, px, p2 = res["win_probs"]

                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:2; text-align:right; font-weight:bold;">{row['home_team']}</div>
                            <div style="flex:1; text-align:center; color:#e74c3c; font-weight:bold;">VS</div>
                            <div style="flex:2; text-align:left; font-weight:bold;">{row['away_team']}</div>
                            <div style="display:flex; gap:5px;">
                                <div class="prob-badge"><small>1</small><br>{p1*100:.0f}%</div>
                                <div class="prob-badge"><small>X</small><br>{px*100:.0f}%</div>
                                <div class="prob-badge"><small>2</small><br>{p2*100:.0f}%</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("📊 تفاصيل التحليل"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.write("**⚽ توزيع الأهداف (%)**")
                            fig = go.Figure(data=[
                                go.Bar(name='الأرض', x=['0','1','2','3','4+'], y=res['h_dist'], marker_color='#34495e'),
                                go.Bar(name='الضيف', x=['0','1','2','3','4+'], y=res['a_dist'], marker_color='#e74c3c')
                            ])
                            fig.update_layout(barmode='group', height=180, margin=dict(t=0,b=0,l=0,r=0), legend=dict(orientation="h", y=1.2))
                            st.plotly_chart(fig, use_container_width=True, key=f"g_{row['match_id']}")
                        with c2:
                            st.write("**🟨 البطاقات الصفراء**")
                            fig_y = go.Figure(go.Bar(x=['الأرض', 'الضيف'], y=res['yellow'], marker_color='#f1c40f'))
                            fig_y.update_layout(height=180, margin=dict(t=0,b=0,l=0,r=0))
                            st.plotly_chart(fig_y, use_container_width=True, key=f"y_{row['match_id']}")
                        with c3:
                            st.write("**🛡️ توقعات إضافية**")
                            st.metric("Total xG", f"{res['xg']:.2f}")
                            st.write(f"نسبة الطرد 🟥: **{res['red_prob']}%**")
                            st.info(f"التوقع: {res['prediction']}")

    with tab2:
        st.subheader("📊 مقارنة دقة الخوارزمية مع النتائج الحقيقية")
        finished = df_full[(df_full['status_upper'] == 'FINISHED') | (df_full['home_score'].notnull())].sort_values('id', ascending=False).head(40)
        
        if finished.empty:
            st.warning("⚠️ لا توجد نتائج منتهية بعد.")
        else:
            for _, row in finished.iterrows():
                res = get_analysis(row['home_team'], row['away_team'], df_full)
                
                # تحديد النتيجة الحقيقية
                if row['home_score'] > row['away_score']: actual = "فوز الأرض"
                elif row['away_score'] > row['home_score']: actual = "فوز الضيف"
                else: actual = "تعادل"
                
                is_match = (res['prediction'] == actual)
                border = "#27ae60" if is_match else "#e74c3c"
                bg = "#f1fcf4" if is_match else "#fef1f1"

                st.markdown(f"""
                <div style="background:{bg}; padding:15px; border-radius:12px; margin-bottom:10px; border: 2px solid {border};">
                    <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                        <b>{row['league']}</b> <span>{row['status']}</span>
                    </div>
                    <div style="text-align:center; font-size:1.2rem; margin:10px 0;">
                        {row['home_team']} <b>{row['home_score']} - {row['away_score']}</b> {row['away_team']}
                    </div>
                    <div style="border-top:1px solid #ddd; padding-top:8px; display:flex; justify-content:space-between; font-size:0.9rem;">
                        <div>توقع النظام: <b>{res['prediction']}</b></div>
                        <div style="font-weight:bold; color:{border};">{'✅ مطابق' if is_match else '❌ غير مطابق'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
else:
    st.error("⚠️ فشل تحميل البيانات من السحابة.")

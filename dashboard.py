import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from supabase import create_client, Client
import numpy as np

# --- إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="SmartScore Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #f8f9fa; color: #2c3e50; }
    .league-header { background: white; padding: 12px; border-radius: 8px; border-right: 6px solid #ff4b4b; margin: 20px 0; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .match-row { background: white; padding: 15px; border-radius: 12px; margin-bottom: 5px; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.02); }
    .prob-box { background: #FFE0B2; color: #E65100; padding: 6px 12px; border-radius: 8px; font-weight: bold; text-align: center; margin-left: 10px; border: 1px solid #FFCC80; min-width: 65px; }
    .team-logo { width: 30px; height: 30px; margin: 0 10px; }
    .badge { background: #f1f3f5; padding: 4px 10px; border-radius: 5px; font-size: 12px; margin: 2px; border: 1px solid #dee2e6; color: #555; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- محرك التوقعات المدمج (Statistical Engine) ---
def calculate_advanced_stats(home_team, away_team):
    # نستخدم "بصمة" اسم الفريقين لتوليد أرقام إحصائية مستقرة (حتى نربطها كلياً بقاعدة البيانات)
    seed = abs(hash(home_team + away_team)) % 1000
    np.random.seed(seed)
    
    # توقعات الأهداف (Poisson-like)
    exp_goals = 2.0 + (seed % 150) / 100
    p_h, p_a = 0.4, 0.3
    p_d = 1.0 - p_h - p_a
    
    # توقعات البطاقات (بناءً على حدة المباراة الافتراضية)
    yellow_cards = {
        "0-2": np.random.randint(20, 40),
        "3-5": np.random.randint(40, 70),
        "6+": np.random.randint(5, 15)
    }
    red_prob = np.random.randint(5, 25)
    
    # النتائج المرجحة
    top_scores = [
        {"score": "1-0", "prob": 12.5},
        {"score": "2-1", "prob": 10.2},
        {"score": "1-1", "prob": 9.8}
    ]
    
    return {
        "win_probs": [p_h, p_d, p_a],
        "yellow_dist": yellow_cards,
        "red_prob": red_prob,
        "expected_goals": exp_goals,
        "top_scores": top_scores
    }

# --- الربط بالسحابة ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=600)
def load_matches():
    response = supabase.table("matches").select("*").execute()
    return pd.DataFrame(response.data)

df = load_matches()

if not df.empty:
    st.title("⚽ SmartScore Pro | مركز التحليل المتقدم")
    
    selected_leagues = st.sidebar.multiselect("اختر الدوري:", df['league'].unique(), default=df['league'].unique()[:2])
    filtered_df = df[df['league'].isin(selected_leagues)]

    for league in filtered_df['league'].unique():
        st.markdown(f'<div class="league-header">🏆 {league}</div>', unsafe_allow_html=True)
        
        for i, row in filtered_df[filtered_df['league'] == league].reset_index().iterrows():
            stats = calculate_advanced_stats(row['home_team'], row['away_team'])
            p_h, p_d, p_a = stats["win_probs"]

            # سطر المباراة الرئيسي
            st.markdown(f"""
            <div class="match-row">
                <div style="flex: 2; text-align: right; font-weight: bold;">{row['home_team']} <img src="{row['home_crest']}" class="team-logo"></div>
                <div style="color: #bdc3c7; font-weight: bold; padding: 0 15px;">VS</div>
                <div style="flex: 2; font-weight: bold;"><img src="{row['away_crest']}" class="team-logo"> {row['away_team']}</div>
                <div style="display: flex;">
                    <div class="prob-box">1<br>{p_h*100:.0f}%</div>
                    <div class="prob-box">X<br>{p_d*100:.0f}%</div>
                    <div class="prob-box">2<br>{p_a*100:.0f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- استعادة قسم التفاصيل (البطاقات والأهداف) ---
            with st.expander(f"📊 تحليل معمق: {row['home_team']} vs {row['away_team']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write("**🟨 البطاقات الصفراء**")
                    y_data = stats["yellow_dist"]
                    fig_y = go.Figure(go.Bar(x=list(y_data.keys()), y=list(y_data.values()), marker_color='#ffd11a'))
                    fig_y.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_y, use_container_width=True, key=f"y_{i}_{row['match_id']}")

                with col2:
                    st.write("**🟥 طرد محتمل**")
                    st.error(f"نسبة الطرد: {stats['red_prob']}%")
                    st.write("**🎯 النتائج المرجحة**")
                    for sc in stats["top_scores"]:
                        st.markdown(f'<span class="badge">{sc["score"]} ({sc["prob"]}%)</span>', unsafe_allow_html=True)

                with col3:
                    st.write("**💡 إجمالي الأهداف**")
                    st.info(f"المتوقع: {stats['expected_goals']:.2f}")
                    # رسم بياني صغير للأهداف
                    fig_g = go.Figure(go.Indicator(mode = "gauge+number", value = stats['expected_goals'], 
                                      gauge = {'axis': {'range': [0, 5]}, 'bar': {'color': "#ff4b4b"}}))
                    fig_g.update_layout(height=180, margin=dict(t=5,b=5,l=5,r=5))
                    st.plotly_chart(fig_g, use_container_width=True, key=f"g_{i}_{row['match_id']}")

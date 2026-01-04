import psycopg2
import math
from math import exp

DB_PARAMS = {"host": "localhost", "dbname": "smartscore_db", "user": "postgres", "password": "123456"}

def poisson_probability(lmbda, k):
    if lmbda <= 0: return 1.0 if k == 0 else 0.0
    return (exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

def predict_match_detailed(home_team, away_team):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    # معدلات افتراضية (تستخدم كمرجع)
    avg_yellow = 4.2
    avg_red = 0.22

    # جلب إحصائيات الأهداف
    def get_stats(team):
        cur.execute("SELECT AVG(home_score), AVG(away_score) FROM matches WHERE home_team=%s AND status='FINISHED'", (team,))
        h = cur.fetchone()
        cur.execute("SELECT AVG(away_score), AVG(home_score) FROM matches WHERE away_team=%s AND status='FINISHED'", (team,))
        a = cur.fetchone()
        return float(h[0] or 1.4), float(h[1] or 1.2), float(a[0] or 1.1), float(a[1] or 1.3)

    h_s, h_c, a_s, a_c = get_stats(home_team)[0], get_stats(home_team)[1], get_stats(away_team)[2], get_stats(away_team)[3]
    
    # حساب Lambda للأهداف
    l_h = max(0.1, (h_s / 1.5) * (a_c / 1.5) * 1.5)
    l_a = max(0.1, (a_s / 1.2) * (h_c / 1.2) * 1.2)

    # احتمالات 1-X-2
    p_h, p_d, p_a = 0, 0, 0
    scores = []
    for i in range(6):
        for j in range(6):
            p = poisson_probability(l_h, i) * poisson_probability(l_a, j)
            if i > j: p_h += p
            elif i == j: p_d += p
            else: p_a += p
            if i < 4 and j < 4: scores.append({"score": f"{i}-{j}", "prob": p * 100})

    # تجهيز توزيع الأهداف (0-4)
    h_g_dist = {str(k): poisson_probability(l_h, k) * 100 for k in range(5)}
    a_g_dist = {str(k): poisson_probability(l_a, k) * 100 for k in range(5)}
    
    # تجهيز توزيع البطاقات الصفراء (0-5)
    y_dist = {str(k): poisson_probability(avg_yellow, k) * 100 for k in range(6)}
    
    # احتمالية البطاقة الحمراء
    r_prob = (1 - poisson_probability(avg_red, 0)) * 100

    conn.close()
    return {
        "win_probs": (p_h, p_d, p_a),
        "top_scores": sorted(scores, key=lambda x: x['prob'], reverse=True)[:3],
        "goal_dist": (h_g_dist, a_g_dist),
        "yellow_dist": y_dist,
        "red_prob": r_prob,
        "expected_goals": l_h + l_a
    }
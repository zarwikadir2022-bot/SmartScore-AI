import requests
import psycopg2
import time

# --- 1. الإعدادات ---
API_KEY = "d54cecd3dac9403c8548158c7a1c4565"
DB_PARAMS = {
    "host": "localhost",
    "database": "smartscore_db",
    "user": "postgres",
    "password": "123456"
}

# الدوريات الخمسة الكبرى
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1']

def fetch_world_data():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        headers = {"X-Auth-Token": API_KEY}

        for league in LEAGUES:
            print(f"⏳ جاري جلب بيانات الدوري: {league}...")
            url = f"https://api.football-data.org/v4/competitions/{league}/matches"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                matches = response.json()['matches']
                print(f"✅ تم العثور على {len(matches)} مباراة.")
                
                for m in matches:
                    h_score = m['score']['fullTime'].get('home')
                    a_score = m['score']['fullTime'].get('away')
                    
                    # سحب روابط الشعارات (Crests)
                    h_crest = m['homeTeam'].get('crest')
                    a_crest = m['awayTeam'].get('crest')
                    
                    cur.execute("""
                        INSERT INTO matches (match_id, home_team, away_team, league, status, home_score, away_score, home_crest, away_crest)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (match_id) DO UPDATE SET 
                            status = EXCLUDED.status,
                            home_score = EXCLUDED.home_score,
                            away_score = EXCLUDED.away_score,
                            home_crest = EXCLUDED.home_crest,
                            away_crest = EXCLUDED.away_crest;
                    """, (m['id'], m['homeTeam']['name'], m['awayTeam']['name'], 
                          m['competition']['name'], m['status'], h_score, a_score,
                          h_crest, a_crest))
                
                conn.commit()
                print("💤 انتظار 15 ثانية لاحترام قوانين السيرفر...")
                time.sleep(15) 
            else:
                print(f"❌ فشل جلب {league}. كود الخطأ: {response.status_code}")
                time.sleep(5)

        cur.close()
        conn.close()
        print("\n🚀 قاعدة البيانات الآن أصبحت عالمية وتحتوي على الشعارات!")

    except Exception as e:
        print(f"⚠️ حدث خطأ: {e}")

if __name__ == "__main__":
    fetch_world_data()
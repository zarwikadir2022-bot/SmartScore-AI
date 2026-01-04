import requests
import psycopg2

API_KEY = "d54cecd3dac9403c8548158c7a1c4565"
DB_PARAMS = {
    "host": "localhost",
    "database": "smartscore_db",
    "user": "postgres",
    "password": "123456"
}

def save_matches(matches):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        for m in matches:
            cur.execute("""
                INSERT INTO matches (match_id, home_team, away_team, league, status)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (match_id) DO UPDATE SET status = EXCLUDED.status;
            """, (m['id'], m['homeTeam']['name'], m['awayTeam']['name'], m['competition']['name'], m['status']))
            
        conn.commit()
        print(f"✅ تم حفظ {len(matches)} مباراة في قاعدة البيانات.")
        conn.close()
    except Exception as e:
        print(f"❌ خطأ في الحفظ: {e}")

def get_today_matches():
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        save_matches(data['matches'])

if __name__ == "__main__":
    get_today_matches()
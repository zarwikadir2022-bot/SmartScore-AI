from flask import Flask, jsonify
from flask_cors import CORS
from prediction_engine import predict_match_detailed
import psycopg2

app = Flask(__name__)
CORS(app)

@app.route('/api/predictions', methods=['GET'])
def get_predictions():
    conn = psycopg2.connect("host=localhost dbname=smartscore_db user=postgres password=123456")
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM matches WHERE status IN ('TIMED', 'SCHEDULED')")
    matches = cur.fetchall()
    
    results = []
    for m in matches:
        data = predict_match_detailed(m['home_team'], m['away_team'])
        results.append({
            "league": m['league'],
            "home": m['home_team'],
            "away": m['away_team'],
            "home_logo": m['home_crest'],
            "away_logo": m['away_crest'],
            "probs": data["win_probs"], # [1, X, 2]
            "expected_goals": data["expected_goals"]
        })
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    # تشغيل السيرفر على IP جهازك لفتحه من الهاتف
    app.run(host='0.0.0.0', port=5000)
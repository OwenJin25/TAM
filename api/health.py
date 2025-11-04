from flask import Flask, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check da API"""
    try:
        # Testar conexão com a BD
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "connected"
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return jsonify({
        'status': 'healthy',
        'service': 'ScanGuard API',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'database': db_status,
        'environment': 'production',
        'version': '1.0.0'
    }), 200, {
        'Access-Control-Allow-Origin': '*'
    }

def handler(request):
    with app.app_context():
        return app.full_dispatch_request()

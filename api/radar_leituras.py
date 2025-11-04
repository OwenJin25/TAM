from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def get_db_connection():
    """Conexão com PostgreSQL"""
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        connect_timeout=10
    )
    return conn

@app.route('/api/radar/leituras', methods=['POST', 'GET', 'OPTIONS'])
def handle_leituras():
    """Gerir leituras do radar - endpoint principal"""
    # CORS headers
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            return handle_post_leituras(conn)
        elif request.method == 'GET':
            return handle_get_leituras(conn)
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({'error': str(e)}), 500, {
            'Access-Control-Allow-Origin': '*'
        }
    finally:
        conn.close()

def handle_post_leituras(conn):
    """Processar POST de novas leituras"""
    data = request.get_json()
    
    # Validar dados obrigatórios
    if not data or 'angulo' not in data or 'distancia' not in data:
        return jsonify({'error': 'Dados incompletos'}), 400, {
            'Access-Control-Allow-Origin': '*'
        }
    
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO leituras_radar 
            (angulo, distancia, objeto_detetado, id_dispositivo, id_sessao)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, timestamp, angulo, distancia, objeto_detetado, id_dispositivo
        """, (
            float(data['angulo']),
            float(data['distancia']),
            bool(data.get('objeto_detetado', False)),
            data.get('id_dispositivo', 'radar_vercel_01'),
            data.get('id_sessao', 'default_session')
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        response_data = {
            'id': result[0],
            'timestamp': result[1].isoformat(),
            'angulo': float(result[2]),
            'distancia': float(result[3]),
            'objeto_detetado': bool(result[4]),
            'id_dispositivo': result[5],
            'status': 'success'
        }
        
        return jsonify(response_data), 201, {
            'Access-Control-Allow-Origin': '*'
        }

def handle_get_leituras(conn):
    """Processar GET para obter leituras"""
    # Parâmetros
    dispositivo = request.args.get('dispositivo', 'radar_vercel_01')
    limite = int(request.args.get('limit', 50))
    horas = int(request.args.get('horas', 24))
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT id, timestamp, angulo, distancia, objeto_detetado, id_dispositivo, id_sessao
            FROM leituras_radar 
            WHERE id_dispositivo = %s 
            AND timestamp >= NOW() - INTERVAL '%s hours'
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (dispositivo, horas, limite))
        
        leituras = []
        for row in cursor.fetchall():
            leituras.append({
                'id': row[0],
                'timestamp': row[1].isoformat(),
                'angulo': float(row[2]),
                'distancia': float(row[3]),
                'objeto_detetado': bool(row[4]),
                'id_dispositivo': row[5],
                'id_sessao': row[6]
            })
        
        return jsonify({
            'leituras': leituras,
            'total': len(leituras),
            'dispositivo': dispositivo
        }), 200, {
            'Access-Control-Allow-Origin': '*'
        }

# Handler para Vercel
def handler(request):
    with app.app_context():
        response = app.full_dispatch_request()
        return response

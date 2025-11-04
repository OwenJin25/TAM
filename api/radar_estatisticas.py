from flask import Flask, jsonify, request
import os
import psycopg2
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )

@app.route('/api/radar/estatisticas', methods=['GET', 'OPTIONS'])
def estatisticas():
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    conn = get_db_connection()
    
    try:
        dispositivo = request.args.get('dispositivo', 'radar_vercel_01')
        horas = int(request.args.get('horas', 24))
        
        with conn.cursor() as cursor:
            # Total de leituras
            cursor.execute("""
                SELECT COUNT(*) FROM leituras_radar 
                WHERE id_dispositivo = %s 
                AND timestamp >= NOW() - INTERVAL '%s hours'
            """, (dispositivo, horas))
            total_leituras = cursor.fetchone()[0] or 0
            
            # Objetos detetados
            cursor.execute("""
                SELECT COUNT(*) FROM leituras_radar 
                WHERE id_dispositivo = %s 
                AND objeto_detetado = TRUE 
                AND timestamp >= NOW() - INTERVAL '%s hours'
            """, (dispositivo, horas))
            objetos_detetados = cursor.fetchone()[0] or 0
            
            # Média de distâncias
            cursor.execute("""
                SELECT AVG(distancia) FROM leituras_radar 
                WHERE id_dispositivo = %s 
                AND timestamp >= NOW() - INTERVAL '%s hours'
                AND distancia > 0
            """, (dispositivo, horas))
            avg_distancia = cursor.fetchone()[0] or 0
            
            # Última leitura
            cursor.execute("""
                SELECT angulo, distancia, objeto_detetado, timestamp 
                FROM leituras_radar 
                WHERE id_dispositivo = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (dispositivo,))
            ultima = cursor.fetchone()
            
            estatisticas = {
                'total_leituras': total_leituras,
                'objetos_detetados': objetos_detetados,
                'taxa_deteccao': round((objetos_detetados / total_leituras * 100) if total_leituras > 0 else 0, 2),
                'media_distancia': round(float(avg_distancia), 2),
                'ultima_leitura': {
                    'angulo': float(ultima[0]),
                    'distancia': float(ultima[1]),
                    'objeto_detetado': bool(ultima[2]),
                    'timestamp': ultima[3].isoformat()
                } if ultima else None,
                'periodo_horas': horas,
                'dispositivo': dispositivo
            }
            
            return jsonify(estatisticas), 200, {
                'Access-Control-Allow-Origin': '*'
            }
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500, {
            'Access-Control-Allow-Origin': '*'
        }
    finally:
        conn.close()

def handler(request):
    with app.app_context():
        return app.full_dispatch_request()

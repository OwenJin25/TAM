from flask import Flask, request, jsonify
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

@app.route('/api/alertas', methods=['GET', 'POST', 'OPTIONS'])
def handle_alertas():
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            data = request.get_json()
            
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alertas_sistema 
                    (tipo_alerta, mensagem, severidade)
                    VALUES (%s, %s, %s)
                    RETURNING id, timestamp
                """, (
                    data['tipo_alerta'],
                    data['mensagem'],
                    data.get('severidade', 'info')
                ))
                
                result = cursor.fetchone()
                conn.commit()
                
                return jsonify({
                    'id': result[0],
                    'timestamp': result[1].isoformat(),
                    'tipo_alerta': data['tipo_alerta'],
                    'mensagem': data['mensagem'],
                    'severidade': data.get('severidade', 'info'),
                    'resolvido': False
                }), 201, {
                    'Access-Control-Allow-Origin': '*'
                }
        
        elif request.method == 'GET':
            limite = int(request.args.get('limit', 20))
            resolvido = request.args.get('resolvido')
            
            query = "SELECT * FROM alertas_sistema"
            params = []
            
            if resolvido is not None:
                query += " WHERE resolvido = %s"
                params.append(resolvido.lower() == 'true')
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limite)
            
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                
                alertas = []
                for row in cursor.fetchall():
                    alertas.append({
                        'id': row[0],
                        'tipo_alerta': row[1],
                        'mensagem': row[2],
                        'severidade': row[3],
                        'timestamp': row[4].isoformat(),
                        'resolvido': row[5]
                    })
                
                return jsonify(alertas), 200, {
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

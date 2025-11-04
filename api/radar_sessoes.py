from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime
import uuid

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD')
    )

@app.route('/api/radar/sessoes', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/radar/sessoes/<session_id>', methods=['PUT', 'OPTIONS'])
def handle_sessoes(session_id=None):
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    conn = get_db_connection()
    
    try:
        if request.method == 'POST':
            return criar_sessao(conn)
        elif request.method == 'GET':
            return listar_sessoes(conn)
        elif request.method == 'PUT' and session_id:
            return atualizar_sessao(conn, session_id)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500, {
            'Access-Control-Allow-Origin': '*'
        }
    finally:
        conn.close()

def criar_sessao(conn):
    """Criar nova sessão de monitorização"""
    session_id = str(uuid.uuid4())
    
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO sessoes_monitorizacao (id_sessao, esta_ativa)
            VALUES (%s, TRUE)
            RETURNING id, hora_inicio
        """, (session_id,))
        
        result = cursor.fetchone()
        conn.commit()
        
        return jsonify({
            'id': result[0],
            'id_sessao': session_id,
            'hora_inicio': result[1].isoformat(),
            'esta_ativa': True
        }), 201, {
            'Access-Control-Allow-Origin': '*'
        }

def listar_sessoes(conn):
    """Listar sessões de monitorização"""
    limite = int(request.args.get('limit', 10))
    
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sessoes_monitorizacao 
            ORDER BY hora_inicio DESC 
            LIMIT %s
        """, (limite,))
        
        sessoes = []
        for row in cursor.fetchall():
            sessoes.append({
                'id': row[0],
                'id_sessao': row[1],
                'hora_inicio': row[2].isoformat(),
                'hora_fim': row[3].isoformat() if row[3] else None,
                'total_leituras': row[4],
                'objetos_detetados': row[5],
                'esta_ativa': row[6]
            })
        
        return jsonify(sessoes), 200, {
            'Access-Control-Allow-Origin': '*'
        }

def atualizar_sessao(conn, session_id):
    """Atualizar sessão (parar monitorização)"""
    data = request.get_json()
    
    with conn.cursor() as cursor:
        if data.get('action') == 'stop':
            cursor.execute("""
                UPDATE sessoes_monitorizacao 
                SET hora_fim = NOW(), esta_ativa = FALSE 
                WHERE id_sessao = %s
                RETURNING *
            """, (session_id,))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Sessão não encontrada'}), 404, {
                    'Access-Control-Allow-Origin': '*'
                }
            
            conn.commit()
            
            return jsonify({
                'id': result[0],
                'id_sessao': result[1],
                'hora_inicio': result[2].isoformat(),
                'hora_fim': result[3].isoformat() if result[3] else None,
                'total_leituras': result[4],
                'objetos_detetados': result[5],
                'esta_ativa': result[6]
            }), 200, {
                'Access-Control-Allow-Origin': '*'
            }

def handler(request):
    with app.app_context():
        return app.full_dispatch_request()

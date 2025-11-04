from flask import Flask, request, jsonify, render_template_string
import psycopg2
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SUAS CREDENCIAIS POSTGRESQL
DB_CONFIG = {
    "host": "aid.estgoh.ipc.pt",
    "database": "db2022145941", 
    "user": "a2022145941",
    "password": "1234567890",
    "port": 5432
}

# Configuração do PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"❌ Erro de conexão com o banco: {e}")
        return None

# Criar tabela automaticamente
def init_db():
    try:
        conn = get_db_connection()
        if conn is None:
            logger.error("Não foi possível conectar ao banco para criar tabela")
            return False
            
        cur = conn.cursor()
        
        # Verificar se tabela existe
        cur.execute('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'radar_data'
            );
        ''')
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            logger.info("🔄 Criando tabela radar_data...")
            cur.execute('''
                CREATE TABLE radar_data (
                    id SERIAL PRIMARY KEY,
                    angle INTEGER NOT NULL,
                    distance INTEGER NOT NULL,
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Criar índice para melhor performance
            cur.execute('''
                CREATE INDEX idx_radar_data_created_at 
                ON radar_data(created_at DESC)
            ''')
            
            conn.commit()
            logger.info("✅ Tabela 'radar_data' criada com sucesso!")
        else:
            logger.info("✅ Tabela 'radar_data' já existe")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar/verificar tabela: {e}")
        return False

# Testar conexão com banco
def test_db_connection():
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()
            cur.close()
            conn.close()
            logger.info(f"✅ Conexão PostgreSQL OK: {version[0]}")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Teste de conexão falhou: {e}")
        return False

# Executar inicialização
logger.info("🔄 Iniciando aplicação Radar DIY...")
db_ok = init_db()
if db_ok:
    test_db_connection()
else:
    logger.error("❌ Falha na inicialização do banco de dados")

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radar DIY - Monitoramento em Tempo Real</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            .card {
                background: white;
                padding: 25px;
                margin: 15px 0;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .card h2 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.4rem;
                border-bottom: 2px solid #667eea;
                padding-bottom: 8px;
            }
            
            .status-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .status {
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
            }
            
            .status.online {
                background: #d4edda;
                color: #155724;
                border: 2px solid #c3e6cb;
            }
            
            .status.offline {
                background: #f8d7da;
                color: #721c24;
                border: 2px solid #f5c6cb;
            }
            
            .status.connecting {
                background: #fff3cd;
                color: #856404;
                border: 2px solid #ffeaa7;
            }
            
            .charts-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            .chart-wrapper {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border: 1px solid #e9ecef;
            }
            
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            
            .data-table th,
            .data-table td {
                padding: 12px;
                text-align: center;
                border-bottom: 1px solid #dee2e6;
            }
            
            .data-table th {
                background: #667eea;
                color: white;
                font-weight: 600;
            }
            
            .data-table tr:nth-child(even) {
                background: #f8f9fa;
            }
            
            .data-table tr:hover {
                background: #e9ecef;
            }
            
            .controls {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                background: #667eea;
                color: white;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            button:hover {
                background: #5a6fd8;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }
            
            button:active {
                transform: translateY(0);
            }
            
            button.clear {
                background: #dc3545;
            }
            
            button.clear:hover {
                background: #c82333;
            }
            
            button.test {
                background: #28a745;
            }
            
            button.test:hover {
                background: #218838;
            }
            
            @media (max-width: 768px) {
                .status-container,
                .charts-container {
                    grid-template-columns: 1fr;
                }
                
                .header h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Radar DIY - Sistema de Monitoramento</h1>
                <p>Monitoramento em tempo real com Arduino, ESP8266 e PostgreSQL</p>
            </div>
            
            <!-- Card de Status -->
            <div class="card">
                <h2>📊 Status do Sistema</h2>
                <div class="status-container">
                    <div id="radarStatus" class="status offline">
                        <div>📡 Radar</div>
                        <div>Aguardando dados...</div>
                    </div>
                    <div id="dbStatus" class="status offline">
                        <div>🗄️ Banco de Dados</div>
                        <div>Testando conexão...</div>
                    </div>
                </div>
                <div id="lastUpdate" style="text-align: center; font-style: italic; color: #666;">
                    Última atualização: Nunca
                </div>
            </div>
            
            <!-- Card de Gráficos -->
            <div class="card">
                <h2>📈 Visualizações</h2>
                <div class="charts-container">
                    <div class="chart-wrapper">
                        <h3>🌐 Visualização Radar</h3>
                        <canvas id="radarChart" width="400" height="400"></canvas>
                    </div>
                    <div class="chart-wrapper">
                        <h3>📏 Distância em Tempo Real</h3>
                        <canvas id="distanceChart" width="400" height="400"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Card de Dados -->
            <div class="card">
                <h2>📋 Últimas Leituras</h2>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Ângulo</th>
                                <th>Distância (cm)</th>
                                <th>Timestamp</th>
                                <th>Hora</th>
                            </tr>
                        </thead>
                        <tbody id="readingsTable">
                            <tr>
                                <td colspan="4" style="text-align: center;">Aguardando dados do radar...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Card de Controles -->
            <div class="card">
                <h2>🎮 Controles</h2>
                <div class="controls">
                    <button onclick="clearOldData()" class="clear">🗑️ Limpar Dados Antigos</button>
                    <button onclick="testConnection()" class="test">🔍 Testar Conexão</button>
                    <button onclick="fetchLatestData()" class="test">🔄 Atualizar Dados</button>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# Endpoints da API
@app.route('/api/status')
def api_status():
    """Endpoint para verificar status do sistema"""
    try:
        # Testar conexão com banco
        conn = get_db_connection()
        if conn:
            conn.close()
            db_status = "connected"
        else:
            db_status = "disconnected"
            
        return jsonify({
            "status": "online",
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Erro no endpoint de status: {e}")
        return jsonify({
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route('/api/radar/data', methods=['POST', 'GET'])
def handle_radar_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                logger.warning("❌ POST sem dados JSON")
                return jsonify({'error': 'Dados JSON inválidos'}), 400
            
            angle = data.get('angle')
            distance = data.get('distance')
            timestamp = data.get('timestamp')
            
            # Validar dados
            if angle is None or distance is None:
                logger.warning("❌ Dados incompletos recebidos")
                return jsonify({'error': 'Ângulo e distância são obrigatórios'}), 400
            
            # Validar ranges
            if not (0 <= angle <= 180):
                return jsonify({'error': 'Ângulo deve estar entre 0 e 180'}), 400
            
            if not (0 <= distance <= 400):
                return jsonify({'error': 'Distância deve estar entre 0 e 400 cm'}), 400
            
            # Salvar no PostgreSQL
            conn = get_db_connection()
            if conn is None:
                logger.error("❌ Não foi possível conectar ao banco para salvar dados")
                return jsonify({'error': 'Erro de conexão com o banco'}), 500
                
            cur = conn.cursor()
            
            cur.execute(
                'INSERT INTO radar_data (angle, distance, timestamp) VALUES (%s, %s, %s)',
                (angle, distance, timestamp)
            )
            
            conn.commit()
            cur.close()
            conn.close()
            
            logger.info(f"✅ Dados salvos: Ângulo={angle}°, Distância={distance}cm, Timestamp={timestamp}")
            return jsonify({
                'message': 'Dados salvos com sucesso',
                'angle': angle,
                'distance': distance,
                'timestamp': timestamp
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET - Buscar todos os dados
        try:
            conn = get_db_connection()
            if conn is None:
                return jsonify({'error': 'Erro de conexão com o banco'}), 500
                
            cur = conn.cursor()
            
            cur.execute('''
                SELECT id, angle, distance, timestamp, created_at 
                FROM radar_data 
                ORDER BY created_at DESC 
                LIMIT 1000
            ''')
            data = cur.fetchall()
            
            result = []
            for row in data:
                result.append({
                    'id': row[0],
                    'angle': row[1],
                    'distance': row[2],
                    'timestamp': row[3],
                    'created_at': row[4].isoformat() if row[4] else None
                })
            
            cur.close()
            conn.close()
            
            logger.info(f"📊 Retornando {len(result)} registros")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dados: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/radar/latest')
def get_latest_data():
    """Buscar os dados mais recentes"""
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
            
        cur = conn.cursor()
        
        cur.execute('''
            SELECT id, angle, distance, timestamp, created_at 
            FROM radar_data 
            ORDER BY created_at DESC 
            LIMIT 10
        ''')
        data = cur.fetchall()
        
        result = []
        for row in data:
            result.append({
                'id': row[0],
                'angle': row[1],
                'distance': row[2],
                'timestamp': row[3],
                'created_at': row[4].isoformat() if row[4] else None
            })
        
        cur.close()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dados recentes: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/radar/clear', methods=['DELETE'])
def clear_old_data():
    """Limpar dados antigos"""
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
            
        cur = conn.cursor()
        
        # Manter apenas os últimos 1000 registros
        cur.execute('''
            DELETE FROM radar_data 
            WHERE id NOT IN (
                SELECT id FROM radar_data 
                ORDER BY created_at DESC 
                LIMIT 1000
            )
        ''')
        
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"🗑️ {deleted_count} registros antigos removidos")
        return jsonify({
            'message': f'{deleted_count} registros antigos removidos',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao limpar dados: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/radar/stats')
def get_stats():
    """Estatísticas dos dados"""
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({'error': 'Erro de conexão com o banco'}), 500
            
        cur = conn.cursor()
        
        # Total de registros
        cur.execute('SELECT COUNT(*) FROM radar_data')
        total_records = cur.fetchone()[0]
        
        # Registros hoje
        cur.execute('''
            SELECT COUNT(*) FROM radar_data 
            WHERE DATE(created_at) = CURRENT_DATE
        ''')
        today_records = cur.fetchone()[0]
        
        # Última atualização
        cur.execute('''
            SELECT MAX(created_at) FROM radar_data
        ''')
        last_update = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return jsonify({
            'total_records': total_records,
            'today_records': today_records,
            'last_update': last_update.isoformat() if last_update else None,
            'database_size': 'N/A'  # Poderia ser calculado com consultas adicionais
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas: {e}")
        return jsonify({'error': str(e)}), 500

# Health check para Vercel
@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Radar DIY API"
    })

# Handler para erros 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

# Handler para erros 500
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    # Executar inicialização final
    logger.info("🚀 Serviço Radar DIY API iniciado!")
    logger.info("📊 Verificando configuração do banco de dados...")
    
    if test_db_connection():
        logger.info("✅ Banco de dados configurado corretamente")
    else:
        logger.error("❌ Problema na configuração do banco de dados")
    
    # Para desenvolvimento local
    app.run(host='0.0.0.0', port=5000, debug=True)

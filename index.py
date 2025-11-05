from flask import Flask, request, jsonify
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SUAS CREDENCIAIS POSTGRESQL
DB_CONFIG = {
    "host": os.environ.get('DB_HOST', 'aid.estgoh.ipc.pt'),
    "database": os.environ.get('DB_NAME', 'db2022145941'), 
    "user": os.environ.get('DB_USER', 'a2022145941'),
    "password": os.environ.get('DB_PASSWORD', '1234567890'),
    "port": int(os.environ.get('DB_PORT', 5432))
}

# Sistema híbrido
USE_POSTGRESQL = False
radar_data = []  # Backup em memória

# Tentar conectar com PostgreSQL
def get_db_connection():
    try:
        import pg8000
        conn = pg8000.connect(**DB_CONFIG)
        global USE_POSTGRESQL
        USE_POSTGRESQL = True
        logger.info("✅ Conectado ao PostgreSQL")
        return conn
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL não disponível: {e}")
        return None

# Inicialização segura
def safe_init():
    try:
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS radar_data (
                        id SERIAL PRIMARY KEY,
                        angle INTEGER NOT NULL,
                        distance INTEGER NOT NULL,
                        timestamp BIGINT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                cur.close()
                conn.close()
                logger.info("✅ Tabela PostgreSQL pronta")
            except Exception as e:
                logger.warning(f"⚠️ Erro na tabela: {e}")
        else:
            logger.info("🔧 Modo em memória ativado")
    except Exception as e:
        logger.error(f"❌ Erro na inicialização: {e}")

# Inicializar
logger.info("🔄 Iniciando Radar DIY...")
safe_init()

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radar DIY - Sistema Online</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
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
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
            }
            .card { 
                background: white; 
                padding: 25px; 
                margin: 20px 0; 
                border-radius: 15px; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            .card h2 { 
                color: #333; 
                margin-bottom: 20px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .status-container {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            .status { 
                padding: 20px; 
                border-radius: 10px; 
                text-align: center; 
                font-weight: bold;
                font-size: 1.1rem;
            }
            .online { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
            .offline { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
            .connecting { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
            .charts-container {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            .chart-wrapper {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
            }
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }
            .data-table th, .data-table td {
                padding: 12px;
                text-align: center;
                border-bottom: 1px solid #dee2e6;
            }
            .data-table th {
                background: #667eea;
                color: white;
            }
            .controls {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            button {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                background: #667eea;
                color: white;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            button:hover {
                background: #5a6fd8;
                transform: translateY(-2px);
            }
            @media (max-width: 768px) {
                .status-container, .charts-container {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Radar DIY - Sistema Online</h1>
                <p>Monitoramento em tempo real com Arduino e PostgreSQL</p>
            </div>
            
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
                    <div id="ledStatus" class="status offline">
                        <div>💡 LED RGB</div>
                        <div>Desconhecido</div>
                    </div>
                </div>
                <div id="lastUpdate" style="text-align: center; margin-top: 15px; font-style: italic; color: #666;">
                    Última atualização: Nunca
                </div>
            </div>

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

            <div class="card">
                <h2>📋 Últimas Leituras</h2>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Ângulo</th>
                                <th>Distância</th>
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

            <div class="card">
                <h2>🎮 Controles</h2>
                <div class="controls">
                    <button onclick="clearData()">🗑️ Limpar Dados</button>
                    <button onclick="testConnection()">🔍 Testar Conexão</button>
                    <button onclick="fetchData()">🔄 Atualizar Dados</button>
                </div>
            </div>
        </div>

        <script>
            let radarChart, distanceChart;
            let updateInterval;

            // Inicializar gráficos
            function initializeCharts() {
                const radarCtx = document.getElementById('radarChart').getContext('2d');
                radarChart = new Chart(radarCtx, {
                    type: 'radar',
                    data: {
                        labels: Array.from({length: 37}, (_, i) => i * 5 + '°'),
                        datasets: [{
                            label: 'Distância (cm)',
                            data: Array(37).fill(0),
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 2
                        }]
                    },
                    options: {
                        scales: {
                            r: {
                                beginAtZero: true,
                                max: 200,
                                ticks: { stepSize: 50 }
                            }
                        }
                    }
                });

                const distanceCtx = document.getElementById('distanceChart').getContext('2d');
                distanceChart = new Chart(distanceCtx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Distância (cm)',
                            data: [],
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.1)',
                            borderWidth: 2,
                            fill: true
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 200
                            }
                        }
                    }
                });
            }

            // Atualizar status
            async function updateDBStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    const dbStatus = document.getElementById('dbStatus');
                    if (data.database === 'postgresql') {
                        dbStatus.className = 'status online';
                        dbStatus.innerHTML = '<div>🗄️ Banco de Dados</div><div>✅ PostgreSQL</div>';
                    } else {
                        dbStatus.className = 'status connecting';
                        dbStatus.innerHTML = '<div>🗄️ Banco de Dados</div><div>🔄 Memória</div>';
                    }
                } catch (error) {
                    document.getElementById('dbStatus').className = 'status offline';
                    document.getElementById('dbStatus').innerHTML = '<div>🗄️ Banco de Dados</div><div>❌ Offline</div>';
                }
            }

            // Buscar dados
            async function fetchData() {
                try {
                    const response = await fetch('/api/radar/latest');
                    const data = await response.json();
                    
                    if (data && data.length > 0) {
                        updateRadarStatus('online');
                        updateCharts(data[0]);
                        updateTable(data);
                        updateLastUpdate();
                    } else {
                        updateRadarStatus('offline');
                    }
                } catch (error) {
                    updateRadarStatus('offline');
                }
            }

            function updateRadarStatus(status) {
                const radarStatus = document.getElementById('radarStatus');
                if (status === 'online') {
                    radarStatus.className = 'status online';
                    radarStatus.innerHTML = '<div>📡 Radar</div><div>✅ Recebendo dados</div>';
                } else {
                    radarStatus.className = 'status offline';
                    radarStatus.innerHTML = '<div>📡 Radar</div><div>❌ Sem dados</div>';
                }
            }

            function updateLEDStatus(distance) {
                const ledStatus = document.getElementById('ledStatus');
                if (distance < 30) {
                    ledStatus.className = 'status offline';
                    ledStatus.innerHTML = '<div>💡 LED RGB</div><div>🔴 Objeto Detectado</div>';
                } else {
                    ledStatus.className = 'status online';
                    ledStatus.innerHTML = '<div>💡 LED RGB</div><div>🟢 Área Livre</div>';
                }
            }

            function updateCharts(latestData) {
                if (!latestData) return;
                
                updateLEDStatus(latestData.distance);
                
                // Radar
                const angleIndex = Math.floor(latestData.angle / 5);
                if (angleIndex >= 0 && angleIndex < 37) {
                    radarChart.data.datasets[0].data[angleIndex] = latestData.distance;
                    radarChart.update('none');
                }
                
                // Linha
                const time = new Date().toLocaleTimeString();
                distanceChart.data.labels.push(time);
                distanceChart.data.datasets[0].data.push(latestData.distance);
                
                if (distanceChart.data.labels.length > 20) {
                    distanceChart.data.labels.shift();
                    distanceChart.data.datasets[0].data.shift();
                }
                distanceChart.update('none');
            }

            function updateTable(data) {
                const tableBody = document.getElementById('readingsTable');
                tableBody.innerHTML = '';
                
                data.slice(0, 10).forEach(item => {
                    const row = document.createElement('tr');
                    const time = new Date(item.created_at || Date.now()).toLocaleTimeString();
                    
                    row.innerHTML = `
                        <td>${item.angle}°</td>
                        <td>${item.distance} cm</td>
                        <td>${item.timestamp}</td>
                        <td>${time}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }

            function updateLastUpdate() {
                document.getElementById('lastUpdate').textContent = 
                    `Última atualização: ${new Date().toLocaleTimeString()}`;
            }

            async function clearData() {
                if (!confirm('Limpar todos os dados?')) return;
                try {
                    await fetch('/api/radar/clear', {method: 'DELETE'});
                    alert('Dados limpos!');
                    location.reload();
                } catch (error) {
                    alert('Erro ao limpar dados.');
                }
            }

            async function testConnection() {
                await updateDBStatus();
                await fetchData();
                alert('Teste de conexão concluído!');
            }

            // Inicializar
            document.addEventListener('DOMContentLoaded', function() {
                initializeCharts();
                updateDBStatus();
                fetchData();
                
                // Atualizar a cada 3 segundos
                updateInterval = setInterval(fetchData, 3000);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/status')
def api_status():
    return jsonify({
        "status": "healthy",
        "database": "postgresql" if USE_POSTGRESQL else "memory",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/radar/data', methods=['POST', 'GET'])
def handle_radar_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            angle = data.get('angle')
            distance = data.get('distance')
            timestamp = data.get('timestamp')

            if angle is None or distance is None:
                return jsonify({'error': 'Dados incompletos'}), 400

            # Salvar no PostgreSQL ou memória
            if USE_POSTGRESQL:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute(
                        'INSERT INTO radar_data (angle, distance, timestamp) VALUES (%s, %s, %s)',
                        (angle, distance, timestamp)
                    )
                    conn.commit()
                    cur.close()
                    conn.close()
            else:
                radar_data.append({
                    'angle': angle,
                    'distance': distance,
                    'timestamp': timestamp,
                    'created_at': datetime.now().isoformat()
                })
                if len(radar_data) > 100:
                    radar_data.pop(0)

            logger.info(f"✅ Dados recebidos: {angle}°, {distance}cm")
            return jsonify({'message': 'Dados salvos'}), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    else:  # GET
        if USE_POSTGRESQL:
            try:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute('''
                        SELECT angle, distance, timestamp, created_at 
                        FROM radar_data 
                        ORDER BY created_at DESC 
                        LIMIT 100
                    ''')
                    results = cur.fetchall()
                    cur.close()
                    conn.close()
                    return jsonify([{
                        'angle': r[0], 'distance': r[1], 'timestamp': r[2],
                        'created_at': r[3].isoformat() if r[3] else None
                    } for r in results])
            except Exception as e:
                logger.error(f"Erro PostgreSQL: {e}")
        
        return jsonify(radar_data)

@app.route('/api/radar/latest')
def get_latest_data():
    if USE_POSTGRESQL:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute('''
                    SELECT angle, distance, timestamp, created_at 
                    FROM radar_data 
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''')
                results = cur.fetchall()
                cur.close()
                conn.close()
                return jsonify([{
                    'angle': r[0], 'distance': r[1], 'timestamp': r[2],
                    'created_at': r[3].isoformat() if r[3] else None
                } for r in results])
        except:
            pass
    
    return jsonify(radar_data[-10:] if radar_data else [])

@app.route('/api/radar/clear', methods=['DELETE'])
def clear_data():
    if USE_POSTGRESQL:
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute('DELETE FROM radar_data')
                conn.commit()
                cur.close()
                conn.close()
        except:
            pass
    
    radar_data.clear()
    return jsonify({'message': 'Dados limpos'})

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    application = app

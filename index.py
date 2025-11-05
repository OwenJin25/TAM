from flask import Flask, request, jsonify, render_template_string
import logging
from datetime import datetime

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dados em memória (para teste)
radar_data = []

@app.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radar DIY - Sistema Online</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f2f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: white; padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { padding: 15px; border-radius: 8px; margin: 10px 0; text-align: center; font-weight: bold; }
            .online { background: #d4edda; color: #155724; }
            .offline { background: #f8d7da; color: #721c24; }
            .header { text-align: center; color: #333; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚨 Radar DIY - Sistema Online</h1>
                <p>Modo de teste (dados em memória)</p>
            </div>
            
            <div class="card">
                <h2>📊 Status do Sistema</h2>
                <div class="status online">
                    ✅ Sistema funcionando na Vercel
                </div>
                <p>Dados em memória: {{ data_count }} registros</p>
                <p><strong>Para conectar o Arduino:</strong></p>
                <p>URL da API: <code>https://tam-two.vercel.app/api/radar/data</code></p>
            </div>

            <div class="card">
                <h2>Últimos Dados Recebidos</h2>
                <div id="dataContainer">
                    {% if radar_data %}
                        {% for item in radar_data[-5:] %}
                            <p>Ângulo: {{ item.angle }}° - Distância: {{ item.distance }}cm</p>
                        {% endfor %}
                    {% else %}
                        <p>Aguardando dados do Arduino...</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', data_count=len(radar_data), radar_data=radar_data)

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy", 
        "message": "Radar DIY API",
        "database": "em_memoria",
        "data_count": len(radar_data)
    })

@app.route('/api/radar/data', methods=['POST', 'GET'])
def handle_radar_data():
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Dados JSON inválidos'}), 400
            
            angle = data.get('angle')
            distance = data.get('distance')
            timestamp = data.get('timestamp')
            
            if angle is None or distance is None:
                return jsonify({'error': 'Ângulo e distância são obrigatórios'}), 400
            
            # Salvar em memória
            radar_data.append({
                'angle': angle,
                'distance': distance,
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat()
            })
            
            # Manter apenas últimos 100 registros
            if len(radar_data) > 100:
                radar_data.pop(0)
            
            logger.info(f"✅ Dados recebidos: Ângulo={angle}°, Distância={distance}cm")
            return jsonify({
                'message': 'Dados salvos em memória',
                'angle': angle,
                'distance': distance
            }), 201
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return jsonify({'error': str(e)}), 500
    
    else:  # GET
        return jsonify(radar_data[-20:])  # Últimos 20 registros

@app.route('/api/radar/latest')
def get_latest():
    return jsonify(radar_data[-5:] if radar_data else [])

@app.route('/api/radar/clear', methods=['DELETE'])
def clear_data():
    radar_data.clear()
    return jsonify({'message': 'Dados limpos'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    application = app

// Configuração
const API_BASE = '/api';
let currentSessionId = null;

// Elementos DOM
const elements = {
    totalLeituras: document.getElementById('totalLeituras'),
    objetosDetetados: document.getElementById('objetosDetetados'),
    taxaDeteccao: document.getElementById('taxaDeteccao'),
    mediaDistancia: document.getElementById('mediaDistancia'),
    currentAngle: document.getElementById('currentAngle'),
    lastDistance: document.getElementById('lastDistance'),
    scanStatus: document.getElementById('scanStatus'),
    leiturasList: document.getElementById('leiturasList'),
    alertasList: document.getElementById('alertasList'),
    radarCanvas: document.getElementById('radarCanvas')
};

// Canvas do radar
const ctx = elements.radarCanvas.getContext('2d');

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 ScanGuard Dashboard Iniciado');
    initRadar();
    loadAllData();
    
    // Atualizar a cada 3 segundos
    setInterval(loadAllData, 3000);
});

// Carregar todos os dados
async function loadAllData() {
    try {
        await Promise.all([
            loadEstatisticas(),
            loadLeituras(),
            loadAlertas()
        ]);
    } catch (error) {
        console.error('Erro a carregar dados:', error);
    }
}

// Carregar estatísticas
async function loadEstatisticas() {
    try {
        const response = await fetch(API_BASE + '/radar/estatisticas');
        const stats = await response.json();
        
        elements.totalLeituras.textContent = stats.total_leituras.toLocaleString();
        elements.objetosDetetados.textContent = stats.objetos_detetados.toLocaleString();
        elements.taxaDeteccao.textContent = stats.taxa_deteccao + '%';
        elements.mediaDistancia.textContent = stats.media_distancia + 'cm';
        
        // Atualizar radar se houver última leitura
        if (stats.ultima_leitura) {
            elements.currentAngle.textContent = stats.ultima_leitura.angulo + '°';
            elements.lastDistance.textContent = stats.ultima_leitura.distancia + 'cm';
            updateRadar(stats.ultima_leitura.angulo, stats.ultima_leitura.distancia, stats.ultima_leitura.objeto_detetado);
        }
        
    } catch (error) {
        console.error('Erro a carregar estatísticas:', error);
    }
}

// Carregar leituras
async function loadLeituras() {
    try {
        const response = await fetch(API_BASE + '/radar/leituras?limit=15');
        const data = await response.json();
        
        elements.leiturasList.innerHTML = '';
        
        if (data.leituras && data.leituras.length > 0) {
            data.leituras.forEach(leitura => {
                const div = document.createElement('div');
                div.className = `leitura-item ${leitura.objeto_detetado ? 'objeto' : ''}`;
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>📍 ${leitura.angulo}°</strong> | 
                            ${leitura.distancia}cm | 
                            <span style="color: ${leitura.objeto_detetado ? '#e74c3c' : '#27ae60'}; font-weight: bold;">
                                ${leitura.objeto_detetado ? '🚨 OBJETO' : '✅ LIVRE'}
                            </span>
                        </div>
                        <div style="font-size: 0.8em; color: #7f8c8d;">
                            ${new Date(leitura.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                `;
                elements.leiturasList.appendChild(div);
            });
        } else {
            elements.leiturasList.innerHTML = '<div class="loading">Nenhuma leitura disponível</div>';
        }
        
    } catch (error) {
        console.error('Erro a carregar leituras:', error);
        elements.leiturasList.innerHTML = '<div class="loading" style="color: #e74c3c;">Erro a carregar leituras</div>';
    }
}

// Carregar alertas
async function loadAlertas() {
    try {
        const response = await fetch(API_BASE + '/alertas?limit=10');
        const alertas = await response.json();
        
        elements.alertasList.innerHTML = '';
        
        if (alertas.length > 0) {
            alertas.forEach(alerta => {
                const div = document.createElement('div');
                div.className = `alerta-item ${alerta.severidade === 'error' ? 'erro' : ''}`;
                div.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <strong style="color: ${alerta.severidade === 'error' ? '#dc3545' : '#856404'};">

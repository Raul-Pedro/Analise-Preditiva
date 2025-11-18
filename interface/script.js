document.addEventListener('DOMContentLoaded', () => {
    
    const form = document.getElementById('previsao-form');
    const bairroInput = document.getElementById('bairro-input');
    const analisarBtn = document.getElementById('analisar-btn');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error-message');
    const resultsDiv = document.getElementById('results-container');
    
    const riscoCard = document.getElementById('risco-card');
    const riscoBairro = document.getElementById('risco-bairro');
    const riscoProb = document.getElementById('risco-probabilidade');
    const riscoNivel = document.getElementById('risco-nivel');
    const previsaoLista = document.getElementById('previsao-lista');
    
    const graficoCanvas = document.getElementById('previsao-grafico');
    let meuGrafico = null;

    // Função de espera
    const esperar = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const bairro = bairroInput.value;
        const dias = document.querySelector('input[name="dias"]:checked').value;
        
        // Mostra Loading
        loadingDiv.classList.remove('hidden'); 
        errorDiv.classList.add('hidden');
        resultsDiv.classList.add('hidden');
        analisarBtn.disabled = true;

        const url = `http://127.0.0.1:5010/prever_risco/${encodeURIComponent(bairro)}?dias=${dias}`;

        try {
            // Suspense de 2 segundos + Busca
            const [_, response] = await Promise.all([
                esperar(2000), 
                fetch(url)
            ]);

            const data = await response.json(); 

            if (!response.ok) {
                throw new Error(data.erro || 'Erro desconhecido ao buscar dados.');
            }
            
            displayResults(data); 

        } catch (error) {
            console.error("ERRO:", error);
            displayError(error.message);
        } finally {
            // Esconde Loading
            loadingDiv.classList.add('hidden');
            analisarBtn.disabled = false;
        }
    });

    function displayResults(data) {
        resultsDiv.classList.remove('hidden');

        // Preenche Texto
        riscoBairro.textContent = data.bairro_pesquisado;
        riscoProb.textContent = `Probabilidade de Surto: ${data.probabilidade_risco_dengue}`;
        riscoNivel.textContent = data.nivel_risco_calculado;

        riscoCard.classList.remove('alto', 'baixo');
        if (data.nivel_risco_calculado === 'ALTO') {
            riscoCard.classList.add('alto');
        } else {
            riscoCard.classList.add('baixo');
        }

        // Preenche Lista
        previsaoLista.innerHTML = '';
        data.previsao_meteorologica_diaria.forEach(dia => {
            const diaHtml = `
                <div class="previsao-dia">
                    <div class="data">${formatarData(dia.data)}</div>
                    <div class="detalhes">
                        <strong>${dia.resumo_tempo}</strong><br>
                        Temp Máx: ${dia.maxima_c.toFixed(1)}°C<br>
                        Chuva: ${dia.probabilidade_chuva_pct}%
                    </div>
                </div>
            `;
            previsaoLista.innerHTML += diaHtml;
        });
        
        // --- CRIAÇÃO DO NOVO GRÁFICO ---
        
        // 1. Prepara os dados
        const labels = data.previsao_meteorologica_diaria.map(dia => formatarData(dia.data));
        const probChuva = data.previsao_meteorologica_diaria.map(dia => dia.probabilidade_chuva_pct);
        
        const probInfeccaoValor = parseFloat(data.probabilidade_risco_dengue.replace('%', ''));
        
        const probInfeccaoData = labels.map(() => probInfeccaoValor);

        if (meuGrafico) {
            meuGrafico.destroy();
        }

        const ctx = graficoCanvas.getContext('2d');
        meuGrafico = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Prob. Chuva (%)',
                        data: probChuva,
                        backgroundColor: 'rgba(52, 152, 219, 0.7)', // Azul transparente
                        borderColor: '#3498db',
                        borderWidth: 1,
                        order: 2
                    },
                    {
                        label: 'Risco de Infecção (%)', // A estrela do show
                        data: probInfeccaoData,
                        type: 'line', // Linha
                        borderColor: '#8e44ad', // Roxo (cor de alerta/vírus)
                        backgroundColor: '#8e44ad',
                        borderWidth: 3,
                        pointRadius: 5, // Pontos maiores
                        tension: 0.1,
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: { 
                        display: true, 
                        text: 'Correlação: Chuva vs Risco de Infecção',
                        font: { size: 16 }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100, 
                        title: { display: true, text: 'Probabilidade (%)' }
                    }
                }
            }
        });
    }

    function displayError(message) {
        errorDiv.textContent = `Erro: ${message}`;
        errorDiv.classList.remove('hidden');
    }
    
    function formatarData(dataString) {
        const [ano, mes, dia] = dataString.split('-');
        return `${dia}/${mes}`;
    }
});
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

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const bairro = bairroInput.value;
        const dias = document.querySelector('input[name="dias"]:checked').value;
        
        loadingDiv.classList.remove('hidden');
        errorDiv.classList.add('hidden');
        resultsDiv.classList.add('hidden');
        analisarBtn.disabled = true;

        const url = `http://127.0.0.1:5010/prever_risco/${encodeURIComponent(bairro)}?dias=${dias}`;

        try {
            const response = await fetch(url);
            const data = await response.json(); 

            if (!response.ok) {
                throw new Error(data.erro || 'Erro desconhecido ao buscar dados.');
            }
            
            displayResults(data);

        } catch (error) {
            displayError(error.message);
        } finally {
            loadingDiv.classList.add('hidden');
            analisarBtn.disabled = false;
        }
    });

    /**
     * Função para exibir os resultados na tela
     */
    function displayResults(data) {
        resultsDiv.classList.remove('hidden');

        riscoBairro.textContent = data.bairro_pesquisado;
        riscoProb.textContent = `Probabilidade: ${data.probabilidade_risco_dengue}`;
        riscoNivel.textContent = data.nivel_risco_calculado;

        riscoCard.classList.remove('alto', 'baixo');
        if (data.nivel_risco_calculado === 'ALTO') {
            riscoCard.classList.add('alto');
        } else {
            riscoCard.classList.add('baixo');
        }

        previsaoLista.innerHTML = '';
        data.previsao_meteorologica_diaria.forEach(dia => {
            const diaHtml = `
                <div class="previsao-dia">
                    <div class="data">${formatarData(dia.data)}</div>
                    <div class="detalhes">
                        <strong>${dia.resumo_tempo}</strong><br>
                        Temp: ${dia.minima_c.toFixed(1)}°C / ${dia.maxima_c.toFixed(1)}°C<br>
                        Chuva: ${dia.probabilidade_chuva_pct}%
                    </div>
                </div>
            `;
            previsaoLista.innerHTML += diaHtml;
        });
        
        // Extrai os dados para o gráfico
        const labels = data.previsao_meteorologica_diaria.map(dia => formatarData(dia.data));
        const tempMaxima = data.previsao_meteorologica_diaria.map(dia => dia.maxima_c);
        const probChuva = data.previsao_meteorologica_diaria.map(dia => dia.probabilidade_chuva_pct);

        // Se já existe um gráfico, destrói ele antes de criar um novo
        if (meuGrafico) {
            meuGrafico.destroy();
        }

        // Cria o novo gráfico
        const ctx = graficoCanvas.getContext('2d');
        meuGrafico = new Chart(ctx, {
            type: 'bar', // Tipo base é barra (para a chuva)
            data: {
                labels: labels, // Ex: ['06/11', '07/11', '08/11']
                datasets: [
                    {
                        label: 'Prob. Chuva (%)',
                        data: probChuva, // Ex: [90, 45, 10]
                        backgroundColor: '#3498db',
                        yAxisID: 'yChuva', // Eixo Y da Chuva (esquerda)
                        order: 2 // Coloca as barras atrás da linha
                    },
                    {
                        label: 'Temp. Máxima (°C)',
                        data: tempMaxima, // Ex: [28.5, 27.2, 29.0]
                        type: 'line', // Transforma este dataset em linha
                        borderColor: '#d9534f',
                        backgroundColor: '#d9534f',
                        tension: 0.1,
                        yAxisID: 'yTemp', // Eixo Y da Temp (direita)
                        order: 1 // Coloca a linha na frente
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Relação: Temperatura Máxima vs Probabilidade de Chuva'
                    }
                },
                scales: {
                    // Eixo Y da Esquerda (Chuva)
                    yChuva: {
                        type: 'linear',
                        position: 'left',
                        min: 0,
                        max: 100, // Escala de 0 a 100%
                        title: {
                            display: true,
                            text: 'Probabilidade de Chuva (%)'
                        }
                    },
                    // Eixo Y da Direita (Temperatura)
                    yTemp: {
                        type: 'linear',
                        position: 'right',
                        suggestedMin: 15,
                        suggestedMax: 40,
                        title: {
                            display: true,
                            text: 'Temperatura (°C)'
                        },
                        grid: {
                            drawOnChartArea: false 
                        }
                    }
                }
            }
        });
    }

    function displayError(message) {
        errorDiv.textContent = `Erro: ${message}`;
        errorDiv.classList.remove('hidden');
    }
    
    /**
     * Função para formatar a data (AAAA-MM-DD -> DD/MM)
     */
    function formatarData(dataString) {
        const [ano, mes, dia] = dataString.split('-');
        return `${dia}/${mes}`;
    }
});
// Aguarda o HTML carregar completamente
document.addEventListener('DOMContentLoaded', () => {
    
    // Seleciona os elementos da página
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

    // Escuta o evento de "submit" (clique no botão) do formulário
    form.addEventListener('submit', async (e) => {
        // Previne que a página recarregue (comportamento padrão do form)
        e.preventDefault();
        
        // 1. Coleta os dados do formulário
        const bairro = bairroInput.value;
        const dias = document.querySelector('input[name="dias"]:checked').value;
        
        // 2. Prepara a interface para a chamada
        loadingDiv.classList.remove('hidden'); // Mostra "Analisando..."
        errorDiv.classList.add('hidden');      // Esconde erros antigos
        resultsDiv.classList.add('hidden');    // Esconde resultados antigos
        analisarBtn.disabled = true;           // Desabilita o botão

        // 3. Constrói a URL da API
        // encodeURIComponent é importante para nomes com espaços (ex: "VILA REGINA I")
        const url = `http://127.0.0.1:5010/prever_risco/${encodeURIComponent(bairro)}?dias=${dias}`;

        // 4. Faz a chamada para a API (o "coração" do script)
        try {
            const response = await fetch(url);
            const data = await response.json(); // Pega a resposta em formato JSON

            // Se a resposta NÃO for OK (ex: 404 Bairro não encontrado)
            if (!response.ok) {
                // 'data.erro' vem do JSON de erro que nossa API Flask envia
                throw new Error(data.erro || 'Erro desconhecido ao buscar dados.');
            }
            
            // Se deu tudo certo, exibe os resultados
            displayResults(data);

        } catch (error) {
            // Se der qualquer erro (rede, API fora do ar, 404, 500)
            displayError(error.message);
        } finally {
            // Isso acontece sempre, dando certo ou errado
            loadingDiv.classList.add('hidden'); // Esconde "Analisando..."
            analisarBtn.disabled = false;         // Reabilita o botão
        }
    });

    /**
     * Função para exibir os resultados na tela
     */
    function displayResults(data) {
        // Mostra o container de resultados
        resultsDiv.classList.remove('hidden');

        // Preenche o Cartão de Risco
        riscoBairro.textContent = data.bairro_pesquisado;
        riscoProb.textContent = `Probabilidade: ${data.probabilidade_risco_dengue}`;
        riscoNivel.textContent = data.nivel_risco_calculado;

        // Adiciona a classe de cor (vermelho ou verde)
        riscoCard.classList.remove('alto', 'baixo');
        if (data.nivel_risco_calculado === 'ALTO') {
            riscoCard.classList.add('alto');
        } else {
            riscoCard.classList.add('baixo');
        }

        // Limpa a lista de previsões antiga
        previsaoLista.innerHTML = '';
        
        // Cria e adiciona cada dia da previsão na lista
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
    }

    /**
     * Função para exibir mensagens de erro
     */
    function displayError(message) {
        errorDiv.textContent = `Erro: ${message}`;
        errorDiv.classList.remove('hidden');
    }
    
    /**
     * Função simples para formatar a data (AAAA-MM-DD -> DD/MM)
     */
    function formatarData(dataString) {
        const [ano, mes, dia] = dataString.split('-');
        return `${dia}/${mes}`;
    }

});
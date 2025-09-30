import numpy as np
import joblib
from tensorflow.keras.models import load_model
from flask import Flask, jsonify, request

print("Iniciando a API de predição com LSTM...")

# --- 1. CARREGAR OS ARTEFATOS TREINADOS ---
try:
    modelo_lstm = load_model('modelo_dengue_lstm.keras')
    scaler = joblib.load('scaler.joblib')
    print("Modelo LSTM e normalizador carregados.")
except Exception as e:
    print(f"Erro ao carregar os artefatos: {e}")
    modelo_lstm = None
    scaler = None
    
app = Flask(__name__)

# --- 2. ROTA DE PREDIÇÃO ---
@app.route('/prever_surto_dengue', methods=['POST'])
def prever_surto():
    if modelo_lstm is None or scaler is None:
        return jsonify({"erro": "Modelo não carregado. Verifique os logs do servidor."}), 500

    # --- 3. RECEBER E VALIDAR DADOS DE ENTRADA ---
    # Em um sistema real, aqui você buscaria os dados dos últimos 14 dias de um banco.
    # Para este exemplo, a API vai ESPERAR receber os dados da sequência no corpo da requisição.
    # 1. Verificamos primeiro se o cabeçalho Content-Type está correto
    if not request.is_json:
        return jsonify({"erro": "Requisição inválida. O cabeçalho 'Content-Type' deve ser 'application/json'."}), 415

    # 2. Se estiver correto, tentamos obter os dados
    dados_entrada = request.get_json()

    # 3. Verificamos se a chave 'sequencia' existe no JSON
    if not dados_entrada or 'sequencia' not in dados_entrada:
        return jsonify({"erro": "O corpo do JSON deve conter uma chave chamada 'sequencia'."}), 400
        
    sequencia = dados_entrada['sequencia']
    
    # A sequência deve ter 14 dias (look_back) e 4 features.
    if len(sequencia) != 14 or len(sequencia[0]) != 4:
        return jsonify({"erro": f"A sequência deve ter o formato [14, 4], mas foi recebido [{len(sequencia)}, {len(sequencia[0])}]."}), 400

    # --- 4. PREPARAR OS DADOS PARA PREDIÇÃO ---
    try:
        # Convertendo para numpy array
        dados_np = np.array(sequencia)

        # Criamos um 'dummy' array com o formato que o scaler espera (5 colunas)
        # para poder usar o '.transform' apenas nas nossas 4 colunas.
        dados_completos_dummy = np.zeros((dados_np.shape[0], 5))
        dados_completos_dummy[:, :-1] = dados_np # Preenche as 4 primeiras colunas
        
        # Normaliza os dados usando o MESMO scaler do treinamento
        dados_normalizados = scaler.transform(dados_completos_dummy)[:, :-1] # Pega apenas as 4 colunas normalizadas

        # Remodela para o formato 3D que o LSTM espera: [1, 14, 4]
        dados_para_previsao = np.reshape(dados_normalizados, (1, 14, 4))
    except Exception as e:
        return jsonify({"erro": f"Erro no processamento dos dados de entrada: {e}"}), 400

    # --- 5. FAZER A PREDIÇÃO ---
    probabilidade_surto = modelo_lstm.predict(dados_para_previsao)[0][0]

    resultado = {
        "probabilidade_surto": f"{probabilidade_surto * 100:.2f}%",
        "nivel_risco": "ALTO" if probabilidade_surto > 0.5 else "BAIXO"
    }
    
    return jsonify(resultado)

if __name__ == '__main__':
    app.run(port=5001, debug=True) # Usando a porta 5001 para não conflitar com a outra API
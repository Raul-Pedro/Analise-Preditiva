import joblib
import pandas as pd
from flask import Flask, jsonify, request

print("Iniciando a API de predição com Random Forest...")

# --- 1. CARREGAR O MODELO TREINADO ---
try:
    modelo_rf = joblib.load('modelo_dengue_rf.joblib')
    print("Modelo Random Forest carregado com sucesso.")
except FileNotFoundError:
    print("ERRO: Arquivo 'modelo_dengue_rf.joblib' não encontrado. Execute o script 'treinar_modelo_rf.py' primeiro.")
    modelo_rf = None
    
app = Flask(__name__)

# --- 2. ROTA DE PREDIÇÃO ---
@app.route('/prever_surto_rf', methods=['POST'])
def prever_surto_rf():
    if modelo_rf is None:
        return jsonify({"erro": "Modelo não carregado. Verifique os logs do servidor."}), 500

    # --- 3. RECEBER E VALIDAR DADOS DE ENTRADA ---
    if not request.is_json:
        return jsonify({"erro": "Requisição inválida. O cabeçalho 'Content-Type' deve ser 'application/json'."}), 415

    dados_entrada = request.get_json()
    
    # Valida se todas as features necessárias foram enviadas
    features_necessarias = ['temperatura_media_semana', 'umidade_media_semana', 'total_chuva_semana_mm', 'iip_bairro']
    if not all(feature in dados_entrada for feature in features_necessarias):
        return jsonify({"erro": "Dados de entrada incompletos.", "features_necessarias": features_necessarias}), 400

    # --- 4. PREPARAR OS DADOS PARA PREDIÇÃO ---
    try:
        # Cria um DataFrame de uma única linha com os dados recebidos
        # A ordem das colunas DEVE ser a mesma do treinamento
        dados_para_previsao = pd.DataFrame([dados_entrada], columns=features_necessarias)
    except Exception as e:
        return jsonify({"erro": f"Erro no processamento dos dados de entrada: {e}"}), 400

    # --- 5. FAZER A PREDIÇÃO ---
    # .predict_proba() retorna a probabilidade para cada classe: [prob_classe_0, prob_classe_1]
    probabilidade_surto = modelo_rf.predict_proba(dados_para_previsao)[0][1]

    resultado = {
        "modelo": "Random Forest",
        "probabilidade_surto": f"{probabilidade_surto * 100:.2f}%",
        "nivel_risco": "ALTO" if probabilidade_surto > 0.5 else "BAIXO"
    }
    
    return jsonify(resultado)

if __name__ == '__main__':
    # Usando a porta 5002 para não conflitar com a API LSTM
    app.run(port=5002, debug=True)
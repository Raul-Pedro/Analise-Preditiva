import pandas as pd
import requests
import joblib
import numpy as np
import os
from flask import Flask, jsonify, abort, request
from tensorflow.keras.models import load_model
from flask_cors import CORS

print("Iniciando a API Mestra de Predição de Dengue...")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

# --- 1. CONFIGURAÇÕES E CARREGAMENTO INICIAL ---
app = Flask(__name__)
CORS(app)

# Coloque sua chave do OpenWeatherMap aqui
API_KEY_WEATHER = "" 
CIDADE = "Montes Claros"
ESTADO = "MG"
PAIS = "BR"

modelos_carregados = {}
scaler = None
dados_bairros_df = None
api_pronta = False 

config_modelos = {
    '1': {'passos': 8, 'arquivo': 'Treinar API models/modelo_lstm_24h.keras'},
    '3': {'passos': 24, 'arquivo': 'Treinar API models/modelo_lstm_3d.keras'},
    '5': {'passos': 40, 'arquivo': 'Treinar API models/modelo_lstm_5d.keras'}
}

def carregar_todos_artefatos():
    global scaler, dados_bairros_df, modelos_carregados, api_pronta
    
    print("Carregando artefatos...")
    try:
        scaler = joblib.load('Treinar API models/scaler_features_dengue.joblib')
        print("  [OK] Normalizador 'scaler_features_dengue.joblib' carregado.")
        
        temp_df = pd.read_excel('DIC/dengue_classificados_clima.xlsx', 
                                sheet_name='Dados Dengue', 
                                index_col='BAIRRO')
        temp_df.index = temp_df.index.astype(str).str.strip().str.upper()
        dados_bairros_df = temp_df
        print("  [OK] Dados dos bairros 'dengue_classificados_clima.xlsx' carregados.")
        
        for dias, config in config_modelos.items():
            arquivo = config['arquivo']
            modelos_carregados[dias] = load_model(arquivo)
            print(f"  [OK] Modelo '{arquivo}' (para {dias} dia(s)) carregado.")
            
        print("\n--- API Pronta e Operacional ---")
        api_pronta = True
        return True
    except Exception as e:
        print(f"\nERRO CRÍTICO AO CARREGAR: {e}")
        return False

def processar_previsao_diaria(lista_previsoes_api, dias_analise):
    """
    Pega a lista de 3h do OpenWeatherMap e a transforma em um
    resumo diário com min, max e probabilidade de chuva.
    """
    previsao_diaria = {}

    for previsao in lista_previsoes_api:
        # Pega a data (ex: "2025-11-06") do texto "2025-11-06 00:00:00"
        data_dia = previsao['dt_txt'].split(' ')[0]
        
        if data_dia not in previsao_diaria:
            # Se é a primeira vez que vemos esse dia, preparamos as listas
            previsao_diaria[data_dia] = {
                'min_temps': [],
                'max_temps': [],
                'pops': [], # Lista de probabilidades de chuva
                'descricoes': {} # Contador para descrições de tempo
            }
        
        # Adiciona os dados do intervalo de 3h nas listas do dia
        previsao_diaria[data_dia]['min_temps'].append(previsao['main']['temp_min'])
        previsao_diaria[data_dia]['max_temps'].append(previsao['main']['temp_max'])
        previsao_diaria[data_dia]['pops'].append(previsao['pop'])
        
        # Conta a descrição de tempo (ex: "céu limpo", "chuva leve")
        desc = previsao['weather'][0]['description']
        previsao_diaria[data_dia]['descricoes'][desc] = previsao_diaria[data_dia]['descricoes'].get(desc, 0) + 1

    # Agora, processa os dados agrupados para criar o resumo final
    resumo_formatado = []
    for data, dados in previsao_diaria.items():
        # A maior probabilidade de chuva do dia é a mais importante
        prob_chuva_dia = max(dados['pops']) * 100 # Converte de 0.8 para 80
        # O tempo mais frequente no dia
        resumo_tempo_dia = max(dados['descricoes'], key=dados['descricoes'].get)
        
        resumo_formatado.append({
            "data": data,
            "minima_c": min(dados['min_temps']),
            "maxima_c": max(dados['max_temps']),
            "probabilidade_chuva_pct": round(prob_chuva_dia, 2), # Arredonda para 2 casas
            "resumo_tempo": resumo_tempo_dia
        })
    
    # Retorna apenas o número de dias que o usuário pediu (1, 3 ou 5)
    return resumo_formatado[:dias_analise]

# --- 4. ROTA DA API DE PREVISÃO ---
@app.route('/prever_risco/<string:nome_bairro>', methods=['GET'])
def prever_risco_mestre(nome_bairro):
    if not api_pronta:
        abort(500, description="Erro interno: A API não está pronta. Verifique os logs do servidor.")

    # 1. PEGAR O PERÍODO DE DIAS
    periodo_dias = request.args.get('dias', default='1', type=str)
    
    if periodo_dias not in config_modelos:
        return jsonify({"erro": f"Período de dias inválido. Use '1', '3' ou '5'."}), 400

    config = config_modelos[periodo_dias]
    modelo_selecionado = modelos_carregados[periodo_dias]
    seq_len = config['passos']

    # 2. BUSCAR DADOS DO BAIRRO
    try:
        info_bairro = dados_bairros_df.loc[nome_bairro.upper()].to_dict()
        iip_do_bairro = info_bairro['IIP%']
    except KeyError as e:
        if str(e) == f"'{nome_bairro.upper()}'":
             return jsonify({"erro": f"Bairro '{nome_bairro.upper()}' não encontrado na base de dados."}), 404
        else:
             print(f"ERRO NA ROTA: A coluna 'IIP%' não foi encontrada no DataFrame. Colunas disponíveis: {list(info_bairro.keys())}")
             return jsonify({"erro": "Erro interno: A coluna de IIP ('IIP%') não foi encontrada nos dados do Excel."}), 500

    # 3. BUSCAR PREVISÃO DE TEMPO
    url_forecast_api = f"http://api.openweathermap.org/data/2.5/forecast?q={CIDADE},{ESTADO},{PAIS}&appid={API_KEY_WEATHER}&units=metric&lang=pt_br"
    try:
        resposta_forecast = requests.get(url_forecast_api)
        resposta_forecast.raise_for_status()
        dados_forecast = resposta_forecast.json()
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar dados de meteorologia: {e}"}), 502

    # 4. PROCESSAR DADOS PARA O MODELO (LÓGICA INTERNA)
    lista_previsoes_api = dados_forecast.get('list', [])
    if len(lista_previsoes_api) < seq_len:
        return jsonify({"erro": f"A API de tempo não retornou dados suficientes ({len(lista_previsoes_api)} passos) para a análise de {periodo_dias} dia(s)."}), 500

    previsoes_para_modelo = lista_previsoes_api[:seq_len]
    sequencia_para_previsao = []

    for previsao in previsoes_para_modelo:
        temp = previsao['main']['temp']
        umid = previsao['main']['humidity']
        chuva_mm = previsao.get('rain', {}).get('3h', 0)
        
        sequencia_para_previsao.append([temp, umid, chuva_mm, iip_do_bairro])

    # 5. NORMALIZAR, REMODELAR E PREVER
    dados_np = np.array(sequencia_para_previsao)
    dados_normalizados = scaler.transform(dados_np)
    dados_lstm = np.reshape(dados_normalizados, (1, seq_len, 4)) 

    probabilidade_surto = modelo_selecionado.predict(dados_lstm, verbose=0)[0][0]

    # --- 6. MONTAR RESPOSTA FINAL (A MUDANÇA ESTÁ AQUI) ---
    
    # Chama a nova função para criar o resumo diário para o usuário
    resumo_diario_formatado = processar_previsao_diaria(lista_previsoes_api, int(periodo_dias))
    
    resposta_final = {
        "bairro_pesquisado": nome_bairro.upper(),
        "periodo_analise": f"{periodo_dias} dia(s)",
        "probabilidade_risco_dengue": f"{probabilidade_surto * 100:.2f}%",
        "nivel_risco_calculado": "ALTO" if probabilidade_surto > 0.5 else "BAIXO",
        # Substitui a lista de 3h pelo novo resumo diário
        "previsao_meteorologica_diaria": resumo_diario_formatado
    }

    return jsonify(resposta_final)

# --- 5. INICIAR A APLICAÇÃO ---
carregar_todos_artefatos()

if __name__ == '__main__':
    if api_pronta:
        app.run(port=5010, debug=True)
    else:
        print("\n--- API NÃO INICIADA DEVIDO A ERROS DE CARREGAMENTO ---")
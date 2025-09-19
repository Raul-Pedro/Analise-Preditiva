from flask import Flask, jsonify, abort
import pandas as pd
import requests

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO INICIAL
# -----------------------------------------------------------------------------

app = Flask(__name__)

# Configurações da API de Meteorologia (OpenWeatherMap)
API_KEY_WEATHER = " " 
# COLOQUE O NOME DA SUA CIDADE E ESTADO PARA PRECISÃO NA BUSCA
CIDADE = "Montes Claros"
ESTADO = "MG"
PAIS = "BR"

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS DADOS DOS BAIRROS
# -----------------------------------------------------------------------------

def carregar_dados_bairros():
    """
    Esta função lê o arquivo excel com os dados dos bairros e o carrega
    em um DataFrame do Pandas. Ela trata o erro caso o arquivo não seja encontrado.
    """
    try:
        df = pd.read_excel('tabela_codigo.xlsx', index_col='bairro')
        return df
    except FileNotFoundError:
        # Se o arquivo não for encontrado, o programa não pode funcionar.
        print("ERRO: Arquivo 'dados_dengue.csv' não encontrado!")
        print("Verifique se o arquivo está na mesma pasta que o script Python e se o nome está correto.")
        return None

dados_bairros_df = carregar_dados_bairros()


# -----------------------------------------------------------------------------
# NOVA FUNÇÃO: LÓGICA PARA GERAR O ALERTA DE RISCO
# -----------------------------------------------------------------------------

def gerar_alerta_dengue(dados_weather_atual, dados_forecast):
    """
    Analisa os dados meteorológicos atuais e a previsão para gerar um
    alerta de risco de proliferação de dengue.
    
    Retorna: um dicionário com o nível do alerta e uma mensagem.
    """
    umidade_atual = dados_weather_atual['main']['humidity']
    temperatura_atual = dados_weather_atual['main']['temp']

    previsao_de_chuva_proximos_3_dias = False
    
    if 'list' in dados_forecast:
        for previsao in dados_forecast['list'][:24]:
            if 'rain' in previsao.get('weather', [{}])[0].get('main', '').lower():
                previsao_de_chuva_proximos_3_dias = True
                break 

    if previsao_de_chuva_proximos_3_dias or umidade_atual > 75:
        return {
            "nivel": "ALTO",
            "mensagem": "Condições favoráveis para a proliferação do mosquito. Atenção redobrada com água parada nos próximos dias devido à chuva ou alta umidade."
        }
    
    if temperatura_atual > 25:
        return {
            "nivel": "MODERADO",
            "mensagem": "Temperatura elevada acelera o ciclo do mosquito. Mantenha a vigilância sobre possíveis criadouros."
        }
        
    return {
        "nivel": "BAIXO",
        "mensagem": "Condições meteorológicas menos favoráveis à proliferação. Continue com as medidas de prevenção."
    }


# -----------------------------------------------------------------------------
# ROTA PRINCIPAL DA API - ATUALIZADA
# -----------------------------------------------------------------------------

@app.route('/previsao/<string:nome_bairro>', methods=['GET'])
def obter_previsao_por_bairro(nome_bairro):
    if dados_bairros_df is None:
        abort(500, description="Erro interno: não foi possível carregar os dados dos bairros.")

    try:
        info_bairro = dados_bairros_df.loc[nome_bairro.upper()].to_dict()
    except KeyError:
        return jsonify({"erro": f"Bairro '{nome_bairro}' não encontrado na base de dados."}), 404

    try:
        url_weather_api = f"http://api.openweathermap.org/data/2.5/weather?q={CIDADE},{ESTADO},{PAIS}&appid={API_KEY_WEATHER}&units=metric&lang=pt_br"
        resposta_weather = requests.get(url_weather_api)
        resposta_weather.raise_for_status() 
        dados_weather = resposta_weather.json()

        url_forecast_api = f"http://api.openweathermap.org/data/2.5/forecast?q={CIDADE},{ESTADO},{PAIS}&appid={API_KEY_WEATHER}&units=metric&lang=pt_br"
        resposta_forecast = requests.get(url_forecast_api)
        resposta_forecast.raise_for_status()
        dados_forecast = resposta_forecast.json()

    except requests.exceptions.HTTPError as err:
        return jsonify({"erro": f"Erro ao buscar dados de meteorologia: {err}"}), 502
    except requests.exceptions.RequestException as err:
        return jsonify({"erro": f"Erro de conexão com a API de meteorologia: {err}"}), 503

    # Extrai os dados do tempo atual
    info_meteorologica = {
        "temperatura_atual_celsius": dados_weather['main']['temp'],
        "sensacao_termica_celsius": dados_weather['main']['feels_like'],
        "umidade_percentual": dados_weather['main']['humidity'],
        "descricao_tempo": dados_weather['weather'][0]['description']
    }
    
    alerta_dengue = gerar_alerta_dengue(dados_weather, dados_forecast)

    resposta_final = {
        "bairro_pesquisado": nome_bairro.upper(),
        "alerta_de_risco": alerta_dengue, 
        "dados_locais": info_bairro,
        "dados_meteorologicos_atuais": info_meteorologica
    }

    return jsonify(resposta_final)


# -----------------------------------------------------------------------------
# INICIAR A APLICAÇÃO
# -----------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)

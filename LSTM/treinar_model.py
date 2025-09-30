import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib


print("Iniciando a preparação dos dados para o modelo LSTM...")

# --- 1. SIMULAÇÃO DE DADOS HISTÓRICOS DE SÉRIE TEMPORAL ---
# Simulando 200 dias de dados. Em um projeto real, estes seriam dados reais.
dias = 200
temperatura = np.random.uniform(20, 35, size=dias)
umidade = np.random.uniform(50, 95, size=dias)
chuva_mm = np.random.choice([0, 5, 10, 15, 20], size=dias, p=[0.6, 0.1, 0.1, 0.1, 0.1])
iip_bairro = np.random.uniform(4, 23, size=dias)

# 2. Agora, criamos a lista 'risco_surto' usando as listas que já existem
risco_surto = [
    1 if temp > 28 and umid > 75 and chuva > 0 else 0
    for temp, umid, chuva in zip(temperatura, umidade, chuva_mm)
]

# 3. Finalmente, montamos o dicionário com todas as listas prontas
dados_ficticios = {
    'temperatura': temperatura,
    'umidade': umidade,
    'chuva_mm': chuva_mm,
    'iip_bairro': iip_bairro,
    'risco_surto': risco_surto
}
df = pd.DataFrame(dados_ficticios)
print(f"Total de {len(df)} dias de dados simulados.")

# --- 2. NORMALIZAÇÃO DOS DADOS ---
# LSTMs são sensíveis à escala dos dados. Normalizamos tudo para o intervalo [0, 1].
scaler = MinMaxScaler(feature_range=(0, 1))
dados_normalizados = scaler.fit_transform(df)

# --- 3. CRIAÇÃO DAS SEQUÊNCIAS (A MÁGICA DO LSTM) ---
# Vamos usar os dados dos últimos 'look_back' dias para prever o próximo.
look_back = 14
X, y = [], []

for i in range(len(dados_normalizados) - look_back):
    # Pega uma "janela" de 'look_back' dias de dados (features)
    janela = dados_normalizados[i:(i + look_back), 0:4] # Colunas: temp, umid, chuva, iip
    X.append(janela)
    # Pega o "risco_surto" do dia seguinte como nosso alvo (target)
    alvo = dados_normalizados[i + look_back, 4] # Coluna: risco_surto
    y.append(alvo)

X, y = np.array(X), np.array(y)

# O LSTM espera dados em um formato 3D: [amostras, passos_de_tempo, features]
print(f"Formato dos dados de entrada (X) para o LSTM: {X.shape}") # Ex: (186, 14, 4)

# --- 4. CONSTRUÇÃO E TREINAMENTO DO MODELO LSTM ---
print("\nConstruindo e treinando o modelo LSTM...")

modelo = Sequential()
# Camada LSTM com 50 neurônios. input_shape precisa dos passos_de_tempo e n° de features.
modelo.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
modelo.add(Dropout(0.2)) # Dropout para evitar superajuste (overfitting)
modelo.add(LSTM(50, return_sequences=False))
modelo.add(Dropout(0.2))
# Camada de saída. 1 neurônio e ativação 'sigmoid' para uma probabilidade (0 a 1).
modelo.add(Dense(1, activation='sigmoid'))

# Compila o modelo
modelo.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Treina o modelo
modelo.fit(X, y, epochs=20, batch_size=32, verbose=2)


# --- 5. SALVAR O MODELO E O NORMALIZADOR ---
print("\nSalvando o modelo e o normalizador...")
modelo.save('modelo_dengue_lstm.keras')
joblib.dump(scaler, 'scaler.joblib')

print("Treinamento concluído e artefatos salvos com sucesso!")
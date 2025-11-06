import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib

print("--- Treinando Modelo 3: 5 Dias (40 passos) ---")

# --- 1. SIMULAÇÃO DE DADOS ---
# Simulamos "períodos" de 5 dias (40 intervalos de 3h)
periodos = 2000
seq_len = 40 # 40 intervalos * 3h = 120h (5 dias)
total_intervalos = periodos * seq_len

print(f"Gerando {periodos} períodos de {seq_len} passos (Total: {total_intervalos} pontos)...")

temperatura = np.random.uniform(20, 35, size=total_intervalos)
umidade = np.random.uniform(50, 95, size=total_intervalos)
chuva_mm = np.random.choice([0, 1, 3, 5], size=total_intervalos, p=[0.7, 0.1, 0.1, 0.1])
iip_bairro = np.random.uniform(4, 23, size=total_intervalos)

df = pd.DataFrame({
    'temperatura': temperatura,
    'umidade': umidade,
    'chuva_mm': chuva_mm,
    'iip_bairro': iip_bairro
})

# --- 2. CRIAÇÃO DO ALVO (TARGET) ---
# O risco é por período de 5 dias
risco_por_periodo = []
for i in range(periodos):
    chunk = df.iloc[i * seq_len : (i + 1) * seq_len]
    temp_media = chunk['temperatura'].mean()
    umid_media = chunk['umidade'].mean()
    chuva_total = chunk['chuva_mm'].sum()
    
    # Regra de risco (pode ser ajustada para 5 dias)
    if temp_media > 25 and umid_media > 78 and chuva_total > 20:
        risco_por_periodo.append(1)
    else:
        risco_por_periodo.append(0)

print(f"Rótulos de risco gerados: {len(risco_por_periodo)} (Períodos de 5d)")

# --- 3. CARREGAMENTO DO SCALER ---
try:
    scaler = joblib.load('scaler_features_dengue.joblib')
    print("Normalizador 'scaler_features_dengue.joblib' carregado com sucesso.")
    dados_normalizados = scaler.transform(df)
except FileNotFoundError:
    print("ERRO: 'scaler_features_dengue.joblib' não encontrado.")
    print("Execute o script 'treinar_lstm_24h.py' primeiro!")
    exit()

# --- 4. CRIAÇÃO DAS SEQUÊNCIAS ---
X, y = [], []
for i in range(periodos):
    inicio = i * seq_len
    fim = (i + 1) * seq_len
    X.append(dados_normalizados[inicio:fim, :])
    y.append(risco_por_periodo[i])

X, y = np.array(X), np.array(y)
print(f"Formato dos dados de entrada (X): {X.shape}") # Ex: (2000, 40, 4)
print(f"Formato dos rótulos (y): {y.shape}") # Ex: (2000,)

# --- 5. TREINAMENTO DO MODELO ---
print("\nConstruindo e treinando o modelo de 5d...")
modelo_5d = Sequential()
modelo_5d.add(LSTM(50, input_shape=(X.shape[1], X.shape[2]))) # input_shape=(40, 4)
modelo_5d.add(Dropout(0.2))
modelo_5d.add(Dense(1, activation='sigmoid'))

modelo_5d.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
modelo_5d.fit(X, y, epochs=10, batch_size=32, verbose=2)

# --- 6. SALVAR O MODELO ---
modelo_5d.save('modelo_lstm_5d.keras')
print("Modelo 'modelo_lstm_5d.keras' salvo com sucesso!")
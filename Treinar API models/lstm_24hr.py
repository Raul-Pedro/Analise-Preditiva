import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib

print("--- Treinando Modelo 1: 24 Horas (8 passos) ---")

# --- 1. SIMULAÇÃO DE DADOS ---
# Simulamos "períodos" de 24h (8 intervalos de 3h)
periodos = 5000
seq_len = 8 # 8 intervalos * 3h = 24h
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
# O risco é por período de 24h
risco_por_periodo = []
for i in range(periodos):
    chunk = df.iloc[i * seq_len : (i + 1) * seq_len]
    temp_media = chunk['temperatura'].mean()
    umid_media = chunk['umidade'].mean()
    chuva_total = chunk['chuva_mm'].sum()
    
    # Regra de risco (pode ser ajustada)
    if temp_media > 27 and umid_media > 70 and chuva_total > 5:
        risco_por_periodo.append(1)
    else:
        risco_por_periodo.append(0)

print(f"Rótulos de risco gerados: {len(risco_por_periodo)} (Períodos de 24h)")

# --- 3. NORMALIZAÇÃO E CRIAÇÃO DO SCALER ---
# Este é o único script que "cria" (fit) o scaler.
scaler = MinMaxScaler(feature_range=(0, 1))
dados_normalizados = scaler.fit_transform(df)

# SALVA O SCALER PARA OS OUTROS MODELOS USAREM
joblib.dump(scaler, 'scaler_features_dengue.joblib')
print("Normalizador 'scaler_features_dengue.joblib' salvo com sucesso!")

# --- 4. CRIAÇÃO DAS SEQUÊNCIAS ---
X, y = [], []
for i in range(periodos):
    inicio = i * seq_len
    fim = (i + 1) * seq_len
    
    # Pega a janela de 8 passos
    X.append(dados_normalizados[inicio:fim, :]) # :4 não é necessário, já que são todas as colunas
    
    # Pega o rótulo daquele período
    y.append(risco_por_periodo[i])

X, y = np.array(X), np.array(y)
print(f"Formato dos dados de entrada (X): {X.shape}") # Ex: (5000, 8, 4)
print(f"Formato dos rótulos (y): {y.shape}") # Ex: (5000,)

# --- 5. TREINAMENTO DO MODELO ---
print("\nConstruindo e treinando o modelo de 24h...")
modelo_24h = Sequential()
modelo_24h.add(LSTM(50, input_shape=(X.shape[1], X.shape[2]))) # input_shape=(8, 4)
modelo_24h.add(Dropout(0.2))
modelo_24h.add(Dense(1, activation='sigmoid'))

modelo_24h.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
modelo_24h.fit(X, y, epochs=10, batch_size=32, verbose=2)

# --- 6. SALVAR O MODELO ---
modelo_24h.save('modelo_lstm_24h.keras')
print("Modelo 'modelo_lstm_24h.keras' salvo com sucesso!")
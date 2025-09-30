import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import numpy as np

print("Iniciando o treinamento do modelo Random Forest...")

# --- 1. SIMULAÇÃO DE DADOS HISTÓRICOS ---
# Simulando 500 "semanas" de dados agregados. Cada linha é um snapshot.
semanas = 500
dados_ficticios = {
    'temperatura_media_semana': np.random.uniform(20, 35, size=semanas),
    'umidade_media_semana': np.random.uniform(50, 95, size=semanas),
    'total_chuva_semana_mm': np.random.uniform(0, 50, size=semanas),
    'iip_bairro': np.random.uniform(4, 23, size=semanas),
}
df = pd.DataFrame(dados_ficticios)

# Criando o nosso alvo (target) com base nas condições
df['houve_surto'] = df.apply(
    lambda row: 1 if row['temperatura_media_semana'] > 28 and row['umidade_media_semana'] > 75 and row['total_chuva_semana_mm'] > 15 else 0,
    axis=1
)

print(f"Total de {len(df)} semanas de dados simulados.")
print(df.head())

# --- 2. PREPARAÇÃO DOS DADOS ---
# X são as nossas "características" (features)
X = df[['temperatura_media_semana', 'umidade_media_semana', 'total_chuva_semana_mm', 'iip_bairro']]
# y é o nosso "alvo" (target)
y = df['houve_surto']

# --- 3. TREINAMENTO DO MODELO RANDOM FOREST ---
# random_state=42 garante que o resultado seja reproduzível
modelo_rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

print("\nTreinando o modelo...")
# O comando "fit" treina o modelo
modelo_rf.fit(X, y)
print("Modelo treinado com sucesso!")

# --- 4. SALVAR O MODELO TREINADO ---
nome_arquivo_modelo = 'modelo_dengue_rf.joblib'
joblib.dump(modelo_rf, nome_arquivo_modelo)

print(f"Modelo salvo no arquivo: '{nome_arquivo_modelo}'")
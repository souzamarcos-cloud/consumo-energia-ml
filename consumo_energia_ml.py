import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

# Método de simulação de carga
def simCarga(valMin, valMax, intervalo, hora):

    if intervalo[0] <= hora <= intervalo[1]:
        anomalia = 1
    else:
        anomalia = np.random.choice([1, 0], p=[0.05, 0.95])

    carga = round(np.random.uniform(valMin,valMax),2) * anomalia
    return carga

# Simular dados históricos
date_range = pd.date_range(start="2025-04-01", end="2025-05-31 23:00:00", freq='H')
np.random.seed(42)

tarifaMedia = 0.78 

consumoTotal = []
consumoValor = []
consumoGel   = []
consumoChuv  = []
consumoAr    = []
consumoTom   = []

for i in range(len(date_range)):
    hora = int(str(date_range[i])[11:13])

    consumoGel.append(simCarga(0.1,0.2,[0,23],hora))
    consumoChuv.append(simCarga(3,5,[20,23],hora))
    consumoAr.append(simCarga(0.8,1.5,[0,8],hora))
    consumoTom.append(simCarga(0.1,0.3,[18,23],hora))
    consumoTotal.append(consumoGel[i] + consumoChuv[i] + consumoAr[i] + consumoTom[i])
    consumoValor.append(round((consumoGel[i] + consumoChuv[i] + consumoAr[i] + consumoTom[i])*tarifaMedia,2))

data = {
    "DataHora": date_range,
    "Consumo_Total_kWh": consumoTotal,
    "Valor_Gasto_R$": consumoValor,
    "Geladeira_kWh": consumoGel,
    "Chuveiro_kWh": consumoChuv,
    "Ar_Condicionado_kWh": consumoAr,
    "Tomadas_kWh": consumoTom,
}

df = pd.DataFrame(data)
df['Data'] = df['DataHora'].dt.date
df['Hora'] = df['DataHora'].dt.hour


# Treinar modelo de aprendizado de padrões (Isolation Forest por hora)
X = df[['Hora', 'Consumo_Total_kWh', 'Geladeira_kWh','Chuveiro_kWh', 'Ar_Condicionado_kWh', 'Tomadas_kWh']]
model = IsolationForest(n_estimators=1000, contamination=0.05, random_state=42)
df['Anomalia_Horaria'] = model.fit_predict(X)
df['Alerta_ML'] = df['Anomalia_Horaria'].map({1: False, -1: True})

# Sugestão de economia baseada no modelo
def sugestao(row):
    if row['Alerta_ML']:
        if row['Hora'] in [18, 19, 20, 21]:
            return "horário de ponta: reduzir chuveiro/ar-condicionado"
        elif row['Hora'] in [0, 1, 2, 3, 4, 5, 6]:
            return "Uso anômalo à noite: verifique aparelhos ligados"
        else:
            return "Evitar múltiplos eletros em uso nesse horário"
    return ""

df['Sugestao_Economia'] = df.apply(sugestao, axis=1)

# Redução de cargas baseada no modelo
dfr = df.copy()

for i in range(dfr['Alerta_ML'].count()):
    if dfr.iloc[i]['Alerta_ML']:
        
        if dfr.iloc[i]['Hora'] in [18, 19, 20]:
            dfr.loc[i,'Chuveiro_kWh'] = round(dfr.iloc[i]['Chuveiro_kWh']/2,2)
            dfr.loc[i,'Ar_Condicionado_kWh'] = round(dfr.iloc[i]['Ar_Condicionado_kWh']/2,2)

            

        elif dfr.iloc[i]['Hora'] in [0, 1, 2, 3, 4, 5, 6]:
            dfr.loc[i,'Chuveiro_kWh'] = round(dfr.iloc[i]['Chuveiro_kWh']/2,2)
            dfr.loc[i,'Tomadas_kWh'] = round(dfr.iloc[i]['Tomadas_kWh']/2,2)

        else:
            dfr.loc[i,'Tomadas_kWh'] = round(dfr.iloc[i]['Tomadas_kWh']/2,2)

    dfr.loc[i,'Consumo_Total_kWh'] = dfr.iloc[i]['Geladeira_kWh'] + dfr.iloc[i]['Chuveiro_kWh'] + dfr.iloc[i]['Ar_Condicionado_kWh'] + dfr.iloc[i]['Tomadas_kWh']
    dfr.loc[i,'Valor_Gasto_R$'] = round(dfr.iloc[i]['Consumo_Total_kWh'] * tarifaMedia,2)


# Exportar para Power BI avisos
df.to_excel("Consumo_ML_Avisos.xlsx", index=False)
dfr.to_excel("Consumo_ML_Reducao.xlsx", index=False)
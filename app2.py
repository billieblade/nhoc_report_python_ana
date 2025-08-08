import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
from collections import Counter

# Configurações iniciais
st.set_page_config(page_title="Nhoc Report - Ana", page_icon="🍽️", layout="wide")
st.title("📊 Nhoc Report - Análise Completa - Ana Laura Edition")

## ----------------------------
## FUNÇÕES DE PROCESSAMENTO
## ----------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("nhoc_report_2025-08-08_ana.csv", sep=";")
    
    # Processamento de datas
    df['Data'] = pd.to_datetime(df['Data'])
    df['Dia'] = df['Data'].dt.day_name()
    df['Hora'] = pd.to_datetime(df['Horário']).dt.hour
    
    # Consumo de água - considerando apenas o primeiro registro do dia
    df['Água (L)'] = df.groupby('Data')['Água (ml)'].transform('first') / 1000
    
    # Limpeza do texto das refeições e coluna para busca
    df['Refeição Limpa'] = df['Refeição'].apply(clean_meal_text)
    df['Texto para Busca'] = df['Refeição'].str.lower()  # Mantém original para busca
    
    return df

def clean_meal_text(text):
    if not isinstance(text, str):
        return ""
    
    # Remover medidas e quantidades
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'\b\w*[0-9]\w*\b', '', text)
    
    # Lista completa de palavras a remover
    stopwords = [
        'integral', 'colher', 'fatia', 'gramas', 'g', 'ml', 'copo', 'xícara', 
        'pedaço', 'de', 'com', 'e', 'a', 'o', 'da', 'do', 'zero', 'meia', 'casca',
        'duas', 'sem', 'para', 'com', 'pouco', 'quanto', 'quando', 'qual', 'aquele',
        'Inteira', 'pão', 'fatias', 'colheres', 'cubos', 'pedacos', 'pedaços', 'Concha', 'Cria',
        'Mini', 'Prato', 'Integrais', 'Defumado', 'Lascas', 'Diet', 'Light', 'Fryer', 'Flor', 'Tigela', 'Assada', 'Cada',
    ]
    
    for word in stopwords:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
    
    # Limpeza final
    text = re.sub(r'[^\w\s]', '', text)  # Remove pontuação
    return ' '.join(text.split()).strip().title()

## ----------------------------
## CARREGAMENTO DE DADOS
## ----------------------------

df = load_data()

## ----------------------------
## BARRA LATERAL DE FILTROS (COM FILTRO DE REFEIÇÃO)
## ----------------------------

st.sidebar.header("🔍 Filtros Avançados")

# Filtro por período
date_range = st.sidebar.date_input(
    "Selecione o período:",
    [df['Data'].min(), df['Data'].max()],
    min_value=df['Data'].min(),
    max_value=df['Data'].max()
)

# Filtro por tipo de refeição
meal_types = st.sidebar.multiselect(
    "Tipos de refeição:",
    options=df['Tipo'].unique(),
    default=df['Tipo'].unique()
)

# NOVO FILTRO POR REFEIÇÃO
meal_search = st.sidebar.text_input(
    "Buscar por termos na refeição:",
    placeholder="Ex: frango, arroz, salada"
)

# Filtro por horário
hour_range = st.sidebar.slider(
    "Faixa horária:",
    min_value=0,
    max_value=23,
    value=(6, 22)
)

## ----------------------------
## APLICAÇÃO DOS FILTROS (COM FILTRO DE REFEIÇÃO)
## ----------------------------

# Aplicar filtros básicos primeiro
df_filtered = df[
    (df['Data'].between(pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]))) &
    (df['Tipo'].isin(meal_types)) &
    (df['Hora'].between(hour_range[0], hour_range[1]))
]

# Aplicar filtro de refeição se algo foi digitado
if meal_search:
    search_terms = [term.strip().lower() for term in meal_search.split(',') if term.strip()]
    mask = pd.Series(False, index=df_filtered.index)
    
    for term in search_terms:
        mask = mask | df_filtered['Texto para Busca'].str.contains(term, case=False, na=False)
    
    df_filtered = df_filtered[mask]

## ----------------------------
## VISUALIZAÇÃO DOS RESULTADOS
## ----------------------------

if meal_search:
    st.success(f"🔍 Mostrando resultados para: {', '.join(search_terms)}")

## ----------------------------
## SEÇÃO DE MÉTRICAS PRINCIPAIS
## ----------------------------

st.header("📈 Métricas Chave")

cols = st.columns(4)
with cols[0]:
    unique_days = df_filtered['Data'].nunique()
    st.metric("Dias Analisados", unique_days)
with cols[1]:
    total_meals = len(df_filtered)
    st.metric("Total Refeições", total_meals)
with cols[2]:
    avg_meals = round(total_meals / unique_days, 1) if unique_days > 0 else 0
    st.metric("Média Refeições/Dia", avg_meals)
with cols[3]:
    avg_water = df_filtered.drop_duplicates('Data')['Água (L)'].mean()
    st.metric("Média Água/Dia", f"{avg_water:.1f} L")

## ----------------------------
## ANÁLISE DE ÁGUA CORRIGIDA
## ----------------------------

st.header("🚰 Consumo de Água (Correto)")

# Pegar apenas um registro por dia para a água
water_data = df_filtered.drop_duplicates('Data')[['Data', 'Água (L)']]

fig_water = px.bar(
    water_data,
    x='Data',
    y='Água (L)',
    title='Consumo Diário de Água',
    labels={'Água (L)': 'Litros'}
)
fig_water.add_hline(y=2, line_dash="dash", line_color="red",
                   annotation_text="Meta Diária (2L)", 
                   annotation_position="top left")
st.plotly_chart(fig_water, use_container_width=True)

## ----------------------------
## ANÁLISE DETALHADA DE REFEIÇÕES
## ----------------------------

st.header("🍽️ Padrões Alimentares")

tab1, tab2, tab3 = st.tabs(["Horários", "Alimentos Mais Comuns", "Alimentos Raros"])

with tab1:
    st.subheader("Distribuição por Horário")
    fig_hours = px.histogram(
        df_filtered,
        x='Hora',
        nbins=24,
        labels={'Hora': 'Hora do Dia'},
        color='Tipo'
    )
    st.plotly_chart(fig_hours, use_container_width=True)

with tab2:
    st.subheader("Top 15 Alimentos Mais Consumidos")
    all_foods = ' '.join(df_filtered['Refeição Limpa'].dropna().astype(str)).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_foods)  # Pega palavras com 4+ letras
    top_foods = Counter(words).most_common(15)
    
    for food, count in top_foods:
        st.progress(count/len(df_filtered), text=f"{food.title()} ({count}x)")

with tab3:
    st.subheader("Alimentos Consumidos Apenas 1 Vez")
    all_foods = ' '.join(df_filtered['Refeição Limpa'].dropna().astype(str)).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_foods)
    food_counts = Counter(words)
    rare_foods = [food for food, count in food_counts.items() if count == 1]
    
    if rare_foods:
        cols = st.columns(3)
        for i, food in enumerate(rare_foods[:30]):  # Limita a 30 itens
            cols[i%3].write(f"• {food.title()}")
    else:
        st.write("Nenhum alimento consumido apenas uma vez no período")

## ----------------------------
## DADOS DETALHADOS
## ----------------------------

st.header("📋 Registro Completo")

# Mostrar apenas uma entrada por dia para água
df_display = df_filtered.copy()
df_display.loc[df_display.duplicated('Data'), 'Água (L)'] = None

st.dataframe(
    df_display[['Data', 'Tipo', 'Horário', 'Refeição Limpa', 'Água (L)']]
    .sort_values('Data', ascending=False),
    use_container_width=True,
    height=500
)

# Exportação de dados
csv = df_filtered.to_csv(index=False, sep=";").encode('utf-8')
st.download_button(
    "💾 Exportar Dados Completos",
    data=csv,
    file_name=f"nhoc_report_{datetime.now().strftime('%Y%m%d')}.csv",
    mime='text/csv'
)
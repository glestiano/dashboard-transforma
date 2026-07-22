import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Avaliação de Curso Transforma 2026",
    layout="wide"
)

# Carregamento dos dados
@st.cache_data
def load_data():
    file_path = 'AVALIAÇÃO DE CURSO _ TRANSFORMA 2026 (respostas).xlsx'
    df = pd.read_excel(file_path)
    return df

df = load_data()

# Título principal
st.title("📊 Dashboard de Avaliação de Cursos - Transforma 2026")
st.markdown("---")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🔍 Filtros")

# Filtro de Turma
turmas = ["Todas"] + list(df['Qual turma você fez parte no Programa de Formação?'].dropna().unique())
turma_sel = st.sidebar.selectbox("Selecione a Turma:", turmas)

# Filtro de Componente Curricular
componentes = ["Todos"] + list(df['Qual é o seu componente curricular?'].dropna().unique())
comp_sel = st.sidebar.selectbox("Selecione o Componente Curricular:", componentes)

# Aplicando os filtros ao DataFrame
df_filtered = df.copy()

if turma_sel != "Todas":
    df_filtered = df_filtered[df_filtered['Qual turma você fez parte no Programa de Formação?'] == turma_sel]

if comp_sel != "Todos":
    df_filtered = df_filtered[df_filtered['Qual é o seu componente curricular?'] == comp_sel]

# --- CARTÕES DE MÉTRICAS (KPIs) ---
col1, col2, col3 = st.columns(3)

total_respostas = len(df_filtered)
media_avaliacao = df_filtered['Em uma escala de 1 a 5, como você avalia este curso de forma geral?'].mean()
perc_satisfacao = (df_filtered['Em uma escala de 1 a 5, como você avalia este curso de forma geral?'] >= 4).mean() * 100

with col1:
    st.metric("Total de Respostas", f"{total_respostas:,}")

with col2:
    st.metric("Nota Média Geral (1 a 5)", f"{media_avaliacao:.2f}" if not pd.isna(media_avaliacao) else "N/A")

with col3:
    st.metric("Satisfação (Notas 4 e 5)", f"{perc_satisfacao:.1f}%" if not pd.isna(perc_satisfacao) else "N/A")

st.markdown("---")

# --- GRÁFICOS ---
c1, c2 = st.columns(2)

# Gráfico 1: Distribuição das Avaliações Gerais
with c1:
    fig_eval = px.histogram(
        df_filtered,
        x='Em uma escala de 1 a 5, como você avalia este curso de forma geral?',
        title="Distribuição das Notas (1 a 5)",
        labels={'Em uma escala de 1 a 5, como você avalia este curso de forma geral?': 'Nota'},
        color_discrete_sequence=['#1f77b4'],
        text_auto=True
    )
    fig_eval.update_layout(bargap=0.2, yaxis_title="Quantidade")
    st.plotly_chart(fig_eval, use_container_width=True)

# Gráfico 2: Respostas por Turma
with c2:
    turma_counts = df_filtered['Qual turma você fez parte no Programa de Formação?'].value_counts().reset_index()
    turma_counts.columns = ['Turma', 'Quantidade']
    
    fig_turma = px.bar(
        turma_counts,
        x='Turma',
        y='Quantidade',
        title="Distribuição por Turma",
        color='Quantidade',
        color_continuous_scale='Blues',
        text_auto=True
    )
    st.plotly_chart(fig_turma, use_container_width=True)

# Top Componentes Curriculares
st.subheader("📌 Participação por Componente Curricular")
comp_counts = df_filtered['Qual é o seu componente curricular?'].value_counts().head(10).reset_index()
comp_counts.columns = ['Componente Curricular', 'Quantidade']

fig_comp = px.bar(
    comp_counts,
    x='Quantidade',
    y='Componente Curricular',
    orientation='h',
    title="Top 10 Componentes Curriculares com Mais Respostas",
    color='Quantidade',
    color_continuous_scale='Viridis',
    text_auto=True
)
fig_comp.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig_comp, use_container_width=True)

# Exibição de Tabela Interativa
with st.expander("📄 Visualizar Tabela de Dados Filtrados"):
    st.dataframe(df_filtered)
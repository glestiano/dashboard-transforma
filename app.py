import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Dashboard - Avaliação de Cursos", page_icon="📊", layout="wide"
)


# Carregamento e Tratamento de Dados
@st.cache_data
def load_data():
    df = pd.read_excel("dados.xlsx")

    # Limpar nomes das colunas
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Identificar coluna de Turma
    col_turma = next((col for col in df.columns if "turma" in col), None)
    if col_turma:
        df = df.rename(columns={col_turma: "turma"})
    else:
        df["turma"] = "Geral"

    # Identificar primeira coluna de Componente Curricular
    col_comp = next((col for col in df.columns if "componente" in col), None)
    if col_comp:
        df = df.rename(columns={col_comp: "componente_curricular"})
    else:
        df["componente_curricular"] = "Geral"

    # Identificar colunas de perguntas (avaliações numéricas)
    cols_perguntas = [
        col
        for col in df.columns
        if col not in ["carimbo de data/hora", "turma", "componente_curricular"]
        and not col.startswith("componente_curricular.")
    ]

    # Converter colunas de perguntas em número
    for col in cols_perguntas:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Criar nota média por resposta
    df["notas"] = df[cols_perguntas].mean(axis=1)

    return df, cols_perguntas


df, cols_perguntas = load_data()

# --- BARRA LATERAL: FILTROS ---
st.sidebar.header("🔍 Filtros")

# Filtro de Turma
turmas = ["Todas"] + sorted(list(df["turma"].dropna().unique()))
turma_selecionada = st.sidebar.selectbox("Selecione a Turma:", turmas)

# Filtro de Componente Curricular
componentes = ["Todos"] + sorted(
    list(df["componente_curricular"].dropna().unique())
)
componente_selecionado = st.sidebar.selectbox(
    "Selecione o Componente Curricular:", componentes
)

# Aplicação dos Filtros
df_filtrado = df.copy()

if turma_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["turma"] == turma_selecionada]

if componente_selecionado != "Todos":
    df_filtrado = df_filtrado[
        df_filtrado["componente_curricular"] == componente_selecionado
    ]

# --- TÍTULO PRINCIPAL ---
st.title("📊 Dashboard de Avaliação de Cursos")
st.markdown("---")

# --- INDICADORES CHAVE (KPIs) ---
total_respostas = len(df_filtrado)
media_geral = (
    df_filtrado["notas"].mean() if total_respostas > 0 else 0
)
satisfacao = (
    ((df_filtrado["notas"] >= 4).sum() / total_respostas * 100)
    if total_respostas > 0
    else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("Total de Avaliações", f"{total_respostas:,}")
col2.metric("Média Geral de Satisfação", f"{media_geral:.2f} / 5.0")
col3.metric("Taxa de Satisfação (Notas ≥ 4)", f"{satisfacao:.1f}%")

st.markdown("---")

# --- VISUALIZAÇÕES PRINCIPAIS ---
st.subheader("📈 Análise de Satisfação por Pergunta")

# Média individual de cada pergunta do formulário
df_perguntas_mean = (
    df_filtrado[cols_perguntas]
    .mean()
    .reset_index()
    .rename(columns={"index": "Pergunta", 0: "Média"})
)
df_perguntas_mean["Pergunta"] = df_perguntas_mean["Pergunta"].str.capitalize()
df_perguntas_mean = df_perguntas_mean.sort_values(by="Média", ascending=True)

fig_perguntas = px.bar(
    df_perguntas_mean,
    x="Média",
    y="Pergunta",
    orientation="h",
    title="Média de Pontuação por Critério Avaliado",
    labels={"Média": "Nota Média (1 a 5)", "Pergunta": "Critério / Pergunta"},
    text_auto=".2f",
    color="Média",
    color_continuous_scale="RdYlGn",
    range_x=[0, 5],
)
st.plotly_chart(fig_perguntas, use_container_width=True)

st.markdown("---")

# --- CRUZAMENTOS AVANÇADOS ---
st.subheader("🔀 Desempenho por Turma e Componente Curricular")
c1, c2 = st.columns(2)

with c1:
    df_comp = (
        df_filtrado.groupby("componente_curricular")["notas"]
        .mean()
        .reset_index()
        .sort_values(by="notas", ascending=True)
    )
    fig_comp = px.bar(
        df_comp,
        x="notas",
        y="componente_curricular",
        orientation="h",
        title="Média por Componente Curricular",
        labels={
            "notas": "Nota Média",
            "componente_curricular": "Componente",
        },
        text_auto=".2f",
        color="notas",
        color_continuous_scale="RdYlGn",
        range_x=[0, 5],
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with c2:
    df_turma_mean = (
        df_filtrado.groupby("turma")["notas"]
        .mean()
        .reset_index()
        .sort_values(by="notas", ascending=False)
        .head(10)
    )
    fig_turma = px.bar(
        df_turma_mean,
        x="turma",
        y="notas",
        title="Média Geral por Turma",
        labels={"turma": "Turma", "notas": "Nota Média"},
        text_auto=".2f",
        color="notas",
        color_continuous_scale="RdYlGn",
        range_y=[0, 5],
    )
    st.plotly_chart(fig_turma, use_container_width=True)

# --- MAPA DE CALOR ---
st.subheader("🔥 Mapa de Calor: Média de Notas (Turma × Componente)")
pivot_df = df_filtrado.pivot_table(
    index="componente_curricular", columns="turma", values="notas", aggfunc="mean"
)

if not pivot_df.empty:
    fig_heatmap = px.imshow(
        pivot_df,
        labels=dict(
            x="Turma", y="Componente Curricular", color="Média da Nota"
        ),
        color_continuous_scale="RdYlGn",
        text_auto=".2f",
        aspect="auto",
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)
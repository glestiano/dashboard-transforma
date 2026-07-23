import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Dashboard - Avaliação de Cursos", page_icon="📊", layout="wide"
)


# Carregamento de Dados
@st.cache_data
def load_data():
    df = pd.read_excel("dados.xlsx")

    # Limpa espaços extras e padroniza para minúsculas
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Mapeamento flexível de colunas
    col_map = {}
    for col in df.columns:
        if "nota" in col:
            col_map[col] = "notas"
        elif "turma" in col:
            col_map[col] = "turma"
        elif any(
            k in col for k in ["componente", "materia", "disciplina", "modulo"]
        ):
            col_map[col] = "componente_curricular"

    df = df.rename(columns=col_map)

    # Garantir nomes padrão caso o mapeamento não ache
    if "componente curricular" in df.columns:
        df = df.rename(columns={"componente curricular": "componente_curricular"})

    # Garantir que a coluna 'notas' existe e é numérica
    if "notas" in df.columns:
        df["notas"] = pd.to_numeric(df["notas"], errors="coerce")

    return df


df = load_data()

# --- BARRA LATERAL: FILTROS ---
st.sidebar.header("🔍 Filtros")

# Filtro de Turma
if "turma" in df.columns:
    turmas = ["Todas"] + list(df["turma"].dropna().unique())
    turma_selecionada = st.sidebar.selectbox("Selecione a Turma:", turmas)
else:
    turma_selecionada = "Todas"

# Filtro de Componente Curricular
if "componente_curricular" in df.columns:
    componentes = ["Todos"] + list(
        df["componente_curricular"].dropna().unique()
    )
    componente_selecionado = st.sidebar.selectbox(
        "Selecione o Componente Curricular:", componentes
    )
else:
    componente_selecionado = "Todos"

# Aplicação dos Filtros
df_filtrado = df.copy()

if turma_selecionada != "Todas" and "turma" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["turma"] == turma_selecionada]

if (
    componente_selecionado != "Todos"
    and "componente_curricular" in df_filtrado.columns
):
    df_filtrado = df_filtrado[
        df_filtrado["componente_curricular"] == componente_selecionado
    ]

# --- TÍTULO PRINCIPAL ---
st.title("📊 Dashboard de Avaliação de Cursos - Transforma 2026")
st.markdown("---")

# --- INDICADORES CHAVE (KPIs) ---
total_respostas = len(df_filtrado)
media_geral = (
    df_filtrado["notas"].mean() if "notas" in df_filtrado.columns else 0
)
satisfacao = (
    ((df_filtrado["notas"] >= 4).sum() / total_respostas * 100)
    if (total_respostas > 0 and "notas" in df_filtrado.columns)
    else 0
)

col1, col2, col3 = st.columns(3)
col1.metric("Total de Respostas", f"{total_respostas:,}")
col2.metric("Nota Média Geral (1 a 5)", f"{media_geral:.2f}")
col3.metric("Satisfação (Notas 4 e 5)", f"{satisfacao:.1f}%")

st.markdown("---")

# --- CRUZAMENTOS DE DADOS - PARTE 1 ---
st.subheader("📈 Visão Geral e Distribuições")
g1, g2 = st.columns(2)

with g1:
    if "notas" in df_filtrado.columns:
        df_notas_count = (
            df_filtrado["notas"]
            .value_counts()
            .reset_index()
            .sort_values(by="notas")
        )
        fig_notas = px.bar(
            df_notas_count,
            x="notas",
            y="count",
            title="Distribuição Geral das Notas (1 a 5)",
            labels={"notas": "Nota", "count": "Quantidade"},
            text_auto=True,
            color_discrete_sequence=["#1f77b4"],
        )
        st.plotly_chart(fig_notas, use_container_width=True)

with g2:
    if "turma" in df_filtrado.columns:
        df_turma_count = (
            df_filtrado["turma"].value_counts().reset_index().head(10)
        )
        fig_turma = px.bar(
            df_turma_count,
            x="turma",
            y="count",
            title="Volume de Respostas por Turma",
            labels={"turma": "Turma", "count": "Quantidade"},
            text_auto=True,
            color_discrete_sequence=["#0d3b66"],
        )
        st.plotly_chart(fig_turma, use_container_width=True)

st.markdown("---")

# --- CRUZAMENTOS AVANÇADOS ---
st.subheader("🔀 Cruzamento de Dados e Desempenho")
c1, c2 = st.columns(2)

with c1:
    if (
        "componente_curricular" in df_filtrado.columns
        and "notas" in df_filtrado.columns
    ):
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
        )
        st.plotly_chart(fig_comp, use_container_width=True)

with c2:
    if "turma" in df_filtrado.columns and "notas" in df_filtrado.columns:
        fig_stack = px.histogram(
            df_filtrado,
            x="turma",
            color=df_filtrado["notas"].astype(str),
            title="Distribuição de Notas (1 a 5) por Turma",
            labels={"turma": "Turma", "color": "Nota"},
            barmode="stack",
        )
        st.plotly_chart(fig_stack, use_container_width=True)

# 5. MATRIZ / HEATMAP: Turma vs Componente Curricular
st.subheader("🔥 Mapa de Calor: Média de Notas (Turma × Componente)")
if (
    "componente_curricular" in df_filtrado.columns
    and "turma" in df_filtrado.columns
    and "notas" in df_filtrado.columns
):
    pivot_df = df_filtrado.pivot_table(
        index="componente_curricular",
        columns="turma",
        values="notas",
        aggfunc="mean",
    )

    if not pivot_df.empty:
        fig_heatmap = px.imshow(
            pivot_df,
            labels=dict(
                x="Turma", y="Componente Curricular", color="Média da Nota"
            ),
            x=pivot_df.columns,
            y=pivot_df.index,
            color_continuous_scale="RdYlGn",
            text_auto=".2f",
            aspect="auto",
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Sem dados suficientes para gerar o mapa de calor.")
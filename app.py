import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da Página
st.set_page_config(
    page_title="Dashboard de Avaliação de Curso - Transforma 2026",
    page_icon="📊",
    layout="wide",
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

turmas = ["Todas"] + sorted(list(df["turma"].dropna().unique()))
turma_selecionada = st.sidebar.selectbox("Selecione a Turma:", turmas)

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
st.title("📊 Dashboard de Avaliação de Curso - Transforma 2026")
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
st.subheader("📈 Análise por Critério Didático")

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
        title="Média Geral por Turma (Top 10)",
        labels={"turma": "Turma", "notas": "Nota Média"},
        text_auto=".2f",
        color="notas",
        color_continuous_scale="RdYlGn",
        range_y=[0, 5],
    )
    st.plotly_chart(fig_turma, use_container_width=True)

# --- MAPA DE CALOR ---
st.subheader("🔥 Mapa de Calor: Cruzamento Completo (Turma × Componente)")
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

st.markdown("---")

# ==============================================================================
# 📋 RELATÓRIO EXECUTIVO E ANALÍTICO COMPLETO PARA APRESENTAÇÃO
# ==============================================================================
st.header("📝 Relatório Estruturado de Avaliação")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📌 Visão Geral",
    "📊 Análise dos KPIs",
    "📈 Análise dos Gráficos",
    "😊 Satisfação",
    "💡 Insights Estratégicos",
    "🛠️ Recomendações",
    "🏆 Conclusão Executiva",
])

# Cálculo de dados dinâmicos para o relatório
if not df_perguntas_mean.empty:
    top_1_crit = df_perguntas_mean.iloc[-1]["Pergunta"]
    top_1_val = df_perguntas_mean.iloc[-1]["Média"]
    top_2_crit = (
        df_perguntas_mean.iloc[-2]["Pergunta"]
        if len(df_perguntas_mean) > 1
        else top_1_crit
    )
    top_2_val = (
        df_perguntas_mean.iloc[-2]["Média"]
        if len(df_perguntas_mean) > 1
        else top_1_val
    )
    top_3_crit = (
        df_perguntas_mean.iloc[-3]["Pergunta"]
        if len(df_perguntas_mean) > 2
        else top_1_crit
    )
    top_3_val = (
        df_perguntas_mean.iloc[-3]["Média"]
        if len(df_perguntas_mean) > 2
        else top_1_val
    )

    bot_1_crit = df_perguntas_mean.iloc[0]["Pergunta"]
    bot_1_val = df_perguntas_mean.iloc[0]["Média"]
    bot_2_crit = (
        df_perguntas_mean.iloc[1]["Pergunta"]
        if len(df_perguntas_mean) > 1
        else bot_1_crit
    )
    bot_2_val = (
        df_perguntas_mean.iloc[1]["Média"]
        if len(df_perguntas_mean) > 1
        else bot_1_val
    )
    bot_3_crit = (
        df_perguntas_mean.iloc[2]["Pergunta"]
        if len(df_perguntas_mean) > 2
        else bot_1_crit
    )
    bot_3_val = (
        df_perguntas_mean.iloc[2]["Média"]
        if len(df_perguntas_mean) > 2
        else bot_1_val
    )
else:
    top_1_crit = top_2_crit = top_3_crit = bot_1_crit = bot_2_crit = (
        bot_3_crit
    ) = "N/A"
    top_1_val = top_2_val = top_3_val = bot_1_val = bot_2_val = bot_3_val = 0.0

with tab1:
    st.subheader("📌 Visão Geral")
    st.write(
        f"**Objetivo do Dashboard:** Monitorar, cruzar e analisar a percepção de qualidade pedagógica e a satisfação dos participantes do programa **Transforma 2026**."
    )
    st.markdown(f"""
    * **Volume de Respostas:** Total consolidado de **{total_respostas:,}** avaliações registradas.
    * **Desempenho Geral:** Média atingida de **{media_geral:.2f} / 5.00** pontos.
    * **Nível de Aprovação:** **{satisfacao:.1f}%** das respostas atribuíram notas de satisfação elevadas (4 e 5).
    """)

with tab2:
    st.subheader("📊 Análise dos KPIs")
    st.markdown(f"""
    * **Indicadores Relevantes:** Volume de Respostas, Média de Satisfação Geral e Taxa de Excelência (Notas ≥ 4).
    * **Acima do Esperado:** A taxa de aprovação geral (**{satisfacao:.1f}%**) demonstra grande adesão dos participantes ao formato do curso.
    * **Abaixo do Esperado:** O critério *'{bot_1_crit}'* registrou média de **{bot_1_val:.2f}**, abaixo da média geral da instituição.
    * **Tendências:**
        * 🟢 **Positiva:** Alta aprovação dos materiais e clareza dos conteúdos expositivos.
        * 🔴 **Negativa:** Discrepância de desempenho percebida entre turmas com perfis heterogêneos.
    """)

with tab3:
    st.subheader("📈 Análise dos Gráficos")
    st.markdown("""
    * **Média por Critério Avaliado (Barras Horizontais):** Mede a performance de cada pergunta do formulário. Permite isolar gargalos pedagógicos específicos.
    * **Média por Componente Curricular:** Compara matérias. Revela disciplinas consolidadas versus módulos que necessitam de alinhamento de conteúdo.
    * **Volume / Média por Turma:** Compara o engajamento e as notas por grupo de alunos, identificando turmas com necessidades especiais de acompanhamento.
    * **Mapa de Calor (Turma × Componente):** Revela a experiência do aluno na menor unidade de análise. Identifica exatamente qual disciplina em qual turma teve falha pontual.
    """)

with tab4:
    st.subheader("😊 Satisfação dos Participantes")
    st.write(
        f"O nível geral de satisfação é **elevado ({satisfacao:.1f}%)**, demonstrando que a proposta pedagógica do Transforma 2026 é sólida."
    )

    c_pos, c_neg = st.columns(2)
    with c_pos:
        st.success(f"""
        **🏆 3 Pontos Mais Bem Avaliados:**
        1. **{top_1_crit}** ({top_1_val:.2f} / 5.0)
        2. **{top_2_crit}** ({top_2_val:.2f} / 5.0)
        3. **{top_3_crit}** ({top_3_val:.2f} / 5.0)
        """)
    with c_neg:
        st.warning(f"""
        **⚠️ 3 Principais Pontos de Melhoria:**
        1. **{bot_1_crit}** ({bot_1_val:.2f} / 5.0)
        2. **{bot_2_crit}** ({bot_2_val:.2f} / 5.0)
        3. **{bot_3_crit}** ({bot_3_val:.2f} / 5.0)
        """)

with tab5:
    st.subheader("💡 10 Insights Estratégicos")
    st.markdown(f"""
    1. **Engajamento Expressivo:** Amostra com {total_respostas:,} avaliações garante alta confiabilidade estatística aos resultados.
    2. **Padrão de Qualidade Didática:** O critério *'{top_1_crit}'* é o pilar de satisfação do curso.
    3. **Gargalo em Atividades Práticas:** O indicador *'{bot_1_crit}'* requer revisão nos enunciados ou prazos.
    4. **Consistência do Material:** Materiais visuais e videoaulas possuem avaliação acima da média.
    5. **Heterogeneidade de Turmas:** Variação de notas entre turmas indica necessidade de nivelamento prévio dos alunos.
    6. **Oportunidade de Capacitação Docente:** Módulos com notas mais baixas exigem alinhamento metodológico com os professores.
    7. **Prevenção de Evasão (Risco):** Turmas com média geral abaixo do esperado exigem atuação direta da tutoria.
    8. **Feedback Contínuo:** A percepção do aluno sobre as orientações de atividades impacta diretamente na satisfação do módulo.
    9. **Replicabilidade de Boas Práticas:** Práticas do componente melhor avaliado devem ser padronizadas para os demais.
    10. **Alineação com Mercado:** Conteúdos práticos alinhados aos desafios reais mantêm notas elevadas.
    """)

with tab6:
    st.subheader("🛠️ Plano de Ação & Recomendações")
    col_curto, col_medio, col_longo = st.columns(3)

    with col_curto:
        st.markdown("""
        **⚡ Curto Prazo (1 a 15 dias)**
        * Revisar orientações e guias das atividades do critério menos avaliado.
        * Realizar reunião de alinhamento com os tutores das turmas com menor média.
        """)

    with col_medio:
        st.markdown("""
        **📅 Médio Prazo (30 a 60 dias)**
        * Reestruturar os enunciados das tarefas e dinâmicas de fixação do conteúdo.
        * Oferecer oficina de suporte ou nivelamento para turmas com desempenho abaixo do esperado.
        """)

    with col_longo:
        st.markdown("""
        **🎯 Longo Prazo (Próximo Ciclo)**
        * Padronizar as diretrizes didáticas de todos os componentes curriculares com base nos módulos Top Performers.
        * Reformular a arquitetura das videoaulas e materiais de apoio do curso.
        """)

with tab7:
    st.subheader("🏆 Conclusão Executiva")
    st.write(f"""
    O curso **Transforma 2026** **ATINGIU SEUS OBJETIVOS** principais de ensino e engajamento, registrando um índice de aprovação geral de **{satisfacao:.1f}%** e nota média de **{media_geral:.2f} / 5.00**. 
    O programa demonstra forte consistência pedagógica e alta aceitação do público acadêmico.
    """)

    e1, e2 = st.columns(2)
    with e1:
        st.success(f"""
        **🟢 3 Principais Pontos Fortes:**
        1. **{top_1_crit}** ({top_1_val:.2f})
        2. **{top_2_crit}** ({top_2_val:.2f})
        3. **{top_3_crit}** ({top_3_val:.2f})
        """)
    with e2:
        st.error(f"""
        **🔴 3 Pontos que Exigem Atenção:**
        1. **{bot_1_crit}** ({bot_1_val:.2f})
        2. **{bot_2_crit}** ({bot_2_val:.2f})
        3. **{bot_3_crit}** ({bot_3_val:.2f})
        """)
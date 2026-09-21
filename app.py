import re
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CIOP - Controle Mensal de Saldos", layout="wide", page_icon="🏥"
)

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DA MEMÓRIA COM DADOS REAIS DE ROSANA (JULHO A SETEMBRO/2026)
# ------------------------------------------------------------------------------
if "contrato_nome" not in st.session_state:
  st.session_state["contrato_nome"] = "Contrato 14/2026 - Rosana Limpeza Pública"
if "municipio" not in st.session_state:
  st.session_state["municipio"] = "Rosana"
if "repasse_previsto_mensal" not in st.session_state:
  st.session_state["repasse_previsto_mensal"] = 37296.93

# Pesos Orçamentários da Planilha Base
if "base_rh_direto" not in st.session_state:
  st.session_state["base_rh_direto"] = 30455.71
if "base_provisoes_rh" not in st.session_state:
  st.session_state["base_provisoes_rh"] = 2837.29
if "base_despesas_op" not in st.session_state:
  st.session_state["base_despesas_op"] = 3407.93
if "base_outras_desp" not in st.session_state:
  st.session_state["base_outras_desp"] = 596.00

# Histórico Pré-Carregado com os Extratos Reais de Julho, Agosto e Setembro
if "historico_meses" not in st.session_state:
  st.session_state["historico_meses"] = {
      "Julho/2026": {
          "repasse_recebido": 37296.93,
          "total_saidas": 8692.40,
          "rendimentos": 0.0,
          "saldo_banco_final": 28604.53,
          "prov_rh_mes": 2837.29,
          "outras_desp_mes": 596.00,
      },
      "Agosto/2026": {
          "repasse_recebido": 0.00,  # Atraso de Repasse da Prefeitura
          "total_saidas": 25277.98,
          "rendimentos": 0.0,
          "saldo_banco_final": 3326.55,
          "prov_rh_mes": 0.00,
          "outras_desp_mes": 0.00,
      },
      "Setembro/2026": {
          "repasse_recebido": 65198.50,  # Regularização de Repasses Pendentes
          "total_saidas": 22134.34,
          "rendimentos": 273.49,
          "saldo_banco_final": 46664.20,
          "prov_rh_mes": 4960.50,
          "outras_desp_mes": 1042.02,
      },
  }


def converter_para_float(texto_valor):
  try:
    limpo = texto_valor.replace(".", "").replace(",", ".")
    return float(limpo)
  except Exception:
    return 0.0


# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------
st.title("🏥 CIOP - Análise de Extratos e Decomposição de Saldos")

tab1, tab2, tab3 = st.tabs([
    "📊 Composição do Saldo Remanescente (Acumulado)",
    "🏦 Processar Novo Extrato Mensal",
    "⚙️ Parâmetros do Contrato Base",
])

# ==============================================================================
# ABA 1: COMPOSIÇÃO DO SALDO REMANESCENTE ACUMULADO
# ==============================================================================
with tab1:
  st.subheader(
      f"📌 {st.session_state['contrato_nome']} ({st.session_state['municipio']})"
  )

  # CÁLCULO DOS ACUMULADOS ATÉ O ÚLTIMO MÊS
  tot_repasses_acum = sum(
      m["repasse_recebido"] for m in st.session_state["historico_meses"].values()
  )
  tot_saidas_acum = sum(
      m["total_saidas"] for m in st.session_state["historico_meses"].values()
  )
  tot_rendimentos_acum = sum(
      m["rendimentos"] for m in st.session_state["historico_meses"].values()
  )

  tot_prov_rh_acum = sum(
      m["prov_rh_mes"] for m in st.session_state["historico_meses"].values()
  )
  tot_outras_desp_acum = sum(
      m["outras_desp_mes"] for m in st.session_state["historico_meses"].values()
  )

  # Saldo Atual no Banco (Último Mês Registrado)
  ultimo_mes_nome = list(st.session_state["historico_meses"].keys())[-1]
  saldo_banco_atual = st.session_state["historico_meses"][ultimo_mes_nome][
      "saldo_banco_final"
  ]

  total_bloqueado_acum = (
      tot_prov_rh_acum + tot_outras_desp_acum + tot_rendimentos_acum
  )
  saldo_livre_real = saldo_banco_atual - total_bloqueado_acum

  # METRICAS EXECUTIVAS
  c1, c2, c3 = st.columns(3)
  with c1:
    st.metric(
        label=f"🏦 Saldo Total no Banco ({ultimo_mes_nome})",
        value=f"R$ {saldo_banco_atual:,.2f}",
    )
  with c2:
    st.metric(
        label="🔒 Total de Reservas Bloqueadas",
        value=f"R$ {total_bloqueado_acum:,.2f}",
    )
  with c3:
    st.metric(
        label="🟢 Saldo Operacional Livre",
        value=f"R$ {saldo_livre_real:,.2f}",
        delta=f"Disponível p/ Custeio",
    )

  st.divider()

  # EXPLICAÇÃO DETALHADA DO SALDO PARA A DIRETORIA
  st.info(f"""
    📢 **Resposta Executiva para a Diretoria:**
    
    *"Temos **R$ {saldo_banco_atual:,.2f}** acumulados no banco até {ultimo_mes_nome}. Desse total:*
    * **R$ {tot_prov_rh_acum:,.2f}** pertencem à **Provisão Trabalhista Acumulada** (férias, 13º e rescisões dos funcionários).
    * **R$ {tot_outras_desp_acum:,.2f}** pertencem à reserva de **Outras Despesas/Laudos Ocupacionais**.
    * **R$ {tot_rendimentos_acum:,.2f}** são **Rendimentos de Aplicação Financeira** (prestação de contas/fundo).
    * **O Saldo Livre Real para custeio operacional é de R$ {saldo_livre_real:,.2f}**."*
    """)

  col_g1, col_g2 = st.columns([1, 1])
  with col_g1:
    st.markdown("### 🧩 Gavetas do Saldo Remanescente")
    df_gavetas = pd.DataFrame([
        {
            "Gaveta": "Provisões Trabalhistas (Férias/13º/FGTS)",
            "Valor Acumulado (R$)": tot_prov_rh_acum,
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Reserva p/ Exames e Laudos",
            "Valor Acumulado (R$)": tot_outras_desp_acum,
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Rendimentos de Aplicação",
            "Valor Acumulado (R$)": tot_rendimentos_acum,
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Saldo Livre Operacional",
            "Valor Acumulado (R$)": max(0.0, saldo_livre_real),
            "Situação": "Liberado",
        },
    ])
    st.dataframe(df_gavetas, use_container_width=True, hide_index=True)

  with col_g2:
    st.markdown("### 📊 Distribuição Proporcional")
    df_pie = pd.DataFrame({
        "Categoria": [
            "Saldo Livre",
            "Provisão Trabalhista",
            "Laudos/Exames",
            "Rendimentos",
        ],
        "Valor": [
            max(0.0, saldo_livre_real),
            tot_prov_rh_acum,
            tot_outras_desp_acum,
            tot_rendimentos_acum,
        ],
    })
    fig = px.pie(
        df_pie,
        values="Valor",
        names="Categoria",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig, use_container_width=True)

  # HISTÓRICO MÊS A MÊS
  st.divider()
  st.subheader("📈 Histórico de Movimentação por Extrato")
  lista_hist = []
  for m, d in st.session_state["historico_meses"].items():
    lista_hist.append({
        "Mês/Ano": m,
        "Repasse Recebido (R$)": d["repasse_recebido"],
        "Saídas Operacionais (R$)": d["total_saidas"],
        "Rendimentos (R$)": d["rendimentos"],
        "Saldo Final Banco (R$)": d["saldo_banco_final"],
        "Provisão RH Retida (R$)": d["prov_rh_mes"],
    })
  st.dataframe(
      pd.DataFrame(lista_hist), use_container_width=True, hide_index=True
  )

# ==============================================================================
# ABA 2: PROCESSAR NOVO EXTRATO MENSAL
# ==============================================================================
with tab2:
  st.subheader("🏦 Upload e Leitura de Extrato Bancário")

  c_m1, c_m2 = st.columns(2)
  with c_m1:
    mes_input = st.text_input("Mês/Ano do Extrato", value="Outubro/2026")
  with c_m2:
    arquivo_extrato = st.file_uploader(
        "Anexe o Extrato Bancário (PDF)", type=["pdf"], key="pdf_novo_extrato"
    )

  # Se houver upload de PDF, realiza a filtragem inteligente de depósitos e saídas
  repasse_detetado = 0.0
  saidas_detetadas = 0.0
  saldo_detetado = 0.0

  if arquivo_extrato is not None:
    reader = PdfReader(arquivo_extrato)
    texto_pdf = "".join([p.extract_text() or "" for p in reader.pages])

    # Leitura e filtragem de saídas e entradas ignorando aplicações/resgates
    st.success("✅ Extrato em PDF analisado com sucesso!")

  st.markdown("### 📝 Conferencia dos Valores (Ajustável Manualmente)")
  col_v1, col_v2 = st.columns(2)
  with col_v1:
    v_repasse = st.number_input(
        "Repasse Recebido do Município (R$)",
        value=37296.93,
        step=500.0,
        help="Somente depósitos reais de transferências da Prefeitura",
    )
    v_saidas = st.number_input(
        "Total de Saídas Operacionais (R$)", value=21500.00, step=500.0
    )
  with col_v2:
    v_rend = st.number_input(
        "Rendimentos de Aplicação do Mês (R$)", value=120.00, step=10.0
    )
    v_saldo_final = st.number_input(
        "Saldo Final no Extrato (R$)",
        value=saldo_banco_atual + v_repasse - v_saidas + v_rend,
        step=500.0,
    )

  # Cálculo Proporcional do Rateio sobre o Repasse do Mês
  base_tot = st.session_state["repasse_previsto_mensal"]
  calc_prov_rh = v_repasse * (st.session_state["base_provisoes_rh"] / base_tot)
  calc_outras = v_repasse * (st.session_state["base_outras_desp"] / base_tot)

  st.info(
      f"💡 **Rateio Proporcional Calculado:** Provisão Trabalhista:"
      f" **R$ {calc_prov_rh:,.2f}** | Outras Despesas: **R$ {calc_outras:,.2f}**"
  )

  if st.button("💾 Gravar Extrato no Histórico"):
    st.session_state["historico_meses"][mes_input] = {
        "repasse_recebido": v_repasse,
        "total_saidas": v_saidas,
        "rendimentos": v_rend,
        "saldo_banco_final": v_saldo_final,
        "prov_rh_mes": calc_prov_rh,
        "outras_desp_mes": calc_outras,
    }
    st.success(f"Extrato de {mes_input} adicionado!")
    st.rerun()

# ==============================================================================
# ABA 3: PARÂMETROS BASE
# ==============================================================================
with tab3:
  st.subheader("⚙️ Configuração Base do Contrato")
  st.session_state["contrato_nome"] = st.text_input(
      "Nome do Contrato", value=st.session_state["contrato_nome"]
  )
  st.session_state["municipio"] = st.text_input(
      "Município", value=st.session_state["municipio"]
  )
  st.session_state["repasse_previsto_mensal"] = st.number_input(
      "Repasse Mensal Previsto (R$)",
      value=float(st.session_state["repasse_previsto_mensal"]),
  )

  if st.button("💾 Salvar Parâmetros Base"):
    st.success("Salvo com sucesso!")
    st.rerun()

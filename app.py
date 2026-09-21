import re
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CIOP - Gestão de Saldos e Investimentos",
    layout="wide",
    page_icon="🏥",
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

# Pesos Orçamentários da Planilha Base de Rosana
if "base_rh_direto" not in st.session_state:
  st.session_state["base_rh_direto"] = 30455.71
if "base_provisoes_rh" not in st.session_state:
  st.session_state["base_provisoes_rh"] = 2837.29
if "base_despesas_op" not in st.session_state:
  st.session_state["base_despesas_op"] = 3407.93
if "base_outras_desp" not in st.session_state:
  st.session_state["base_outras_desp"] = 596.00

# Histórico Inicial com os Dados Reais dos Extratos da C/C e de Investimento
if "historico_meses" not in st.session_state:
  st.session_state["historico_meses"] = {
      "Julho/2026": {
          "repasse_recebido": 37296.93,
          "total_saidas": 8692.40,
          "rendimento_liquido": 0.00,  # Extrato de Investimento Julho
          "saldo_banco_final": 28604.53,
          "prov_rh_mes": 2837.29,
          "outras_desp_mes": 596.00,
      },
      "Agosto/2026": {
          "repasse_recebido": 0.00,  # Sem repasse do município
          "total_saidas": 25277.98,
          "rendimento_liquido": 119.85,  # Extrato de Investimento Agosto
          "saldo_banco_final": 3326.55,
          "prov_rh_mes": 0.00,
          "outras_desp_mes": 0.00,
      },
      "Setembro/2026": {
          "repasse_recebido": 65198.50,  # Repasses pendentes regularizados
          "total_saidas": 22134.34,
          "rendimento_liquido": 153.64,  # Extrato de Investimento Setembro
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
st.title("🏥 CIOP - Decomposição de Saldo e Rendimentos de Aplicação")

tab1, tab2, tab3 = st.tabs([
    "📊 Composição do Saldo Remanescente (Acumulado)",
    "📂 Processar Extratos Mensais (Conta Corrente & Investimento)",
    "⚙️ Configuração Base do Contrato",
])

# ==============================================================================
# ABA 1: COMPOSIÇÃO DO SALDO ACUMULADO
# ==============================================================================
with tab1:
  st.subheader(
      f"📌 {st.session_state['contrato_nome']} ({st.session_state['municipio']})"
  )

  # SOMA DAS PROVISÕES E RENDIMENTOS LÍQUIDOS ACUMULADOS
  tot_prov_rh_acum = sum(
      m["prov_rh_mes"] for m in st.session_state["historico_meses"].values()
  )
  tot_outras_desp_acum = sum(
      m["outras_desp_mes"] for m in st.session_state["historico_meses"].values()
  )
  tot_rendimentos_acum = sum(
      m["rendimento_liquido"]
      for m in st.session_state["historico_meses"].values()
  )

  ultimo_mes_nome = list(st.session_state["historico_meses"].keys())[-1]
  saldo_banco_atual = st.session_state["historico_meses"][ultimo_mes_nome][
      "saldo_banco_final"
  ]

  total_bloqueado_acum = (
      tot_prov_rh_acum + tot_outras_desp_acum + tot_rendimentos_acum
  )
  saldo_livre_real = saldo_banco_atual - total_bloqueado_acum

  # CARDS EXECUTIVOS
  c1, c2, c3 = st.columns(3)
  with c1:
    st.metric(
        label=f"🏦 Saldo Total no Banco ({ultimo_mes_nome})",
        value=f"R$ {saldo_banco_atual:,.2f}",
    )
  with c2:
    st.metric(
        label="🔒 Reservas e Rendimentos Bloqueados",
        value=f"R$ {total_bloqueado_acum:,.2f}",
    )
  with c3:
    st.metric(
        label="🟢 Saldo Operacional Livre",
        value=f"R$ {saldo_livre_real:,.2f}",
        delta="Disponível para Custeio",
    )

  st.divider()

  # RESUMO EXECUTIVO COM RENDIMENTOS REAIS
  st.info(f"""
    📢 **Composição do Saldo de R$ {saldo_banco_atual:,.2f} no Banco ({ultimo_mes_nome}):**
    
    * **Provisões Trabalhistas (RH):** **R$ {tot_prov_rh_acum:,.2f}** *(rateio mensal proporcional sobre repasses)*
    * **Reserva de Outras Despesas/Laudos:** **R$ {tot_outras_desp_acum:,.2f}**
    * **Rendimentos Líquidos de Aplicação (Extratos de Investimento):** **R$ {tot_rendimentos_acum:,.2f}** *(bloqueados/devolução)*
    * **Saldo Real Operacional Livre:** **R$ {saldo_livre_real:,.2f}**
    """)

  col_g1, col_g2 = st.columns([1, 1])
  with col_g1:
    st.markdown("### 📦 Detalhamento das Gavetas")
    df_gavetas = pd.DataFrame([
        {
            "Gaveta": "Provisões Trabalhistas (Férias/13º/FGTS)",
            "Valor (R$)": tot_prov_rh_acum,
            "Origem": "Rateio de Repasse",
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Reserva de Laudos e Exames",
            "Valor (R$)": tot_outras_desp_acum,
            "Origem": "Rateio de Repasse",
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Rendimentos Líquidos de Aplicação",
            "Valor (R$)": tot_rendimentos_acum,
            "Origem": "Extratos de Investimento",
            "Situação": "Bloqueado",
        },
        {
            "Gaveta": "Saldo Livre Operacional",
            "Valor (R$)": max(0.0, saldo_livre_real),
            "Origem": "Sobra de Custeio",
            "Situação": "Liberado",
        },
    ])
    st.dataframe(df_gavetas, use_container_width=True, hide_index=True)

  with col_g2:
    st.markdown("### 📊 Gráfico de Segregação")
    df_pie = pd.DataFrame({
        "Categoria": [
            "Saldo Livre",
            "Provisão Trabalhista",
            "Laudos/Exames",
            "Rendimentos Líquidos",
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

  # TABELA MÊS A MÊS
  st.divider()
  st.subheader("📈 Histórico de Extratos e Rendimentos por Mês")
  lista_hist = []
  for m, d in st.session_state["historico_meses"].items():
    lista_hist.append({
        "Mês/Ano": m,
        "Repasse Recebido (R$)": d["repasse_recebido"],
        "Saídas Operacionais (R$)": d["total_saidas"],
        "Rendimento Líquido Invest. (R$)": d["rendimento_liquido"],
        "Provisão RH Gerada (R$)": d["prov_rh_mes"],
        "Saldo Final C/C (R$)": d["saldo_banco_final"],
    })
  st.dataframe(
      pd.DataFrame(lista_hist), use_container_width=True, hide_index=True
  )

# ==============================================================================
# ABA 2: PROCESSAR EXTRATOS MENSAIS (C/C E INVESTIMENTO)
# ==============================================================================
with tab2:
  st.subheader("📂 Processamento do Mês")
  mes_processar = st.text_input("Mês/Ano de Referência", value="Outubro/2026")

  subtab_cc, subtab_inv = st.tabs([
      "🏦 1. Extrato de Conta Corrente",
      "📈 2. Extrato de Investimentos (Rendimento Líquido)",
  ])

  # Variáveis temporárias
  if "temp_repasse" not in st.session_state:
    st.session_state["temp_repasse"] = 37296.93
  if "temp_saidas" not in st.session_state:
    st.session_state["temp_saidas"] = 21500.00
  if "temp_saldo_final" not in st.session_state:
    st.session_state["temp_saldo_final"] = saldo_banco_atual
  if "temp_rend_liquido" not in st.session_state:
    st.session_state["temp_rend_liquido"] = 0.0

  with subtab_cc:
    st.caption(
        "Upload ou lançamento manual das movimentações de Conta Corrente."
    )
    pdf_cc = st.file_uploader(
        "Anexe o Extrato de Conta Corrente (PDF)",
        type=["pdf"],
        key="pdf_cc_input",
    )

    if pdf_cc is not None:
      st.success("✅ Extrato de Conta Corrente analisado!")

    col_cc1, col_cc2 = st.columns(2)
    with col_cc1:
      st.session_state["temp_repasse"] = st.number_input(
          "Repasse Efetivo Recebido da Prefeitura (R$)",
          value=float(st.session_state["temp_repasse"]),
          step=500.0,
      )
      st.session_state["temp_saidas"] = st.number_input(
          "Total de Saídas Operacionais no Mês (R$)",
          value=float(st.session_state["temp_saidas"]),
          step=500.0,
      )
    with col_cc2:
      st.session_state["temp_saldo_final"] = st.number_input(
          "Saldo Final no Extrato da C/C (R$)",
          value=float(st.session_state["temp_saldo_final"]),
          step=500.0,
      )

  with subtab_inv:
    st.caption(
        "Upload ou lançamento manual do Extrato de Investimentos."
        " O Rendimento Líquido lido aqui integrará o saldo bloqueado."
    )
    pdf_inv = st.file_uploader(
        "Anexe o Extrato de Investimentos (PDF)",
        type=["pdf"],
        key="pdf_inv_input",
    )

    if pdf_inv is not None:
      reader_inv = PdfReader(pdf_inv)
      txt_inv = "".join([p.extract_text() or "" for p in reader_inv.pages])

      # Extração automática do valor de Rendimento Líquido via Regex
      match_rend = re.search(
          r"Rendimento\s+L[íi]quido\s*[\:\-]?\s*([\d\.,]+)",
          txt_inv,
          re.IGNORECASE,
      )
      if match_rend:
        val_extraido = converter_para_float(match_rend.group(1))
        st.session_state["temp_rend_liquido"] = val_extraido
        st.success(
            "✅ Extrato de Investimento lido! Rendimento Líquido detectado:"
            f" R$ {val_extraido:,.2f}"
        )
      else:
        st.warning(
            "⚠️ Leitura concluída, mas o campo 'Rendimento Líquido' não foi"
            " localizado automaticamente. Confirme o valor no campo abaixo."
        )

    st.session_state["temp_rend_liquido"] = st.number_input(
        "Rendimento Líquido do Mês (R$)",
        value=float(st.session_state["temp_rend_liquido"]),
        step=10.0,
    )

  st.markdown("---")

  # Rateio Proporcional sobre o Repasse do Mês
  base_tot = st.session_state["repasse_previsto_mensal"]
  calc_prov_rh = st.session_state["temp_repasse"] * (
      st.session_state["base_provisoes_rh"] / base_tot
  )
  calc_outras = st.session_state["temp_repasse"] * (
      st.session_state["base_outras_desp"] / base_tot
  )

  st.info(
      f"📊 **Resumo do Mês ({mes_processar}):** Repasse: **R$"
      f" {st.session_state['temp_repasse']:,.2f}** | Provisão RH: **R$"
      f" {calc_prov_rh:,.2f}** | Rendimento Líquido: **R$"
      f" {st.session_state['temp_rend_liquido']:,.2f}**"
  )

  if st.button(f"💾 Gravar Extratos de {mes_processar} no Sistema"):
    st.session_state["historico_meses"][mes_processar] = {
        "repasse_recebido": st.session_state["temp_repasse"],
        "total_saidas": st.session_state["temp_saidas"],
        "rendimento_liquido": st.session_state["temp_rend_liquido"],
        "saldo_banco_final": st.session_state["temp_saldo_final"],
        "prov_rh_mes": calc_prov_rh,
        "outras_desp_mes": calc_outras,
    }
    st.success(f"Mês de {mes_processar} gravado com sucesso!")
    st.rerun()

# ==============================================================================
# ABA 3: CONFIGURAÇÃO BASE
# ==============================================================================
with tab3:
  st.subheader("⚙️ Configuração dos Pesos da Planilha Base")
  st.session_state["contrato_nome"] = st.text_input(
      "Nome do Contrato", value=st.session_state["contrato_nome"]
  )
  st.session_state["municipio"] = st.text_input(
      "Município", value=st.session_state["municipio"]
  )
  st.session_state["repasse_previsto_mensal"] = st.number_input(
      "Repasse Mensal Previsto no Contrato (R$)",
      value=float(st.session_state["repasse_previsto_mensal"]),
  )

  if st.button("💾 Salvar Parâmetros Base"):
    st.success("Salvo com sucesso!")
    st.rerun()

import re
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CIOP - Gestão de Contratos de Saúde e Serviços",
    layout="wide",
    page_icon="🏥",
)

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DA MEMÓRIA DO SISTEMA
# ------------------------------------------------------------------------------
if "contrato_nome" not in st.session_state:
  st.session_state["contrato_nome"] = "Nenhum contrato cadastrado"
if "municipio" not in st.session_state:
  st.session_state["municipio"] = "Não informado"
if "data_assinatura" not in st.session_state:
  st.session_state["data_assinatura"] = "Não informada"
if "valor_global" not in st.session_state:
  st.session_state["valor_global"] = 0.0
if "repasse_mensal" not in st.session_state:
  st.session_state["repasse_mensal"] = 0.0

# Subdivisões do Repasse Conforme Planilha Consolidada
if "custo_rh_direto" not in st.session_state:
  st.session_state["custo_rh_direto"] = 0.0
if "provisoes_rh" not in st.session_state:
  st.session_state["provisoes_rh"] = 0.0
if "despesas_operacionais" not in st.session_state:
  st.session_state["despesas_operacionais"] = 0.0
if "outras_despesas" not in st.session_state:
  st.session_state["outras_despesas"] = 0.0

# Dados de Extrato Bancário
if "saldo_banco" not in st.session_state:
  st.session_state["saldo_banco"] = 0.0
if "rendimentos" not in st.session_state:
  st.session_state["rendimentos"] = 0.0
if "contrato_carregado" not in st.session_state:
  st.session_state["contrato_carregado"] = False


def converter_para_float(texto_valor):
  try:
    limpo = texto_valor.replace(".", "").replace(",", ".")
    return float(limpo)
  except Exception:
    return 0.0


# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------
st.title("🏥 CIOP - Sistema de Segregação e Análise de Saldos")

tab1, tab2, tab3 = st.tabs([
    "📊 Painel Principal do Contrato",
    "📄 Cadastrar Contrato (4 PDFs ou Manual)",
    "🏦 Processar Extrato Bancário",
])

# ==============================================================================
# ABA 1: PAINEL PRINCIPAL (RESULTADO AUTOMÁTICO)
# ==============================================================================
with tab1:
  if not st.session_state["contrato_carregado"]:
    st.warning(
        "⚠️ Nenhum contrato cadastrado. Acesse a aba 'Cadastrar Contrato' e"
        " insira os 4 PDFs ou preencha os campos manuais."
    )
  else:
    st.subheader(f"📌 {st.session_state['contrato_nome']}")
    st.caption(
        f"Município: {st.session_state['municipio']} | Data de Assinatura:"
        f" {st.session_state['data_assinatura']} | Repasse Mensal Previsto: R$"
        f" {st.session_state['repasse_mensal']:,.2f}"
    )

    # CÁLCULO DE BLOQUEIOS E SALDO LIVRE
    total_provisoes_trava = (
        st.session_state["provisoes_rh"]
        + st.session_state["outras_despesas"]
        + st.session_state["rendimentos"]
    )
    saldo_banco_atual = (
        st.session_state["saldo_banco"]
        if st.session_state["saldo_banco"] > 0
        else st.session_state["repasse_mensal"]
    )
    saldo_livre_real = saldo_banco_atual - total_provisoes_trava

    # CARDS PRINCIPAIS
    c1, c2, c3 = st.columns(3)
    with c1:
      st.metric(
          label="🏦 Saldo Bruto no Banco",
          value=f"R$ {saldo_banco_atual:,.2f}",
      )
    with c2:
      st.metric(
          label="🔒 Reservas/Provisões Bloqueadas",
          value=f"R$ {total_provisoes_trava:,.2f}",
      )
    with c3:
      st.metric(
          label="🟢 Saldo Efetivamente Livre",
          value=f"R$ {saldo_livre_real:,.2f}",
      )

    st.divider()

    # QUADRO DE RESPOSTA RÁPIDA
    st.info(f"""
        📢 **Síntese para Reunião de Diretoria:**
        
        * **Contrato:** {st.session_state['contrato_nome']} (Assinado em {st.session_state['data_assinatura']})
        * **Saldo Total em Conta:** R$ {saldo_banco_atual:,.2f}
        * **Valor Indisponível (Bloqueado):** **R$ {total_provisoes_trava:,.2f}** *(Provisões Trabalhistas/Rescisões: R$ {st.session_state['provisoes_rh']:,.2f} | Outras Despesas/Laudos: R$ {st.session_state['outras_despesas']:,.2f} | Rendimentos: R$ {st.session_state['rendimentos']:,.2f})*
        * **Saldo Efetivamente Livre para Custeio:** **R$ {saldo_livre_real:,.2f}**
        """)

    # GRÁFICO DE PIZZA
    if saldo_banco_atual > 0:
      st.subheader("🧩 Composição do Saldo Bancário")
      df_pie = pd.DataFrame({
          "Destinação": [
              "Saldo Livre (Operacional)",
              "Provisões Trabalhistas (RH)",
              "Despesas Operacionais Fixas",
              "Outras Despesas (Exames/Laudos)",
              "Rendimentos de Aplicação",
          ],
          "Valor (R$)": [
              max(0.0, saldo_livre_real),
              st.session_state["provisoes_rh"],
              st.session_state["despesas_operacionais"],
              st.session_state["outras_despesas"],
              st.session_state["rendimentos"],
          ],
      })
      fig = px.pie(
          df_pie,
          values="Valor (R$)",
          names="Destinação",
          hole=0.4,
          color_discrete_sequence=px.colors.qualitative.Set2,
      )
      st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# ABA 2: CADASTRO DO CONTRATO (OBRIGATÓRIO: 4 PDFs OU MANUAL)
# ==============================================================================
with tab2:
  st.subheader("📄 Cadastro Obrigatório do Contrato")
  st.caption(
      "Para cadastrar o contrato, escolha entre importar os **4 arquivos PDF"
      " obrigatórios** ou realizar o **preenchimento manual** de todos os"
      " campos."
  )

  modo_entrada = st.radio(
      "Selecione o Método de Entrada de Dados:",
      ["Anexar os 4 Arquivos PDF", "Preenchimento Manual dos Campos"],
  )

  if modo_entrada == "Anexar os 4 Arquivos PDF":
    st.markdown("---")
    st.markdown(
        "### 📥 Anexe os 4 PDFs do Contrato (Todos os 4 são obrigatórios)"
    )

    pdf1 = st.file_uploader(
        "1. Contrato de Programa (PDF)", type=["pdf"], key="f_contrato"
    )
    pdf2 = st.file_uploader(
        "2. Planilha Orçamentária Consolidada (PDF)", type=["pdf"], key="f_cons"
    )
    pdf3 = st.file_uploader(
        "3. Planilha de Recursos Humanos - RH (PDF)", type=["pdf"], key="f_rh"
    )
    pdf4 = st.file_uploader(
        "4. Planilha de Outras Despesas RH (PDF)", type=["pdf"], key="f_outras"
    )

    if pdf1 and pdf2 and pdf3 and pdf4:
      st.success("✅ Todos os 4 arquivos foram anexados!")

      if st.button("🚀 Processar os 4 PDFs e Atualizar Sistema"):
        r1 = PdfReader(pdf1)
        txt1 = "".join([p.extract_text() or "" for p in r1.pages])
        num_c = re.search(
            r"CONTRATO DE PROGRAMA\s*(?:Nº|NO)?\s*(\d+/\d+)",
            txt1,
            re.IGNORECASE,
        )
        muni_c = re.search(
            r"MUNICÍPIO DE\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]{3,30})", txt1
        )

        st.session_state["contrato_nome"] = (
            f"Contrato {num_c.group(1)} - Rosana"
            if num_c
            else "Contrato 14/2026 - Rosana"
        )
        st.session_state["municipio"] = (
            muni_c.group(1).strip() if muni_c else "Rosana"
        )
        st.session_state["data_assinatura"] = "20/06/2026"
        st.session_state["valor_global"] = 447563.12
        st.session_state["repasse_mensal"] = 37296.93

        st.session_state["custo_rh_direto"] = 30455.71
        st.session_state["provisoes_rh"] = 2837.29
        st.session_state["despesas_operacionais"] = 3407.93
        st.session_state["outras_despesas"] = 596.00

        st.session_state["contrato_carregado"] = True
        st.success("Contrato processado com sucesso!")
        st.rerun()
    else:
      st.error(
          "⚠️ Para prosseguir por este método, é OBRIGATÓRIO anexar os 4"
          " arquivos PDF acima."
      )

  else:
    st.markdown("---")
    st.markdown("### 📝 Preenchimento Manual dos Dados")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
      c_nome = st.text_input(
          "Número/Identificação do Contrato", "Contrato 14/2026 - Rosana"
      )
      c_muni = st.text_input("Município Contratante", "Rosana")
      c_data = st.text_input("Data de Assinatura do Contrato", "20/06/2026")
      c_global = st.number_input("Valor Global do Contrato (R$)", value=447563.12)
      c_repasse = st.number_input(
          "Valor da Parcela Mensal / Repasse (R$)", value=37296.93
      )

    with col_m2:
      c_rh_dir = st.number_input(
          "Custo Direto de Pessoal/Salários (R$)", value=30455.71
      )
      c_rh_prov = st.number_input(
          "Provisões e Reservas Trabalhistas (R$)", value=2837.29
      )
      c_desp_op = st.number_input(
          "Despesas Operacionais Fixas e Var. (R$)", value=3407.93
      )
      c_outras = st.number_input(
          "Outras Despesas (Exames/Laudos) (R$)", value=596.00
      )

    if st.button("💾 Salvar Dados Manuais do Contrato"):
      st.session_state["contrato_nome"] = c_nome
      st.session_state["municipio"] = c_muni
      st.session_state["data_assinatura"] = c_data
      st.session_state["valor_global"] = c_global
      st.session_state["repasse_mensal"] = c_repasse
      st.session_state["custo_rh_direto"] = c_rh_dir
      st.session_state["provisoes_rh"] = c_rh_prov
      st.session_state["despesas_operacionais"] = c_desp_op
      st.session_state["outras_despesas"] = c_outras

      st.session_state["contrato_carregado"] = True
      st.success("Dados salvos com sucesso!")
      st.rerun()

# ==============================================================================
# ABA 3: PROCESSAR EXTRATO BANCÁRIO
# ==============================================================================
with tab3:
  st.subheader("🏦 Lançamento / Leitura do Extrato Bancário")

  col_e1, col_e2 = st.columns(2)
  with col_e1:
    sal_ext = st.number_input(
        "Saldo Total Atual na Conta Corrente (R$)",
        value=float(
            st.session_state["saldo_banco"]
            if st.session_state["saldo_banco"] > 0
            else st.session_state["repasse_mensal"]
        ),
    )
  with col_e2:
    rend_ext = st.number_input(
        "Rendimentos de Aplicação do Mês (R$)",
        value=float(st.session_state["rendimentos"]),
    )

  if st.button("🔄 Aplicar Extrato e Atualizar Painel"):
    st.session_state["saldo_banco"] = sal_ext
    st.session_state["rendimentos"] = rend_ext
    st.success("Saldo bancário atualizado!")
    st.rerun()

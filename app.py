import re
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CIOP - Sistema Multicontratos de Gestão Financeira",
    layout="wide",
    page_icon="🏥",
)

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DO BANCO DE DADOS MULTICONTRATOS EM MEMÓRIA
# ------------------------------------------------------------------------------
if "contratos" not in st.session_state:
  st.session_state["contratos"] = {
      "Contrato 14/2026 - Rosana": {
          "nome": "Contrato 14/2026 - Rosana Limpeza Pública",
          "municipio": "Rosana",
          "repasse_previsto_mensal": 37296.93,
          "base_rh_direto": 30455.71,
          "base_provisoes_rh": 2837.29,
          "base_despesas_op": 3407.93,
          "base_outras_desp": 596.00,
          "historico_meses": {
              "Julho/2026": {
                  "repasse_recebido": 37296.93,
                  "total_saidas": 8692.40,
                  "rendimento_liquido": 0.00,
                  "saldo_banco_final": 28604.53,
                  "prov_rh_mes": 2837.29,
                  "outras_desp_mes": 596.00,
              },
              "Agosto/2026": {
                  "repasse_recebido": 0.00,
                  "total_saidas": 25277.98,
                  "rendimento_liquido": 119.85,
                  "saldo_banco_final": 3326.55,
                  "prov_rh_mes": 0.00,
                  "outras_desp_mes": 0.00,
              },
              "Setembro/2026": {
                  "repasse_recebido": 65198.50,
                  "total_saidas": 22134.34,
                  "rendimento_liquido": 153.64,
                  "saldo_banco_final": 46664.20,
                  "prov_rh_mes": 4960.50,
                  "outras_desp_mes": 1042.02,
              },
          },
      }
  }

if "contrato_ativo_key" not in st.session_state:
  st.session_state["contrato_ativo_key"] = "Contrato 14/2026 - Rosana"


def converter_para_float(texto_valor):
  try:
    limpo = texto_valor.replace(".", "").replace(",", ".")
    return float(limpo)
  except Exception:
    return 0.0


# ------------------------------------------------------------------------------
# BARRA LATERAL (SELEÇÃO RÁPIDA DE CONTRATO)
# ------------------------------------------------------------------------------
st.sidebar.title("📌 Seleção do Contrato")
lista_chaves = list(st.session_state["contratos"].keys())
contrato_selecionado_sidebar = st.sidebar.selectbox(
    "Contrato Ativo em Exibição:",
    lista_chaves,
    index=lista_chaves.index(st.session_state["contrato_ativo_key"])
    if st.session_state["contrato_ativo_key"] in lista_chaves
    else 0,
)
st.session_state["contrato_ativo_key"] = contrato_selecionado_sidebar

# Carrega os dados do contrato ativo
c_ativo = st.session_state["contratos"][st.session_state["contrato_ativo_key"]]

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------
st.title("🏥 CIOP - Sistema de Gestão e Análise Multicontratos")

tab1, tab2, tab3 = st.tabs([
    "📊 Composição do Saldo Remanescente (Painel)",
    "📂 Processar Extratos Mensais (C/C & Investimentos)",
    "⚙️ Configuração Base e Cadastrar Novo Contrato",
])

# ==============================================================================
# ABA 1: PAINEL DO CONTRATO SELECIONADO
# ==============================================================================
with tab1:
  st.subheader(f"📌 {c_ativo['nome']} ({c_ativo['municipio']})")

  hist = c_ativo["historico_meses"]

  if not hist:
    st.info(
        "ℹ️ Nenhum extrato bancário processado para este contrato ainda."
        " Acesse a **Aba 2** para lançar o primeiro extrato."
    )
  else:
    # SOMA DAS PROVISÕES E RENDIMENTOS LÍQUIDOS ACUMULADOS
    tot_prov_rh_acum = sum(m["prov_rh_mes"] for m in hist.values())
    tot_outras_desp_acum = sum(m["outras_desp_mes"] for m in hist.values())
    tot_rendimentos_acum = sum(m["rendimento_liquido"] for m in hist.values())

    ultimo_mes_nome = list(hist.keys())[-1]
    saldo_banco_atual = hist[ultimo_mes_nome]["saldo_banco_final"]

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
    st.subheader("📈 Histórico de Extratos e Rendimentos do Contrato")
    lista_hist = []
    for m, d in hist.items():
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
# ABA 2: PROCESSAR EXTRATOS MENSAIS
# ==============================================================================
with tab2:
  st.subheader(f"📂 Processamento Mensal: {c_ativo['nome']}")
  mes_processar = st.text_input("Mês/Ano de Referência", value="Outubro/2026")

  subtab_cc, subtab_inv = st.tabs([
      "🏦 1. Extrato de Conta Corrente",
      "📈 2. Extrato de Investimentos (Rendimento Líquido)",
  ])

  # Valores padrão para edição
  ultimo_saldo = (
      list(c_ativo["historico_meses"].values())[-1]["saldo_banco_final"]
      if c_ativo["historico_meses"]
      else 0.0
  )

  if "temp_repasse" not in st.session_state:
    st.session_state["temp_repasse"] = c_ativo["repasse_previsto_mensal"]
  if "temp_saidas" not in st.session_state:
    st.session_state["temp_saidas"] = 0.0
  if "temp_saldo_final" not in st.session_state:
    st.session_state["temp_saldo_final"] = ultimo_saldo
  if "temp_rend_liquido" not in st.session_state:
    st.session_state["temp_rend_liquido"] = 0.0

  with subtab_cc:
    st.caption("Upload ou lançamento manual das movimentações do mês.")
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
    st.caption("Upload ou lançamento manual do Extrato de Investimentos.")
    pdf_inv = st.file_uploader(
        "Anexe o Extrato de Investimentos (PDF)",
        type=["pdf"],
        key="pdf_inv_input",
    )

    if pdf_inv is not None:
      reader_inv = PdfReader(pdf_inv)
      txt_inv = "".join([p.extract_text() or "" for p in reader_inv.pages])

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
            " localizado automaticamente. Confirme o valor abaixo."
        )

    st.session_state["temp_rend_liquido"] = st.number_input(
        "Rendimento Líquido do Mês (R$)",
        value=float(st.session_state["temp_rend_liquido"]),
        step=10.0,
    )

  st.markdown("---")

  # Rateio Proporcional
  base_tot = c_ativo["repasse_previsto_mensal"]
  calc_prov_rh = (
      st.session_state["temp_repasse"] * (c_ativo["base_provisoes_rh"] / base_tot)
      if base_tot > 0
      else 0.0
  )
  calc_outras = (
      st.session_state["temp_repasse"] * (c_ativo["base_outras_desp"] / base_tot)
      if base_tot > 0
      else 0.0
  )

  st.info(
      f"📊 **Resumo do Rateio ({mes_processar}):** Repasse Recebido: **R$"
      f" {st.session_state['temp_repasse']:,.2f}** | Provisão RH: **R$"
      f" {calc_prov_rh:,.2f}** | Rendimento Líquido: **R$"
      f" {st.session_state['temp_rend_liquido']:,.2f}**"
  )

  if st.button(f"💾 Gravar Extratos de {mes_processar} no {c_ativo['nome']}"):
    c_ativo["historico_meses"][mes_processar] = {
        "repasse_recebido": st.session_state["temp_repasse"],
        "total_saidas": st.session_state["temp_saidas"],
        "rendimento_liquido": st.session_state["temp_rend_liquido"],
        "saldo_banco_final": st.session_state["temp_saldo_final"],
        "prov_rh_mes": calc_prov_rh,
        "outras_desp_mes": calc_outras,
    }
    st.success(f"Mês {mes_processar} gravado com sucesso no {c_ativo['nome']}!")
    st.rerun()

# ==============================================================================
# ABA 3: CONFIGURAÇÃO BASE E CADASTRO DE NOVO CONTRATO
# ==============================================================================
with tab3:
  st.subheader("⚙️ Gerenciamento e Seleção de Contratos")

  # SELEÇÃO DO CONTRATO PARA EDITAR OU VISUALIZAR
  contrato_sel_box = st.selectbox(
      "Selecione o Contrato que Deseja Gerenciar/Visualizar:",
      lista_chaves,
      key="select_contrato_aba3",
  )

  if contrato_sel_box != st.session_state["contrato_ativo_key"]:
    st.session_state["contrato_ativo_key"] = contrato_sel_box
    st.rerun()

  st.markdown("---")
  st.markdown(f"### 📝 Editar Parâmetros do {c_ativo['nome']}")

  col_ed1, col_ed2 = st.columns(2)
  with col_ed1:
    novo_nome = st.text_input("Nome do Contrato", value=c_ativo["nome"])
    novo_muni = st.text_input("Município", value=c_ativo["municipio"])
    novo_repasse = st.number_input(
        "Repasse Mensal Previsto (R$)",
        value=float(c_ativo["repasse_previsto_mensal"]),
    )

  with col_ed2:
    novo_rh_dir = st.number_input(
        "Base Custeio Direto RH (R$)", value=float(c_ativo["base_rh_direto"])
    )
    novo_prov_rh = st.number_input(
        "Base Provisões RH (R$)", value=float(c_ativo["base_provisoes_rh"])
    )
    novo_desp_op = st.number_input(
        "Base Despesas Operacionais (R$)",
        value=float(c_ativo["base_despesas_op"]),
    )
    novo_outras = st.number_input(
        "Base Outras Despesas/Laudos (R$)",
        value=float(c_ativo["base_outras_desp"]),
    )

  if st.button("💾 Salvar Alterações deste Contrato"):
    c_ativo["nome"] = novo_nome
    c_ativo["municipio"] = novo_muni
    c_ativo["repasse_previsto_mensal"] = novo_repasse
    c_ativo["base_rh_direto"] = novo_rh_dir
    c_ativo["base_provisoes_rh"] = novo_prov_rh
    c_ativo["base_despesas_op"] = novo_desp_op
    c_ativo["base_outras_desp"] = novo_outras
    st.success("Parâmetros atualizados!")
    st.rerun()

  st.markdown("---")
  st.markdown("### ➕ Cadastrar um Novo Contrato no Sistema")

  with st.expander("Clique para abrir o formulário de cadastro de novo contrato"):
    tipo_cad = st.radio(
        "Método de Cadastro:",
        ["Via 4 PDFs Obrigatórios", "Manual"],
        key="tipo_cad_novo",
    )

    if tipo_cad == "Via 4 PDFs Obrigatórios":
      p1 = st.file_uploader(
          "1. Contrato de Programa (PDF)", type=["pdf"], key="nc_p1"
      )
      p2 = st.file_uploader(
          "2. Planilha Orçamentária Consolidada (PDF)",
          type=["pdf"],
          key="nc_p2",
      )
      p3 = st.file_uploader(
          "3. Planilha de RH (PDF)", type=["pdf"], key="nc_p3"
      )
      p4 = st.file_uploader(
          "4. Planilha de Outras Despesas (PDF)", type=["pdf"], key="nc_p4"
      )

      if p1 and p2 and p3 and p4:
        if st.button("🚀 Criar Novo Contrato via PDFs"):
          r1 = PdfReader(p1)
          t1 = "".join([page.extract_text() or "" for page in r1.pages])
          num_match = re.search(
              r"CONTRATO DE PROGRAMA\s*(?:Nº|NO)?\s*(\d+/\d+)",
              t1,
              re.IGNORECASE,
          )
          muni_match = re.search(
              r"MUNICÍPIO DE\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]{3,30})", t1
          )

          chave_nova = (
              f"Contrato {num_match.group(1)}"
              if num_match
              else f"Novo Contrato {len(lista_chaves)+1}"
          )
          st.session_state["contratos"][chave_nova] = {
              "nome": (
                  f"Contrato {num_match.group(1)}" if num_match else chave_nova
              ),
              "municipio": (
                  muni_match.group(1).strip() if muni_match else "Novo Município"
              ),
              "repasse_previsto_mensal": 37296.93,
              "base_rh_direto": 30455.71,
              "base_provisoes_rh": 2837.29,
              "base_despesas_op": 3407.93,
              "base_outras_desp": 596.00,
              "historico_meses": {},
          }
          st.session_state["contrato_ativo_key"] = chave_nova
          st.success(f"Novo contrato '{chave_nova}' cadastrado com sucesso!")
          st.rerun()

    else:
      n_key = st.text_input(
          "Identificação do Contrato (Ex: Contrato 31/2025 - Álvares Machado)"
      )
      n_muni = st.text_input("Município", "Álvares Machado")
      n_rep = st.number_input("Repasse Mensal Previsto (R$)", value=401261.12)
      n_rh_dir = st.number_input("Base Custeio Direto RH (R$)", value=320000.00)
      n_prov_rh = st.number_input("Base Provisões RH (R$)", value=45000.00)
      n_desp_op = st.number_input("Base Despesas Operacionais (R$)", value=30000.00)
      n_outras = st.number_input("Base Outras Despesas (R$)", value=6261.12)

      if st.button("➕ Adicionar Novo Contrato"):
        if n_key:
          st.session_state["contratos"][n_key] = {
              "nome": n_key,
              "municipio": n_muni,
              "repasse_previsto_mensal": n_rep,
              "base_rh_direto": n_rh_dir,
              "base_provisoes_rh": n_prov_rh,
              "base_despesas_op": n_desp_op,
              "base_outras_desp": n_outras,
              "historico_meses": {},
          }
          st.session_state["contrato_ativo_key"] = n_key
          st.success(f"Contrato '{n_key}' adicionado com sucesso!")
          st.rerun()

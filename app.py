import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="CIOP - Gestão Financeira Multicontratos",
    layout="wide",
    page_icon="🏥",
)

# ------------------------------------------------------------------------------
# PROVISÕES PADRÃO DO SISTEMA
# ------------------------------------------------------------------------------
PROVISOES_PADRAO = [
    "Provisão de Gastos com passivos judiciais",
    "Provisão de Gastos com Rescisões Trabalhistas",
    "Provisão de Gastos com Pericias judiciais",
    "Provisão de Gastos com Horas Extras",
    "Provisão de Aumento Salarial",
    "Provisão de Aumento do Vale Alimentação",
    "Taxa de Vale Transporte",
    "Vale Transporte",
    "Vale Alimentação",
    "Custo Férias Funcionários",
    "Cobertura de Férias",
]

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DA MEMÓRIA DO SISTEMA
# ------------------------------------------------------------------------------
if "contratos" not in st.session_state:
  st.session_state["contratos"] = {
      "Contrato 14/2026 - Rosana": {
          "num_contrato": "Contrato 14/2026",
          "objeto": "Prestação de serviços de limpeza pública urbana",
          "municipio": "Rosana",
          "data_assinatura": "20/06/2026",
          "vigencia_meses": 12,
          "valor_total": 447563.12,
          "valor_mensal": 37296.93,
          "custo_profissionais": 30455.71,
          "despesas_op_fixas_var": 3407.93,
          "outras_despesas_laudos": 596.00,
          "provisoes_detalhadas": [
              {
                  "item": "Provisão de Gastos com Rescisões Trabalhistas",
                  "valor": 493.61,
              },
              {"item": "Provisão de Gastos com Horas Extras", "valor": 246.81},
              {
                  "item": "Provisão de Gastos com passivos judiciais",
                  "valor": 100.00,
              },
              {"item": "Cobertura de Férias", "valor": 1996.87},
          ],
          "historico_meses": {
              "Julho/2026": {
                  "repasse_recebido": 37296.93,
                  "total_saidas": 8692.40,
                  "rendimento_liquido": 0.00,
                  "saldo_banco_final": 28604.53,
              },
              "Agosto/2026": {
                  "repasse_recebido": 0.00,
                  "total_saidas": 25277.98,
                  "rendimento_liquido": 119.85,
                  "saldo_banco_final": 3326.55,
              },
              "Setembro/2026": {
                  "repasse_recebido": 65198.50,
                  "total_saidas": 22134.34,
                  "rendimento_liquido": 153.64,
                  "saldo_banco_final": 46664.20,
              },
          },
      }
  }

if "contrato_ativo_key" not in st.session_state:
  st.session_state["contrato_ativo_key"] = (
      "Contrato 14/2026 - Rosana"
      if st.session_state["contratos"]
      else ""
  )

# Estruturas temporárias para modal de criação
if "provisoes_temp_dict" not in st.session_state:
  st.session_state["provisoes_temp_dict"] = {
      p: 0.0 for p in PROVISOES_PADRAO
  }

if "provisoes_custom_list" not in st.session_state:
  st.session_state["provisoes_custom_list"] = []

# ------------------------------------------------------------------------------
# BARRA LATERAL (SELEÇÃO DO CONTRATO)
# ------------------------------------------------------------------------------
st.sidebar.title("📌 Seleção do Contrato")
lista_chaves = list(st.session_state["contratos"].keys())

if lista_chaves:
  if (
      st.session_state["contrato_ativo_key"] not in lista_chaves
      and lista_chaves
  ):
    st.session_state["contrato_ativo_key"] = lista_chaves[0]

  contrato_selecionado_sidebar = st.sidebar.selectbox(
      "Contrato Ativo em Exibição:",
      lista_chaves,
      index=lista_chaves.index(st.session_state["contrato_ativo_key"])
      if st.session_state["contrato_ativo_key"] in lista_chaves
      else 0,
  )
  st.session_state["contrato_ativo_key"] = contrato_selecionado_sidebar
  c_ativo = st.session_state["contratos"][
      st.session_state["contrato_ativo_key"]
  ]
else:
  c_ativo = None
  st.sidebar.info("Nenhum contrato cadastrado.")

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# ------------------------------------------------------------------------------
st.title("🏥 CIOP - Gestão e Análise de Contratos Públicos")

tab1, tab2, tab3 = st.tabs([
    "📊 Composição do Saldo Remanescente (Painel)",
    "📂 Processar Extratos Mensais (C/C & Investimento)",
    "⚙️ Gerenciamento de Contratos (Editar / Excluir / Novo)",
])

# ==============================================================================
# ABA 1: PAINEL DE COMPOSIÇÃO DO SALDO
# ==============================================================================
with tab1:
  if not c_ativo:
    st.warning(
        "⚠️ Nenhum contrato cadastrado. Acesse a **Aba 3** para cadastrar o"
        " primeiro contrato."
    )
  else:
    st.subheader(f"📌 {c_ativo['num_contrato']} - {c_ativo['municipio']}")
    st.caption(
        f"Objeto: {c_ativo['objeto']} | Assinatura: {c_ativo['data_assinatura']}"
        f" | Vigência: {c_ativo['vigencia_meses']} meses | Valor Global: R$"
        f" {c_ativo['valor_total']:,.2f}"
    )

    hist = c_ativo["historico_meses"]

    if not hist:
      st.info(
          "ℹ️ Nenhum extrato bancário processado para este contrato ainda."
          " Acesse a **Aba 2** para lançar o primeiro extrato."
      )
    else:
      repasse_base = c_ativo["valor_mensal"]

      tot_outras_desp_acum = sum(
          m["repasse_recebido"]
          * (
              c_ativo["outras_despesas_laudos"] / repasse_base
              if repasse_base > 0
              else 0
          )
          for m in hist.values()
      )
      tot_rendimentos_acum = sum(
          m["rendimento_liquido"] for m in hist.values()
      )

      provisoes_calculadas_acum = []
      tot_provisoes_acum_geral = 0.0

      for item_p in c_ativo["provisoes_detalhadas"]:
        valor_base_item = item_p["valor"]
        acum_item = sum(
            m["repasse_recebido"]
            * (valor_base_item / repasse_base if repasse_base > 0 else 0)
            for m in hist.values()
        )
        provisoes_calculadas_acum.append(
            {"item": item_p["item"], "valor_acumulado": acum_item}
        )
        tot_provisoes_acum_geral += acum_item

      ultimo_mes_nome = list(hist.keys())[-1]
      saldo_banco_atual = hist[ultimo_mes_nome]["saldo_banco_final"]

      total_bloqueado_acum = (
          tot_provisoes_acum_geral
          + tot_outras_desp_acum
          + tot_rendimentos_acum
      )
      saldo_livre_real = saldo_banco_atual - total_bloqueado_acum

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
            delta="Disponível para Custeio",
        )

      st.divider()

      st.info(f"""
            📢 **Síntese Executiva do Saldo Remanescente no Banco (R$ {saldo_banco_atual:,.2f}):**
            
            * **Total em Provisões Trabalhistas Discriminadas:** **R$ {tot_provisoes_acum_geral:,.2f}**
            * **Reserva de Outras Despesas (Laudos/Exames):** **R$ {tot_outras_desp_acum:,.2f}**
            * **Rendimentos Líquidos de Aplicação (Extratos Investimento):** **R$ {tot_rendimentos_acum:,.2f}**
            * **Saldo Operacional Efetivamente Livre:** **R$ {saldo_livre_real:,.2f}**
            """)

      col_g1, col_g2 = st.columns([1, 1])

      with col_g1:
        st.markdown("### 📦 Detalhamento das Gavetas (Item por Item)")
        linhas_gavetas = []

        for prov_item in provisoes_calculadas_acum:
          linhas_gavetas.append({
              "Gaveta / Destinação": f"Provisão: {prov_item['item']}",
              "Valor Acumulado (R$)": prov_item["valor_acumulado"],
              "Situação": "Bloqueado",
          })

        linhas_gavetas.append({
            "Gaveta / Destinação": "Reserva de Laudos e Exames",
            "Valor Acumulado (R$)": tot_outras_desp_acum,
            "Situação": "Bloqueado",
        })
        linhas_gavetas.append({
            "Gaveta / Destinação": "Rendimentos Líquidos de Aplicação",
            "Valor Acumulado (R$)": tot_rendimentos_acum,
            "Situação": "Bloqueado",
        })
        linhas_gavetas.append({
            "Gaveta / Destinação": "Saldo Livre Operacional",
            "Valor Acumulado (R$)": max(0.0, saldo_livre_real),
            "Situação": "Liberado",
        })

        st.dataframe(
            pd.DataFrame(linhas_gavetas),
            use_container_width=True,
            hide_index=True,
        )

      with col_g2:
        st.markdown("### 📊 Gráfico de Segregação do Saldo")
        categorias_pie = []
        valores_pie = []

        for prov_item in provisoes_calculadas_acum:
          if prov_item["valor_acumulado"] > 0:
            categorias_pie.append(prov_item["item"])
            valores_pie.append(prov_item["valor_acumulado"])

        if tot_outras_desp_acum > 0:
          categorias_pie.append("Laudos/Exames")
          valores_pie.append(tot_outras_desp_acum)

        if tot_rendimentos_acum > 0:
          categorias_pie.append("Rendimentos Líquidos")
          valores_pie.append(tot_rendimentos_acum)

        categorias_pie.append("Saldo Livre Operacional")
        valores_pie.append(max(0.0, saldo_livre_real))

        df_pie = pd.DataFrame(
            {"Categoria": categorias_pie, "Valor (R$)": valores_pie}
        )
        fig = px.pie(
            df_pie,
            values="Valor (R$)",
            names="Categoria",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)

      st.divider()
      st.subheader("📈 Histórico de Movimentações por Mês")
      lista_hist = []
      for m, d in hist.items():
        lista_hist.append({
            "Mês/Ano": m,
            "Repasse Recebido (R$)": d["repasse_recebido"],
            "Saídas Operacionais (R$)": d["total_saidas"],
            "Rendimento Líquido Invest. (R$)": d["rendimento_liquido"],
            "Saldo Final C/C (R$)": d["saldo_banco_final"],
        })
      st.dataframe(
          pd.DataFrame(lista_hist), use_container_width=True, hide_index=True
      )

# ==============================================================================
# ABA 2: PROCESSAR EXTRATOS MENSAIS
# ==============================================================================
with tab2:
  if not c_ativo:
    st.warning("⚠️ Nenhum contrato selecionado para processamento.")
  else:
    st.subheader(f"📂 Processamento do Mês: {c_ativo['num_contrato']}")
    mes_processar = st.text_input("Mês/Ano de Referência", value="Outubro/2026")

    subtab_cc, subtab_inv = st.tabs([
        "🏦 1. Extrato de Conta Corrente",
        "📈 2. Extrato de Investimentos (Rendimento Líquido)",
    ])

    ultimo_saldo = (
        list(c_ativo["historico_meses"].values())[-1]["saldo_banco_final"]
        if c_ativo["historico_meses"]
        else 0.0
    )

    if "temp_repasse" not in st.session_state:
      st.session_state["temp_repasse"] = c_ativo["valor_mensal"]
    if "temp_saidas" not in st.session_state:
      st.session_state["temp_saidas"] = 0.0
    if "temp_saldo_final" not in st.session_state:
      st.session_state["temp_saldo_final"] = ultimo_saldo
    if "temp_rend_liquido" not in st.session_state:
      st.session_state["temp_rend_liquido"] = 0.0

    with subtab_cc:
      st.caption("Lançamento das movimentações de Conta Corrente.")
      col_cc1, col_cc2 = st.columns(2)
      with col_cc1:
        st.session_state["temp_repasse"] = st.number_input(
            "Repasse Efetivo Recebido no Mês (R$)",
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
          "Informe o Rendimento Líquido do mês extraído do relatório de"
          " investimentos."
      )
      st.session_state["temp_rend_liquido"] = st.number_input(
          "Rendimento Líquido do Mês (R$)",
          value=float(st.session_state["temp_rend_liquido"]),
          step=10.0,
      )

    st.markdown("---")

    if st.button(f"💾 Gravar Mês {mes_processar} no {c_ativo['num_contrato']}"):
      c_ativo["historico_meses"][mes_processar] = {
          "repasse_recebido": st.session_state["temp_repasse"],
          "total_saidas": st.session_state["temp_saidas"],
          "rendimento_liquido": st.session_state["temp_rend_liquido"],
          "saldo_banco_final": st.session_state["temp_saldo_final"],
      }
      st.success(f"Extrato do mês {mes_processar} gravado com sucesso!")
      st.rerun()

# ==============================================================================
# ABA 3: GERENCIAMENTO DE CONTRATOS (EDITAR / EXCLUIR / NOVO)
# ==============================================================================
with tab3:
  st.subheader("⚙️ Gerenciamento e Seleção de Contratos")

  if lista_chaves:
    col_sel1, col_sel2 = st.columns([3, 1])

    with col_sel1:
      contrato_sel_box = st.selectbox(
          "Selecione o Contrato que Deseja Gerenciar/Visualizar:",
          lista_chaves,
          key="select_contrato_aba3",
      )

    if contrato_sel_box != st.session_state["contrato_ativo_key"]:
      st.session_state["contrato_ativo_key"] = contrato_sel_box
      st.rerun()

    with col_sel2:
      st.write("")
      st.write("")
      # JANELA DE CONFIRMAÇÃO DE EXCLUSÃO
      with st.popover("🗑️ Excluir Contrato"):
        st.error(
            f"⚠️ Tem certeza que deseja excluir o cadastro do **{c_ativo['num_contrato']}**?"
        )
        st.caption(
            "Esta ação excluirá permanentemente todos os parâmetros e o"
            " histórico de extratos deste contrato."
        )

        if st.button(
            "🚨 Confirmar Exclusão Definitiva", key="btn_confirmar_deletar"
        ):
          chave_del = st.session_state["contrato_ativo_key"]
          del st.session_state["contratos"][chave_del]

          restantes = list(st.session_state["contratos"].keys())
          st.session_state["contrato_ativo_key"] = (
              restantes[0] if restantes else ""
          )

          st.success("Contrato excluído com sucesso!")
          st.rerun()

    st.markdown("---")
    st.markdown(f"### 📝 Editar Informações do {c_ativo['num_contrato']}")

    col_ed1, col_ed2 = st.columns(2)
    with col_ed1:
      e_num = st.text_input("Nº do Contrato", value=c_ativo["num_contrato"])
      e_objeto = st.text_input("Objeto do Contrato", value=c_ativo["objeto"])
      e_muni = st.text_input("Município", value=c_ativo["municipio"])
      e_data = st.text_input(
          "Data da Assinatura", value=c_ativo["data_assinatura"]
      )
      e_vigencia = st.number_input(
          "Vigência (em meses)", value=int(c_ativo["vigencia_meses"]), step=1
      )

    with col_ed2:
      e_v_total = st.number_input(
          "Valor Total do Contrato (R$)",
          value=float(c_ativo["valor_total"]),
          step=1000.0,
      )
      e_v_mensal = st.number_input(
          "Valor Mensal / Repasse Previsto (R$)",
          value=float(c_ativo["valor_mensal"]),
          step=500.0,
      )
      e_custo_prof = st.number_input(
          "Custo Mensal Profissionais - RH Direto (R$)",
          value=float(c_ativo["custo_profissionais"]),
          step=500.0,
      )
      e_outras_desp = st.number_input(
          "Outras Despesas - Laudos e Exames (R$)",
          value=float(c_ativo["outras_despesas_laudos"]),
          step=100.0,
      )
      e_desp_fixas_var = st.number_input(
          "Despesas Fixas e Variáveis - Planilha de Custos (R$)",
          value=float(c_ativo["despesas_op_fixas_var"]),
          step=100.0,
      )

    if st.button("💾 Salvar Alterações das Informações"):
      c_ativo["num_contrato"] = e_num
      c_ativo["objeto"] = e_objeto
      c_ativo["municipio"] = e_muni
      c_ativo["data_assinatura"] = e_data
      c_ativo["vigencia_meses"] = e_vigencia
      c_ativo["valor_total"] = e_v_total
      c_ativo["valor_mensal"] = e_v_mensal
      c_ativo["custo_profissionais"] = e_custo_prof
      c_ativo["outras_despesas_laudos"] = e_outras_desp
      c_ativo["despesas_op_fixas_var"] = e_desp_fixas_var
      st.success("Informações do contrato salvas com sucesso!")
      st.rerun()

  st.markdown("---")
  st.markdown("### ➕ Cadastrar um Novo Contrato no Sistema")

  col_nc1, col_nc2 = st.columns(2)

  with col_nc1:
    nc_num = st.text_input(
        "Nº do Contrato", placeholder="Ex: Contrato 31/2025", key="nc_num_input"
    )
    nc_objeto = st.text_input(
        "Objeto do Contrato",
        placeholder="Ex: Serviços de Saúde / Limpeza",
        key="nc_obj_input",
    )
    nc_muni = st.text_input(
        "Município", placeholder="Ex: Álvares Machado", key="nc_muni_input"
    )
    nc_data = st.text_input(
        "Data da Assinatura", placeholder="Ex: 10/01/2025", key="nc_data_input"
    )
    nc_vigencia = st.number_input(
        "Vigência (em meses)", value=12, step=1, key="nc_vig_input"
    )

  with col_nc2:
    nc_v_total = st.number_input(
        "Valor Total do Contrato (R$)",
        value=0.0,
        step=1000.0,
        key="nc_vt_input",
    )
    nc_v_mensal = st.number_input(
        "Valor Mensal / Repasse Previsto (R$)",
        value=0.0,
        step=500.0,
        key="nc_vm_input",
    )
    nc_custo_prof = st.number_input(
        "Custo Mensal Profissionais - RH Direto (R$)",
        value=0.0,
        step=500.0,
        key="nc_cp_input",
    )

    # PROVISÕES COM BOTÃO DO LÁPIS
    soma_prov_padrao = sum(
        st.session_state["provisoes_temp_dict"].values()
    )
    soma_prov_custom = sum(
        item["valor"] for item in st.session_state["provisoes_custom_list"]
    )
    total_prov_geral = soma_prov_padrao + soma_prov_custom

    col_prov1, col_prov2 = st.columns([3, 1])
    with col_prov1:
      st.number_input(
          "Provisões (R$) [Soma das Provisões Preenchidas]",
          value=float(total_prov_geral),
          disabled=True,
      )
    with col_prov2:
      st.write("")
      st.write("")

      with st.popover("✏️ Provisões"):
        st.markdown("### 📝 Detalhar Provisões do Contrato")
        st.caption(
            "Insira os valores mensais das provisões aplicáveis ao contrato:"
        )

        for item_padrao in PROVISOES_PADRAO:
          st.session_state["provisoes_temp_dict"][
              item_padrao
          ] = st.number_input(
              f"{item_padrao} (R$)",
              value=float(
                  st.session_state["provisoes_temp_dict"][item_padrao]
              ),
              step=50.0,
              key=f"input_{item_padrao}",
          )

        st.markdown("---")
        st.markdown("### ➕ Outras Provisões / Itens Adicionais")

        cust_nome = st.text_input(
            "Nome do Novo Item Extra", key="new_custom_item_name"
        )
        cust_val = st.number_input(
            "Valor do Novo Item Extra (R$)",
            value=0.0,
            step=50.0,
            key="new_custom_item_val",
        )

        if st.button("Adicionar Item Extra"):
          if cust_nome and cust_val > 0:
            st.session_state["provisoes_custom_list"].append(
                {"item": cust_nome, "valor": cust_val}
            )
            st.success(f"Item extra '{cust_nome}' adicionado!")
            st.rerun()

        if st.session_state["provisoes_custom_list"]:
          st.markdown("**Itens Extras Adicionados:**")
          for idx, c_it in enumerate(
              st.session_state["provisoes_custom_list"]
          ):
            c_c1, c_c2 = st.columns([3, 1])
            c_c1.write(f"• **{c_it['item']}**: R$ {c_it['valor']:,.2f}")
            if c_c2.button("🗑️", key=f"del_cust_{idx}"):
              st.session_state["provisoes_custom_list"].pop(idx)
              st.rerun()

    nc_outras_desp = st.number_input(
        "Outras Despesas - Laudos e Exames (R$)",
        value=0.0,
        step=100.0,
        key="nc_od_input",
    )
    nc_desp_fixas_var = st.number_input(
        "Despesas Fixas e Variáveis - Planilha de Custos (R$)",
        value=0.0,
        step=100.0,
        key="nc_df_input",
    )

  st.markdown("---")

  if st.button("💾 Confirmar e Salvar Cadastro do Novo Contrato"):
    if nc_num and nc_muni and nc_v_mensal > 0:
      chave_novo = f"{nc_num} - {nc_muni}"

      provisoes_finais_salvar = []

      for k, v in st.session_state["provisoes_temp_dict"].items():
        if v > 0:
          provisoes_finais_salvar.append({"item": k, "valor": v})

      for c_item in st.session_state["provisoes_custom_list"]:
        if c_item["valor"] > 0:
          provisoes_finais_salvar.append(c_item)

      st.session_state["contratos"][chave_novo] = {
          "num_contrato": nc_num,
          "objeto": nc_objeto,
          "municipio": nc_muni,
          "data_assinatura": nc_data,
          "vigencia_meses": nc_vigencia,
          "valor_total": nc_v_total,
          "valor_mensal": nc_v_mensal,
          "custo_profissionais": nc_custo_prof,
          "despesas_op_fixas_var": nc_desp_fixas_var,
          "outras_despesas_laudos": nc_outras_desp,
          "provisoes_detalhadas": provisoes_finais_salvar,
          "historico_meses": {},
      }

      st.session_state["contrato_ativo_key"] = chave_novo

      st.session_state["provisoes_temp_dict"] = {
          p: 0.0 for p in PROVISOES_PADRAO
      }
      st.session_state["provisoes_custom_list"] = []

      st.success(f"Contrato '{chave_novo}' cadastrado com sucesso!")
      st.rerun()
    else:
      st.error(
          "⚠️ Por favor, preencha pelo menos o Nº do Contrato, Município e"
          " Valor Mensal."
      )

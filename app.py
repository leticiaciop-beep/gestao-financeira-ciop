import streamlit as st
import pandas as pd
import plotly.express as px
from pypdf import PdfReader
import re

# ------------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Gestão de Saldos - CIOP", layout="wide", page_icon="🏥")

# Estilização CSS personalizada
st.markdown("""

""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# INICIALIZAÇÃO DA MEMÓRIA DO SISTEMA (SISTEMA ZERADO)
# ------------------------------------------------------------------------------
if "contrato_nome" not in st.session_state: st.session_state["contrato_nome"] = "Nenhum contrato carregado"
if "municipio" not in st.session_state: st.session_state["municipio"] = "Não informado"
if "valor_global" not in st.session_state: st.session_state["valor_global"] = 0.0
if "repasse_mensal" not in st.session_state: st.session_state["repasse_mensal"] = 0.0

if "saldo_banco" not in st.session_state: st.session_state["saldo_banco"] = 0.0
if "total_entradas" not in st.session_state: st.session_state["total_entradas"] = 0.0
if "total_saidas" not in st.session_state: st.session_state["total_saidas"] = 0.0

if "prov_rescisao" not in st.session_state: st.session_state["prov_rescisao"] = 0.0
if "rendimentos" not in st.session_state: st.session_state["rendimentos"] = 0.0
if "impostos" not in st.session_state: st.session_state["impostos"] = 0.0
if "outras_provisoes" not in st.session_state: st.session_state["outras_provisoes"] = 0.0

def converter_para_float(texto_valor):
    try:
        limpo = texto_valor.replace(".", "").replace(",", ".")
        return float(limpo)
    except:
        return 0.0

# ------------------------------------------------------------------------------
# INTERFACE PRINCIPAL EM ABAS
# ------------------------------------------------------------------------------
st.title("🏥 CIOP - Sistema de Gestão Financeira de Contratos")

tab1, tab2, tab3 = st.tabs([
    "📊 Painel do Contrato", 
    "📄 Importar Contrato (PDF)", 
    "🏦 Importar Extrato Bancário (PDF)"
])

# ==============================================================================
# ABA 1: PAINEL DO CONTRATO (DASHBOARD)
# ==============================================================================
with tab1:
    st.subheader(f"📌 {st.session_state['contrato_nome']}")
    st.caption(f"Município: {st.session_state['municipio']} | Repasse Mensal Previsto: R$ {st.session_state['repasse_mensal']:,.2f}")
    
    st.sidebar.header("⚙️ Ajuste Manual de Saldos")
    st.session_state["saldo_banco"] = st.sidebar.number_input("Saldo Bruto no Banco (R$)", value=st.session_state["saldo_banco"], step=500.0)
    st.session_state["prov_rescisao"] = st.sidebar.number_input("Provisões Trabalhistas/Rescisões (R$)", value=st.session_state["prov_rescisao"], step=500.0)
    st.session_state["rendimentos"] = st.sidebar.number_input("Rendimentos de Aplicação (R$)", value=st.session_state["rendimentos"], step=100.0)
    st.session_state["impostos"] = st.sidebar.number_input("Impostos/Retenções (R$)", value=st.session_state["impostos"], step=100.0)
    st.session_state["outras_provisoes"] = st.sidebar.number_input("Outras Reservas (R$)", value=st.session_state["outras_provisoes"], step=100.0)
    
    total_bloqueado = st.session_state["prov_rescisao"] + st.session_state["rendimentos"] + st.session_state["impostos"] + st.session_state["outras_provisoes"]
    saldo_livre = st.session_state["saldo_banco"] - total_bloqueado
    meses_cobertura = saldo_livre / st.session_state["repasse_mensal"] if st.session_state["repasse_mensal"] > 0 else 0.0
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""

Saldo Total no Banco

R$ {st.session_state["saldo_banco"]:,.2f}

', unsafe_allow_html=True)

with col2:
    st.markdown(f'

Reservas Bloqueadas

R$ {total_bloqueado:,.2f}

', unsafe_allow_html=True)

with col3:
    st.markdown(f'

Saldo Real Livre

R$ {saldo_livre:,.2f}

', unsafe_allow_html=True)

st.markdown("


", unsafe_allow_html=True)

st.info(f"""
💡 **Síntese para a Diretoria:**
* **Entradas no Mês:** R$ {st.session_state['total_entradas']:,.2f} | **Saídas no Mês:** R$ {st.session_state['total_saidas']:,.2f}
* **Saldo em Conta:** R$ {st.session_state['saldo_banco']:,.2f}
* **Valor Total Indisponível/Bloqueado:** R$ {total_bloqueado:,.2f}
* **Saldo Operacional Efetivamente Livre:** **R$ {saldo_livre:,.2f}** *(Cobre {meses_cobertura:.2f} meses de custeio)*
""")

if st.session_state["saldo_banco"] > 0:
    st.subheader("🧩 Divisão do Saldo")
    df_pie = pd.DataFrame({
        "Categoria": ["Saldo Livre", "Provisão Rescisória", "Rendimentos", "Impostos", "Outras Reservas"],
        "Valor": [max(0, saldo_livre), st.session_state["prov_rescisao"], st.session_state["rendimentos"], st.session_state["impostos"], st.session_state["outras_provisoes"]]
    })
    fig = px.pie(df_pie, values="Valor", names="Categoria", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

==============================================================================
ABA 2: LEITOR AUTOMÁTICO DE CONTRATO (PDF)
==============================================================================

with tab2:
st.subheader("📄 Upload do Contrato de Programa (PDF)")
st.caption("Anexe o documento em PDF para extrair o número do contrato, município, valor global e repasses.")

arquivo_contrato = st.file_uploader("Selecione o arquivo do Contrato (PDF)", type=["pdf"], key="pdf_contrato")

if arquivo_contrato is not None:
    reader = PdfReader(arquivo_contrato)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() or ""
    
    num_contrato_match = re.search(r"(CONTRATO DE PROGRAMA\s*(?:Nº|Nº\.|NO)?\s*\d+/\d+)", texto_completo, re.IGNORECASE)
    municipio_match = re.search(r"MUNICÍPIO DE\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ\s]{3,30})", texto_completo)
    valores_match = re.findall(r"R\$\s*([\d\.,]+)", texto_completo)
    
    st.success("✅ Arquivo processado com sucesso! Confira os dados extraídos abaixo:")
    
    c1, c2 = st.columns(2)
    with c1:
        nome_ext = st.text_input("Número/Identificação do Contrato", value=num_contrato_match.group(1) if num_contrato_match else "Contrato Identificado")
        muni_ext = st.text_input("Município Contratante", value=municipio_match.group(1).strip() if municipio_match else "Álvares Machado")
    with c2:
        v_global = st.number_input("Valor Global Extraído (R$)", value=converter_para_float(valores_match[0]) if len(valores_match) > 0 else 0.0)
        v_mensal = st.number_input("Parcela Mensal Prevista (R$)", value=converter_para_float(valores_match[1]) if len(valores_match) > 1 else 0.0)
        
    if st.button("💾 Gravar Dados do Contrato no Sistema"):
        st.session_state["contrato_nome"] = nome_ext
        st.session_state["municipio"] = muni_ext
        st.session_state["valor_global"] = v_global
        st.session_state["repasse_mensal"] = v_mensal
        st.success("Dados do contrato atualizados com sucesso! Acesse a aba 'Painel do Contrato' para visualizar.")

==============================================================================
ABA 3: LEITOR AUTOMÁTICO DE EXTRATO BANCÁRIO (PDF)
==============================================================================

with tab3:
st.subheader("🏦 Upload do Extrato Bancário (PDF)")
st.caption("Anexe o extrato do banco para extrair o saldo final, movimentações de entradas/saídas e rendimentos.")

arquivo_extrato = st.file_uploader("Selecione o arquivo do Extrato Bancário (PDF)", type=["pdf"], key="pdf_extrato")

if arquivo_extrato is not None:
    reader_ex = PdfReader(arquivo_extrato)
    texto_extrato = ""
    for page in reader_ex.pages:
        texto_extrato += page.extract_text() or ""
    
    saldos_encontrados = re.findall(r"SALDO\s*(?:FINAL|DISPONÍVEL|ATUAL)?\s*:?\s*R\$\s*([\d\.,]+)", texto_extrato, re.IGNORECASE)
    rendimentos_encontrados = re.findall(r"(?:RENDIMENTO|RESGATE AUTOMATICO|APLICACAO)\s*:?\s*R\$\s*([\d\.,]+)", texto_extrato, re.IGNORECASE)
    
    st.success("✅ Extrato bancário analisado!")
    
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        saldo_ext = st.number_input("Saldo Final do Banco (R$)", value=converter_para_float(saldos_encontrados[0]) if saldos_encontrados else st.session_state["saldo_banco"])
        entradas_ext = st.number_input("Total de Entradas / Repasses no Mês (R$)", value=st.session_state["repasse_mensal"])
    with col_ex2:
        saidas_ext = st.number_input("Total de Saídas / Despesas no Mês (R$)", value=0.0)
        rendimento_ext = st.number_input("Rendimentos de Aplicação Encontrados (R$)", value=converter_para_float(rendimentos_encontrados[0]) if rendimentos_encontrados else st.session_state["rendimentos"])
    
    if st.button("💾 Aplicar Saldos do Extrato ao Painel"):
        st.session_state["saldo_banco"] = saldo_ext
        st.session_state["total_entradas"] = entradas_ext
        st.session_state["total_saidas"] = saidas_ext
        st.session_state["rendimentos"] = rendimento_ext
        st.success("Saldos e movimentações atualizados com sucesso! Verifique a aba 'Painel do Contrato'.")

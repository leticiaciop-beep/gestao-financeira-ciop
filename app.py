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

# Funções auxiliares para tratamento de texto e conversão de valores R$
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
    
    # Barra Lateral para Ajuste Manual Se Necessário
    st.sidebar.header("⚙️ Ajuste Manual de Saldos")
    st.session_state["saldo_banco"] = st.sidebar.number_input("Saldo Bruto no Banco (R$)", value=st.session_state["saldo_banco"], step=500.0)
    st.session_state["prov_rescisao"] = st.sidebar.number_input("Provisões Trabalhistas/Rescisões (R$)", value=st.session_state["prov_rescisao"], step=500.0)
    st.session_state["rendimentos"] = st.sidebar.number_input("Rendimentos de Aplicação (R$)", value=st.session_state["rendimentos"], step=100.0)
    st.session_state["impostos"] = st.sidebar.number_input("Impostos/Retenções (R$)", value=st.session_state["impostos"], step=100.0)
    st.session_state["outras_provisoes"] = st.sidebar.number_input("Outras Reservas (R$)", value=st.session_state["outras_provisoes"], step=100.0)
    
    # CÁLCULOS
    total_bloqueado = st.session_state["prov_rescisao"] + st.session_state["rendimentos"] + st.session_state["impostos"] + st.session_state["outras_provisoes"]
    saldo_livre = st.session_state["saldo_banco"] - total_bloqueado
    meses_cobertura = saldo_livre / st.session_state["repasse_mensal"] if st.session_state["repasse_mensal"] > 0 else 0.0

    # CARDS DE RESPOSTA RÁPIDA
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""

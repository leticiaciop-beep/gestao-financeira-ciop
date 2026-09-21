import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página no navegador
st.set_page_config(page_title="Gestão de Saldos - CIOP", layout="wide")

# Estilização básica dos cartões de saldo
st.markdown("""
<style>
    .card-total { background-color: #e9ecef; padding: 15px; border-radius: 8px; border-left: 5px solid #6c757d; }
    .card-bloqueado { background-color: #ffe3e3; padding: 15px; border-radius: 8px; border-left: 5px solid #dc3545; }
    .card-livre { background-color: #d3f9d8; padding: 15px; border-radius: 8px; border-left: 5px solid #28a745; }
    .card-title { font-size: 0.85rem; font-weight: bold; color: #495057; text-transform: uppercase; }
    .card-value { font-size: 1.8rem; font-weight: bold; color: #212529; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Sistema de Análise de Saldos Contratuais")
st.caption("Visão em tempo real do Saldo Bancário x Saldo Operacional Livre")

# BARRA LATERAL: ENTRADA DE DADOS
st.sidebar.header("⚙️ Painel de Controle (Simulador)")
contrato_nome = st.sidebar.text_input("Nome do Contrato", "Contrato 31/2025 - Álvares Machado")
repasse_mensal = st.sidebar.number_input("Valor do Repasse Mensal (R$)", value=401261.12, step=1000.0)

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Lançamento de Saldo e Reservas")
saldo_banco = st.sidebar.number_input("Saldo Bruto do Extrato (R$)", value=450000.00, step=1000.0)

prov_rescisao = st.sidebar.number_input("Provisões Trabalhistas / Rescisões (R$)", value=70000.00, step=500.0)
rendimentos = st.sidebar.number_input("Rendimentos de Aplicação (R$)", value=5000.00, step=100.0)
impostos = st.sidebar.number_input("Impostos / Retenções a Recolher (R$)", value=10000.00, step=500.0)
outras_provisoes = st.sidebar.number_input("Outras Reservas (VT / Dissídios) (R$)", value=0.00, step=500.0)

# CÁLCULOS AUTOMÁTICOS
total_bloqueado = prov_rescisao + rendimentos + impostos + outras_provisoes
saldo_livre = saldo_banco - total_bloqueado
meses_cobertura = saldo_livre / repasse_mensal if repasse_mensal > 0 else 0

# TELA PRINCIPAL: CARDS DE RESPOSTA RÁPIDA
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card-total">
        <div class="card-title">Saldo Total no Banco</div>
        <div class="card-value">R$ {saldo_banco:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card-bloqueado">
        <div class="card-title">Reservas Bloqueadas</div>
        <div class="card-value">R$ {total_bloqueado:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card-livre">
        <div class="card-title">Saldo Real Livre</div>
        <div class="card-value">R$ {saldo_livre:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# RESUMO PARA A DIRETORIA
st.info(f"""
💡 **Resumo para a Diretoria ({contrato_nome}):**
* **Saldo em Conta:** R$ {saldo_banco:,.2f}
* **Valor Bloqueado:** R$ {total_bloqueado:,.2f} *(comprometido com rescisões, impostos e rendimentos)*
* **Saldo Efetivamente Livre:** **R$ {saldo_livre:,.2f}** *(garante {meses_cobertura:.2f} meses de custeio operacional)*
""")

# GRÁFICO DE DECOMPOSIÇÃO
st.subheader("🧩 Composição do Saldo Indisponível")
df_grafico = pd.DataFrame({
    "Categoria": ["Saldo Livre", "Provisão Rescisória", "Impostos", "Rendimentos", "Outras Reservas"],
    "Valor": [max(0, saldo_livre), prov_rescisao, impostos, rendimentos, outras_provisoes]
})

fig = px.pie(df_grafico, values="Valor", names="Categoria", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig, use_container_width=True)

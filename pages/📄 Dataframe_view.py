import streamlit as st
import pandas as pd

st.title("📄 Visualização dos Dados")

if 'df' in st.session_state and isinstance(st.session_state.df, pd.DataFrame):
    st.dataframe(st.session_state.df)
else:
    st.info("Nenhum DataFrame carregado ainda.")
    st.markdown(
        """
    <div style="margin-top: 10px; color: gray; font-size: 0.9em;">
        💡 <b>Dica:</b> Peça para o agente carregar os dados de um arquivo.</code><br>
    </div>
    """,
        unsafe_allow_html=True
    )

# ==============================================================================
# FUNZIONE DI SUPPORTO ROBUSTA PER IL RECUPERO DATI (Evita KeyError)
# ==============================================================================
def safe_get(data, keys, default="N/D"):
    """
    Cerca in modo sicuro una chiave all'interno di una Series o di un Dict di pandas,
    verificando diverse possibili varianti di nomi colonna e gestendo i valori NaN.
    """
    if data is None:
        return default
        
    # Se keys è una stringa, la trasformiamo in lista
    if isinstance(keys, str):
        keys = [keys]
        
    for k in keys:
        if hasattr(data, "index") and k in data.index:
            val = data[k]
        elif isinstance(data, dict) and k in data:
            val = data[k]
        else:
            continue
            
        # Controlla se il valore è NaN o None di pandas/numpy
        try:
            import pandas as pd
            if pd.isna(val):
                continue
        except ImportError:
            pass
            
        return val
        
    return default


# ==============================================================================
# BLOCCO RIFATTO: ANALISI GIOCATORE & METRICHE AVANZATE (Intorno a riga 730)
# ==============================================================================

st.markdown("### 📊 Metriche Avanzate & Partite (Titolare / Subentrato)")

# Tentativo di estrazione sicura delle metriche con fallback multipli per i nomi delle colonne
p_titolare = safe_get(g_data, ['Partite_Titolare', 'Partite Titolare', 'Titolare', 'Presenze_Titolare'], 0)
p_subentrato = safe_get(g_data, ['Partite_Subentrato', 'Partite Subentrato', 'Subentrato', 'Presenze_Sub'], 0)
fanta_media = safe_get(g_data, ['FantaMedia', 'Fanta_Media', 'FM', 'Media_Voto'], '6.0')
prezzo_listone = safe_get(g_data, ['Prezzo', 'Quotazione', 'Valore', 'Prezzo_Listone'], 1)

# Layout delle metriche sicuro e pulito in Streamlit
m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric("Partite Titolare 🟢", f"{p_titolare}")

with m_col2:
    st.metric("Partite Subentrato 🟡", f"{p_subentrato}")

with m_col3:
    st.metric("FantaMedia Stimata", f"{fanta_media} FM")

with m_col4:
    st.metric("Quotazione Listone", f"{prezzo_listone} cr")

# Controllo aggiuntivo per visualizzare eventuali dati grezzi in caso di debug
with st.expander("🔍 Visualizza dati completi del giocatore (Debug)"):
    try:
        st.dataframe(g_data)
    except Exception:
        st.write(g_data)
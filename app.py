st.divider()
st.subheader("🎯 Scout di Rendimento: Trova i Top Player")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_ruolo = st.selectbox("Filtra per Ruolo:", ["Tutti", "P", "D", "C", "A"])
with col_f2:
    filtro_tier = st.selectbox("Filtra per Tier:", ["Tutti", "Top", "Semitop", "Titolare", "Scommessa"])
with col_f3:
    solo_rigoristi = st.checkbox("Solo Rigoristi / Piazzati (Score 3)")

# Applicazione filtri sul DataFrame dei giocatori liberi
df_scout = df[df["Stato"] == "LIBERO"].copy()

if filtro_ruolo != "Tutti":
    df_scout = df_scout[df_scout["Ruolo"] == filtro_ruolo]
if filtro_tier != "Tutti":
    df_scout = df_scout[df_scout["Tier"] == filtro_tier]
if solo_rigoristi:
    df_scout = df_scout[df_scout["Status_Piazzati"] == 3]

# Ordinamento per Indice Value-for-Money o Valore Atteso
criterio_ordinamento = st.radio(
    "Ordina i risultati per:", 
    ["Valore Atteso di Rendimento (xG + xA)", "Indice Value-for-Money (VfM)", "Quotazione Base"],
    horizontal=True
)

col_sort = "Valore_Atteso" if criterio_ordinamento.startswith("Valore") else ("Indice_VfM" if criterio_ordinamento.startswith("Indice") else "Quotazione")
df_scout = df_scout.sort_values(by=col_sort, ascending=False)

# Mostra tabella dei migliori profili trovati
st.dataframe(
    df_scout[["Nome", "Squadra", "Ruolo", "Quotazione", "Valore_Atteso", "Indice_VfM", "Partite_Attese"]],
    use_container_width=True,
    hide_index=True
)
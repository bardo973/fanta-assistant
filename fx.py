# fix.py
import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Trova e sostituisci la funzione calcola_prezzo_consigliato
start_marker = 'def calcola_prezzo_consigliato(g_info, stats_df=None, crediti_squadra=None):'
end_marker = 'def tabella_prezzi_fvm('

s = code.find(start_marker)
e = code.find(end_marker)
if s == -1 or e == -1:
    print("Marker non trovati. Assicurati di eseguire lo script nella cartella di app.py")
    exit(1)

new_func = '''def calcola_prezzo_consigliato(g_info, stats_df=None, crediti_squadra=None):
    nome = g_info.get("Nome", "")
    ruolo = g_info.get("Ruolo", "C")

    # --- PARAMETRI CUSTOM (se l'utente li ha configurati) ---
    custom = st.session_state.get("ai_formula_params", {})
    use_custom = st.session_state.get("use_ai_formula_custom", False)
    
    DEF = {
        "coef_fm": 0.15,
        "fascia_top": 1.15,
        "fascia_cons": 1.0,
        "fascia_scomm": 0.85,
        "scarsita_step": 0.05,
        "scarsita_max": 3,
        "trend_crescita": 0.10,
        "trend_calo": 0.10,
        "trend_gol_dc": 0.08,
        "trend_gol_dc_soglia": 5,
        "trend_gol_a": 0.12,
        "trend_gol_a_soglia": 15,
        "trend_pres": 0.05,
        "trend_pres_soglia": 30,
        "soglia_affare_alto": 0.20,
        "soglia_affare_medio": 0.15,
        "fattore_affare_alto": 1.0,
        "fattore_affare_medio": 0.95,
        "fattore_affare_basso": 0.90,
    }
    P = {k: custom.get(k, v) for k, v in DEF.items()}
    
    # --- FVM PRIORITY ---
    fvm = g_info.get("FVM")
    if fvm is not None and pd.notna(fvm) and float(fvm) > 0:
        base_crediti = crediti_squadra if crediti_squadra is not None and crediti_squadra > 0 else CREDITI_INIZIALI
        prezzo_fvm = max(1, round(float(fvm) * base_crediti / 1000))
        spiegazione = (
            "**Base FVM:** " + str(float(fvm)) + " (indice su 1000)\\n"
            "**Crediti riferimento:** " + str(base_crediti) + "\\n"
            "**Formula:** FVM x Crediti / 1000 = " + str(prezzo_fvm) + "cr\\n\\n"
            "**Prezzo consigliato FVM: " + str(prezzo_fvm) + "cr**"
        )
        return prezzo_fvm, spiegazione

    quot = float(g_info.get("Quotazione", 10))
    fm = float(g_info.get("FantaMedia", 6.0))
    fascia = g_info.get("Consiglio", "consigliato")

    base = quot
    medie_ruolo = {"P": 5.5, "D": 6.2, "C": 6.8, "A": 7.5}
    media_rif = medie_ruolo.get(ruolo, 6.5)
    delta_fm = fm - media_rif
    fattore_fm = 1 + (delta_fm * P["coef_fm"])
    fattore_fascia = {"top": P["fascia_top"], "consigliato": P["fascia_cons"], "scommessa": P["fascia_scomm"]}.get(fascia, 1.0)

    db = st.session_state.giocatori_db
    svinc = get_svincolati(db)
    total_fascia = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == fascia)])
    rimasti = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == fascia)])
    fattore_scarsita = 1 + max(0, (P["scarsita_max"] - rimasti)) * P["scarsita_step"] if total_fascia > 0 else 1.0

    fattore_trend = 1.0
    trend_note = ""
    if stats_df is not None and not stats_df.empty and "Nome" in stats_df.columns:
        g_stats = stats_df[stats_df["Nome"].str.lower() == nome.lower()]
        if g_stats.empty:
            nome_fuzzy = fuzzy_match(nome, stats_df["Nome"].tolist())
            if nome_fuzzy:
                g_stats = stats_df[stats_df["Nome"] == nome_fuzzy]
        if not g_stats.empty:
            if "Stagione" in g_stats.columns:
                g_stats = g_stats.sort_values("Stagione", ascending=False)
            ultima = g_stats.iloc[0]
            if "FantaMedia" in ultima and pd.notna(ultima["FantaMedia"]):
                fm_storica = float(ultima["FantaMedia"])
                if fm > fm_storica + 0.3:
                    fattore_trend += P["trend_crescita"]
                    trend_note = " Trend in crescita"
                elif fm < fm_storica - 0.3:
                    fattore_trend -= P["trend_calo"]
                    trend_note = " Trend in calo"
                else:
                    trend_note = " Trend stabile"
            gol = float(ultima.get("Gol", 0)) if "Gol" in ultima and pd.notna(ultima.get("Gol")) else 0
            if ruolo in ["D", "C"] and gol >= P["trend_gol_dc_soglia"]:
                fattore_trend += P["trend_gol_dc"]
                trend_note += " | " + str(int(gol)) + " gol"
            if ruolo == "A" and gol >= P["trend_gol_a_soglia"]:
                fattore_trend += P["trend_gol_a"]
                trend_note += " | " + str(int(gol)) + " gol"
            if "Partite" in ultima and pd.notna(ultima["Partite"]):
                partite = int(ultima["Partite"])
                if partite >= P["trend_pres_soglia"]:
                    fattore_trend += P["trend_pres"]
                    trend_note += " | " + str(partite) + " presenze"

    indice_affare = fm / max(quot, 1)
    if indice_affare > P["soglia_affare_alto"]:
        fattore_affare = P["fattore_affare_alto"]
    elif indice_affare > P["soglia_affare_medio"]:
        fattore_affare = P["fattore_affare_medio"]
    else:
        fattore_affare = P["fattore_affare_basso"]

    prezzo = base * fattore_fm * fattore_fascia * fattore_scarsita * fattore_trend * fattore_affare
    if math.isnan(prezzo) or math.isinf(prezzo):
        prezzo = base
    prezzo = max(1, round(prezzo))

    custom_tag = " **FORMULA CUSTOM ATTIVA**\\n\\n" if use_custom else ""
    spiegazione = (
        custom_tag +
        "**Base listone:** " + str(int(base)) + "cr\\n"
        "**FantaMedia:** " + str(fm) + " (media ruolo " + ruolo + ": " + str(media_rif) + ") -> fattore " + str(round(fattore_fm, 2)) + "\\n"
        "**Fascia:** " + fascia + " -> fattore " + str(round(fattore_fascia, 2)) + "\\n"
        "**Scarsita:** " + str(rimasti) + "/" + str(total_fascia) + " rimasti -> fattore " + str(round(fattore_scarsita, 2)) + "\\n"
        "**Indice affare:** " + str(round(indice_affare, 3)) + " -> fattore " + str(round(fattore_affare, 2)) + "\\n"
    )
    if trend_note:
        spiegazione += "**Statistiche:**" + trend_note + " -> fattore " + str(round(fattore_trend, 2)) + "\\n"
    spiegazione += "\\n**Prezzo consigliato: " + str(prezzo) + "cr**"
    return prezzo, spiegazione

'''

code = code[:s] + new_func + code[e:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("✅ Corretto! Esegui: streamlit run app.py")
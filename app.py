import streamlit as st
import sqlite3
import pandas as pd

# 1. Configurazione Database
def get_connection():
    return sqlite3.connect('fanta_db.sqlite', check_same_thread=False)

conn = get_connection()

st.title("Fanta-Assistant ⚽")

# --- MENU DI NAVIGAZIONE ---
menu = ["La Mia Rosa", "Mercato / Svincoli"]
scelta = st.sidebar.selectbox("Menu", menu)

# --- 2. LOGICA VISUALIZZAZIONE ROSA ---
if scelta == "La Mia Rosa":
    st.subheader("La tua rosa attuale")
    query = "SELECT nome, ruolo, valore FROM rose"
    df = pd.read_sql(query, conn)
    st.dataframe(df)

# --- 3. LOGICA VENDITA / SVINCOLO (COMPLETA) ---
elif scelta == "Mercato / Svincoli":
    st.subheader("Gestione Mercato: Svincola Giocatore")
    
    # Recupera giocatori in rosa
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, ruolo FROM rose")
    giocatori_rosa = cursor.fetchall()
    
    if giocatori_rosa:
        opzioni = {f"{g[1]} ({g[2]})": g[0] for g in giocatori_rosa}
        scelta_giocatore = st.selectbox("Seleziona il giocatore da svincolare:", options=list(opzioni.keys()))
        
        if st.button("Conferma Svincolo"):
            giocatore_id = opzioni[scelta_giocatore]
            
            try:
                # Esegui la rimozione
                cursor.execute("DELETE FROM rose WHERE id = ?", (giocatore_id,))
                
                # Opzionale: Reinserimento nel database generale (se hai la tabella)
                # cursor.execute("INSERT INTO lista_liberi (id, nome, ruolo) VALUES (?, ?, ?)", ...)
                
                conn.commit()
                st.success(f"Giocatore {scelta_giocatore} rimosso dalla rosa!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")
    else:
        st.info("Rosa vuota.")

# --- 4. GESTIONE BACKUP (Come da tua richiesta precedente) ---
st.sidebar.markdown("---")
if st.sidebar.button("Salva Backup (.zip)"):
    # Logica per zippare il DB
    import zipfile
    with zipfile.ZipFile('backup_fanta.zip', 'w') as zf:
        zf.write('fanta_db.sqlite')
    st.sidebar.success("Backup creato!")
            # ============================================================
        # FORMAZIONI TITOLARI SERIE A — DA FANTACALCIO.IT
        # ============================================================
        st.markdown("---")
        st.subheader("⚽ Probabili Formazioni Serie A")

        c_agg, c_info = st.columns([1, 3])
        with c_agg:
            if st.button("🔄 Aggiorna da Fantacalcio.it", type="primary", use_container_width=True):
                if aggiorna_formazioni_da_fantacalcio():
                    st.success("Formazioni aggiornate!")
                    st.rerun()
        with c_info:
            last_up = st.session_state.get("formazioni_last_update", "Mai")
            st.caption("Ultimo aggiornamento: **" + last_up + "** | Fonte: fantacalcio.it")

        if not st.session_state.get("formazioni_sa"):
            st.info("📭 Nessuna formazione caricata. Clicca '🔄 Aggiorna' per scaricare.")
        else:
            formazioni = st.session_state.formazioni_sa
            squadre_list = sorted(formazioni.keys())
            tabs_sa = st.tabs(squadre_list)
            colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444", "?": "#888"}
            ruoli_nomi = {"P": "🧤", "D": "🛡️", "C": "⚙️", "A": "⚔️", "?": "❓"}

            for i, sa in enumerate(squadre_list):
                with tabs_sa[i]:
                    dati = formazioni[sa]
                    modulo_reale = dati.get("modulo_reale", dati["modulo"])
                    modulo_conv = dati["modulo"]

                    st.markdown(
                        "<div style='font-size:1.1em;font-weight:bold;color:#00d26a;margin-bottom:8px;'>"
                        + sa + " — Modulo: " + modulo_reale + " (app: " + modulo_conv + ")</div>",
                        unsafe_allow_html=True
                    )

                    conti = {"P": 0, "D": 0, "C": 0, "A": 0}
                    for g in dati["titolari"]:
                        r = g.get("ruolo", "?")
                        if r in conti: conti[r] += 1
                    st.caption(
                        "Titolari: " + str(conti["P"]) + "P + " + str(conti["D"]) + "D + " +
                        str(conti["C"]) + "C + " + str(conti["A"]) + "A | Tot: " +
                        str(len(dati["titolari"])) + " titolari, " +
                        str(len(dati.get("panchina", []))) + " panchina"
                    )

                    col_ruoli = st.columns(4)
                    ruoli_order = ["P", "D", "C", "A"]

                    for j, ruolo in enumerate(ruoli_order):
                        with col_ruoli[j]:
                            st.markdown("**" + ruoli_nomi[ruolo] + " " + ruolo + "**")
                            titolari_r = [g for g in dati["titolari"] if g.get("ruolo") == ruolo]
                            panchina_r = [g for g in dati.get("panchina", []) if g.get("ruolo") == ruolo]

                            for g in titolari_r:
                                prob = g.get("prob", 0)
                                if prob >= 80:
                                    prob_col = "#00d26a"
                                    prob_badge = "🟢"
                                elif prob >= 50:
                                    prob_col = "#eab308"
                                    prob_badge = "🟡"
                                else:
                                    prob_col = "#ef4444"
                                    prob_badge = "🔴"
                                prop = g.get("proprietario", "Svincolato")
                                prop_col = "#ff6b6b" if prop != "Svincolato" else "#00d26a"
                                prop_txt = "🔒 " + prop if prop != "Svincolato" else "🟢 Libero"
                                col_r = colori_ruolo.get(ruolo, "#888")

                                card_html = (
                                    '<div style="background: linear-gradient(145deg, #1e1e3f, #2a2a4a);'
                                    ' border-left: 4px solid ' + col_r + ';'
                                    ' border-radius: 12px; padding: 10px 12px; margin-bottom: 6px;'
                                    ' box-shadow: 0 6px 12px rgba(0,0,0,0.4);">'
                                    ' <div style="display:flex;justify-content:space-between;align-items:center;">'
                                    ' <div style="font-size:0.95em;font-weight:700;color:#fff;">' + g["nome"] + '</div>'
                                    ' <div style="font-size:0.8em;color:' + prob_col + ';font-weight:bold;">' + prob_badge + ' ' + str(prob) + '%</div>'
                                    ' </div>'
                                    ' <div style="font-size:0.75em;color:#aaa;margin-top:2px;">FM ' + str(g.get("fm", 0)) + ' | ' + str(g.get("quot", 0)) + 'cr</div>'
                                    ' <div style="font-size:0.7em;color:' + prop_col + ';margin-top:2px;">' + prop_txt + '</div>'
                                    ' </div>'
                                )
                                st.html(card_html)

                            if not titolari_r:
                                st.caption("Nessun titolare")

                            if panchina_r:
                                st.markdown("<div style='font-size:0.7em;color:#666;margin-top:8px;margin-bottom:4px;'>🪑 Panchina " + ruolo + "</div>", unsafe_allow_html=True)
                                for g in panchina_r:
                                    prob = g.get("prob", 0)
                                    prop = g.get("proprietario", "Svincolato")
                                    prop_col = "#ff6b6b" if prop != "Svincolato" else "#00d26a"
                                    prop_txt = "🔒 " + prop if prop != "Svincolato" else "🟢 Libero"
                                    col_r = colori_ruolo.get(ruolo, "#888")

                                    card_pan = (
                                        '<div style="background: linear-gradient(145deg, #15152b, #1a1a2e);'
                                        ' border-left: 3px solid #2a2a4a;'
                                        ' border-radius: 10px; padding: 8px 12px; margin-bottom: 4px;'
                                        ' box-shadow: 0 2px 4px rgba(0,0,0,0.2); opacity: 0.75;">'
                                        ' <div style="font-size:0.9em;font-weight:600;color:#ccc;">' + g["nome"] + '</div>'
                                        ' <div style="font-size:0.7em;color:#666;margin-top:1px;">FM ' + str(g.get("fm", 0)) + ' | ' + str(g.get("quot", 0)) + 'cr | ' + str(prob) + '%</div>'
                                        ' <div style="font-size:0.65em;color:' + prop_col + ';margin-top:1px;">' + prop_txt + '</div>'
                                        ' </div>'
                                    )
                                    st.html(card_pan)
                      st.subheader("🏆 Top Svincolati — Flip Card 3D")
                st.caption("🖱️ Passa il mouse sulla card per girarla e vedere le statistiche!")
                svinc_df = df[df["Proprietario"] == "Svincolato 🟢"].copy()
                if not svinc_df.empty:
                    top_mixed = svinc_df.nlargest(8, "Indice_Titolarita")
                    cards = st.columns(4)
                    stats_ps = st.session_state.get("stats_per_stagione", {})
                    for i, (_, row) in enumerate(top_mixed.iterrows()):
                        with cards[i % 4]:
                            nome = row["Nome"]
                            ruolo = row["Ruolo"]
                            sa = row.get("Squadra_SerieA", "N/D")
                            fm = row.get("FantaMedia", 0)
                            quot = int(row.get("Quotazione", 0))
                            fascia = row.get("Consiglio", "consigliato")
                            idx_aff = row.get("Indice_Affare", 0)
                            idx_tit = row.get("Indice_Titolarita", 0)
                            pc = row.get("Prezzo_Consigliato")
                            pc_txt = f"💡 {int(pc)}cr" if pd.notna(pc) else ""
                            note = row.get("Note", "")
                            
                            colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
                            colore = colori_ruolo.get(ruolo, "#888")
                            badge_fascia = {"top": "⭐ TOP", "consigliato": "👍 CONSIGLIATO", "scommessa": "🎲 SCOMMESSA"}.get(fascia, "")
                            flame_badge = flame_indicator(nome, stats_ps) if stats_ps else ""
                            
                            # FRONTE
                            front_html = f'<div style="background:linear-gradient(135deg, rgba(30,30,63,0.95) 0%, rgba(42,42,74,0.8) 100%);backdrop-filter:blur(10px);border-radius:12px;padding:14px;height:100%;box-sizing:border-box;border-left:4px solid {colore};box-shadow:0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);display:flex;flex-direction:column;justify-content:space-between;"><div><div style="font-size:1.1em;font-weight:bold;color:#fff;text-shadow:0 2px 4px rgba(0,0,0,0.5);">{nome}</div><div style="font-size:0.85em;color:#aaa;">{sa} | <span style="color:{colore};font-weight:600;">{ruolo}</span></div></div><div style="text-align:center;margin:8px 0;"><div style="font-size:2em;font-weight:bold;color:#ffd700;">{fm}</div><div style="font-size:0.75em;color:#888;">FantaMedia</div></div><div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:center;"><span style="background:{colore}30;color:{colore};padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:600;border:1px solid {colore}40;">{badge_fascia}</span><span style="background:rgba(26,26,46,0.6);color:#ddd;padding:2px 8px;border-radius:12px;font-size:0.7em;">{quot}cr</span>{pc_txt}</div>{flame_badge}</div>'
                            
                            # RETRO (stats)
                            stats_html = _build_stats_html(nome, stats_ps)
                            back_html = f'<div style="background:linear-gradient(135deg, #0f0f24 0%, #1a1a2e 100%);border-radius:12px;padding:14px;height:100%;box-sizing:border-box;border:1px solid {colore}40;box-shadow:0 8px 32px rgba(0,0,0,0.4);display:flex;flex-direction:column;justify-content:center;overflow:hidden;"><div style="font-size:0.85em;color:#00d26a;font-weight:bold;margin-bottom:6px;">📊 {nome}</div><div style="overflow-y:auto;max-height:140px;">{stats_html}</div></div>'
                            
                            # FLIP CARD HTML
                            flip = f'<div class="flip-card" style="height:200px;margin-bottom:10px;"><div class="flip-card-inner"><div class="flip-card-front">{front_html}</div><div class="flip-card-back">{back_html}</div></div></div>'
                            st.markdown(flip, unsafe_allow_html=True)
                else:
                    st.info("Nessuno svincolato disponibile.")
                       /* 🎴 Flip Card 3D */
    .flip-card {
        background-color: transparent;
        perspective: 1000px;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: left;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
    }
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 12px;
    }
    .flip-card-back {
        transform: rotateY(180deg);
    }
                                   
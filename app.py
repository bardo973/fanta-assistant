import io
import pandas as pd
import streamlit as st

def ripara_testo(testo):
    """Funzione di supporto per pulire eventuali caratteri corrotti nel testo del file."""
    if not isinstance(testo, str):
        return str(testo)
    return testo

def elabora_file_caricato(uploaded_file):
    """
    Legge e processa in modo robusto qualsiasi file Excel (.xlsx, .xls) o CSV/TXT,
    gestendo codifiche multiple, pulizia delle colonne e righe vuote.
    """
    if uploaded_file is None:
        return None
        
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df_excel = None
    
    try:
        if file_extension in ['xlsx', 'xls', 'ods']:
            df_excel = pd.read_excel(uploaded_file, dtype=str)
        else:
            content_bytes = uploaded_file.read()
            text_content = None
            for enc in ['utf-8', 'cp1252', 'latin1', 'iso-8859-1']:
                try:
                    text_content = content_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if text_content is None:
                text_content = content_bytes.decode('latin1', errors='ignore')
                
            text_content = ripara_testo(text_content)
            lines = [line.strip() for line in text_content.splitlines() if line.strip()]
            
            if not lines:
                return None

            sep_char = '\t' if '\t' in lines[0] else (';' if ';' in lines[0] else (',' if ',' in lines[0] else ';'))
            df_excel = pd.read_csv(io.StringIO(text_content), sep=sep_char, dtype=str, on_bad_lines='skip')

        if df_excel is None or df_excel.empty:
            return None

        # Pulizia radicale dei nomi delle colonne
        df_excel.columns = [str(c).strip().lower() for c in df_excel.columns]
        
        # Cerca la colonna del nome del calciatore
        col_nome = next((c for c in df_excel.columns if c in ['nome', 'calciatore', 'player']), df_excel.columns[1] if len(df_excel.columns) > 1 else df_excel.columns[0])
        
        # Pulizia delle righe vuote basata sul nome
        df_excel = df_excel.dropna(subset=[col_nome])
        df_excel = df_excel[df_excel[col_nome].str.strip().str.lower() != 'nan']
        df_excel = df_excel[df_excel[col_nome].str.strip() != '']
        df_excel = df_excel.reset_index(drop=True)

        return df_excel

    except Exception as e:
        st.error(f"Errore durante la lettura del file: {e}")
        return None

def sincronizza_rose_e_listone(df_listone, df_rose):
    """
    Incrocia il listone ufficiale con il file delle rose.
    Assegna i proprietari e imposta 'LIBERO' per tutti gli altri.
    """
    if df_listone is None or df_listone.empty:
        return None

    # Normalizza le colonne del listone
    df_listone.columns = [str(c).strip().lower() for c in df_listone.columns]
    col_nome_listone = next((c for c in df_listone.columns if c in ['nome', 'calciatore', 'player']), df_listone.columns[1] if len(df_listone.columns) > 1 else df_listone.columns[0])
    
    # Se non viene caricato il file delle rose, tutti sono liberi
    if df_rose is None or df_rose.empty:
        df_listone['proprietario'] = 'LIBERO'
        return df_listone

    # Cerca le colonne chiave nel file delle rose
    col_nome_rose = next((c for c in df_rose.columns if c in ['nome', 'calciatore', 'player']), None)
    col_prop_rose = next((c for c in df_rose.columns if c in ['proprietario', 'prop', 'squadra_fantacalcio', 'vincolato', 'mister', 'rosa']), None)

    if not col_nome_rose or not col_prop_rose:
        st.warning("Il file delle rose non contiene una colonna valida per il nome del giocatore o per il proprietario.")
        df_listone['proprietario'] = 'LIBERO'
        return df_listone

    # Chiavi di join normalizzate (senza spazi e minuscole) per evitare errori di corrispondenza
    df_listone['chiave_join'] = df_listone[col_nome_listone].astype(str).str.strip().str.lower()
    df_rose['chiave_join'] = df_rose[col_nome_rose].astype(str).str.strip().str.lower()

    # Prepara il dataframe delle rose ridotto alle sole colonne necessarie
    df_rose_filtrato = df_rose[['chiave_join', col_prop_rose]].copy()
    df_rose_filtrato.rename(columns={col_prop_rose: 'proprietario'}, inplace=True)

    # Rimuovi eventuali duplicati nel file rose per evitare conflitti di merge
    df_rose_filtrato = df_rose_filtrato.drop_duplicates(subset=['chiave_join'])

    # Unione (Left Join) tra il listone ufficiale e le rose
    df_unito = pd.merge(df_listone, df_rose_filtrato, on='chiave_join', how='left')

    # Gestione dei valori mancanti o celle vuote -> diventano LIBERO
    df_unito['proprietario'] = df_unito['proprietario'].fillna('LIBERO').astype(str).str.strip()
    df_unito.loc[df_unito['proprietario'].isin(['', 'nan', 'None', '-']), 'proprietario'] = 'LIBERO'

    # Pulizia della colonna di servizio
    df_unito = df_unito.drop(columns=['chiave_join'])

    return df_unito

def main():
    st.title("Gestione Rose e Listone Fantacalcio")
    
    st.sidebar.header("📂 Caricamento File")
    
    # 1. Caricamento del Listone Ufficiale (es. RM, Nome, Squadra, Qt.A, ecc.)
    file_listone = st.sidebar.file_uploader("1. Carica Listone Ufficiale (Excel/CSV)", type=["xlsx", "xls", "csv", "txt"])
    
    # 2. Caricamento del File delle Rose con i Proprietari (Opzionale)
    file_rose = st.sidebar.file_uploader("2. Carica File Rose con Proprietari (Opzionale)", type=["xlsx", "xls", "csv", "txt"])
    
    if file_listone is not None:
        # Elaborazione file
        df_listone_raw = elabora_file_caricato(file_listone)
        df_rose_raw = elabora_file_caricato(file_rose) if file_rose is not None else None
        
        # Sincronizzazione rose e listone
        df_finale = sincronizza_rose_e_listone(df_listone_raw, df_rose_raw)
        
        if df_finale is not None and not df_finale.empty:
            st.success("Dati caricati e sincronizzati correttamente!")
            
            # Statistiche rapide nella dashboard
            totale_giocatori = len(df_finale)
            liberi = len(df_finale[df_finale['proprietario'].str.upper() == "LIBERO"])
            occupati = totale_giocatori - liberi
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Totale Giocatori", totale_giocatori)
            col2.metric("Giocatori in Rosa (Occupati)", occupati)
            col3.metric("Giocatori Svincolati (Liberi)", liberi)
            
            # Filtri di visualizzazione
            st.subheader("📋 Lista Giocatori Sincronizzati")
            filtro_proprietario = st.selectbox(
                "Filtra per proprietario / stato:", 
                ["Tutti"] + sorted(df_finale['proprietario'].unique().tolist())
            )
            
            if filtro_proprietario != "Tutti":
                df_mostra = df_finale[df_finale['proprietario'] == filtro_proprietario]
            else:
                df_mostra = df_finale
                
            st.dataframe(df_mostra, use_container_width=True)
            
    else:
        st.info("👈 Carica almeno il **Listone Ufficiale** dalla barra laterale per iniziare.")

if __name__ == '__main__':
    main()
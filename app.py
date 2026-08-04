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
    gestendo codifiche multiple, pulizia delle colonne, sinonimi e righe vuote.
    """
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df_excel = None
    
    try:
        # 1. Lettura robusta a seconda dell'estensione del file
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
                st.error("Il file caricato è vuoto.")
                return None, {}

            sep_char = '\t' if '\t' in lines[0] else (';' if ';' in lines[0] else (',' if ',' in lines[0] else ';'))
            df_excel = pd.read_csv(io.StringIO(text_content), sep=sep_char, dtype=str, on_bad_lines='skip')

        if df_excel is None or df_excel.empty:
            st.warning("Nessun dato trovato all'interno del file.")
            return None, {}

        # 2. Pulizia radicale dei nomi delle colonne
        df_excel.columns = [str(c).strip().lower() for c in df_excel.columns]
        
        # 3. Mappatura avanzata dei sinonimi
        map_colonne = {}
        for col in df_excel.columns:
            if any(k in col for k in ["calciatore", "giocatore", "nome", "player", "fotbalist"]):
                map_colonne["calciatore"] = col
            elif any(k in col for k in ["ruolo", "pos", "role"]):
                map_colonne["ruolo"] = col
            elif any(k in col for k in ["squadra", "team", "club"]):
                map_colonne["squadra"] = col
            elif any(k in col for k in ["quotazione", "prezzo", "valore", "qt", "costo"]):
                map_colonne["quotazione"] = col
            elif any(k in col for k in ["proprietario", "prop", "squadra_fantacalcio", "vincolato", "titolare", "rosa", "mister"]):
                map_colonne["proprietario"] = col
            elif any(k in col for k in ["scad", "contratto", "scadenza", "fine"]):
                map_colonne["scadenza"] = col

        if "calciatore" not in map_colonne and len(df_excel.columns) > 0:
            map_colonne["calciatore"] = df_excel.columns[0]
            
        # 4. Pulizia delle righe
        if "calciatore" in map_colonne:
            df_excel = df_excel.dropna(subset=[map_colonne["calciatore"]])
            df_excel = df_excel[df_excel[map_colonne["calciatore"]].str.strip().str.lower() != 'nan']
            df_excel = df_excel[df_excel[map_colonne["calciatore"]].str.strip() != '']
            df_excel = df_excel.reset_index(drop=True)

        return df_excel, map_colonne

    except Exception as e:
        st.error(f"Errore critico durante la lettura del file: {e}")
        return None, {}


def main():
    st.title("Importazione Dati / Rosa")
    
    uploaded_file = st.file_uploader("Carica il tuo file Excel o CSV", type=["xlsx", "xls", "csv", "txt"])
    
    if uploaded_file is not None:
        df, mapeggiamento = elabora_file_caricato(uploaded_file)
        
        if df is not None and not df.empty:
            st.success(f"File caricato con successo! Righe valide rilevate: {len(df)}")
            
            st.write("### Mappatura Colonne Riconosciute:")
            st.json(mapeggiamento)
            
            st.write("### Anteprima Dati:")
            st.dataframe(df.head(10))
            
            col_nome = mapeggiamento.get("calciatore")
            col_prop = mapeggiamento.get("proprietario")
            
            if col_prop:
                df[col_prop] = df[col_prop].fillna("LIBERO").astype(str).str.strip()
                df.loc[df[col_prop].isin(['', 'nan', 'None', '-']), col_prop] = "LIBERO"
                
                liberi = len(df[df[col_prop].str.upper() == "LIBERO"])
                occupati = len(df) - liberi
                st.info(f"Giocatori assegnati a rose: {occupati} | Giocatori liberi: {liberi}")

if __name__ == '__main__':
    main()
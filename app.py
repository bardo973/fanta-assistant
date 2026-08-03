import pandas as pd
import io

# Configura l'uploader per accettare anche i file di testo (.txt)
uploaded_file = st.file_uploader(
    "Carica il listone o la rosa", 
    type=["csv", "xlsx", "xls", "txt"]
)

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension in ['csv', 'txt']:
            # Legge il file come testo o CSV
            content_bytes = uploaded_file.read()
            
            # Proviamo a decodificare in utf-8 (o latin1 come fallback)
            try:
                text_content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text_content = content_bytes.decode('latin1')
                
            if file_extension == 'txt':
                # Gestione file di testo: ogni riga è un giocatore (o dati separati da tab/virgola)
                lines = [line.strip() for line in text_content.splitlines() if line.strip()]
                
                # Se il file di testo ha un'intestazione o righe tabulate
                if any(',' in line or '\t' in line for line in lines[:3]):
                    sep = '\t' if '\t' in lines[0] else ','
                    df = pd.read_csv(io.StringIO(text_content), sep=sep)
                else:
                    # Semplice elenco di nomi di giocatori riga per riga
                    df = pd.DataFrame({'Giocatore': lines})
            else:
                # File CSV standard
                df = pd.read_csv(io.StringIO(text_content))
                
        elif file_extension in ['xlsx', 'xls']:
            # Gestione file Excel
            df = pd.read_excel(uploaded_file)
            
        # Controllo di sicurezza sulla colonna del nome/giocatore
        possible_columns = ['Giocatore', 'Calciatore', 'Nome', 'Player']
        col_trovata = next((col for col in possible_columns if col in df.columns), None)
        
        if col_trovata is None and len(df.columns) > 0:
            # Se non trova l'intestazione esatta ma il file ha una prima colonna utile
            # o se è un elenco semplice da file di testo, usiamo la prima colonna come 'Giocatore'
            if file_extension == 'txt' and 'Giocatore' in df.columns:
                col_trovata = 'Giocatore'
            else:
                st.warning(f"Impossibile individuare automaticamente la colonna del nome. Uso la prima colonna: {df.columns[0]}")
                df = df.rename(columns={df.columns[0]: 'Giocatore'})
                col_trovata = 'Giocatore'
                
        st.success(In "Rosa caricata con successo! Trovati {len(df)} elementi.")
        
    except Exception as e:
        st.error(f"Errore durante la lettura del file: {e}")
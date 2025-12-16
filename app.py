import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Satish CRM", layout="centered")

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def connect_gsheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Carrega os segredos do arquivo secrets.toml
    secrets_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(secrets_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    return client.open_by_url(spreadsheet_url).sheet1

def load_data():
    sheet = connect_gsheets()
    # Pega todos os registros para manter o índice original (essencial para edição)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Erro de Conexão. Por favor verifique o secrets.toml")
    st.stop()

# --- MAPEAMENTO DE COLUNAS ---
# Interno: Deve bater exatamente com os cabeçalhos do Google Sheets (Português)
# Visual: O que o Satish vê na tela (Inglês)
COL_STATUS = "Ativo/Morno/Frio"  
COL_TRADER = "Trader"            
COL_POD = "POD"                  
COL_PRODUTO = "Product"          
COL_EMPRESA = "Empresa"          
COL_NOME = "Nome"                
COL_EMAIL = "Email Client"       
COL_ZAP = "Whatsapp Cliente"     

# Garante que a coluna Status existe no DataFrame
if COL_STATUS not in df.columns:
    df[COL_STATUS] = None

# --- LISTAS GLOBAIS ---
# 1. PODs (Portos)
PODS_DEFAULT = [
    "Abidjan – Costa do Marfim", "Aden - Yemen", "Alexandria - Egito", "Algeciras - Espanha",
    "Algiers - Argelia", "Altamira - México", "Apapa – Nigéria", "Aqaba - Jordânia",
    "Banjul – Gâmbia", "Bata – Guiné Equatorial", "Beira – Moçambique", "Beirut – Líbano",
    "Belarus", "Buenos Aires - Argentina", "Bulgária - Varna", "Busan – Coreia do Sul",
    "Callao - Peru", "Cape Town - South Africa", "Chittagong - Bangladesh", "Conakry – Guiné",
    "Cotonou – Benim", "Dakar – Senegal", "Dammam – Saudi Arabia", "Djibouti - Djibouti",
    "Doha - Catar", "Douala – Camarões", "Durban - South Africa", "Durres - Albânia",
    "USA", "Freetown – Serra Leoa", "Georgetown - Guyana", "Greece",
    "Hamad - Catar", "Hamilton - Bermuda", "Ho Chi Min - Vietnã", "Hong Kong – Hong Kong",
    "Italy", "Jebel Ali – UAE", "Khalifa Bin Salman - Bahrain",
    "Kingston - Jamaica", "Kosovo", "Kribi – Camarões", "Libreville – Gabão",
    "Limassol - Chipre", "Lomé – Togo", "Louis - Rep. das Mauricias", "Luanda – Angola",
    "Macedonia", "Malabo – Guiné Equatorial", "Manila - Filipinas", "Manzanillo - Rep. Dominicana",
    "Maputo – Moçambique", "Mariel – Cuba", "Matadi – DRC",
    "Monrovia – Libéria", "Montevideo - Uruguay", "Nacala – Moçambique", "Nassau - Bahamas",
    "Odesa - Ukraine", "Oranjestad - Aruba", "Pointe Noire – Congo", "Port Au Prince - Haiti",
    "Port Gentil – Gabão", "Port Klang - Malaysia", "Port Réunion", "Port Sudan - Sudão",
    "Port of Berbera - Somália", "Port of Hamburg - Germany", "Port of Klaipėda- Lituânia",
    "Poti - Georgia", "Praia - Cabo Verde", "Riga - Letônia", "Rotterdam - Netherlands",
    "Shanghai - China", "Shuwaikh – Kuwait", "Sohar – Omã", "St. Petersburg - Russia",
    "Tanger Med - Marrocos", "Tema – Gana", "Tenerife - Ilhas Canárias", "Toamasina - Madagascar",
    "Tokyo - Japan", "Tripoli - Libia", "Umm Qasr – Iraq", "Valparaíso - Chile",
    "Veracruz - México", "Victoria - Seychelles", "Vladivostok - Russia", "Walvis Bay – Namíbia",
    "Willemstad - Curacao", "Zamzibar – Tânzania"
]

# 2. Produtos
PRODUCTS_LIST = ["Beef", "Chicken", "Hen", "Pork", "Fish", "Lamb", "Mutton", "Turkey", "Duck"]

# --- INTERFACE DO APP ---
st.title("📱 Satish CRM")
tab_search, tab_add = st.tabs(["🔍 Search & Edit", "➕ New Client"])

# ==========================================
# ABA 1: BUSCA E EDIÇÃO
# ==========================================
with tab_search:
    with st.expander("Show Filters", expanded=False):
        c1, c2 = st.columns(2)
        
        # Filtro de POD
        current_pods = df[COL_POD].dropna().unique().tolist()
        all_pods = sorted(list(set(PODS_DEFAULT + current_pods)))
        filter_pod = c1.selectbox("Port (POD)", ["All"] + all_pods)
        
        # Filtro de Status
        filter_status = c2.selectbox("Status", ["All", "Ativo", "Morno", "Frio", "supplier"])
        search_text = st.text_input("Search by Name or Company")

    # Lógica de Filtragem
    df_filtered = df.copy()
    
    if filter_pod != "All":
        df_filtered = df_filtered[df_filtered[COL_POD] == filter_pod]
        
    if filter_status != "All":
        df_filtered = df_filtered[df_filtered[COL_STATUS] == filter_status]
        
    if search_text:
        df_filtered = df_filtered[
            df_filtered[COL_EMPRESA].str.contains(search_text, case=False, na=False) |
            df_filtered[COL_NOME].str.contains(search_text, case=False, na=False)
        ]

    st.caption(f"{len(df_filtered)} clients found")

    for index, row in df_filtered.iterrows():
        with st.container(border=True):
            col_top_a, col_top_b = st.columns([3, 1])
            
            # Cores do Status
            status_val = str(row[COL_STATUS]) if pd.notna(row[COL_STATUS]) else "-"
            color = "gray"
            if "Ativo" in status_val: color = "red"
            elif "Morno" in status_val: color = "orange"
            elif "Frio" in status_val: color = "blue"
            elif "supplier" in status_val: color = "green"
            
            col_top_a.write(f"**{row[COL_EMPRESA]}**")
            col_top_b.markdown(f":{color}[**{status_val}**]")
            
            st.caption(f"👤 {row[COL_NOME]} | 📍 {row[COL_POD]}")
            
            if pd.notna(row[COL_PRODUTO]) and row[COL_PRODUTO]:
                st.code(f"{row[COL_PRODUTO]}", language="text")
            
            # Botão do WhatsApp
            tel = str(row[COL_ZAP])
            tel_clean = ''.join(filter(str.isdigit, tel))
            if tel_clean:
                st.link_button(" WhatsApp", f"https://wa.me/{tel_clean}", use_container_width=True)

            # --- SEÇÃO DE EDIÇÃO ---
            with st.expander("✎ Edit Details"):
                with st.form(f"edit_form_{index}"):
                    st.write("Update Client Information:")
                    
                    # 1. Status
                    edit_status = st.select_slider("Status", options=["Frio", "Morno", "Ativo", "supplier"], value=status_val if status_val in ["Frio", "Morno", "Ativo", "supplier"] else "Frio")
                    
                    # 2. Produtos (Lógica de Multi-seleção na edição)
                    # Prepara lista dos produtos atuais deste cliente
                    current_prods_list = []
                    if pd.notna(row[COL_PRODUTO]) and row[COL_PRODUTO]:
                        # Separa a string "Beef | Chicken" em uma lista ["Beef", "Chicken"]
                        current_prods_list = [p.strip() for p in str(row[COL_PRODUTO]).split("|")]
                    
                    # Garante que todos os produtos atuais estejam na lista de opções para evitar erros
                    edit_prod_options = sorted(list(set(PRODUCTS_LIST + current_prods_list)))
                    
                    edit_products = st.multiselect(
                        "Products", 
                        options=edit_prod_options, 
                        default=[p for p in current_prods_list if p in edit_prod_options]
                    )

                    # 3. Outros campos
                    edit_empresa = st.text_input("Company", value=row[COL_EMPRESA])
                    edit_nome = st.text_input("Contact Name", value=row[COL_NOME])
                    edit_pod = st.selectbox("POD", options=["Keep Current"] + all_pods, index=0)
                    edit_zap = st.text_input("WhatsApp", value=row[COL_ZAP])
                    
                    update_btn = st.form_submit_button("Update Client")
                    
                    if update_btn:
                        try:
                            sheet = connect_gsheets()
                            # Calcula o número real da linha (Index do DataFrame + 2 por causa do cabeçalho)
                            row_num = index + 2
                            
                            # Decide qual POD salvar
                            pod_to_save = row[COL_POD] if edit_pod == "Keep Current" else edit_pod
                            # Junta a lista de volta em String
                            str_products_final = " | ".join(edit_products) 
                            
                            # Atualiza células específicas (Colunas A, C, D, E, F, H)
                            sheet.update_cell(row_num, 1, edit_status)      # Col A: Status
                            sheet.update_cell(row_num, 3, pod_to_save)      # Col C: POD
                            sheet.update_cell(row_num, 4, str_products_final) # Col D: Product
                            sheet.update_cell(row_num, 5, edit_empresa)     # Col E: Empresa
                            sheet.update_cell(row_num, 6, edit_nome)        # Col F: Nome
                            sheet.update_cell(row_num, 8, edit_zap)         # Col H: Zap
                            
                            st.success("Client Updated! Please refresh.")
                            st.cache_resource.clear() # Limpa o cache para mostrar mudanças
                            
                        except Exception as e:
                            st.error(f"Error updating: {e}")

# ==========================================
# ABA 2: ADICIONAR NOVO CLIENTE
# ==========================================
with tab_add:
    st.write("Add a new client to database:")
    
    with st.form("add_form", clear_on_submit=True):
        st.write("**Status (Level):**")
        new_status = st.select_slider(
            "Select Status:",
            options=["Frio", "Morno", "Ativo", "supplier"],
            value="Ativo"
        )
        
        st.divider()
        st.write("**POD / Location:**")
        # Lógica para adicionar POD customizado
        current_pods_add = df[COL_POD].dropna().unique().tolist()
        options_pod_add = sorted(list(set(PODS_DEFAULT + current_pods_add)))
        final_options = ["➕ Other (Type New)..."] + options_pod_add
        
        choice_pod = st.selectbox("Select Port:", options=final_options)
        
        pod_final = choice_pod
        if choice_pod == "➕ Other (Type New)...":
            pod_typed = st.text_input("Type new Port/Country:", placeholder="e.g. Santos - Brazil")
            pod_final = pod_typed
        
        st.divider()
        st.write("**Products of Interest:**")
        
        # Usando checkboxes aqui (mais fácil para entrada mobile)
        cols = st.columns(3)
        selected_prods = []
        for i, p in enumerate(PRODUCTS_LIST):
            if cols[i % 3].checkbox(p):
                selected_prods.append(p)
        
        st.divider()
        new_company = st.text_input("Company Name")
        new_name = st.text_input("Contact Name")
        new_email = st.text_input("Email")
        new_zap = st.text_input("WhatsApp (with Country Code)")
        
        submit_btn = st.form_submit_button("💾 Save to Sheet", type="primary")
        
        if submit_btn:
            str_prods = " | ".join(selected_prods)
            
            if not new_company:
                st.error("Company Name is required!")
            elif choice_pod == "➕ Other (Type New)..." and not pod_typed:
                st.error("Please type the new Port name.")
            else:
                try:
                    # Prepara nova linha
                    new_row = [
                        new_status,     # A
                        "Satish",       # B (Fixo)
                        pod_final,      # C
                        str_prods,      # D
                        new_company,    # E
                        new_name,       # F
                        new_email,      # G
                        new_zap         # H
                    ]
                    
                    sheet = connect_gsheets()
                    sheet.append_row(new_row)
                    st.toast(f"Saved! {new_company} added.", icon="✅")
                    st.cache_resource.clear() 
                    
                except Exception as e:
                    st.error(f"Error saving: {e}")
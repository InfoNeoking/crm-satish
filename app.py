import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from PIL import Image
from google import genai
import json
import time

# Configuração da página
st.set_page_config(page_title="Satish CRM", layout="centered")

# --- SISTEMA DE LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def check_login():
    email = st.session_state["input_email"].strip().lower()
    password = st.session_state["input_password"]
    
    # Validação: Email deve terminar com @neokingfoods.com e senha deve ser 123456
    if email.endswith("@neokingfoods.com") and password == "123456":
        st.session_state["logged_in"] = True
        st.success("Login authorized")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("Access Denied. Use a Neo King Foods email.")

if not st.session_state["logged_in"]:
    st.title("Neo King Foods CRM")
    st.write("Please log in to access the system.")
    
    st.text_input("Email", key="input_email", placeholder="name@neokingfoods.com")
    st.text_input("Password", type="password", key="input_password")
    
    st.button("Login", on_click=check_login, type="primary")
    st.stop() # Para a execução do código aqui se não estiver logado

# ========================================================
# DAQUI PARA BAIXO É O CÓDIGO DO CRM (SÓ RODA SE LOGADO)
# ========================================================

# Função: Ler cartão com IA
def ler_cartao_com_ia(image_file):
    try:
        if "api" not in st.secrets or "gemini" not in st.secrets["api"]:
            st.error("AI Key not found in secrets.toml")
            return None

        api_key = st.secrets["api"]["gemini"]
        client = genai.Client(api_key=api_key)
        img = Image.open(image_file)
        
        prompt = """
        Analise esta imagem de cartão de visita. Extraia os dados em formato JSON estrito:
        {
            "nome": "Nome da pessoa",
            "empresa": "Nome da empresa",
            "email": "O email principal",
            "telefone": "O telefone principal (com código do país se houver)",
            "cargo": "O cargo da pessoa"
        }
        Se não encontrar algum campo, deixe como string vazia "". Responda APENAS o JSON, sem markdown.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt, img]
        )
        
        texto_limpo = response.text.replace("```json", "").replace("```", "").strip()
        dados = json.loads(texto_limpo)
        return dados

    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# Conexão Google Sheets
@st.cache_resource
def connect_gsheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    secrets_dict = dict(st.secrets["connections"]["gsheets"])
    creds = Credentials.from_service_account_info(secrets_dict, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    return client.open_by_url(spreadsheet_url).sheet1

def load_data():
    sheet = connect_gsheets()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

try:
    df = load_data()
except:
    st.stop()

# Mapeamento de Colunas
COL_STATUS = "Ativo/Morno/Frio"
COL_POD = "POD"
COL_EMPRESA = "Empresa"
COL_NOME = "Nome"
COL_EMAIL = "Email Client"
COL_ZAP = "Whatsapp Cliente"
COL_PRODUTO = "Product"

if COL_STATUS not in df.columns: df[COL_STATUS] = None

# Listas de Dados
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
PRODUCTS_LIST = ["Beef", "Chicken", "Hen", "Pork", "Fish", "Lamb", "Mutton", "Turkey", "Duck"]
STATUS_OPTIONS = ["Frio", "Morno", "Ativo", "supplier"]

# Interface Principal (Só aparece se passar do login)
st.title("Satish CRM")
if st.button("Logout", type="secondary"):
    st.session_state["logged_in"] = False
    st.rerun()

# Menu de navegação
view_option = st.radio(
    "Menu:", 
    ["Search & Edit", "New Client"], 
    horizontal=True,
    label_visibility="collapsed"
)

st.divider()

# --- ABA 1: BUSCA E EDIÇÃO ---
if view_option == "Search & Edit":
    with st.expander("Show Filters", expanded=False):
        c1, c2 = st.columns(2)
        current_pods = df[COL_POD].dropna().unique().tolist()
        all_pods = sorted(list(set(PODS_DEFAULT + current_pods)))
        filter_pod = c1.selectbox("Port (POD)", ["All"] + all_pods)
        filter_status = c2.selectbox("Status", ["All"] + STATUS_OPTIONS)
        search_text = st.text_input("Search by Name or Company")

    df_filtered = df.copy()
    if filter_pod != "All": df_filtered = df_filtered[df_filtered[COL_POD] == filter_pod]
    if filter_status != "All": df_filtered = df_filtered[df_filtered[COL_STATUS] == filter_status]
    if search_text:
        df_filtered = df_filtered[
            df_filtered[COL_EMPRESA].str.contains(search_text, case=False, na=False) |
            df_filtered[COL_NOME].str.contains(search_text, case=False, na=False)
        ]

    st.caption(f"{len(df_filtered)} clients found")

    for index, row in df_filtered.iterrows():
        with st.container(border=True):
            col_top_a, col_top_b = st.columns([3, 1])
            status_val = str(row[COL_STATUS]) if pd.notna(row[COL_STATUS]) else "-"
            color = "gray"
            if "Ativo" in status_val: color = "red"
            elif "Morno" in status_val: color = "orange"
            elif "Frio" in status_val: color = "blue"
            elif "supplier" in status_val: color = "green"
            
            col_top_a.write(f"**{row[COL_EMPRESA]}**")
            col_top_b.markdown(f":{color}[**{status_val}**]")
            st.caption(f"Contact: {row[COL_NOME]} | Port: {row[COL_POD]}")
            
            if pd.notna(row[COL_PRODUTO]) and row[COL_PRODUTO]: st.code(f"{row[COL_PRODUTO]}", language="text")
            
            c_zap, c_mail = st.columns(2)
            tel = ''.join(filter(str.isdigit, str(row[COL_ZAP])))
            if tel: c_zap.link_button("WhatsApp", f"https://wa.me/{tel}", use_container_width=True)
            else: c_zap.button("No Number", disabled=True, use_container_width=True, key=f"no_zap_{index}")
            
            email_val = str(row[COL_EMAIL]) if pd.notna(row[COL_EMAIL]) else ""
            if "@" in email_val: c_mail.link_button("Email", f"mailto:{email_val.strip()}", use_container_width=True)
            else: c_mail.button("No Email", disabled=True, use_container_width=True, key=f"no_email_{index}")

            with st.expander("Edit Details"):
                with st.form(f"edit_form_{index}"):
                    edit_status = st.selectbox("Status", options=STATUS_OPTIONS, index=STATUS_OPTIONS.index(status_val) if status_val in STATUS_OPTIONS else 0)
                    edit_empresa = st.text_input("Company", value=row[COL_EMPRESA])
                    edit_nome = st.text_input("Contact Name", value=row[COL_NOME])
                    edit_email = st.text_input("Email", value=row[COL_EMAIL])
                    
                    current_prods_list = []
                    if pd.notna(row[COL_PRODUTO]) and row[COL_PRODUTO]:
                        current_prods_list = [p.strip() for p in str(row[COL_PRODUTO]).split("|")]
                    edit_prod_options = sorted(list(set(PRODUCTS_LIST + current_prods_list)))
                    edit_products = st.multiselect("Products", options=edit_prod_options, default=[p for p in current_prods_list if p in edit_prod_options])
                    
                    edit_pod = st.selectbox("POD", options=["Keep Current"] + all_pods, index=0)
                    edit_zap = st.text_input("WhatsApp", value=row[COL_ZAP])
                    
                    if st.form_submit_button("Update Client"):
                        try:
                            sheet = connect_gsheets()
                            row_num = index + 2
                            pod_save = row[COL_POD] if edit_pod == "Keep Current" else edit_pod
                            str_products_final = " | ".join(edit_products)
                            sheet.update_cell(row_num, 1, edit_status)
                            sheet.update_cell(row_num, 3, pod_save)
                            sheet.update_cell(row_num, 4, str_products_final)
                            sheet.update_cell(row_num, 5, edit_empresa)
                            sheet.update_cell(row_num, 6, edit_nome)
                            sheet.update_cell(row_num, 7, edit_email)
                            sheet.update_cell(row_num, 8, edit_zap)
                            st.success("Updated!"); st.cache_resource.clear()
                        except Exception as e: st.error(f"Error updating: {e}")

# --- ABA 2: NOVO CLIENTE (IA) ---
elif view_option == "New Client":
    st.write("Add a new client:")

    st.info("Tip: Take a photo of the business card to auto-fill details.")
    card_photo = st.camera_input("Take a photo")
    
    if 'ai_data' not in st.session_state:
        st.session_state.ai_data = {}
    
    if card_photo:
        bytes_data = card_photo.getvalue()
        if st.session_state.ai_data.get('last_photo_bytes') != bytes_data:
            with st.spinner("AI is reading the card..."):
                dados = ler_cartao_com_ia(card_photo)
                if dados:
                    st.session_state.ai_data = dados
                    st.session_state.ai_data['last_photo_bytes'] = bytes_data
                    st.success("Card read successfully!")
    
    ai_vals = st.session_state.ai_data
    
    with st.form("add_form", clear_on_submit=True):
        st.write("**Status:**")
        new_status = st.selectbox("Select Status:", options=STATUS_OPTIONS, index=2)
        
        st.divider()
        st.write("**POD / Location:**")
        current_pods_add = df[COL_POD].dropna().unique().tolist()
        options_pod_add = sorted(list(set(PODS_DEFAULT + current_pods_add)))
        final_options = ["Other (Type New)..."] + options_pod_add
        
        choice_pod = st.selectbox("Select Port:", options=final_options)
        pod_final = choice_pod
        if choice_pod == "Other (Type New)...":
            pod_typed = st.text_input("Type new Port/Country:")
            pod_final = pod_typed
        
        st.divider()
        st.write("**Products:**")
        cols = st.columns(3)
        selected_prods = []
        for i, p in enumerate(PRODUCTS_LIST):
            if cols[i % 3].checkbox(p): selected_prods.append(p)
        
        st.divider()
        # Campos preenchidos pela IA
        new_company = st.text_input("Company Name", value=ai_vals.get("empresa", ""))
        new_name = st.text_input("Contact Name", value=ai_vals.get("nome", ""))
        new_email = st.text_input("Email", value=ai_vals.get("email", ""))
        new_zap = st.text_input("WhatsApp", value=ai_vals.get("telefone", ""))
        
        if st.form_submit_button("Save to Sheet", type="primary"):
            str_prods = " | ".join(selected_prods)
            if not new_company: st.error("Company Name is required!")
            else:
                try:
                    new_row = [
                        new_status, "Satish", pod_final, str_prods, 
                        new_company, new_name, new_email, new_zap
                    ]
                    sheet = connect_gsheets()
                    sheet.append_row(new_row)
                    st.toast(f"Saved! {new_company} added.")
                    
                    st.session_state.ai_data = {}
                    st.cache_resource.clear() 
                except Exception as e: st.error(f"Error: {e}")
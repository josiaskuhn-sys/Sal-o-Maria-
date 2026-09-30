import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# --- BASE DE DADOS & LIXEIRA ---
def init_db():
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()

    # Tabela 1: Agendamentos por Horário
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            telefone TEXT,
            servico TEXT NOT NULL,
            data_atendimento DATE NOT NULL,
            horario TEXT NOT NULL,
            status TEXT DEFAULT 'Agendado',
            profissional TEXT DEFAULT 'Maria',
            valor REAL DEFAULT 0.0,
            forma_pagamento TEXT DEFAULT 'Pix',
            duracao_minutos INTEGER DEFAULT 60
        )
    """
    )

    c.execute("PRAGMA table_info(agendamentos)")
    colunas_atuais = [col[1] for col in c.fetchall()]
    if "valor" not in colunas_atuais:
        c.execute("ALTER TABLE agendamentos ADD COLUMN valor REAL DEFAULT 0.0")
    if "forma_pagamento" not in colunas_atuais:
        c.execute("ALTER TABLE agendamentos ADD COLUMN forma_pagamento TEXT DEFAULT 'Pix'")
    if "duracao_minutos" not in colunas_atuais:
        c.execute("ALTER TABLE agendamentos ADD COLUMN duracao_minutos INTEGER DEFAULT 60")
    if "profissional" not in colunas_atuais:
        c.execute("ALTER TABLE agendamentos ADD COLUMN profissional TEXT DEFAULT 'Maria'")

    # Tabela 2: Clientes e Ciclos (CRM)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes_retencao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            ciclo_dias INTEGER NOT NULL,
            ultimo_atendimento DATE NOT NULL,
            profissional TEXT DEFAULT 'Maria',
            valor REAL DEFAULT 50.0,
            forma_pagamento TEXT DEFAULT 'Pix'
        )
    """
    )

    c.execute("PRAGMA table_info(clientes_retencao)")
    colunas_crm = [col[1] for col in c.fetchall()]
    if "profissional" not in colunas_crm:
        c.execute("ALTER TABLE clientes_retencao ADD COLUMN profissional TEXT DEFAULT 'Maria'")
    if "valor" not in colunas_crm:
        c.execute("ALTER TABLE clientes_retencao ADD COLUMN valor REAL DEFAULT 50.0")
    if "forma_pagamento" not in colunas_crm:
        c.execute("ALTER TABLE clientes_retencao ADD COLUMN forma_pagamento TEXT DEFAULT 'Pix'")

    # Tabela 3: Contatos Salvos (Independente)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            profissional TEXT DEFAULT 'Maria'
        )
    """
    )

    # Tabela 4: Minhas Tarefas / Anotações
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            prioridade TEXT DEFAULT 'Média',
            data_criacao DATE NOT NULL,
            concluido INTEGER DEFAULT 0
        )
    """
    )

    # Tabela 5: Lixeira Inteligente
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS lixeira (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_item TEXT NOT NULL,
            dados_item TEXT NOT NULL,
            data_exclusao DATE NOT NULL
        )
    """
    )

    # Tabela 6: Configurações Gerais do Studio
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """
    )

    # Tabela 7: Perfis, Senhas, Serviços e WhatsApp
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS perfis (
            nome TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            servicos TEXT NOT NULL,
            whatsapp TEXT
        )
    """
    )

    c.execute("PRAGMA table_info(perfis)")
    colunas_perfis = [col[1] for col in c.fetchall()]
    if "whatsapp" not in colunas_perfis:
        c.execute("ALTER TABLE perfis ADD COLUMN whatsapp TEXT DEFAULT ''")

    def upsert_config(cursor, chave, valor):
        cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, valor))

    upsert_config(c, 'titulo_studio', 'Studio Maria Rossatto')
    upsert_config(c, 'subtitulo_studio', 'Sistema de Gestão & Retenção')
    upsert_config(c, 'tema_estilo', 'Dourado Luxo')

    servicos_maria_default = "Mão tradicional\nPé tradicional\nBlindagem\nEsmaltação em gel\nBanho de gel\nAlongamento\nManutenção\nPacote de mão"
    servicos_camily_default = "Design de Sobrancelha\nSobrancelha com Henna\nExtensão de Cílios Fio a Fio\nVolume Russo\nLash Lifting\nManutenção de Cílios"

    def upsert_perfil(cursor, nome, senha, servicos, whatsapp):
        cursor.execute("SELECT senha FROM perfis WHERE nome = ?", (nome,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO perfis (nome, senha, servicos, whatsapp) VALUES (?, ?, ?, ?)", (nome, senha, servicos, whatsapp))

    upsert_perfil(c, 'Maria', 'maria123', servicos_maria_default, '5554992508467')
    upsert_perfil(c, 'Camily', 'camily123', servicos_camily_default, '5554992406892')

    c.execute("UPDATE perfis SET whatsapp = '5554992508467' WHERE nome = 'Maria' AND (whatsapp IS NULL OR whatsapp = '')")
    c.execute("UPDATE perfis SET whatsapp = '5554992406892' WHERE nome = 'Camily' AND (whatsapp IS NULL OR whatsapp = '')")

    limite_30_dias = str(date.today() - timedelta(days=30))
    c.execute("DELETE FROM lixeira WHERE data_exclusao < ?", (limite_30_dias,))

    conn.commit()
    conn.close()


init_db()

# --- FUNÇÕES DE BUSCA ---
def get_config(chave):
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def get_perfil_info(nome_prof):
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()
    c.execute("SELECT senha, servicos, whatsapp FROM perfis WHERE nome = ?", (nome_prof,))
    row = c.fetchone()
    conn.close()
    return row if row else ("", "", "")

# Configuração da página
st.set_page_config(
    page_title=get_config("titulo_studio"),
    layout="wide",
    page_icon="💅",
)

# --- APLICAÇÃO DINÂMICA DE TEMAS ---
tema_atual = get_config("tema_estilo")

estilos_css = {
    "Dourado Luxo": """
        <style>
            .stApp { background-color: #FDFBF7 !important; color: #1F1E1B !important; -webkit-font-smoothing: antialiased; }
            .stSidebar { background-color: #F4EFEA !important; border-right: 1px solid #D6CEC2; color: #1F1E1B !important; }
            .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar div { color: #1F1E1B !important; }
            div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #D6CEC2 !important; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            div[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D6CEC2 !important; border-radius: 10px; }
            .stButton>button { background-color: #C5A059 !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; width: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            div[data-testid="stMetricValue"] { color: #9A752A !important; font-weight: 700 !important; }
            .stTabs [data-baseweb="tab-list"] button p { font-size: 0.95rem !important; font-weight: 700 !important; color: #1F1E1B !important; }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #C5A059 !important; }
            input, textarea, select, input[type="text"], input[type="date"], input[type="time"], input[type="number"], input[type="password"] {
                background-color: #FFFFFF !important; color: #1F1E1B !important; -webkit-text-fill-color: #1F1E1B !important; border: 1px solid #D6CEC2 !important; border-radius: 6px !important;
            }
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; border-color: #D6CEC2 !important; color: #1F1E1B !important; }
            label, .stRadio label, .stSelectbox label, .stDateInput label, .stTimeInput label { color: #2C2A26 !important; font-weight: 600 !important; }
            .fc, .fc-theme-standard, .fc-view, .fc-scrollgrid, .fc-daygrid-body, .fc-timegrid { background-color: #FFFFFF !important; color: #1F1E1B !important; border-color: #E2DBD2 !important; }
            .fc-daygrid-day, .fc-timegrid-slot, .fc-col-header-cell { background-color: #FFFFFF !important; color: #1F1E1B !important; }
            .fc-daygrid-day-number { color: #1F1E1B !important; font-weight: 700 !important; font-size: 0.9rem !important; }
            .fc-col-header-cell-cushion { color: #5C544B !important; font-weight: 700 !important; }
            .fc-day-today { background-color: #F9F3EA !important; }
            .fc-event { background-color: #FDFBF7 !important; border: 1px solid #D6CEC2 !important; border-left: 3px solid #C5A059 !important; border-radius: 4px !important; padding: 3px 6px !important; }
            .fc-event-title { color: #1F1E1B !important; font-weight: 700 !important; font-size: 0.75rem !important; }
        </style>
    """,
    "Clean White (Tudo Branco)": """
        <style>
            .stApp { background-color: #FFFFFF !important; color: #111111 !important; -webkit-font-smoothing: antialiased; }
            .stSidebar { background-color: #FAFAFA !important; border-right: 1px solid #E5E5E5; color: #111111 !important; }
            .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar div { color: #111111 !important; }
            div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; }
            div[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #D1D5DB !important; }
            .stButton>button { background-color: #111827 !important; color: white !important; border-radius: 8px !important; border: none !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 700 !important; }
            .stTabs [data-baseweb="tab-list"] button p { font-size: 0.95rem !important; font-weight: 700 !important; color: #111111 !important; }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #111827 !important; }
            input, textarea, select, input[type="text"], input[type="date"], input[type="time"], input[type="number"], input[type="password"] {
                background-color: #FFFFFF !important; color: #111111 !important; -webkit-text-fill-color: #111111 !important; border: 1px solid #D1D5DB !important; border-radius: 6px !important;
            }
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; border-color: #D1D5DB !important; color: #111111 !important; }
            label, .stRadio label, .stSelectbox label, .stDateInput label, .stTimeInput label { color: #111111 !important; font-weight: 600 !important; }
            .fc, .fc-theme-standard, .fc-view, .fc-scrollgrid, .fc-daygrid-body, .fc-timegrid { background-color: #FFFFFF !important; color: #111111 !important; border-color: #D1D5DB !important; }
            .fc-daygrid-day, .fc-timegrid-slot, .fc-col-header-cell { background-color: #FFFFFF !important; color: #111111 !important; }
            .fc-daygrid-day-number { color: #111827 !important; font-weight: 700 !important; font-size: 0.9rem !important; }
            .fc-col-header-cell-cushion { color: #374151 !important; font-weight: 700 !important; }
            .fc-day-today { background-color: #F3F4F6 !important; }
            .fc-event { background-color: #F9FAFB !important; border: 1px solid #D1D5DB !important; border-left: 3px solid #111827 !important; border-radius: 4px !important; padding: 3px 6px !important; }
            .fc-event-title { color: #111827 !important; font-weight: 700 !important; font-size: 0.75rem !important; }
        </style>
    """,
    "Nude / Rosé": """
        <style>
            .stApp { background-color: #FFF9F9 !important; color: #3D2E2E !important; -webkit-font-smoothing: antialiased; }
            .stSidebar { background-color: #FFF0F2 !important; color: #3D2E2E !important; }
            .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar div { color: #3D2E2E !important; }
            .stButton>button { background-color: #D68D8D !important; color: white !important; border-radius: 8px !important; border: none !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #B85C5C !important; font-weight: 700 !important; }
            .stTabs [data-baseweb="tab-list"] button p { font-size: 0.95rem !important; font-weight: 700 !important; color: #3D2E2E !important; }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #B85C5C !important; }
            input, textarea, select, input[type="text"], input[type="date"], input[type="time"], input[type="number"], input[type="password"] {
                background-color: #FFFFFF !important; color: #3D2E2E !important; -webkit-text-fill-color: #3D2E2E !important; border: 1px solid #E5C4C4 !important; border-radius: 6px !important;
            }
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; border-color: #E5C4C4 !important; color: #3D2E2E !important; }
            label, .stRadio label, .stSelectbox label, .stDateInput label, .stTimeInput label { color: #3D2E2E !important; font-weight: 600 !important; }
            .fc, .fc-theme-standard, .fc-view, .fc-scrollgrid, .fc-daygrid-body, .fc-timegrid { background-color: #FFFFFF !important; color: #3D2E2E !important; border-color: #E5C4C4 !important; }
            .fc-daygrid-day, .fc-timegrid-slot, .fc-col-header-cell { background-color: #FFFFFF !important; color: #3D2E2E !important; }
            .fc-daygrid-day-number { color: #3D2E2E !important; font-weight: 700 !important; font-size: 0.9rem !important; }
            .fc-col-header-cell-cushion { color: #5C4444 !important; font-weight: 700 !important; }
            .fc-day-today { background-color: #FDF0F0 !important; }
            .fc-event { background-color: #FFFFFF !important; border: 1px solid #E5C4C4 !important; border-left: 3px solid #D68D8D !important; border-radius: 4px !important; padding: 3px 6px !important; }
            .fc-event-title { color: #3D2E2E !important; font-weight: 700 !important; font-size: 0.75rem !important; }
        </style>
    """,
    "Dark Elegance": """
        <style>
            .stApp { background-color: #1E1E1E !important; color: #F3F4F6 !important; -webkit-font-smoothing: antialiased; }
            .stSidebar { background-color: #2D2D2D !important; border-right: 1px solid #3D3D3D; color: #F3F4F6 !important; }
            .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar div { color: #F3F4F6 !important; }
            div[data-testid="stForm"] { background-color: #2D2D2D !important; border: 1px solid #3D3D3D !important; border-radius: 10px; }
            div[data-testid="stExpander"] { background-color: #2D2D2D !important; border: 1px solid #3D3D3D !important; border-radius: 10px; }
            .stButton>button { background-color: #BB86FC !important; color: #121212 !important; border-radius: 8px !important; font-weight: bold !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #BB86FC !important; font-weight: 700 !important; }
            .stTabs [data-baseweb="tab-list"] button p { font-size: 0.95rem !important; font-weight: 700 !important; color: #F3F4F6 !important; }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #BB86FC !important; }
            input, textarea, select, input[type="text"], input[type="date"], input[type="time"], input[type="number"], input[type="password"] {
                background-color: #FFFFFF !important; color: #1F1E1B !important; -webkit-text-fill-color: #1F1E1B !important; border: 1px solid #4B5563 !important; border-radius: 6px !important;
            }
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; border-color: #4B5563 !important; color: #1F1E1B !important; }
            label, .stRadio label, .stSelectbox label, .stDateInput label, .stTimeInput label { color: #F3F4F6 !important; font-weight: 600 !important; }
            .fc, .fc-theme-standard, .fc-view, .fc-scrollgrid, .fc-daygrid-body, .fc-timegrid { background-color: #FFFFFF !important; color: #1F1E1B !important; border-color: #4B5563 !important; }
            .fc-daygrid-day, .fc-timegrid-slot, .fc-col-header-cell { background-color: #FFFFFF !important; color: #1F1E1B !important; }
            .fc-daygrid-day-number { color: #1F1E1B !important; font-weight: 700 !important; font-size: 0.9rem !important; }
            .fc-col-header-cell-cushion { color: #374151 !important; font-weight: 700 !important; }
            .fc-day-today { background-color: #F3E8FF !important; }
            .fc-event { background-color: #F9FAFB !important; border: 1px solid #4B5563 !important; border-left: 3px solid #BB86FC !important; border-radius: 4px !important; padding: 3px 6px !important; }
            .fc-event-title { color: #1F1E1B !important; font-weight: 700 !important; font-size: 0.75rem !important; }
        </style>
    """,
    "Lavanda / Soft Purple": """
        <style>
            .stApp { background-color: #F8F7FF !important; color: #2D263B !important; -webkit-font-smoothing: antialiased; }
            .stSidebar { background-color: #EDE9FE !important; border-right: 1px solid #DDD6FE; color: #2D263B !important; }
            .stSidebar p, .stSidebar span, .stSidebar label, .stSidebar div { color: #2D263B !important; }
            div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #DDD6FE !important; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            div[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #DDD6FE !important; border-radius: 10px; }
            .stButton>button { background-color: #8B5CF6 !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; width: 100%; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            div[data-testid="stMetricValue"] { color: #7C3AED !important; font-weight: 700 !important; }
            .stTabs [data-baseweb="tab-list"] button p { font-size: 0.95rem !important; font-weight: 700 !important; color: #2D263B !important; }
            .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] p { color: #7C3AED !important; }
            input, textarea, select, input[type="text"], input[type="date"], input[type="time"], input[type="number"], input[type="password"] {
                background-color: #FFFFFF !important; color: #2D263B !important; -webkit-text-fill-color: #2D263B !important; border: 1px solid #DDD6FE !important; border-radius: 6px !important;
            }
            div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="base-input"] { background-color: #FFFFFF !important; border-color: #DDD6FE !important; color: #2D263B !important; }
            label, .stRadio label, .stSelectbox label, .stDateInput label, .stTimeInput label { color: #3A354A !important; font-weight: 600 !important; }
            .fc, .fc-theme-standard, .fc-view, .fc-scrollgrid, .fc-daygrid-body, .fc-timegrid { background-color: #FFFFFF !important; color: #2D263B !important; border-color: #DDD6FE !important; }
            .fc-daygrid-day, .fc-timegrid-slot, .fc-col-header-cell { background-color: #FFFFFF !important; color: #2D263B !important; }
            .fc-daygrid-day-number { color: #2D263B !important; font-weight: 700 !important; font-size: 0.9rem !important; }
            .fc-col-header-cell-cushion { color: #5B4E77 !important; font-weight: 700 !important; }
            .fc-day-today { background-color: #F3E8FF !important; }
            .fc-event { background-color: #F8F7FF !important; border: 1px solid #DDD6FE !important; border-left: 3px solid #8B5CF6 !important; border-radius: 4px !important; padding: 3px 6px !important; }
            .fc-event-title { color: #2D263B !important; font-weight: 700 !important; font-size: 0.75rem !important; }
        </style>
    """
}

st.markdown(estilos_css.get(tema_atual, estilos_css["Dourado Luxo"]), unsafe_allow_html=True)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# --- CONTROLO DE SESSÃO / LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario = ""
    st.session_state.perfil = ""

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.container(border=True):
            try:
                st.image("logo.JPG", use_container_width=True)
            except:
                st.title("💅 Studio")

            st.subheader("🔒 Acesso Restrito")
            st.write("Selecione a sua conta e introduza a palavra-passe:")

            with st.form("form_login"):
                escolha_usuario = st.selectbox("Profissional:", ["Maria", "Camily"])
                senha_input = st.text_input("Palavra-passe:", type="password")
                btn_entrar = st.form_submit_button("Entrar no Sistema")

                if btn_entrar:
                    senha_db, _, _ = get_perfil_info(escolha_usuario)
                    if senha_input == senha_db:
                        st.session_state.autenticado = True
                        st.session_state.usuario = escolha_usuario
                        st.session_state.perfil = f"{'Unhas (Maria)' if escolha_usuario == 'Maria' else 'Sobrancelhas & Cílios (Camily)'}"
                        st.rerun()
                    else:
                        st.error("Palavra-passe incorreta!")
        st.stop()

usuario_atual = st.session_state.usuario
perfil_atual = st.session_state.perfil

_, servicos_str_db, whatsapp_prof_db = get_perfil_info(usuario_atual)
servicos_disponiveis = [s.strip() for s in servicos_str_db.split("\n") if s.strip()]

# Buscar contatos salvos para autocomplete
conn_ct = sqlite3.connect("agenda_unhas_v2.db")
df_contatos_db = pd.read_sql_query("SELECT nome, telefone FROM contatos WHERE profissional = ?", conn_ct, params=(usuario_atual,))
conn_ct.close()
lista_contatos_nomes = df_contatos_db["nome"].tolist() if not df_contatos_db.empty else []

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        st.image("logo.JPG", use_container_width=True)
    except:
        pass
    st.success(f"Com sessão iniciada como:\n**{perfil_atual}**")
    
    if st.button("🚪 Sair (Mudar de Utilizador)"):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.session_state.perfil = ""
        st.rerun()

    st.divider()

    tipo_cadastro = st.radio(
        "Ações Rápidas:",
        [
            "📅 Novo Agendamento (Horário)",
            "👤 Cadastrar Cliente (CRM)",
            "📝 Nova Tarefa / Anotação",
        ],
    )

    st.divider()

    if tipo_cadastro == "📅 Novo Agendamento (Horário)":
        st.header(f"➕ Agendar ({usuario_atual})")

        modo_cli = st.radio("Origem da Cliente:", ["Cliente Existente", "Novo Contato"], horizontal=True, key="modo_cli_agenda_radio")

        with st.form("form_rapido", clear_on_submit=True):
            if modo_cli == "Cliente Existente":
                if lista_contatos_nomes:
                    nome_cliente = st.selectbox("Selecione a Cliente", lista_contatos_nomes, key="sel_cliente_existente_form")
                    match_tel = df_contatos_db[df_contatos_db["nome"] == nome_cliente]["telefone"].values
                    tel_sugestao = match_tel[0] if len(match_tel) > 0 and match_tel[0] else ""
                else:
                    st.warning("Nenhum contato salvo. Selecione 'Novo Contato'.")
                    nome_cliente = ""
                    tel_sugestao = ""
                telefone = st.text_input("WhatsApp", value=tel_sugestao, placeholder="54991341375", key="tel_existente_form")
            else:
                nome_cliente = st.text_input("Nome da Nova Cliente*", key="input_novo_nome_form")
                telefone = st.text_input("WhatsApp do Novo Contato", placeholder="54991341375", key="tel_novo_form")

            servico = st.selectbox("Serviço*", servicos_disponiveis, key="servico_agendamento_form")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                valor_servico = st.number_input("Valor (R$)*", min_value=0.0, value=50.0, step=5.0, key="valor_agendamento_form")
            with col_v2:
                duracao_servico = st.number_input("Duração (minutos)*", min_value=5, max_value=480, value=60, step=5, key="duracao_agendamento_form")

            forma_pagto = st.selectbox("Forma de Pagamento*", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], key="pagto_agendamento_form")
            
            data_atendimento = st.date_input("Data*", value=date.today(), format="DD/MM/YYYY", key="data_agendamento_form")
            horario = st.time_input("Horário*", value=datetime.strptime("14:00", "%H:%M").time(), key="horario_agendamento_form")

            salvar = st.form_submit_button("Guardar Horário")

            if salvar:
                tel_clean = "".join(filter(str.isdigit, str(telefone))) if telefone else "Não informado"
                if not nome_cliente:
                    st.error("Preencha o nome da cliente!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    
                    c.execute(
                        """INSERT INTO agendamentos (nome_cliente, telefone, servico, data_atendimento, horario, profissional, valor, forma_pagamento, duracao_minutos) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nome_cliente,
                            telefone,
                            servico,
                            str(data_atendimento),
                            str(horario)[:5],
                            usuario_atual,
                            valor_servico,
                            forma_pagto,
                            int(duracao_servico),
                        ),
                    )

                    c.execute("SELECT id FROM contatos WHERE nome = ? AND profissional = ?", (nome_cliente, usuario_atual))
                    if not c.fetchone():
                        c.execute("INSERT INTO contatos (nome, telefone, profissional) VALUES (?, ?, ?)", (nome_cliente, telefone, usuario_atual))
                    else:
                        if telefone:
                            c.execute("UPDATE contatos SET telefone = ? WHERE nome = ? AND profissional = ?", (telefone, nome_cliente, usuario_atual))

                    c.execute("SELECT id FROM clientes_retencao WHERE nome = ? AND profissional = ?", (nome_cliente, usuario_atual))
                    existente_crm = c.fetchone()
                    data_iso = data_atendimento.strftime("%Y-%m-%d")
                    if existente_crm:
                        c.execute("UPDATE clientes_retencao SET ultimo_atendimento = ?, telefone = ?, valor = ?, forma_pagamento = ? WHERE id = ?", (data_iso, tel_clean, valor_servico, forma_pagto, existente_crm[0]))
                    else:
                        c.execute("INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento, profissional, valor, forma_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (nome_cliente, tel_clean, 21, data_iso, usuario_atual, valor_servico, forma_pagamento))

                    conn.commit()
                    conn.close()
                    st.success("Horário marcado e contato guardado com sucesso!")
                    st.rerun()

    elif tipo_cadastro == "👤 Cadastrar Cliente (CRM)":
        st.header(f"➕ CRM ({usuario_atual})")
        with st.form("form_cliente_crm", clear_on_submit=True):
            nome = st.text_input("Nome da Cliente*", key="crm_nome_input")
            telefone = st.text_input("WhatsApp*", placeholder="54991341375", key="crm_tel_input")
            
            ciclo_opcao_crm = st.selectbox("Ciclo de Retorno (Dias)*", [15, 21, 25, 30, "Outro (Personalizado)"], index=1, key="sidebar_crm_ciclo_op")
            if ciclo_opcao_crm == "Outro (Personalizado)":
                ciclo_dias_crm = st.number_input("Digite a quantidade de dias:", min_value=1, max_value=365, value=10, step=1, key="sidebar_crm_ciclo_dig")
            else:
                ciclo_dias_crm = int(ciclo_opcao_crm)

            col_vc1, col_vc2 = st.columns(2)
            with col_vc1:
                val_crm_cad = st.number_input("Valor Padrão (R$)*", min_value=0.0, value=50.0, step=5.0, key="crm_val_input")
            with col_vc2:
                pag_crm_cad = st.selectbox("Pagamento Padrão*", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], key="crm_pag_input")

            ultimo_atendimento = st.date_input("Último Atendimento*", value=date.today(), format="DD/MM/YYYY", key="crm_data_input")

            salvar_crm = st.form_submit_button("Guardar no CRM")

            if salvar_crm:
                tel_clean = "".join(filter(str.isdigit, str(telefone))) if telefone else "Não informado"
                if not nome:
                    st.error("Preencha o Nome da cliente!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    data_iso = ultimo_atendimento.strftime("%Y-%m-%d")
                    
                    c.execute("SELECT id FROM contatos WHERE nome = ? AND profissional = ?", (nome, usuario_atual))
                    if not c.fetchone():
                        c.execute("INSERT INTO contatos (nome, telefone, profissional) VALUES (?, ?, ?)", (nome, telefone, usuario_atual))

                    c.execute("SELECT id FROM clientes_retencao WHERE nome = ? AND profissional = ?", (nome, usuario_atual))
                    existente = c.fetchone()

                    if existente:
                        c.execute("UPDATE clientes_retencao SET ciclo_dias = ?, ultimo_atendimento = ?, telefone = ?, valor = ?, forma_pagamento = ? WHERE id = ?", (ciclo_dias_crm, data_iso, tel_clean, val_crm_cad, pag_crm_cad, existente[0]))
                        st.success(f"Cadastro de {nome} atualizado!")
                    else:
                        c.execute("INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento, profissional, valor, forma_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)", (nome, tel_clean, ciclo_dias_crm, data_iso, usuario_atual, val_crm_cad, pag_crm_cad))
                        st.success(f"Cliente {nome} salva!")
                    conn.commit()
                    conn.close()
                    st.rerun()

    else:
        st.header("➕ Nova Anotação")
        with st.form("form_tarefa", clear_on_submit=True):
            titulo_t = st.text_input("Título / Lembrete*", key="tarefa_titulo_input")
            desc_t = st.text_area("Detalhes", placeholder="Ex: Comprar material", key="tarefa_desc_input")
            prio_t = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1, key="tarefa_prio_input")
            salvar_t = st.form_submit_button("Guardar Tarefa")

            if salvar_t:
                if not titulo_t:
                    st.error("Preencha o título!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO tarefas (titulo, descricao, prioridade, data_criacao) VALUES (?, ?, ?, ?)", (titulo_t, desc_t, prio_t, str(date.today())))
                    conn.commit()
                    conn.close()
                    st.success("Tarefa salva!")
                    st.rerun()

# --- PAINEL PRINCIPAL ---
titulo_atual = get_config("titulo_studio")
subtitulo_atual = get_config("subtitulo_studio")

emoji_perfil = "💅" if usuario_atual == "Maria" else "👁️✨"
st.title(f"{emoji_perfil} {titulo_atual} — Painel da {usuario_atual}")

# --- CENTRAL DE ALERTAS (HOJE + RESTO DA SEMANA CRM) ---
conn = sqlite3.connect("agenda_unhas_v2.db")
hoje_str = date.today().isoformat()

df_agenda_hoje = pd.read_sql_query(
    "SELECT horario, nome_cliente, servico, valor FROM agendamentos WHERE data_atendimento = ? AND profissional = ? ORDER BY horario ASC", 
    conn, params=(hoje_str, usuario_atual)
)

df_crm_tudo = pd.read_sql_query("SELECT id, nome, telefone, ultimo_atendimento, ciclo_dias FROM clientes_retencao WHERE profissional = ?", conn, params=(usuario_atual,))
conn.close()

hoje_dt = date.today()
inicio_semana = hoje_dt - timedelta(days=hoje_dt.weekday())
fim_semana = inicio_semana + timedelta(days=6)
amanha_dt = hoje_dt + timedelta(days=1)

if not df_crm_tudo.empty:
    df_crm_tudo["ultimo_atendimento"] = pd.to_datetime(df_crm_tudo["ultimo_atendimento"], errors="coerce").dt.date
    df_crm_tudo["proximo_atendimento"] = df_crm_tudo.apply(lambda r: r["ultimo_atendimento"] + timedelta(days=int(r["ciclo_dias"])), axis=1)
    df_crm_tudo["dias_atraso"] = df_crm_tudo["proximo_atendimento"].apply(lambda d: (hoje_dt - d).days)
    chamar_semana_topo = df_crm_tudo[(df_crm_tudo["proximo_atendimento"] >= amanha_dt) & (df_crm_tudo["proximo_atendimento"] <= fim_semana)].sort_values(by="proximo_atendimento")
else:
    chamar_semana_topo = pd.DataFrame()

ultimo_dia_mes = (hoje_dt.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
aviso_fim_mes = ""
if hoje_dt.day >= ultimo_dia_mes.day - 3:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_mes_atual = pd.read_sql_query("SELECT valor FROM agendamentos WHERE profissional = ? AND data_atendimento LIKE ?", conn, params=(usuario_atual, f"{hoje_dt.strftime('%Y-%m')}%"))
    conn.close()
    faturamento_mes_atual = df_mes_atual["valor"].sum() if not df_mes_atual.empty else 0.0
    aviso_fim_mes = f"🎉 **Fechamento de Mês:** O mês está a acabar! O seu faturamento total até agora é de **R$ {faturamento_mes_atual:.2f}**. Parabéns!"

if not df_agenda_hoje.empty or not chamar_semana_topo.empty or aviso_fim_mes:
    with st.expander("🔔 Central de Notificações Internas", expanded=True):
        if aviso_fim_mes:
            st.success(aviso_fim_mes)
        col_al1, col_al2 = st.columns(2)
        with col_al1:
            if not df_agenda_hoje.empty:
                st.warning(f"📅 **Hoje ({len(df_agenda_hoje)}):**")
                for _, row in df_agenda_hoje.iterrows():
                    st.markdown(f"- ⏰ **{row['horario']}** — {row['nome_cliente']} *({row['servico']})*")
            else:
                st.info("📅 Sem agendamentos para hoje.")
        with col_al2:
            if not chamar_semana_topo.empty:
                st.info(f"📲 **Próximos Dias da Semana ({len(chamar_semana_topo)}):**")
                for _, row in chamar_semana_topo.iterrows():
                    dt_prox_fmt = row["proximo_atendimento"].strftime('%d/%m')
                    dias_sem_pt = {0: "Seg", 1: "Ter", 2: "Qua", 3: "Qui", 4: "Sex", 5: "Sáb", 6: "Dom"}
                    dia_nome = dias_sem_pt.get(row["proximo_atendimento"].weekday(), "")
                    st.markdown(f"- 👤 **{row['nome']}** *(Retorno: {dia_nome}, {dt_prox_fmt})*")
            else:
                st.info("📅 Nenhuma cliente para chamar nos próximos dias desta semana.")
else:
    st.success("✅ Tudo em dia! Sem pendências para hoje ou próximos dias.")

st.divider()

aba_agenda, aba_crm, aba_fin, aba_contatos, aba_tarefas, aba_lixeira, aba_config = st.tabs(
    [
        "📅 Agenda",
        "🎯 CRM",
        "📊 Financeiro & Ganhos",
        "📇 Contatos",
        "📝 Tarefas",
        "🗑️ Lixeira",
        "⚙ Configurações",
    ]
)

# ==========================================
# ABA 1: AGENDA DE HORÁRIOS
# ==========================================
with aba_agenda:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_todos = pd.read_sql_query("SELECT * FROM agendamentos WHERE profissional = ? ORDER BY data_atendimento ASC, horario ASC", conn, params=(usuario_atual,))
    conn.close()

    eventos_calendario = []
    for _, row in df_todos.iterrows():
        eventos_calendario.append(
            {
                "title": f"{row['horario']} - {row['nome_cliente']} ({row['servico']})",
                "start": row['data_atendimento'],
                "allDay": True,
                "backgroundColor": "#FFFFFF",
                "borderColor": "#D6CEC2",
                "textColor": "#1F1E1B"
            }
        )

    if "cal_data_base" not in st.session_state:
        st.session_state.cal_data_base = date.today().replace(day=1)
    if "cal_view_mode" not in st.session_state:
        st.session_state.cal_view_mode = "dayGridMonth"

    st.markdown(f"### 📅 Visão Geral de Atendimentos — {usuario_atual}")

    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns([1, 2.2, 1, 1])
    with col_nav1:
        if st.button("◀ Mês", use_container_width=True, key=f"ant_{usuario_atual}"):
            mes_ant = st.session_state.cal_data_base.month - 1
            ano_ant = st.session_state.cal_data_base.year
            if mes_ant == 0:
                mes_ant = 12
                ano_ant -= 1
            st.session_state.cal_data_base = date(ano_ant, mes_ant, 1)
            st.rerun()

    with col_nav2:
        meses_pt = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
        nome_mes = meses_pt.get(st.session_state.cal_data_base.month, "")
        ano_corrente = st.session_state.cal_data_base.year
        st.markdown(f"<div style='text-align:center; font-weight:700; font-size:1.0rem; padding-top:6px;'>{nome_mes} de {ano_corrente}</div>", unsafe_allow_html=True)

    with col_nav3:
        if st.button("Mês ▶", use_container_width=True, key=f"prox_{usuario_atual}"):
            mes_prox = st.session_state.cal_data_base.month + 1
            ano_prox = st.session_state.cal_data_base.year
            if mes_prox == 13:
                mes_prox = 1
                ano_prox += 1
            st.session_state.cal_data_base = date(ano_prox, mes_prox, 1)
            st.rerun()

    with col_nav4:
        if st.button("Hoje", use_container_width=True, key=f"hoje_{usuario_atual}"):
            st.session_state.cal_data_base = date.today().replace(day=1)
            st.rerun()

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if st.button("📅 Visão Mês", use_container_width=True, type="primary" if st.session_state.cal_view_mode == "dayGridMonth" else "secondary", key=f"vm_{usuario_atual}"):
            st.session_state.cal_view_mode = "dayGridMonth"
            st.rerun()
    with col_v2:
        if st.button("📋 Visão Lista", use_container_width=True, type="primary" if st.session_state.cal_view_mode == "listMonth" else "secondary", key=f"vl_{usuario_atual}"):
            st.session_state.cal_view_mode = "listMonth"
            st.rerun()

    opcoes_calendario = {
        "headerToolbar": False,
        "initialView": st.session_state.cal_view_mode,
        "initialDate": st.session_state.cal_data_base.strftime("%Y-%m-%d"),
        "selectable": True,
        "locale": "pt-br",
    }

    state = calendar(
        events=eventos_calendario, 
        options=opcoes_calendario, 
        key=f"cal_studio_{usuario_atual}_{st.session_state.cal_view_mode}_{st.session_state.cal_data_base}"
    )

    st.divider()
    st.markdown("### 📋 Filtro e Consulta de Atendimentos")

    modo_filtro_data = st.radio(
        "Como deseja visualizar os agendamentos abaixo?",
        ["📆 Apenas um Dia", "📅 Por Período (Intervalo de Datas)"],
        horizontal=True,
        key=f"modo_filtro_{usuario_atual}"
    )

    conn = sqlite3.connect("agenda_unhas_v2.db")
    if modo_filtro_data == "📆 Apenas um Dia":
        data_selecionada = st.date_input("📆 Selecione o dia:", value=date.today(), format="DD/MM/YYYY", key=f"date_agenda_{usuario_atual}")
        df = pd.read_sql_query("SELECT * FROM agendamentos WHERE data_atendimento = ? AND profissional = ? ORDER BY horario ASC", conn, params=(str(data_selecionada), usuario_atual))
        conn.close()
        st.markdown(f"### 📋 Horários de **{data_selecionada.strftime('%d/%m/%Y')}** ({len(df)} encontrados)")
    else:
        col_df1, col_df2 = st.columns(2)
        with col_df1:
            data_inicio = st.date_input("Data Inicial:", value=date.today().replace(day=1), format="DD/MM/YYYY", key=f"data_ini_{usuario_atual}")
        with col_df2:
            data_fim = st.date_input("Data Final:", value=date.today(), format="DD/MM/YYYY", key=f"data_fim_{usuario_atual}")
        
        df = pd.read_sql_query("SELECT * FROM agendamentos WHERE data_atendimento >= ? AND data_atendimento <= ? AND profissional = ? ORDER BY data_atendimento ASC, horario ASC", 
                               conn, params=(str(data_inicio), str(data_fim), usuario_atual))
        conn.close()
        st.markdown(f"### 📋 Horários de **{data_inicio.strftime('%d/%m/%Y')}** até **{data_fim.strftime('%d/%m/%Y')}** ({len(df)} encontrados)")

    if not df.empty:
        emoji_msg = "💅" if usuario_atual == "Maria" else "👁️✨"
        texto_resumo = f"{emoji_msg} *Resumo de Atendimentos ({usuario_atual}):*\n\n"
        for _, row in df.iterrows():
            dt_r_fmt = datetime.strptime(str(row['data_atendimento']), "%Y-%m-%d").strftime('%d/%m')
            texto_resumo += f"📅 *{dt_r_fmt}* às *{row['horario']}* — {row['nome_cliente']} ({row['servico']}) | R$ {row['valor']:.2f}\n"

        if whatsapp_prof_db:
            link_resumo = f"https://wa.me/{whatsapp_prof_db}?text={texto_resumo.replace(' ', '%20').replace('\n', '%0A')}"
            st.markdown(
                f"""
                <a href="{link_resumo}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-bottom: 20px;">
                        📲 Enviar Lista Filtrada no Meu WhatsApp
                    </button>
                </a>
            """,
                unsafe_allow_html=True,
            )

        cols = st.columns(2)
        for idx, row in df.iterrows():
            col_atual = cols[idx % 2]
            with col_atual:
                with st.container(border=True):
                    dt_card_fmt = datetime.strptime(str(row['data_atendimento']), "%Y-%m-%d").strftime('%d/%m/%Y')
                    st.subheader(f"📅 {dt_card_fmt} - ⏰ {row['horario']} — {row['nome_cliente']}")
                    st.write(f"**Serviço:** {row['servico']}")
                    st.write(f"💰 **Valor:** R$ {row['valor']:.2f} ({row['forma_pagamento']}) | ⏱ {row['duracao_minutos']} min")

                    if row["telefone"]:
                        tel_digits = "".join(filter(str.isdigit, str(row["telefone"])))
                        if tel_digits and tel_digits != "Naoinformado":
                            if usuario_atual == "Maria":
                                dt_atend = datetime.strptime(str(row['data_atendimento']), "%Y-%m-%d")
                                dias_sem_pt = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}
                                dia_sem_nome = dias_sem_pt.get(dt_atend.weekday(), "")
                                data_fmt_msg = dt_atend.strftime("%d/%m")
                                msg = f"Olá, {row['nome_cliente']}! Estou passando para te lembrar que possui um agendamento para o dia {data_fmt_msg} / ({dia_sem_nome}-Feira) às {row['horario']}h. Confirme o agendamento respondendo: Confirmar ou Reagendar ou Cancelar."
                            else:
                                msg = f"Olá {row['nome_cliente']}! Confirmado seu horário para {row['servico']} no dia {dt_card_fmt} às {row['horario']}?"
                            
                            link_wa = f"https://wa.me/55{tel_digits}?text={msg.replace(' ', '%20')}"
                            st.markdown(f"[💬 Mandar Lembrete no WhatsApp]({link_wa})")

                    with st.expander("✏️ Editar Atendimento / Valores / Serviço"):
                        with st.form(f"form_ed_atend_{row['id']}"):
                            novo_servico_card = st.selectbox("Serviço", servicos_disponiveis, index=servicos_disponiveis.index(row['servico']) if row['servico'] in servicos_disponiveis else 0)
                            col_ev1, col_ev2 = st.columns(2)
                            with col_ev1:
                                novo_val_card = st.number_input("Valor (R$)", min_value=0.0, value=float(row['valor']), step=5.0)
                            with col_ev2:
                                novo_pag_card = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], index=["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"].index(row['forma_pagamento']) if row['forma_pagamento'] in ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"] else 0)
                            
                            novo_dur_card = st.number_input("Duração (minutos)", min_value=5, max_value=480, value=int(row['duracao_minutos']), step=5, key=f"dur_card_{row['id']}")
                            novo_hor_card = st.time_input("Horário", value=datetime.strptime(row['horario'], "%H:%M").time())
                            
                            salvar_edicao_atend = st.form_submit_button("Guardar Alterações do Atendimento")
                            if salvar_edicao_atend:
                                conn_ed = sqlite3.connect("agenda_unhas_v2.db")
                                c_ed = conn_ed.cursor()
                                c_ed.execute("UPDATE agendamentos SET servico = ?, valor = ?, forma_pagamento = ?, duracao_minutos = ?, horario = ? WHERE id = ?",
                                             (novo_servico_card, novo_val_card, novo_pag_card, int(novo_dur_card), str(novo_hor_card)[:5], row['id']))
                                conn_ed.commit()
                                conn_ed.close()
                                st.success("Atendimento atualizado com sucesso!")
                                st.rerun()

                    st.write("🔁 **Ciclo de Retorno:**")
                    ciclo_escolha = st.selectbox(
                        "Opção de Ciclo",
                        [15, 21, 25, 30, "Outro (Personalizado)"],
                        index=1,
                        key=f"ciclo_escolha_{row['id']}"
                    )
                    
                    if ciclo_escolha == "Outro (Personalizado)":
                        ciclo_card = st.number_input("Digite os dias:", min_value=1, max_value=365, value=10, step=1, key=f"ciclo_custom_{row['id']}")
                    else:
                        ciclo_card = int(ciclo_escolha)

                    if st.button("➕ Adicionar/Atualizar no CRM", key=f"btn_crm_card_{row['id']}"):
                        conn_c = sqlite3.connect("agenda_unhas_v2.db")
                        c_cursor = conn_c.cursor()
                        c_cursor.execute("SELECT id FROM clientes_retencao WHERE nome = ? AND profissional = ?", (row['nome_cliente'], usuario_atual))
                        cli_existente = c_cursor.fetchone()
                        tel_reg = row['telefone'] if row['telefone'] else "Não informado"
                        if cli_existente:
                            c_cursor.execute("UPDATE clientes_retencao SET ultimo_atendimento = ?, ciclo_dias = ?, telefone = ?, valor = ?, forma_pagamento = ? WHERE id = ?", 
                                             (row['data_atendimento'], ciclo_card, tel_reg, row['valor'], row['forma_pagamento'], cli_existente[0]))
                        else:
                            c_cursor.execute("INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento, profissional, valor, forma_pagamento) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                             (row['nome_cliente'], tel_reg, ciclo_card, row['data_atendimento'], usuario_atual, row['valor'], row['forma_pagamento']))
                        conn_c.commit()
                        conn_c.close()
                        st.success(f"Cliente {row['nome_cliente']} adicionada/atualizada no CRM!")
                        st.rerun()

                    novo_status = st.selectbox(
                        "Status:", ["Agendado", "Confirmado", "Realizado", "Cancelado"],
                        index=["Agendado", "Confirmado", "Realizado", "Cancelado"].index(row["status"]),
                        key=f"status_select_{row['id']}"
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Atualizar Status", key=f"btn_update_{row['id']}"):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            c.execute("UPDATE agendamentos SET status = ? WHERE id = ?", (novo_status, row["id"]))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with col_btn2:
                        if st.button("🗑️ Excluir", key=f"btn_del_{row['id']}"):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            info_str = f"[{usuario_atual}] Agendamento: {row['nome_cliente']} | {row['servico']} | R$ {row['valor']}"
                            c.execute("INSERT INTO lixeira (tipo_item, dados_item, data_exclusao) VALUES (?, ?, ?)", ("agendamento", info_str, str(date.today())))
                            c.execute("DELETE FROM agendamentos WHERE id = ?", (row["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()
    else:
        st.info("Nenhum atendimento encontrado para o período selecionado.")

# ==========================================
# ABA 2: CENTRAL DE RETENÇÃO (CRM)
# ==========================================
with aba_crm:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_crm = pd.read_sql_query("SELECT * FROM clientes_retencao WHERE profissional = ?", conn, params=(usuario_atual,))
    df_agendamentos_todos = pd.read_sql_query("SELECT * FROM agendamentos WHERE profissional = ?", conn, params=(usuario_atual,))
    conn.close()

    if not df_crm.empty:
        df_crm["ultimo_atendimento"] = pd.to_datetime(df_crm["ultimo_atendimento"], errors="coerce").dt.date
        df_crm["proximo_atendimento"] = df_crm.apply(lambda r: r["ultimo_atendimento"] + timedelta(days=int(r["ciclo_dias"])), axis=1)
        df_crm["dias_para_retorno"] = df_crm["proximo_atendimento"].apply(lambda d: (d - date.today()).days)
        df_crm = df_crm.sort_values(by="dias_para_retorno", ascending=True)

        termo_busca = st.text_input("🔍 Pesquisar Cliente no CRM:", placeholder="Nome ou WhatsApp...", key=f"busca_crm_{usuario_atual}")

        if termo_busca:
            resultados_busca = df_crm[df_crm["nome"].str.contains(termo_busca, case=False, na=False) | df_crm["telefone"].str.contains(termo_busca, case=False, na=False)]
            for _, row in resultados_busca.iterrows():
                with st.container(border=True):
                    st.markdown(f"### 👤 {row['nome']}")
                    st.write(f"📱 {row['telefone']} | Ciclo: {row['ciclo_dias']} dias | 💰 R$ {row.get('valor', 50.0):.2f} ({row.get('forma_pagamento', 'Pix')})")
                    digits_cli = "".join(filter(str.isdigit, str(row['telefone']))) if row['telefone'] else ""
                    if digits_cli:
                        msg = f"Oi {row['nome']}! Passando para avisar que já deu o prazo da sua manutenção!"
                        link_wa = f"https://wa.me/55{digits_cli}?text={msg.replace(' ', '%20')}"
                        st.markdown(f"[💬 WhatsApp]({link_wa})")
            st.divider()

        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        chamar_semana = df_crm[(df_crm["proximo_atendimento"] <= fim_semana)]

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total no CRM", len(df_crm))
        col_m2.metric("Chamar Esta Semana", len(chamar_semana))
        col_m3.metric("Hoje", hoje.strftime("%d/%m/%Y"))

        st.divider()
        sub_aba1, sub_aba_semana, sub_aba2 = st.tabs(["📲 Chamar Esta Semana (Retorno)", "📅 Visão Semanal (Atendimentos)", "📋 Todas as Clientes"])

        with sub_aba1:
            if chamar_semana.empty:
                st.success("🎉 Nenhuma cliente pendente para chamar esta semana!")
            else:
                for _, row in chamar_semana.reset_index().iterrows():
                    with st.container(border=True):
                        st.markdown(f"### 👤 {row['nome']}")
                        st.write(f"🔁 Ciclo: {row['ciclo_dias']} dias | Previsão: {row['proximo_atendimento'].strftime('%d/%m/%Y')}")
                        
                        col_val_crm, col_pag_crm = st.columns(2)
                        with col_val_crm:
                            val_atend_hoje = st.number_input("Valor (R$)", min_value=0.0, value=float(row.get('valor', 50.0)), step=5.0, key=f"val_crm_{row['id']}")
                        with col_pag_crm:
                            pag_atend_hoje = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], 
                                                          index=["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"].index(row.get('forma_pagamento', 'Pix')) if row.get('forma_pagamento') in ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"] else 0,
                                                          key=f"pag_crm_{row['id']}")

                        digits_cli = "".join(filter(str.isdigit, str(row['telefone']))) if row['telefone'] else ""
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            if digits_cli and digits_cli != "Naoinformado":
                                msg = f"Oi {row['nome']}! Tudo bem? Passando para avisar que já deu o prazo da sua manutenção essa semana!"
                                link_wa = f"https://wa.me/55{digits_cli}?text={msg.replace(' ', '%20')}"
                                st.markdown(f"[💬 WhatsApp]({link_wa})")
                            else:
                                st.write("📱 Sem WhatsApp")
                        with col_b2:
                            if st.button("✅ Atendido Hoje", key=f"renovar_{row['id']}"):
                                hoje_iso = date.today().strftime("%Y-%m-%d")
                                conn = sqlite3.connect("agenda_unhas_v2.db")
                                c = conn.cursor()
                                c.execute("UPDATE clientes_retencao SET ultimo_atendimento = ?, valor = ?, forma_pagamento = ? WHERE id = ?", 
                                          (hoje_iso, val_atend_hoje, pag_atend_hoje, row['id']))
                                c.execute("""INSERT INTO agendamentos (nome_cliente, telefone, servico, data_atendimento, horario, profissional, valor, forma_pagamento, duracao_minutos, status) 
                                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                          (row['nome'], row['telefone'], 'Manutenção / Retorno', hoje_iso, '12:00', usuario_atual, val_atend_hoje, pag_atend_hoje, 60, 'Realizado'))
                                conn.commit()
                                conn.close()
                                st.success(f"Atendimento de {row['nome']} registrado com sucesso!")
                                st.rerun()

        with sub_aba_semana:
            st.markdown(f"### 📅 Lista de Agendamentos da Semana ({inicio_semana.strftime('%d/%m')} a {fim_semana.strftime('%d/%m')})")
            if not df_agendamentos_todos.empty:
                df_agendamentos_todos["data_dt"] = pd.to_datetime(df_agendamentos_todos["data_atendimento"]).dt.date
                agendamentos_semana = df_agendamentos_todos[(df_agendamentos_todos["data_dt"] >= inicio_semana) & (df_agendamentos_todos["data_dt"] <= fim_semana)].sort_values(by=["data_atendimento", "horario"])
                
                if not agendamentos_semana.empty:
                    for _, ag_row in agendamentos_semana.iterrows():
                        with st.container(border=True):
                            dt_fmt = pd.to_datetime(ag_row['data_atendimento']).strftime('%d/%m/%Y')
                            st.markdown(f"**👤 {ag_row['nome_cliente']}** — 📅 {dt_fmt} às ⏰ {ag_row['horario']}")
                            st.write(f"💅 **Serviço:** {ag_row['servico']} | ⏱ {ag_row['duracao_minutos']} min | 💰 R$ {ag_row['valor']:.2f} ({ag_row['forma_pagamento']}) | Status: *{ag_row['status']}*")
                            
                            with st.expander(f"✏️ Editar Agendamento de {ag_row['nome_cliente']}"):
                                with st.form(f"form_crm_semana_{ag_row['id']}"):
                                    s_serv = st.selectbox("Serviço", servicos_disponiveis, index=servicos_disponiveis.index(ag_row['servico']) if ag_row['servico'] in servicos_disponiveis else 0)
                                    col_cs1, col_cs2 = st.columns(2)
                                    with col_cs1:
                                        s_val = st.number_input("Valor (R$)", min_value=0.0, value=float(ag_row['valor']), step=5.0)
                                    with col_cs2:
                                        s_pag = st.selectbox("Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], index=["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"].index(ag_row['forma_pagamento']) if ag_row['forma_pagamento'] in ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"] else 0)
                                    s_dur = st.number_input("Duração (minutos)", min_value=5, max_value=480, value=int(ag_row['duracao_minutos']), step=5, key=f"dur_sem_{ag_row['id']}")
                                    s_hor = st.time_input("Horário", value=datetime.strptime(ag_row['horario'], "%H:%M").time())
                                    
                                    if st.form_submit_button("Salvar Alterações na Semana"):
                                        conn_s = sqlite3.connect("agenda_unhas_v2.db")
                                        cs = conn_s.cursor()
                                        cs.execute("UPDATE agendamentos SET servico = ?, valor = ?, forma_pagamento = ?, duracao_minutos = ?, horario = ? WHERE id = ?",
                                                   (s_serv, s_val, s_pag, int(s_dur), str(s_hor)[:5], ag_row['id']))
                                        conn_s.commit()
                                        conn_s.close()
                                        st.success("Atualizado com sucesso!")
                                        st.rerun()
                else:
                    st.info("Nenhum atendimento agendado para esta semana.")
            else:
                st.info("Nenhum agendamento registado.")

        with sub_aba2:
            for _, row in df_crm.iterrows():
                with st.expander(f"👤 {row['nome']} (Retorno: {row['proximo_atendimento'].strftime('%d/%m/%Y')})"):
                    st.write(f"📱 WhatsApp: {row['telefone']}")
                    st.write(f"💰 Valor Padrão: R$ {row.get('valor', 50.0):.2f} ({row.get('forma_pagamento', 'Pix')}) | Ciclo: {row['ciclo_dias']} dias")

                    digits_cli = "".join(filter(str.isdigit, str(row['telefone']))) if row['telefone'] else ""
                    if digits_cli and digits_cli != "Naoinformado":
                        msg = f"Oi {row['nome']}! Tudo bem? Passando para avisar que já deu o prazo da sua manutenção!"
                        link_wa = f"https://wa.me/55{digits_cli}?text={msg.replace(' ', '%20')}"
                        st.markdown(
                            f"""
                            <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                                <button style="background-color: #25D366; color: white; padding: 8px 16px; border: none; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; width: 100%; margin-bottom: 10px;">
                                    💬 Enviar Mensagem no WhatsApp
                                </button>
                            </a>
                        """,
                            unsafe_allow_html=True,
                        )
                    
                    st.markdown("---")
                    st.write("✏️️ **Editar Dados da Cliente e Ciclo:**")
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        padroes_crm = [15, 21, 25, 30, "Outro (Personalizado)"]
                        c_atual = row['ciclo_dias']
                        idx_inicial = padroes_crm.index(c_atual) if c_atual in [15, 21, 25, 30] else 4
                        ed_ciclo_escolha = st.selectbox("Ciclo de Retorno", padroes_crm, index=idx_inicial, key=f"ed_ciclo_escolha_{row['id']}")
                        if ed_ciclo_escolha == "Outro (Personalizado)":
                            val_custom = c_atual if c_atual not in [15, 21, 25, 30] else 10
                            ed_ciclo_final = st.number_input("Dias exatos", min_value=1, max_value=365, value=int(val_custom), step=1, key=f"ed_custom_{row['id']}")
                        else:
                            ed_ciclo_final = int(ed_ciclo_escolha)
                    
                    with col_e2:
                        ed_valor = st.number_input("Valor Padrão (R$)", min_value=0.0, value=float(row.get('valor', 50.0)), step=5.0, key=f"ed_val_{row['id']}")
                        ed_pag = st.selectbox("Forma de Pagamento", ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"], 
                                              index=["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"].index(row.get('forma_pagamento', 'Pix')) if row.get('forma_pagamento') in ["Dinheiro", "Pix", "Cartão Débito", "Cartão Crédito"] else 0,
                                              key=f"ed_pag_{row['id']}")

                    if st.button("💾 Salvar Alterações", key=f"btn_salvar_cli_{row['id']}"):
                        conn_e = sqlite3.connect("agenda_unhas_v2.db")
                        c_e = conn_e.cursor()
                        c_e.execute("UPDATE clientes_retencao SET ciclo_dias = ?, valor = ?, forma_pagamento = ? WHERE id = ?", 
                                  (ed_ciclo_final, ed_valor, ed_pag, row['id']))
                        conn_e.commit()
                        conn_e.close()
                        st.success("Atualizado com sucesso!")
                        st.rerun()

                    st.markdown("---")
                    if st.button("🗑️ Excluir do CRM", key=f"del_crm_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM clientes_retencao WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.success("Removida do CRM.")
                        st.rerun()
    else:
        st.info("Nenhuma cliente cadastrada no CRM.")

# ==========================================
# ABA 3: FINANCEIRO & GANHOS
# ==========================================
with aba_fin:
    st.subheader(f"📊 Relatório Financeiro — {usuario_atual}")
    st.write("Acompanhe os ganhos por dia, semana ou mês e baixe o relatório pronto para PDF/Impressão.")

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_fin = pd.read_sql_query("SELECT * FROM agendamentos WHERE profissional = ?", conn, params=(usuario_atual,))
    conn.close()

    if not df_fin.empty:
        df_fin["data_atendimento"] = pd.to_datetime(df_fin["data_atendimento"]).dt.date

        filtro_periodo = st.selectbox("Selecione o Período:", ["Mês Atual", "Esta Semana", "Hoje", "Personalizado"])
        
        hoje_f = date.today()
        if filtro_periodo == "Hoje":
            df_filtrado = df_fin[df_fin["data_atendimento"] == hoje_f]
        elif filtro_periodo == "Esta Semana":
            inicio_sem = hoje_f - timedelta(days=hoje_f.weekday())
            fim_sem = inicio_sem + timedelta(days=6)
            df_filtrado = df_fin[(df_fin["data_atendimento"] >= inicio_sem) & (df_fin["data_atendimento"] <= fim_sem)]
        elif filtro_periodo == "Mês Atual":
            df_filtrado = df_fin[(df_fin["data_atendimento"].apply(lambda d: d.strftime('%Y-%m')) == hoje_f.strftime('%Y-%m'))]
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                d_ini = st.date_input("Data Inicial", value=hoje_f.replace(day=1))
            with col_d2:
                d_fim = st.date_input("Data Final", value=hoje_f)
            df_filtrado = df_fin[(df_fin["data_atendimento"] >= d_ini) & (df_fin["data_atendimento"] <= d_fim)]

        total_ganho = df_filtrado["valor"].sum() if not df_filtrado.empty else 0.0
        qtd_atendimentos = len(df_filtrado)
        ticket_medio = total_ganho / qtd_atendimentos if qtd_atendimentos > 0 else 0.0

        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("💵 Total no Período", f"R$ {total_ganho:.2f}")
        col_f2.metric("📋 Atendimentos", qtd_atendimentos)
        col_f3.metric("⭐ Ticket Médio", f"R$ {ticket_medio:.2f}")

        st.divider()

        if not df_filtrado.empty:
            pagto_html = ""
            pagto_resumo = df_filtrado.groupby("forma_pagamento")["valor"].sum().reset_index()
            for _, r in pagto_resumo.iterrows():
                pagto_html += f"<li><b>{r['forma_pagamento']}:</b> R$ {r['valor']:.2f}</li>"

            linhas_tabela = ""
            for _, r in df_filtrado.iterrows():
                dt_fmt = pd.to_datetime(r['data_atendimento']).strftime('%d/%m/%Y')
                linhas_tabela += f"<tr><td>{dt_fmt}</td><td>{r['horario']}</td><td>{r['nome_cliente']}</td><td>{r['servico']}</td><td>R$ {r['valor']:.2f}</td><td>{r['forma_pagamento']}</td></tr>"

            html_documento = f"""
            <html>
            <head><meta charset="utf-8"><title>Relatório - {usuario_atual}</title></head>
            <body>
                <h1>💅 {titulo_atual} — Relatório Financeiro ({usuario_atual})</h1>
                <p><b>Período:</b> {filtro_periodo}</p>
                <h3>Total Faturado: R$ {total_ganho:.2f} | Atendimentos: {qtd_atendimentos}</h3>
                <ul>{pagto_html}</ul>
                <table border="1" cellpadding="5" style="border-collapse:collapse; width:100%;">
                    <tr><th>Data</th><th>Horário</th><th>Cliente</th><th>Serviço</th><th>Valor</th><th>Pagamento</th></tr>
                    {linhas_tabela}
                </table>
            </body>
            </html>
            """
            st.download_button("📥 Baixar Relatório em PDF / HTML", data=html_documento, file_name=f"relatorio_{usuario_atual}.html", mime="text/html")

        st.markdown("### 💳 Faturamento por Forma de Pagamento")
        pagto_resumo = df_filtrado.groupby("forma_pagamento")["valor"].sum().reset_index()
        for _, r in pagto_resumo.iterrows():
            st.write(f"- **{r['forma_pagamento']}:** R$ {r['valor']:.2f}")

        st.dataframe(df_filtrado[["data_atendimento", "horario", "nome_cliente", "servico", "valor", "forma_pagamento"]], use_container_width=True)
    else:
        st.info("Nenhum dado financeiro registrado ainda.")

# ==========================================
# ABA 4: CONTATOS
# ==========================================
with aba_contatos:
    st.subheader(f"📇 Agenda de Contatos — {usuario_atual}")
    st.write("Adicione novos contatos aqui para que o sistema sugira automaticamente ao agendar.")

    with st.form("form_novo_contato_tab", clear_on_submit=True):
        st.markdown("### ➕ Adicionar Novo Contato")
        novo_c_nome = st.text_input("Nome da Cliente*")
        novo_c_tel = st.text_input("WhatsApp", placeholder="54991341375")
        btn_salvar_c = st.form_submit_button("Guardar Contato na Agenda")
        
        if btn_salvar_c:
            if not novo_c_nome:
                st.error("Preencha o nome da cliente!")
            else:
                conn_nc = sqlite3.connect("agenda_unhas_v2.db")
                cnc = conn_nc.cursor()
                cnc.execute("SELECT id FROM contatos WHERE nome = ? AND profissional = ?", (novo_c_nome, usuario_atual))
                if cnc.fetchone():
                    cnc.execute("UPDATE contatos SET telefone = ? WHERE nome = ? AND profissional = ?", (novo_c_tel, novo_c_nome, usuario_atual))
                    st.success(f"Contato de {novo_c_nome} atualizado!")
                else:
                    cnc.execute("INSERT INTO contatos (nome, telefone, profissional) VALUES (?, ?, ?)", (novo_c_nome, novo_c_tel, usuario_atual))
                    st.success(f"Contato de {novo_c_nome} guardado com sucesso!")
                conn_nc.commit()
                conn_nc.close()
                st.rerun()

    st.divider()

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_contatos_tabela = pd.read_sql_query("SELECT * FROM contatos WHERE profissional = ? ORDER BY nome ASC", conn, params=(usuario_atual,))
    conn.close()

    if not df_contatos_tabela.empty:
        busca_agenda = st.text_input("🔍 Pesquisar na Agenda de Contatos:", placeholder="Digite o nome ou número...")
        if busca_agenda:
            df_contatos_tabela = df_contatos_tabela[df_contatos_tabela["nome"].str.contains(busca_agenda, case=False, na=False) | df_contatos_tabela["telefone"].str.contains(busca_agenda, case=False, na=False)]

        st.markdown(f"**Total de contatos:** {len(df_contatos_tabela)}")
        cols_cont = st.columns(2)
        for idx, row in df_contatos_tabela.reset_index().iterrows():
            col_atual = cols_cont[idx % 2]
            with col_atual:
                with st.container(border=True):
                    st.markdown(f"### 👤 {row['nome']}")
                    tel_exib = row['telefone'] if row['telefone'] else "Não cadastrado"
                    st.write(f"📱 **WhatsApp:** {tel_exib}")

                    digits_cont = "".join(filter(str.isdigit, str(row['telefone']))) if row['telefone'] else ""
                    if digits_cont and digits_cont != "Naoinformado":
                        link_wa_contato = f"https://wa.me/55{digits_cont}?text=Olá%20{row['nome']}!%20Tudo%20bem?"
                        st.markdown(
                            f"""
                            <a href="{link_wa_contato}" target="_blank" style="text-decoration: none;">
                                <button style="background-color: #25D366; color: white; padding: 8px 16px; border: none; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; width: 100%;">
                                    💬 Abrir WhatsApp
                                </button>
                            </a>
                        """,
                            unsafe_allow_html=True,
                        )
    else:
        st.info("Nenhum contato cadastrado ainda.")

# ==========================================
# ABA 5: TAREFAS
# ==========================================
with aba_tarefas:
    st.subheader("📝 Tarefas")
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_t = pd.read_sql_query("SELECT * FROM tarefas ORDER BY concluido ASC", conn)
    conn.close()

    if df_t.empty:
        st.info("Nenhuma tarefa cadastrada.")
    else:
        for _, row in df_t.iterrows():
            with st.container(border=True):
                st.markdown(f"### {'✅' if row['concluido'] else '📌'} {row['titulo']}")
                st.write(row["descricao"])
                if not row["concluido"] and st.button("Concluir", key=f"t_{row['id']}"):
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    c.execute("UPDATE tarefas SET concluido = 1 WHERE id = ?", (row["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

# ==========================================
# ABA 6: LIXEIRA
# ==========================================
with aba_lixeira:
    st.subheader("🗑️ Lixeira")
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_lix = pd.read_sql_query("SELECT * FROM lixeira ORDER BY id DESC", conn)
    conn.close()
    if df_lix.empty:
        st.success("Lixeira limpa.")
    else:
        for _, row in df_lix.iterrows():
            with st.container(border=True):
                st.write(f"**Tipo:** {row['tipo_item']} | **Info:** {row['dados_item']}")
                if st.button("Excluir Permanentemente", key=f"lix_{row['id']}"):
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    c.execute("DELETE FROM lixeira WHERE id = ?", (row["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

# ==========================================
# ABA 7: CONFIGURAÇÕES
# ==========================================
with aba_config:
    st.subheader("⚙️ Configurações & Perfil")
    with st.form("form_config"):
        novo_titulo = st.text_input("Nome do Studio:", value=titulo_atual)
        
        temas_disponiveis = ["Dourado Luxo", "Clean White (Tudo Branco)", "Nude / Rosé", "Dark Elegance", "Lavanda / Soft Purple"]
        idx_tema_atual = temas_disponiveis.index(tema_atual) if tema_atual in temas_disponiveis else 0
        novo_tema = st.selectbox("Tema Visual:", temas_disponiveis, index=idx_tema_atual)
        
        _, servicos_atuais_db, wa_db = get_perfil_info(usuario_atual)
        novo_wa = st.text_input("O meu WhatsApp:", value=wa_db)
        novos_servicos = st.text_area("Os meus Serviços (um por linha):", value=servicos_atuais_db, height=120)
        
        nova_senha = st.text_input("Nova Palavra-passe (opcional):", type="password")
        repete_senha = st.text_input("Repetir Nova Palavra-passe:", type="password")

        if st.form_submit_button("Guardar Alterações"):
            if nova_senha and nova_senha != repete_senha:
                st.error("As palavras-passe não coincidem!")
            else:
                conn = sqlite3.connect("agenda_unhas_v2.db")
                c = conn.cursor()
                c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'titulo_studio'", (novo_titulo,))
                c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'tema_estilo'", (novo_tema,))
                if nova_senha:
                    c.execute("UPDATE perfis SET senha = ?, servicos = ?, whatsapp = ? WHERE nome = ?", (nova_senha, novos_servicos, novo_wa, usuario_atual))
                else:
                    c.execute("UPDATE perfis SET servicos = ?, whatsapp = ? WHERE nome = ?", (novos_servicos, novo_wa, usuario_atual))
                conn.commit()
                conn.close()
                st.success("Guardado com sucesso! A atualizar...")
                st.rerun()

    st.divider()
    st.subheader("🛡️ Cópia de Segurança do Sistema")
    try:
        with open("agenda_unhas_v2.db", "rb") as f:
            st.download_button("📥 Descarregar Base de Dados (.db)", f, file_name=f"backup_studio_{date.today()}.db")
    except:
        st.error("Erro ao gerar cópia de segurança.")

    st.divider()
    st.subheader("📂 Restaurar Base de Dados (Backup)")
    st.write("Se precisar de recuperar os seus dados de um backup anterior, carregue aqui o seu ficheiro `.db`:")
    uploaded_db = st.file_uploader("Escolher ficheiro de base de dados (.db)", type=["db"])
    if uploaded_db is not None:
        if st.button("Restaurar Dados"):
            try:
                with open("agenda_unhas_v2.db", "wb") as f:
                    f.write(uploaded_db.getbuffer())
                st.success("Base de dados restaurada com sucesso! A atualizar a aplicação...")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao restaurar o ficheiro: {e}")

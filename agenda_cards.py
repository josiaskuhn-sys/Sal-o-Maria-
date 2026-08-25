import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# --- BANCO DE DADOS & LIXEIRA ---
def init_db():
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()

    # Tabela 1: Agendamentos por Horário (com valor, pagamento e duração)
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

    # Verificação inteligente e segura de colunas para bancos já existentes
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
            telefone TEXT NOT NULL,
            ciclo_dias INTEGER NOT NULL,
            ultimo_atendimento DATE NOT NULL,
            profissional TEXT DEFAULT 'Maria'
        )
    """
    )

    c.execute("PRAGMA table_info(clientes_retencao)")
    colunas_crm = [col[1] for col in c.fetchall()]
    if "profissional" not in colunas_crm:
        c.execute("ALTER TABLE clientes_retencao ADD COLUMN profissional TEXT DEFAULT 'Maria'")

    # Tabela 3: Minhas Tarefas / Anotações
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

    # Tabela 4: Lixeira Inteligente
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

    # Tabela 5: Configurações Gerais do Studio
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """
    )

    # Tabela 6: Perfis, Senhas, Serviços e WhatsApp Individual
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

    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('titulo_studio', 'Studio Maria Rossatto')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('subtitulo_studio', 'Sistema de Gestão & Retenção')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('tema_estilo', 'Dourado Luxo')")

    servicos_maria_default = "Mão tradicional\nPé tradicional\nBlindagem\nEsmaltação em gel\nBanho de gel\nAlongamento\nManutenção\nPacote de mão"
    servicos_camily_default = "Design de Sobrancelha\nSobrancelha com Henna\nExtensão de Cílios Fio a Fio\nVolume Russo\nLash Lifting\nManutenção de Cílios"

    c.execute("INSERT OR IGNORE INTO perfis (nome, senha, servicos, whatsapp) VALUES ('Maria', 'maria123', ?, '5554991341375')", (servicos_maria_default,))
    c.execute("INSERT OR IGNORE INTO perfis (nome, senha, servicos, whatsapp) VALUES ('Camily', 'camily123', ?, '')", (servicos_camily_default,))

    limite_30_dias = str(date.today() - timedelta(days=30))
    c.execute("DELETE FROM lixeira WHERE data_exclusao < ?", (limite_30_dias,))

    conn.commit()
    conn.close()


init_db()

# --- FUNÇÕES DE BUSCA NO BANCO ---
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

# --- APLICAÇÃO DE TEMAS DINÂMICOS & ESTILO NOTION OTIMIZADO PARA CELULAR (CSS) ---
tema_atual = get_config("tema_estilo")

estilos_css = {
    "Dourado Luxo": """
        <style>
            .stApp { background-color: #FDFBF7 !important; color: #33322E !important; }
            .stSidebar { background-color: #F4EFEA !important; border-right: 1px solid #E3DDD5; }
            div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #E3DDD5 !important; border-radius: 10px; }
            div[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #E3DDD5 !important; border-radius: 10px; }
            .stButton>button { background-color: #C5A059 !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #A88234 !important; }
            
            /* Estilo Notion Card Perfeito para Calendário */
            .fc-event {
                background-color: #FFFFFF !important;
                border: 1px solid #E3DDD5 !important;
                border-left: 3px solid #C5A059 !important;
                border-radius: 4px !important;
                padding: 2px 4px !important;
                margin-bottom: 2px !important;
                box-shadow: 0 1px 2px rgba(0,0,0,0.04);
            }
            .fc-event-title {
                white-space: normal !important;
                word-break: break-word !important;
                font-size: 0.68rem !important;
                font-weight: 600 !important;
                color: #33322E !important;
            }
            .fc-daygrid-event {
                white-space: normal !important;
                align-items: normal !important;
            }
            
            /* Ajustes ultra-otimizados para Celular / Telas Pequenas */
            @media (max-width: 768px) {
                .block-container { padding-left: 0.3rem !important; padding-right: 0.3rem !important; padding-top: 0.6rem !important; }
                h1 { font-size: 1.2rem !important; }
                h2 { font-size: 1.0rem !important; }
                h3 { font-size: 0.95rem !important; }
                
                /* Calendário Header Responsivo (Evita cortes e quebras feias) */
                .fc-toolbar.fc-header-toolbar {
                    display: flex !important;
                    flex-direction: column !important;
                    align-items: center !important;
                    gap: 6px !important;
                    margin-bottom: 0.5rem !important;
                }
                .fc-toolbar-chunk {
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                    flex-wrap: nowrap !important;
                    width: 100% !important;
                }
                .fc-toolbar-title {
                    font-size: 0.9rem !important;
                    font-weight: bold !important;
                    white-space: nowrap !important;
                }
                .fc-button {
                    padding: 3px 5px !important;
                    font-size: 0.65rem !important;
                    line-height: 1.1 !important;
                }
                
                .fc-event { padding: 1px 2px !important; margin-bottom: 1px !important; }
                .fc-event-title { font-size: 0.58rem !important; line-height: 1.1 !important; }
                .fc-daygrid-day-number { font-size: 0.68rem !important; padding: 2px !important; }
            }
        </style>
    """,
    "Clean White (Tudo Branco)": """
        <style>
            .stApp { background-color: #FFFFFF !important; color: #222222 !important; }
            .stSidebar { background-color: #FAFAFA !important; border-right: 1px solid #EAEAEA; }
            div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 1px solid #E0E0E0 !important; }
            div[data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #E0E0E0 !important; }
            .stButton>button { background-color: #000000 !important; color: white !important; border-radius: 8px !important; border: none !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #000000 !important; }
            .fc-event { background-color: #F9FAFB !important; border: 1px solid #E5E7EB !important; border-left: 3px solid #000000 !important; border-radius: 4px !important; padding: 2px 4px !important; }
            .fc-event-title { white-space: normal !important; word-break: break-word !important; font-size: 0.68rem !important; font-weight: 600 !important; color: #111827 !important; }
            @media (max-width: 768px) { 
                .block-container { padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
                .fc-toolbar.fc-header-toolbar { display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; }
                .fc-toolbar-chunk { display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; }
                .fc-toolbar-title { font-size: 0.9rem !important; white-space: nowrap !important; }
                .fc-button { padding: 3px 5px !important; font-size: 0.65rem !important; }
                .fc-event-title { font-size: 0.58rem !important; }
            }
        </style>
    """,
    "Nude / Rosé": """
        <style>
            .stApp { background-color: #FFF9F9; color: #4A3E3D; }
            .stSidebar { background-color: #FFF0F2; }
            .stButton>button { background-color: #E8A5A5 !important; color: white !important; border-radius: 8px !important; border: none !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #D87070 !important; }
            .fc-event { background-color: #FFFFFF !important; border: 1px solid #F5D0D0 !important; border-left: 3px solid #E8A5A5 !important; border-radius: 4px !important; padding: 2px 4px !important; }
            .fc-event-title { white-space: normal !important; word-break: break-word !important; font-size: 0.68rem !important; font-weight: 600 !important; color: #4A3E3D !important; }
            @media (max-width: 768px) { 
                .block-container { padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
                .fc-toolbar.fc-header-toolbar { display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; }
                .fc-toolbar-chunk { display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; }
                .fc-toolbar-title { font-size: 0.9rem !important; white-space: nowrap !important; }
                .fc-button { padding: 3px 5px !important; font-size: 0.65rem !important; }
                .fc-event-title { font-size: 0.58rem !important; }
            }
        </style>
    """,
    "Dark Elegance": """
        <style>
            .stApp { background-color: #121212; color: #E0E0E0; }
            .stSidebar { background-color: #1E1E1E; }
            .stButton>button { background-color: #BB86FC !important; color: #121212 !important; border-radius: 8px !important; font-weight: bold !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #BB86FC !important; }
            .fc-event { background-color: #1E1E1E !important; border: 1px solid #333333 !important; border-left: 3px solid #BB86FC !important; border-radius: 4px !important; padding: 2px 4px !important; }
            .fc-event-title { white-space: normal !important; word-break: break-word !important; font-size: 0.68rem !important; font-weight: 600 !important; color: #E0E0E0 !important; }
            @media (max-width: 768px) { 
                .block-container { padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
                .fc-toolbar.fc-header-toolbar { display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; }
                .fc-toolbar-chunk { display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; }
                .fc-toolbar-title { font-size: 0.9rem !important; white-space: nowrap !important; }
                .fc-button { padding: 3px 5px !important; font-size: 0.65rem !important; }
                .fc-event-title { font-size: 0.58rem !important; }
            }
        </style>
    """,
    "Lavanda / Soft Purple": """
        <style>
            .stApp { background-color: #F8F7FF; color: #3A354A; }
            .stSidebar { background-color: #EDE9FE; }
            .stButton>button { background-color: #8B5CF6 !important; color: white !important; border-radius: 8px !important; width: 100%; }
            div[data-testid="stMetricValue"] { color: #7C3AED !important; }
            .fc-event { background-color: #FFFFFF !important; border: 1px solid #DDD6FE !important; border-left: 3px solid #8B5CF6 !important; border-radius: 4px !important; padding: 2px 4px !important; }
            .fc-event-title { white-space: normal !important; word-break: break-word !important; font-size: 0.68rem !important; font-weight: 600 !important; color: #3A354A !important; }
            @media (max-width: 768px) { 
                .block-container { padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
                .fc-toolbar.fc-header-toolbar { display: flex !important; flex-direction: column !important; align-items: center !important; gap: 6px !important; }
                .fc-toolbar-chunk { display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; }
                .fc-toolbar-title { font-size: 0.9rem !important; white-space: nowrap !important; }
                .fc-button { padding: 3px 5px !important; font-size: 0.65rem !important; }
                .fc-event-title { font-size: 0.58rem !important; }
            }
        </style>
    """,
}

st.markdown(estilos_css.get(tema_atual, estilos_css["Dourado Luxo"]), unsafe_allow_html=True)

# --- BLOQUEIO ANTI-TRADUÇÃO ---
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# --- CONTROLE DE SESSÃO / LOGIN ---
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
            st.write("Selecione sua conta e digite sua senha:")

            with st.form("form_login"):
                escolha_usuario = st.selectbox("Profissional:", ["Maria", "Camily"])
                senha_input = st.text_input("Senha:", type="password")
                btn_entrar = st.form_submit_button("Entrar no Sistema")

                if btn_entrar:
                    senha_db, _, _ = get_perfil_info(escolha_usuario)
                    if senha_input == senha_db:
                        st.session_state.autenticado = True
                        st.session_state.usuario = escolha_usuario
                        st.session_state.perfil = f"{'Unhas (Maria)' if escolha_usuario == 'Maria' else 'Sobrancelhas & Cílios (Camily)'}"
                        st.rerun()
                    else:
                        st.error("Senha incorreta!")
        st.stop()

usuario_atual = st.session_state.usuario
perfil_atual = st.session_state.perfil

_, servicos_str_db, whatsapp_prof_db = get_perfil_info(usuario_atual)
servicos_disponiveis = [s.strip() for s in servicos_str_db.split("\n") if s.strip()]

# --- BARRA LATERAL ---
with st.sidebar:
    try:
        st.image("logo.JPG", use_container_width=True)
    except:
        pass
    st.success(f"Logada como:\n**{perfil_atual}**")
    
    if st.button("🚪 Sair (Trocar de Usuário)"):
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

        with st.form("form_rapido", clear_on_submit=True):
            nome_cliente = st.text_input("Nome da Cliente*")
            telefone = st.text_input("WhatsApp", placeholder="54991341375")
            servico = st.selectbox("Serviço*", servicos_disponiveis)
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                valor_servico = st.number_input("Valor (R$)*", min_value=0.0, value=50.0, step=5.0)
            with col_v2:
                duracao_servico = st.selectbox("Duração*", [30, 45, 60, 90, 120, 150, 180], index=2, format_func=lambda x: f"{x} min")

            forma_pagto = st.selectbox("Forma de Pagamento*", ["Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito"])
            
            data_atendimento = st.date_input("Data*", value=date.today(), format="DD/MM/YYYY")
            horario = st.time_input("Horário*", value=datetime.strptime("14:00", "%H:%M").time())

            salvar = st.form_submit_button("Salvar Horário")

            if salvar:
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
                            duracao_servico,
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Horário marcado com sucesso!")
                    st.rerun()

    elif tipo_cadastro == "👤 Cadastrar Cliente (CRM)":
        st.header(f"➕ CRM ({usuario_atual})")
        with st.form("form_cliente_crm", clear_on_submit=True):
            nome = st.text_input("Nome da Cliente*")
            telefone = st.text_input("WhatsApp*", placeholder="54991341375")
            ciclo_dias = st.selectbox("Ciclo de Retorno (Dias)*", [15, 21, 25, 30], index=1)
            ultimo_atendimento = st.date_input("Último Atendimento*", value=date.today(), format="DD/MM/YYYY")

            salvar_crm = st.form_submit_button("Salvar no CRM")

            if salvar_crm:
                tel_clean = "".join(filter(str.isdigit, str(telefone)))
                if not nome or not tel_clean:
                    st.error("Preencha o Nome e WhatsApp válido!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    data_iso = ultimo_atendimento.strftime("%Y-%m-%d")
                    c.execute("SELECT id FROM clientes_retencao WHERE telefone = ? AND profissional = ?", (tel_clean, usuario_atual))
                    existente = c.fetchone()

                    if existente:
                        c.execute("UPDATE clientes_retencao SET nome = ?, ciclo_dias = ?, ultimo_atendimento = ? WHERE id = ?", (nome, ciclo_dias, data_iso, existente[0]))
                        st.success(f"Cadastro de {nome} atualizado!")
                    else:
                        c.execute("INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento, profissional) VALUES (?, ?, ?, ?, ?)", (nome, tel_clean, ciclo_dias, data_iso, usuario_atual))
                        st.success(f"Cliente {nome} salva!")
                    conn.commit()
                    conn.close()
                    st.rerun()

    else:
        st.header("➕ Nova Anotação")
        with st.form("form_tarefa", clear_on_submit=True):
            titulo_t = st.text_input("Título / Lembrete*")
            desc_t = st.text_area("Detalhes", placeholder="Ex: Comprar material")
            prio_t = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1)
            salvar_t = st.form_submit_button("Salvar Tarefa")

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

st.title(f"💅 {titulo_atual} — Painel da {usuario_atual}")

# --- CENTRAL DE ALERTAS COM NOMES ---
conn = sqlite3.connect("agenda_unhas_v2.db")
hoje_str = date.today().isoformat()

df_agenda_hoje = pd.read_sql_query(
    "SELECT horario, nome_cliente, servico, valor FROM agendamentos WHERE data_atendimento = ? AND profissional = ? ORDER BY horario ASC", 
    conn, params=(hoje_str, usuario_atual)
)

df_crm_tudo = pd.read_sql_query("SELECT id, nome, ultimo_atendimento, ciclo_dias FROM clientes_retencao WHERE profissional = ?", conn, params=(usuario_atual,))
conn.close()

if not df_crm_tudo.empty:
    df_crm_tudo["ultimo_atendimento"] = pd.to_datetime(df_crm_tudo["ultimo_atendimento"], errors="coerce").dt.date
    df_crm_tudo["proximo_atendimento"] = df_crm_tudo.apply(lambda r: r["ultimo_atendimento"] + timedelta(days=int(r["ciclo_dias"])), axis=1)
    df_crm_tudo["dias_atraso"] = df_crm_tudo["proximo_atendimento"].apply(lambda d: (date.today() - d).days)
    df_crm_pendente = df_crm_tudo[df_crm_tudo["proximo_atendimento"] <= date.today()].sort_values(by="dias_atraso", ascending=False)
else:
    df_crm_pendente = pd.DataFrame()

hoje_dt = date.today()
ultimo_dia_mes = (hoje_dt.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
aviso_fim_mes = ""
if hoje_dt.day >= ultimo_dia_mes.day - 3:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_mes_atual = pd.read_sql_query("SELECT valor FROM agendamentos WHERE profissional = ? AND data_atendimento LIKE ?", conn, params=(usuario_atual, f"{hoje_dt.strftime('%Y-%m')}%"))
    conn.close()
    faturamento_mes_atual = df_mes_atual["valor"].sum() if not df_mes_atual.empty else 0.0
    aviso_fim_mes = f"🎉 **Fechamento de Mês:** O mês está acabando! Seu faturamento total até agora é de **R$ {faturamento_mes_atual:.2f}**. Parabéns!"

if not df_agenda_hoje.empty or not df_crm_pendente.empty or aviso_fim_mes:
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
            if not df_crm_pendente.empty:
                st.error(f"⚠️ **CRM Para Chamar ({len(df_crm_pendente)}):**")
                for _, row in df_crm_pendente.iterrows():
                    dias = row["dias_atraso"]
                    status_dias = "Vence hoje" if dias == 0 else f"Atrasada há {dias} dia(s)"
                    st.markdown(f"- 👤 **{row['nome']}** *({status_dias})*")
            else:
                st.success("✅ Nenhuma cliente pendente no CRM.")
else:
    st.success("✅ Tudo em dia! Sem pendências para hoje.")

st.divider()

aba_agenda, aba_crm, aba_fin, aba_tarefas, aba_lixeira, aba_config = st.tabs(
    [
        "📅 Agenda",
        "🎯 CRM",
        "📊 Financeiro & Ganhos",
        "📝 Tarefas",
        "🗑️ Lixeira",
        "⚙️ Configurações",
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
                "borderColor": "#E3DDD5",
                "textColor": "#33322E"
            }
        )

    opcoes_calendario = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,listMonth",
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "locale": "pt-br",
        "buttonText": {"today": "Hoje", "month": "Mês", "week": "Semana", "list": "Lista"},
    }

    st.markdown(f"### 📅 Visão Geral de Atendimentos — {usuario_atual}")
    state = calendar(events=eventos_calendario, options=opcoes_calendario, key=f"cal_studio_{usuario_atual}")

    st.divider()

    data_selecionada = st.date_input("📆 Ver detalhes do dia:", value=date.today(), format="DD/MM/YYYY", key=f"date_agenda_{usuario_atual}")

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df = pd.read_sql_query("SELECT * FROM agendamentos WHERE data_atendimento = ? AND profissional = ? ORDER BY horario ASC", conn, params=(str(data_selecionada), usuario_atual))
    conn.close()

    st.markdown(f"### 📋 Horários de **{data_selecionada.strftime('%d/%m/%Y')}**")

    if not df.empty:
        texto_resumo = f"💅 *Resumo de Atendimentos ({data_selecionada.strftime('%d/%m/%Y')} - {usuario_atual}):*\n\n"
        for _, row in df.iterrows():
            texto_resumo += f"⏰ *{row['horario']}* — {row['nome_cliente']} ({row['servico']}) | R$ {row['valor']:.2f}\n"

        if whatsapp_prof_db:
            link_resumo = f"https://wa.me/{whatsapp_prof_db}?text={texto_resumo.replace(' ', '%20').replace('\n', '%0A')}"
            st.markdown(
                f"""
                <a href="{link_resumo}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #25D366; color: white; padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-bottom: 20px;">
                        📲 Enviar Lista de Hoje no Meu WhatsApp
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
                    st.subheader(f"⏰ {row['horario']} — {row['nome_cliente']}")
                    st.write(f"**Serviço:** {row['servico']}")
                    st.write(f"💰 **Valor:** R$ {row['valor']:.2f} ({row['forma_pagamento']}) | ⏱️ {row['duracao_minutos']} min")

                    if row["telefone"]:
                        tel_digits = "".join(filter(str.isdigit, str(row["telefone"])))
                        if tel_digits:
                            msg = f"Olá {row['nome_cliente']}! Confirmado seu horário para {row['servico']} hoje às {row['horario']}?"
                            link_wa = f"https://wa.me/55{tel_digits}?text={msg.replace(' ', '%20')}"
                            st.markdown(f"[💬 Mandar Lembrete no WhatsApp]({link_wa})")

                    novo_status = st.selectbox(
                        "Status:", ["Agendado", "Confirmado", "Realizado", "Cancelado"],
                        index=["Agendado", "Confirmado", "Realizado", "Cancelado"].index(row["status"]),
                        key=f"status_select_{row['id']}"
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Atualizar", key=f"btn_update_{row['id']}"):
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
        st.info("Nenhum atendimento marcado para este dia.")

# ==========================================
# ABA 2: CENTRAL DE RETENÇÃO (CRM)
# ==========================================
with aba_crm:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_crm = pd.read_sql_query("SELECT * FROM clientes_retencao WHERE profissional = ?", conn, params=(usuario_atual,))
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
                    st.write(f"📱 {row['telefone']} | Ciclo: {row['ciclo_dias']} dias")
                    msg = f"Oi {row['nome']}! Passando para avisar que já deu o prazo da sua manutenção!"
                    link_wa = f"https://wa.me/55{row['telefone']}?text={msg.replace(' ', '%20')}"
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
        sub_aba1, sub_aba2 = st.tabs(["📲 Chamar Esta Semana", "📋 Todas as Clientes"])

        with sub_aba1:
            if chamar_semana.empty:
                st.success("🎉 Nenhuma cliente pendente para chamar esta semana!")
            else:
                for _, row in chamar_semana.reset_index().iterrows():
                    with st.container(border=True):
                        st.markdown(f"### 👤 {row['nome']}")
                        st.write(f"🔁 Ciclo: {row['ciclo_dias']} dias | Previsão: {row['proximo_atendimento'].strftime('%d/%m/%Y')}")
                        msg = f"Oi {row['nome']}! Tudo bem? Passando para avisar que já deu o prazo da sua manutenção essa semana!"
                        link_wa = f"https://wa.me/55{row['telefone']}?text={msg.replace(' ', '%20')}"
                        
                        col_b1, col_b2 = st.columns(2)
                        with col_b1:
                            st.markdown(f"[💬 WhatsApp]({link_wa})")
                        with col_b2:
                            if st.button("✅ Atendido Hoje", key=f"renovar_{row['id']}"):
                                conn = sqlite3.connect("agenda_unhas_v2.db")
                                c = conn.cursor()
                                c.execute("UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?", (date.today().strftime("%Y-%m-%d"), row["id"]))
                                conn.commit()
                                conn.close()
                                st.rerun()

        with sub_aba2:
            for _, row in df_crm.iterrows():
                with st.expander(f"👤 {row['nome']} (Retorno: {row['proximo_atendimento'].strftime('%d/%m/%Y')})"):
                    st.write(f"📱 WhatsApp: {row['telefone']} | Ciclo: {row['ciclo_dias']} dias")
                    if st.button("🗑️ Excluir do CRM", key=f"del_crm_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM clientes_retencao WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()
    else:
        st.info("Nenhuma cliente cadastrada no CRM.")

# ==========================================
# ABA 3: FINANCEIRO & GANHOS (COM RELATÓRIO PDF)
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

        # Botão de Download do Documento PDF / Impressão
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
            <head>
                <meta charset="utf-8">
                <title>Relatório Financeiro - {usuario_atual}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; margin: 40px; }}
                    h1 {{ color: #C5A059; border-bottom: 2px solid #C5A059; padding-bottom: 10px; }}
                    .info {{ margin-bottom: 20px; font-size: 15px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }}
                    th {{ background-color: #F4EFEA; color: #333; }}
                    .totais {{ background-color: #F9F9F9; padding: 15px; border-radius: 8px; margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h1>💅 {titulo_atual} — Relatório Financeiro</h1>
                <div class="info">
                    <p><b>Profissional:</b> {usuario_atual}</p>
                    <p><b>Período:</b> {filtro_periodo} (Gerado em {date.today().strftime('%d/%m/%Y')})</p>
                </div>
                <div class="totais">
                    <h3>Resumo do Período</h3>
                    <p><b>Total Faturado:</b> R$ {total_ganho:.2f}</p>
                    <p><b>Total de Atendimentos:</b> {qtd_atendimentos}</p>
                    <p><b>Ticket Médio:</b> R$ {ticket_medio:.2f}</p>
                    <h4>Faturamento por Forma de Pagamento:</h4>
                    <ul>{pagto_html}</ul>
                </div>
                <h3>Detalhamento dos Atendimentos</h3>
                <table>
                    <tr>
                        <th>Data</th>
                        <th>Horário</th>
                        <th>Cliente</th>
                        <th>Serviço</th>
                        <th>Valor</th>
                        <th>Pagamento</th>
                    </tr>
                    {linhas_tabela}
                </table>
            </body>
            </html>
            """

            st.download_button(
                label="📥 Baixar Relatório em PDF / Impressão",
                data=html_documento,
                file_name=f"relatorio_financeiro_{usuario_atual}_{filtro_periodo.lower().replace(' ', '_')}.html",
                mime="text/html",
                help="Baixa o documento estilizado. Ao abrir no PC ou celular, basta clicar em Imprimir / Salvar como PDF."
            )

        st.markdown("### 💳 Faturamento por Forma de Pagamento")
        if not df_filtrado.empty:
            pagto_resumo = df_filtrado.groupby("forma_pagamento")["valor"].sum().reset_index()
            for _, r in pagto_resumo.iterrows():
                st.write(f"- **{r['forma_pagamento']}:** R$ {r['valor']:.2f}")

            st.divider()
            st.markdown("### 📋 Detalhado dos Atendimentos no Período")
            st.dataframe(df_filtrado[["data_atendimento", "horario", "nome_cliente", "servico", "valor", "forma_pagamento"]], use_container_width=True)
        else:
            st.info("Nenhum atendimento registrado neste período.")
    else:
        st.info("Nenhum dado financeiro registrado ainda.")

# ==========================================
# ABA 4: TAREFAS
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
# ABA 5: LIXEIRA
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
# ABA 6: CONFIGURAÇÕES
# ==========================================
with aba_config:
    st.subheader("⚙️ Configurações & Perfil")
    with st.form("form_config"):
        novo_titulo = st.text_input("Nome do Studio:", value=titulo_atual)
        novo_tema = st.selectbox("Tema Visual:", ["Dourado Luxo", "Clean White (Tudo Branco)", "Nude / Rosé", "Dark Elegance", "Lavanda / Soft Purple"], index=0)
        
        _, servicos_atuais_db, wa_db = get_perfil_info(usuario_atual)
        novo_wa = st.text_input("Meu WhatsApp (ex: 5554991341375):", value=wa_db)
        novos_servicos = st.text_area("Meus Serviços (um por linha):", value=servicos_atuais_db, height=120)
        
        nova_senha = st.text_input("Nova Senha (opcional):", type="password")
        repete_senha = st.text_input("Repetir Nova Senha:", type="password")

        if st.form_submit_button("Salvar Alterações"):
            if nova_senha != repete_senha:
                st.error("As senhas não conferem! Por favor, digite a mesma senha nos dois campos.")
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
                st.success("Salvo com sucesso!")
                st.rerun()

    st.divider()
    st.subheader("🛡️ Backup do Sistema")
    try:
        with open("agenda_unhas_v2.db", "rb") as f:
            st.download_button("📥 Baixar Banco de Dados (.db)", f, file_name=f"backup_studio_{date.today()}.db")
    except:
        st.error("Erro ao gerar backup.")

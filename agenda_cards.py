import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# --- BANCO DE DADOS & LIXEIRA ---
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
            status TEXT DEFAULT 'Agendado'
        )
    """
    )

    # Tabela 2: Clientes e Ciclos (CRM)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS clientes_retencao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            ciclo_dias INTEGER NOT NULL,
            ultimo_atendimento DATE NOT NULL
        )
    """
    )

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

    # Tabela 5: Configurações Editáveis
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """
    )

    # Valores padrão iniciais (se não existirem)
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('titulo_studio', 'Studio Maria Rossatto')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('subtitulo_studio', 'Sistema de Gestão & Retenção')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('whatsapp_studio', '5554991341375')")
    c.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES ('tema_estilo', 'Nude / Rosé')")

    # Auto-delete da lixeira (mais de 30 dias)
    limite_30_dias = str(date.today() - timedelta(days=30))
    c.execute("DELETE FROM lixeira WHERE data_exclusao < ?", (limite_30_dias,))

    conn.commit()
    conn.close()


init_db()

# --- FUNÇÃO PARA BUSCAR CONFIGURAÇÕES ---
def get_config(chave):
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()
    c.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

# Configuração da página
st.set_page_config(
    page_title=get_config("titulo_studio"),
    layout="wide",
    page_icon="💅",
)

# --- APLICAÇÃO DE TEMAS DINÂMICOS (CSS) ---
tema_atual = get_config("tema_estilo")

estilos_css = {
    "Nude / Rosé": """
        <style>
            .stApp { background-color: #FFF9F9; color: #4A3E3D; }
            .stSidebar { background-color: #FFF0F2; }
            .stButton>button { background-color: #E8A5A5 !important; color: white !important; border-radius: 8px !important; border: none !important; }
            div[data-testid="stMetricValue"] { color: #D87070 !important; }
        </style>
    """,
    "Dark Elegance": """
        <style>
            .stApp { background-color: #121212; color: #E0E0E0; }
            .stSidebar { background-color: #1E1E1E; }
            .stButton>button { background-color: #BB86FC !important; color: #121212 !important; border-radius: 8px !important; font-weight: bold !important; }
            div[data-testid="stMetricValue"] { color: #BB86FC !important; }
        </style>
    """,
    "Lavanda / Soft Purple": """
        <style>
            .stApp { background-color: #F8F7FF; color: #3A354A; }
            .stSidebar { background-color: #EDE9FE; }
            .stButton>button { background-color: #8B5CF6 !important; color: white !important; border-radius: 8px !important; }
            div[data-testid="stMetricValue"] { color: #7C3AED !important; }
        </style>
    """,
    "Nude / Minimalista": """
        <style>
            .stApp { background-color: #FAF8F5; color: #3D3B37; }
            .stSidebar { background-color: #F0ECE1; }
            .stButton>button { background-color: #C5A059 !important; color: white !important; border-radius: 8px !important; }
            div[data-testid="stMetricValue"] { color: #A37E38 !important; }
        </style>
    """,
}

st.markdown(estilos_css.get(tema_atual, estilos_css["Nude / Rosé"]), unsafe_allow_html=True)

# --- BLOQUEIO ANTI-TRADUÇÃO ---
st.markdown(
    '<meta name="google" content="notranslate">', unsafe_allow_html=True
)

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("logo.JPG", use_container_width=True)

    tipo_cadastro = st.radio(
        "Selecione a ação:",
        [
            "📅 Novo Agendamento (Horário)",
            "👤 Cadastrar Cliente (CRM)",
            "📝 Nova Tarefa / Anotação",
        ],
    )

    st.divider()

    if tipo_cadastro == "📅 Novo Agendamento (Horário)":
        st.header("➕ Agendar Horário")
        with st.form("form_rapido", clear_on_submit=True):
            nome_cliente = st.text_input("Nome da Cliente*")
            telefone = st.text_input("WhatsApp", placeholder="54991341375")
            servico = st.selectbox(
                "Serviço*",
                [
                    "Mão tradicional",
                    "Pé tradicional",
                    "Blindagem",
                    "Esmaltação em gel",
                    "Banho de gel",
                    "Alongamento",
                    "Manutenção",
                    "Pacote de mão",
                ],
            )
            data_atendimento = st.date_input(
                "Data*", value=date.today(), format="DD/MM/YYYY"
            )
            horario = st.time_input(
                "Horário*", value=datetime.strptime("14:00", "%H:%M").time()
            )

            salvar = st.form_submit_button("Salvar Horário")

            if salvar:
                if not nome_cliente:
                    st.error("Preencha o nome da cliente!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    c.execute(
                        """INSERT INTO agendamentos (nome_cliente, telefone, servico, data_atendimento, horario) 
                                   VALUES (?, ?, ?, ?, ?)""",
                        (
                            nome_cliente,
                            telefone,
                            servico,
                            str(data_atendimento),
                            str(horario)[:5],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Horário marcado!")
                    st.rerun()

    elif tipo_cadastro == "👤 Cadastrar Cliente (CRM)":
        st.header("➕ Cadastrar p/ CRM")
        with st.form("form_cliente_crm", clear_on_submit=True):
            nome = st.text_input("Nome da Cliente*")
            telefone = st.text_input("WhatsApp*", placeholder="54991341375")
            ciclo_dias = st.selectbox(
                "Ciclo de Retorno (Dias)*",
                [15, 21, 25, 30],
                index=1,
            )
            ultimo_atendimento = st.date_input(
                "Último Atendimento*", value=date.today(), format="DD/MM/YYYY"
            )

            salvar_crm = st.form_submit_button("Salvar no CRM")

            if salvar_crm:
                tel_clean = "".join(filter(str.isdigit, str(telefone)))
                if not nome or not tel_clean:
                    st.error("Preencha o Nome e um WhatsApp válido!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    data_iso = ultimo_atendimento.strftime("%Y-%m-%d")

                    c.execute(
                        "SELECT id FROM clientes_retencao WHERE telefone = ?",
                        (tel_clean,),
                    )
                    existente = c.fetchone()

                    if existente:
                        c.execute(
                            """UPDATE clientes_retencao 
                               SET nome = ?, ciclo_dias = ?, ultimo_atendimento = ? 
                               WHERE id = ?""",
                            (nome, ciclo_dias, data_iso, existente[0]),
                        )
                        st.success(f"Cadastro de {nome} atualizado no CRM!")
                    else:
                        c.execute(
                            """INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento) 
                               VALUES (?, ?, ?, ?)""",
                            (nome, tel_clean, ciclo_dias, data_iso),
                        )
                        st.success(f"Cliente {nome} salva no CRM!")

                    conn.commit()
                    conn.close()
                    st.rerun()

    else:
        st.header("➕ Nova Anotação / Tarefa")
        with st.form("form_tarefa", clear_on_submit=True):
            titulo_t = st.text_input("Título / Lembrete*")
            desc_t = st.text_area("Detalhes (Opcional)", placeholder="Ex: Comprar acetona e lixas novas")
            prio_t = st.selectbox("Prioridade", ["Baixa", "Média", "Alta"], index=1)

            salvar_t = st.form_submit_button("Salvar Tarefa")

            if salvar_t:
                if not titulo_t:
                    st.error("Preencha o título da tarefa!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    c.execute(
                        """INSERT INTO tarefas (titulo, descricao, prioridade, data_criacao)
                                   VALUES (?, ?, ?, ?)""",
                        (titulo_t, desc_t, prio_t, str(date.today())),
                    )
                    conn.commit()
                    conn.close()
                    st.success("Anotação salva!")
                    st.rerun()

# --- PAINEL PRINCIPAL (TÍTULO DINÂMICO) ---
titulo_atual = get_config("titulo_studio")
subtitulo_atual = get_config("subtitulo_studio")

st.title(f"💅 {titulo_atual} — {subtitulo_atual}")

aba_agenda, aba_crm, aba_tarefas, aba_lixeira, aba_config = st.tabs(
    [
        "📅 Agenda de Horários",
        "🎯 Central de Retenção (CRM)",
        "📝 Minhas Tarefas",
        "🗑️ Lixeira (30 dias)",
        "⚙️ Configurações & Estilo",
    ]
)

# ==========================================
# ABA 1: AGENDA DE HORÁRIOS
# ==========================================
with aba_agenda:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_todos = pd.read_sql_query("SELECT * FROM agendamentos", conn)
    conn.close()

    eventos_calendario = []
    for _, row in df_todos.iterrows():
        eventos_calendario.append(
            {
                "title": f"⏰ {row['horario']} - {row['nome_cliente']} ({row['servico']})",
                "start": f"{row['data_atendimento']}T{row['horario']}:00",
                "backgroundColor": (
                    "#FF4B4B" if row["status"] == "Agendado" else "#25D366"
                ),
                "borderColor": "#ffffff",
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
        "buttonText": {
            "today": "Hoje",
            "month": "Mês",
            "week": "Semana",
            "list": "Lista",
        },
    }

    st.markdown("### 📅 Visão Geral de Atendimentos")
    state = calendar(
        events=eventos_calendario,
        options=opcoes_calendario,
        key="cal_studio",
    )

    st.divider()

    data_selecionada = st.date_input(
        "📆 Ver detalhes do dia:", value=date.today(), format="DD/MM/YYYY"
    )

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df = pd.read_sql_query(
        "SELECT * FROM agendamentos WHERE data_atendimento = ? ORDER BY horario ASC",
        conn,
        params=(str(data_selecionada),),
    )
    conn.close()

    st.markdown(
        f"### 📋 Horários de **{data_selecionada.strftime('%d/%m/%Y')}**"
    )

    if not df.empty:
        texto_resumo = f"💅 *Resumo de Atendimentos ({data_selecionada.strftime('%d/%m/%Y')}):*\n\n"
        for _, row in df.iterrows():
            texto_resumo += f"⏰ *{row['horario']}* — {row['nome_cliente']} ({row['servico']})\n"

        numero_whatsapp = get_config("whatsapp_studio")
        link_resumo = f"https://wa.me/{numero_whatsapp}?text={texto_resumo.replace(' ', '%20').replace('\n', '%0A')}"

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

                    if row["telefone"]:
                        st.write(f"📱 **WhatsApp:** {row['telefone']}")
                        tel_digits = "".join(
                            filter(str.isdigit, str(row["telefone"]))
                        )
                        if tel_digits:
                            msg = f"Olá {row['nome_cliente']}! Confirmado seu horário para {row['servico']} hoje às {row['horario']}?"
                            link_wa = f"https://wa.me/55{tel_digits}?text={msg.replace(' ', '%20')}"
                            st.markdown(
                                f"[💬 Mandar Lembrete no WhatsApp]({link_wa})"
                            )

                    status_atual = row["status"]
                    novo_status = st.selectbox(
                        "Status:",
                        ["Agendado", "Confirmado", "Realizado", "Cancelado"],
                        index=[
                            "Agendado",
                            "Confirmado",
                            "Realizado",
                            "Cancelado",
                        ].index(status_atual),
                        key=f"status_select_{row['id']}",
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(
                            "Atualizar Status", key=f"btn_update_{row['id']}"
                        ):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            c.execute(
                                "UPDATE agendamentos SET status = ? WHERE id = ?",
                                (novo_status, row["id"]),
                            )
                            conn.commit()
                            conn.close()
                            st.rerun()

                    with col_btn2:
                        if st.button(
                            "🗑️ Mover p/ Lixeira", key=f"btn_del_{row['id']}"
                        ):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            info_str = f"Agendamento: {row['nome_cliente']} | Serviço: {row['servico']} | Data: {row['data_atendimento']} {row['horario']} | Tel: {row['telefone']}"
                            c.execute(
                                "INSERT INTO lixeira (tipo_item, dados_item, data_exclusao) VALUES (?, ?, ?)",
                                ("agendamento", info_str, str(date.today())),
                            )
                            c.execute(
                                "DELETE FROM agendamentos WHERE id = ?",
                                (row["id"],),
                            )
                            conn.commit()
                            conn.close()
                            st.success("Movido para a Lixeira!")
                            st.rerun()

                    st.divider()
                    st.markdown("  **Lançar/Atualizar no CRM de Retenção:**")
                    col_crm1, col_crm2 = st.columns([1, 1])
                    with col_crm1:
                        ciclo_escolhido = st.selectbox(
                            "Ciclo de Retorno:",
                            [15, 21, 25, 30],
                            index=1,
                            key=f"ciclo_card_{row['id']}",
                        )
                    with col_crm2:
                        st.write("")
                        st.write("")
                        if st.button("🔄 Salvar no CRM", key=f"btn_crm_auto_{row['id']}"):
                            if not row["telefone"]:
                                st.error("Cadastre um WhatsApp para vincular ao CRM!")
                            else:
                                tel_clean = "".join(filter(str.isdigit, str(row["telefone"])))
                                conn = sqlite3.connect("agenda_unhas_v2.db")
                                c = conn.cursor()
                                c.execute("SELECT id FROM clientes_retencao WHERE telefone = ?", (tel_clean,))
                                cliente_existente = c.fetchone()
                                data_atend_iso = str(row["data_atendimento"])

                                if cliente_existente:
                                    c.execute(
                                        """UPDATE clientes_retencao 
                                           SET nome = ?, ultimo_atendimento = ?, ciclo_dias = ? 
                                           WHERE id = ?""",
                                        (row["nome_cliente"], data_atend_iso, ciclo_escolhido, cliente_existente[0]),
                                    )
                                    st.success(f"{row['nome_cliente']} atualizada no CRM!")
                                else:
                                    c.execute(
                                        """INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento)
                                           VALUES (?, ?, ?, ?)""",
                                        (row["nome_cliente"], tel_clean, ciclo_escolhido, data_atend_iso),
                                    )
                                    st.success(f"{row['nome_cliente']} cadastrada no CRM!")

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
    df_crm = pd.read_sql_query("SELECT * FROM clientes_retencao", conn)
    conn.close()

    if not df_crm.empty:
        df_crm["ultimo_atendimento"] = pd.to_datetime(
            df_crm["ultimo_atendimento"], errors="coerce"
        ).dt.date

        df_crm["proximo_atendimento"] = df_crm.apply(
            lambda r: r["ultimo_atendimento"]
            + timedelta(days=int(r["ciclo_dias"])),
            axis=1,
        )
        df_crm["dias_para_retorno"] = df_crm["proximo_atendimento"].apply(
            lambda d: (d - date.today()).days
        )

        df_crm = df_crm.sort_values(by="dias_para_retorno", ascending=True)

        termo_busca = st.text_input(
            "🔍 Pesquisar Cliente no CRM:",
            placeholder="Digite o nome da cliente ou WhatsApp e pressione Enter...",
        )

        if termo_busca:
            resultados_busca = df_crm[
                df_crm["nome"].str.contains(termo_busca, case=False, na=False)
                | df_crm["telefone"].str.contains(termo_busca, case=False, na=False)
            ]

            st.markdown(f"### 🔎 Resultado da busca para: *'{termo_busca}'*")
            if resultados_busca.empty:
                st.warning("Nenhuma cliente encontrada com esse nome ou número.")
            else:
                for _, row in resultados_busca.iterrows():
                    dias_texto = (
                        f"⚠️ Atrasada há {abs(row['dias_para_retorno'])} dias"
                        if row["dias_para_retorno"] < 0
                        else (
                            "⏰ Vence HOJE"
                            if row["dias_para_retorno"] == 0
                            else f"⏳ Vence em {row['dias_para_retorno']} dias"
                        )
                    )
                    with st.container(border=True):
                        st.markdown(f"### 👤 {row['nome']} — {dias_texto}")
                        st.write(f"📱 **WhatsApp:** {row['telefone']}")
                        st.write(f"🔁 **Ciclo:** A cada {row['ciclo_dias']} dias")
                        st.write(f"🗓️ **Último Atendimento:** {row['ultimo_atendimento'].strftime('%d/%m/%Y')}")
                        st.write(f"🎯 **Previsão de Retorno:** {row['proximo_atendimento'].strftime('%d/%m/%Y')}")

                        msg = (
                            f"Oi {row['nome']}! Tudo bem? 💅 "
                            f"Passando para avisar que já deu o prazo da sua manutenção essa semana! "
                            f"Como está sua agenda para a gente encaixar o seu horário no planner?"
                        )
                        link_wa = f"https://wa.me/55{row['telefone']}?text={msg.replace(' ', '%20')}"

                        col_sb1, col_sb2 = st.columns(2)
                        with col_sb1:
                            st.markdown(
                                f"""
                                <a href="{link_wa}" target="_blank">
                                    <button style="background-color: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                                        💬 Chamada no WhatsApp
                                    </button>
                                </a>
                            """,
                                unsafe_allow_html=True,
                            )
                        with col_sb2:
                            if st.button("🔄 Renovou Hoje", key=f"renovar_busca_{row['id']}"):
                                conn = sqlite3.connect("agenda_unhas_v2.db")
                                c = conn.cursor()
                                data_hoje = date.today().strftime("%Y-%m-%d")
                                c.execute(
                                    "UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?",
                                    (data_hoje, row["id"]),
                                )
                                conn.commit()
                                conn.close()
                                st.rerun()

            st.divider()

        hoje = date.today()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)

        chamar_semana = df_crm[(df_crm["proximo_atendimento"] <= fim_semana)]

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(" Total Clientes no CRM", len(df_crm))
        col_m2.metric(
            "📲 Chamar Esta Semana",
            len(chamar_semana),
            delta=f"{len(chamar_semana)} pendentes",
            delta_color="inverse",
        )
        col_m3.metric("📅 Hoje", hoje.strftime("%d/%m/%Y"))

        st.divider()

        sub_aba1, sub_aba2 = st.tabs(
            ["📲 Chamar Esta Semana", "📋 Todas as Clientes & Próximos Vencimentos"]
        )

        with sub_aba1:
            st.subheader("🎯 Clientes para chamar esta semana")
            if chamar_semana.empty:
                st.success("🎉 Nenhuma cliente pendente para chamar esta semana!")
            else:
                cols_crm = st.columns(2)
                for idx, row in chamar_semana.reset_index().iterrows():
                    col_curr = cols_crm[idx % 2]
                    with col_curr:
                        with st.container(border=True):
                            st.markdown(f"### 👤 {row['nome']}")
                            st.write(
                                f"🔁 **Ciclo:** A cada {row['ciclo_dias']} dias"
                            )
                            st.write(
                                f"📅 **Último atendimento:** {row['ultimo_atendimento'].strftime('%d/%m/%Y')}"
                            )
                            st.write(
                                f"🎯 **Previsão de Retorno:** {row['proximo_atendimento'].strftime('%d/%m/%Y')}"
                            )

                            if row["dias_para_retorno"] < 0:
                                st.error(
                                    f"⚠️ Atrasada há {abs(row['dias_para_retorno'])} dia(s)!"
                                )
                            elif row["dias_para_retorno"] == 0:
                                st.warning("⏰ Vence HOJE!")
                            else:
                                st.info(
                                    f"⏳ Vence em {row['dias_para_retorno']} dia(s)"
                                )

                            msg = (
                                f"Oi {row['nome']}! Tudo bem? 💅 "
                                f"Passando para avisar que já deu o prazo da sua manutenção essa semana! "
                                f"Como está sua agenda para a gente encaixar o seu horário no planner?"
                            )
                            link_wa = f"https://wa.me/55{row['telefone']}?text={msg.replace(' ', '%20')}"

                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                st.markdown(
                                    f"""
                                    <a href="{link_wa}" target="_blank">
                                        <button style="background-color: #25D366; color: white; padding: 8px 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                                            💬 WhatsApp
                                        </button>
                                    </a>
                                """,
                                    unsafe_allow_html=True,
                                )
                            with col_b2:
                                if st.button(
                                    "✅ Atendido Hoje", key=f"renovar_{row['id']}"
                                ):
                                    conn = sqlite3.connect("agenda_unhas_v2.db")
                                    c = conn.cursor()
                                    data_hoje = date.today().strftime("%Y-%m-%d")
                                    c.execute(
                                        "UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?",
                                        (data_hoje, row["id"]),
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.rerun()

        with sub_aba2:
            st.subheader("📋 Banco Geral de Clientes")
            for idx, row in df_crm.iterrows():
                dias_texto = (
                    f"⚠️ Atrasada há {abs(row['dias_para_retorno'])} dias"
                    if row["dias_para_retorno"] < 0
                    else (
                        "⏰ Vence HOJE"
                        if row["dias_para_retorno"] == 0
                        else f"⏳ Vence em {row['dias_para_retorno']} dias"
                    )
                )

                with st.expander(
                    f"👤 {row['nome']} — {dias_texto} (Previsão: {row['proximo_atendimento'].strftime('%d/%m/%Y')})"
                ):
                    st.write(f"📱 **WhatsApp:** {row['telefone']}")
                    st.write(f"🔁 **Ciclo:** {row['ciclo_dias']} dias")
                    st.write(
                        f"🗓️ **Último Atendimento:** {row['ultimo_atendimento'].strftime('%d/%m/%Y')}"
                    )

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        if st.button(
                            "🔄 Renovou Atendimento Hoje",
                            key=f"renovar_geral_{row['id']}",
                        ):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            data_hoje = date.today().strftime("%Y-%m-%d")
                            c.execute(
                                "UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?",
                                (data_hoje, row["id"]),
                            )
                            conn.commit()
                            conn.close()
                            st.rerun()

                    with col_e2:
                        if st.button(
                            "🗑️ Mover p/ Lixeira", key=f"del_{row['id']}"
                        ):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            info_str = f"Cliente CRM: {row['nome']} | Tel: {row['telefone']} | Ciclo: {row['ciclo_dias']} dias | Último Atend: {row['ultimo_atendimento']}"
                            c.execute(
                                "INSERT INTO lixeira (tipo_item, dados_item, data_exclusao) VALUES (?, ?, ?)",
                                ("crm", info_str, str(date.today())),
                            )
                            c.execute(
                                "DELETE FROM clientes_retencao WHERE id = ?",
                                (row["id"],),
                            )
                            conn.commit()
                            conn.close()
                            st.success("Movida para a Lixeira!")
                            st.rerun()

    else:
        st.info(
            "Nenhuma cliente cadastrada no CRM ainda. Use a barra lateral para cadastrar!"
        )

# ==========================================
# ABA 3: MINHAS TAREFAS / ANOTAÇÕES
# ==========================================
with aba_tarefas:
    st.subheader(f"📝 Bloco de Notas & Tarefas do {titulo_atual}")

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_t = pd.read_sql_query("SELECT * FROM tarefas ORDER BY concluido ASC, id DESC", conn)
    conn.close()

    if df_t.empty:
        st.info("Nenhuma tarefa ou anotação cadastrada. Use a barra lateral para criar a primeira!")
    else:
        for idx, row in df_t.iterrows():
            with st.container(border=True):
                col_t1, col_t2, col_t3 = st.columns([3, 1, 1])

                with col_t1:
                    status_prefix = "✅ " if row["concluido"] else "📌 "
                    st.markdown(f"### {status_prefix} {row['titulo']}")
                    if row["descricao"]:
                        st.write(f"**Detalhes:** {row['descricao']}")
                    st.caption(f"Criado em: {row['data_criacao']}")

                with col_t2:
                    prio_color = (
                        "🔴 Alta"
                        if row["prioridade"] == "Alta"
                        else ("🟡 Média" if row["prioridade"] == "Média" else "🟢 Baixa")
                    )
                    st.write(f"**Prioridade:** {prio_color}")

                with col_t3:
                    if not row["concluido"]:
                        if st.button("✔ Concluir", key=f"done_t_{row['id']}"):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            c.execute("UPDATE tarefas SET concluido = 1 WHERE id = ?", (row["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()

                    if st.button("🗑️ Mover p/ Lixeira", key=f"del_t_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        info_str = f"Tarefa: {row['titulo']} | Detalhes: {row['descricao']} | Prioridade: {row['prioridade']}"
                        c.execute(
                            "INSERT INTO lixeira (tipo_item, dados_item, data_exclusao) VALUES (?, ?, ?)",
                            ("tarefa", info_str, str(date.today())),
                        )
                        c.execute("DELETE FROM tarefas WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.success("Movido para a Lixeira!")
                        st.rerun()

# ==========================================
# ABA 4: LIXEIRA INTELIGENTE (30 DIAS)
# ==========================================
with aba_lixeira:
    st.subheader("🗑️ Lixeira (Itens excluídos são apagados permanentemente após 30 dias)")

    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_lix = pd.read_sql_query("SELECT * FROM lixeira ORDER BY id DESC", conn)
    conn.close()

    if df_lix.empty:
        st.success("🎉 A lixeira está limpa! Nenhum item excluído no momento.")
    else:
        for idx, row in df_lix.iterrows():
            with st.container(border=True):
                col_lx1, col_lx2 = st.columns([4, 1])

                with col_lx1:
                    data_exc = pd.to_datetime(row["data_exclusao"]).date()
                    dias_na_lixeira = (date.today() - data_exc).days
                    dias_restantes = 30 - dias_na_lixeira

                    st.markdown(f"**Tipo:** `{row['tipo_item'].upper()}`")
                    st.write(f"📄 **Conteúdo:** {row['dados_item']}")
                    st.caption(
                        f"Excluído em: {data_exc.strftime('%d/%m/%Y')} | ⏳ Será apagado em {dias_restantes} dia(s)"
                    )

                with col_lx2:
                    if st.button("🗑️ Excluir Agora", key=f"perm_del_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        c.execute("DELETE FROM lixeira WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.success("Apagado permanentemente!")
                        st.rerun()

# ==========================================
# ABA 5: CONFIGURAÇÕES & TEMA VISUAL
# ==========================================
with aba_config:
    st.subheader("⚙️ Configurações de Nome, Contato e Aparência do Studio")
    st.write("Altere as informações e as cores do aplicativo a qualquer momento.")

    with st.form("form_config_studio"):
        novo_titulo = st.text_input("Nome do Studio / Empresa:", value=titulo_atual)
        novo_subtitulo = st.text_input("Subtítulo / Descrição:", value=subtitulo_atual)
        novo_wa_padrao = st.text_input("WhatsApp Principal (para receber a lista do dia):", value=get_config("whatsapp_studio"))

        # SELETOR DE TEMAS VISUAIS
        temas_disponiveis = ["Nude / Rosé", "Dark Elegance", "Lavanda / Soft Purple", "Nude / Minimalista"]
        index_tema = temas_disponiveis.index(tema_atual) if tema_atual in temas_disponiveis else 0
        novo_tema = st.selectbox("🎨 Tema Visual de Cores:", temas_disponiveis, index=index_tema)

        btn_salvar_config = st.form_submit_button("💾 Salvar Configurações e Cores")

        if btn_salvar_config:
            conn = sqlite3.connect("agenda_unhas_v2.db")
            c = conn.cursor()
            c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'titulo_studio'", (novo_titulo,))
            c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'subtitulo_studio'", (novo_subtitulo,))
            c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'whatsapp_studio'", ("".join(filter(str.isdigit, novo_wa_padrao)),))
            c.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'tema_estilo'", (novo_tema,))
            conn.commit()
            conn.close()
            st.success("Configurações e cores salvas com sucesso!")
            st.rerun()
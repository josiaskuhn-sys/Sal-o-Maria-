import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# Configuração da página
st.set_page_config(
    page_title="Studio de Beleza - Agenda", layout="wide", page_icon="💅"
)

# --- BLOQUEIO ANTI-TRADUÇÃO ---
st.markdown(
    '<meta name="google" content="notranslate">', unsafe_allow_html=True
)


# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()
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
    conn.commit()
    conn.close()


init_db()

# --- BARRA LATERAL (FOTO E NOVO AGENDAMENTO) ---
with st.sidebar:
    st.image("logo.JPG", use_container_width=True)
    st.header("➕ Novo Agendamento")

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

# --- PAINEL PRINCIPAL ---
st.title("💅 Agenda studio Maria Rossatto")

# --- BUSCA TODOS OS AGENDAMENTOS PARA O CALENDÁRIO ---
conn = sqlite3.connect("agenda_unhas_v2.db")
df_todos = pd.read_sql_query("SELECT * FROM agendamentos", conn)
conn.close()

# Converte os agendamentos no formato de eventos que o calendário entende
eventos_calendario = []
for _, row in df_todos.iterrows():
    eventos_calendario.append(
        {
            "title": f"⏰ {row['horario']} - {row['nome_cliente']} ({row['servico']})",
            "start": f"{row['data_atendimento']}T{row['horario']}:00",
            "backgroundColor": "#FF4B4B"
            if row["status"] == "Agendado"
            else "#25D366",
            "borderColor": "#ffffff",
        }
    )

# Configurações do Calendário Interativo
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

# Renderiza o Calendário Visual
st.markdown("### 📅 Visão Geral de Atendimentos")
state = calendar(events=eventos_calendario, options=opcoes_calendario, key="cal_studio")

st.divider()

# --- FILTRO POR DIA SELECIONADO ---
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

st.markdown(f"### 📋 Horários de **{data_selecionada.strftime('%d/%m/%Y')}**")

# --- BOTÃO DE RESUMO NO WHATSAPP ---
if not df.empty:
    texto_resumo = f"💅 *Resumo de Atendimentos ({data_selecionada.strftime('%d/%m/%Y')}):*\n\n"
    for _, row in df.iterrows():
        texto_resumo += f"⏰ *{row['horario']}* — {row['nome_cliente']} ({row['servico']})\n"

    numero_whatsapp = "5554991341375"

    link_resumo = f"https://wa.me/{numero_whatsapp}?text={texto_resumo.replace(' ', '%20').replace('\n', '%0A')}"

    st.markdown(
        f"""
        <a href="{link_resumo}" target="_blank" style="text-decoration: none;">
            <button style="
                background-color: #25D366;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                cursor: pointer;
                margin-bottom: 20px;">
                📲 Enviar Lista de Hoje no Meu WhatsApp
            </button>
        </a>
    """,
        unsafe_allow_html=True,
    )
else:
    st.info("Nenhum atendimento marcado para este dia.")

# --- CARDS DOS AGENDAMENTOS ---
if not df.empty:
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
                    if st.button("🗑️ Excluir", key=f"btn_del_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        c.execute(
                            "DELETE FROM agendamentos WHERE id = ?", (row["id"],)
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

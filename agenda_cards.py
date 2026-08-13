import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Agenda de Atendimentos", layout="wide", page_icon="💅"
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

st.title("💅 Agenda studio Maria Rossatto")

# Barra lateral para cadastro rápido de novo horário
with st.sidebar:
    st.image("logo.JPG", use_container_width=True)
    st.header("➕ Novo Agendamento")
    with st.form("form_rapido", clear_on_submit=True):
        nome_cliente = st.text_input("Nome da Cliente*")
        telefone = st.text_input("WhatsApp", placeholder="54999999999")
        servico = st.selectbox(
            "Serviço*",
            [
                "Aplicação de Gel",
                "Manutenção",
                "Esmaltação em Gel",
                "Pé e Mão",
                "Retoque",
            ],
        )
        data_atendimento = st.date_input("Data*", value=date.today())
        horario = st.time_input("Horário*", value=datetime.strptime("14:00", "%H:%M").time())

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

# --- FILTRO POR DIA NO CORPO PRINCIPAL ---
data_selecionada = st.date_input(
    "📆 Escolha o dia para visualizar:", value=date.today()
)

conn = sqlite3.connect("agenda_unhas_v2.db")
df = pd.read_sql_query(
    "SELECT * FROM agendamentos WHERE data_atendimento = ? ORDER BY horario ASC",
    conn,
    params=(str(data_selecionada),),
)
conn.close()

st.markdown(f"### 📋 Horários de **{data_selecionada.strftime('%d/%m/%Y')}**")

if df.empty:
    st.info("Nenhum atendimento marcado para este dia.")
else:
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
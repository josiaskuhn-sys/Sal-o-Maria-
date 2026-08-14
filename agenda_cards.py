import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
from streamlit_calendar import calendar

# Configuração da página
st.set_page_config(
    page_title="Studio Maria Rossatto - Agenda & CRM",
    layout="wide",
    page_icon="💅",
)

# --- BLOQUEIO ANTI-TRADUÇÃO ---
st.markdown(
    '<meta name="google" content="notranslate">', unsafe_allow_html=True
)


# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect("agenda_unhas_v2.db")
    c = conn.cursor()

    # Tabela 1: Agendamentos por Horário (Agenda Antiga)
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

    # Tabela 2: Clientes e Ciclos (CRM Novo)
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

    conn.commit()
    conn.close()


init_db()

# --- BARRA LATERAL (FOTO E NAVEGAÇÃO DE CADASTRO) ---
with st.sidebar:
    st.image("logo.JPG", use_container_width=True)

    tipo_cadastro = st.radio(
        "Selecione a ação:",
        ["📅 Novo Agendamento (Horário)", "👤 Cadastrar Cliente (CRM)"],
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

    else:
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
                if not nome or not telefone:
                    st.error("Preencha o Nome e o WhatsApp!")
                else:
                    conn = sqlite3.connect("agenda_unhas_v2.db")
                    c = conn.cursor()
                    tel_clean = "".join(filter(str.isdigit, str(telefone)))
                    c.execute(
                        """INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento) 
                                   VALUES (?, ?, ?, ?)""",
                        (nome, tel_clean, ciclo_dias, str(ultimo_atendimento)),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Cliente {nome} salva no CRM!")
                    st.rerun()

# --- PAINEL PRINCIPAL COM ABAS ---
st.title("💅 Studio Maria Rossatto — Sistema de Gestão")

aba_agenda, aba_crm = st.tabs(
    ["📅 Agenda de Horários", "🎯 Central de Retenção (CRM)"]
)

# ==========================================
# ABA 1: AGENDA COMPLETA (CÓDIGO ORIGINAL)
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

        numero_whatsapp = "5554991341375"
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
                            "🗑️ Excluir", key=f"btn_del_{row['id']}"
                        ):
                            conn = sqlite3.connect("agenda_unhas_v2.db")
                            c = conn.cursor()
                            c.execute(
                                "DELETE FROM agendamentos WHERE id = ?",
                                (row["id"],),
                            )
                            conn.commit()
                            conn.close()
                            st.rerun()
    else:
        st.info("Nenhum atendimento marcado para este dia.")

# ==========================================
# ABA 2: CENTRAL DE RETENÇÃO (CRM NOVO)
# ==========================================
with aba_crm:
    conn = sqlite3.connect("agenda_unhas_v2.db")
    df_crm = pd.read_sql_query("SELECT * FROM clientes_retencao", conn)
    conn.close()

    if not df_crm.empty:
        df_crm["ultimo_atendimento"] = pd.to_datetime(
            df_crm["ultimo_atendimento"]
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
                                c.execute(
                                    "UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?",
                                    (str(date.today()), row["id"]),
                                )
                                conn.commit()
                                conn.close()
                                st.rerun()
    else:
        st.info(
            "Nenhuma cliente cadastrada no CRM ainda. Use a barra lateral para cadastrar!"
        )
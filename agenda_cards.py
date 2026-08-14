import sqlite3
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Studio Maria Rossatto - Controle de Retenção",
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

# --- BARRA LATERAL (CADASTRO DE CLIENTES) ---
with st.sidebar:
    st.image("logo.JPG", use_container_width=True)
    st.header("➕ Cadastrar / Atualizar Cliente")

    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome da Cliente*")
        telefone = st.text_input("WhatsApp*", placeholder="54991341375")
        ciclo_dias = st.selectbox(
            "Ciclo de Retorno (Dias)*",
            [15, 21, 25, 30],
            index=1,  # Padrão em 21 dias
            help="De quanto em quanto tempo ela costuma fazer manutenção?",
        )
        ultimo_atendimento = st.date_input(
            "Último Atendimento*", value=date.today(), format="DD/MM/YYYY"
        )

        salvar = st.form_submit_button("Salvar Cliente")

        if salvar:
            if not nome or not telefone:
                st.error("Preencha o Nome e o WhatsApp!")
            else:
                conn = sqlite3.connect("agenda_unhas_v2.db")
                c = conn.cursor()
                # Remove caracteres não numéricos do telefone
                tel_clean = "".join(filter(str.isdigit, str(telefone)))
                c.execute(
                    """INSERT INTO clientes_retencao (nome, telefone, ciclo_dias, ultimo_atendimento) 
                               VALUES (?, ?, ?, ?)""",
                    (nome, tel_clean, ciclo_dias, str(ultimo_atendimento)),
                )
                conn.commit()
                conn.close()
                st.success(f"Cliente {nome} salva com sucesso!")
                st.rerun()

# --- PAINEL PRINCIPAL ---
st.title("💅 Studio Maria Rossatto — Central de Retenção")
st.markdown(
    "Gerenciador de ciclos de retorno para contato e agendamento semanal."
)

# --- BUSCA TODAS AS CLIENTES ---
conn = sqlite3.connect("agenda_unhas_v2.db")
df = pd.read_sql_query("SELECT * FROM clientes_retencao", conn)
conn.close()

if not df.empty:
    df["ultimo_atendimento"] = pd.to_datetime(df["ultimo_atendimento"]).dt.date

    # Calcula a próxima data e quantos dias faltam
    df["proximo_atendimento"] = df.apply(
        lambda r: r["ultimo_atendimento"] + timedelta(days=int(r["ciclo_dias"])),
        axis=1,
    )
    df["dias_para_retorno"] = df["proximo_atendimento"].apply(
        lambda d: (d - date.today()).days
    )

    # Ordena: Quem precisa ser chamada primeiro fica no topo
    df = df.sort_values(by="dias_para_retorno", ascending=True)

    # Métricas rápidas no topo
    col_m1, col_m2, col_m3 = st.columns(3)
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    chamar_semana = df[
        (df["proximo_atendimento"] <= fim_semana)
    ]

    col_m1.metric(" Total de Clientes", len(df))
    col_m2.metric(
        "📲 Chamar Esta Semana",
        len(chamar_semana),
        delta=f"{len(chamar_semana)} pendentes",
        delta_color="inverse",
    )
    col_m3.metric(
        "📅 Hoje", hoje.strftime("%d/%m/%Y")
    )

    st.divider()

    # --- ABAS DE VISUALIZAÇÃO ---
    aba1, aba2 = st.tabs(["📲 Chamar Esta Semana", "📋 Todas as Clientes"])

    # --- ABA 1: QUEM CHAMAR NA SEMANA ---
    with aba1:
        st.subheader("🎯 Clientes que precisam de contato esta semana")

        if chamar_semana.empty:
            st.success("🎉 Nenhuma cliente pendente para chamar esta semana!")
        else:
            cols = st.columns(2)
            for idx, row in chamar_semana.reset_index().iterrows():
                col_atual = cols[idx % 2]
                with col_atual:
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

                        # Alerta de status
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

                        # Mensagem personalizada pro Whats
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
                                st.success("Ciclo renovado com sucesso!")
                                st.rerun()

    # --- ABA 2: LISTA COMPLETA & EDIÇÃO ---
    with aba2:
        st.subheader("📋 Banco Geral de Clientes")

        for idx, row in df.iterrows():
            with st.expander(
                f"👤 {row['nome']} — Ciclo de {row['ciclo_dias']} dias (Próximo: {row['proximo_atendimento'].strftime('%d/%m/%Y')})"
            ):
                st.write(f"📱 **WhatsApp:** {row['telefone']}")
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
                        c.execute(
                            "UPDATE clientes_retencao SET ultimo_atendimento = ? WHERE id = ?",
                            (str(date.today()), row["id"]),
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

                with col_e2:
                    if st.button("🗑️ Excluir Cliente", key=f"del_{row['id']}"):
                        conn = sqlite3.connect("agenda_unhas_v2.db")
                        c = conn.cursor()
                        c.execute(
                            "DELETE FROM clientes_retencao WHERE id = ?",
                            (row["id"],),
                        )
                        conn.commit()
                        conn.close()
                        st.rerun()

else:
    st.info(
        "Nenhuma cliente cadastrada ainda. Use a barra lateral à esquerda para cadastrar a primeira cliente!"
    )
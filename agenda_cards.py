# ... (Manter todo o código anterior de imports e init_db igual)

# ... (Manter a parte de Login e Sidebar igual)

# --- PAINEL PRINCIPAL ---
st.title(f"💅 {titulo_atual} — Painel da {usuario_atual}")

# --- NOVA CENTRAL DE ALERTAS (INBOX) ---
conn = sqlite3.connect("agenda_unhas_v2.db")
hoje_str = date.today().isoformat()

# Conta agendamentos de hoje
df_agenda_hoje = pd.read_sql_query(
    "SELECT * FROM agendamentos WHERE data_atendimento = ? AND profissional = ?", 
    conn, params=(hoje_str, usuario_atual)
)

# Conta CRM pendente (calcula via pandas como na aba CRM)
df_crm_tudo = pd.read_sql_query("SELECT * FROM clientes_retencao WHERE profissional = ?", conn, params=(usuario_atual,))
conn.close()

if not df_crm_tudo.empty:
    df_crm_tudo["ultimo_atendimento"] = pd.to_datetime(df_crm_tudo["ultimo_atendimento"], errors="coerce").dt.date
    df_crm_tudo["proximo_atendimento"] = df_crm_tudo.apply(lambda r: r["ultimo_atendimento"] + timedelta(days=int(r["ciclo_dias"])), axis=1)
    # Filtra quem deveria ter retornado até hoje (atrasadas + quem vence hoje)
    df_crm_pendente = df_crm_tudo[df_crm_tudo["proximo_atendimento"] <= date.today()]
else:
    df_crm_pendente = pd.DataFrame()

# Exibe o alerta se tiver algo pendente
if not df_agenda_hoje.empty or not df_crm_pendente.empty:
    with st.expander("🔔 Central de Notificações Internas (Clique aqui para ver pendências)", expanded=True):
        col_al1, col_al2 = st.columns(2)
        if not df_agenda_hoje.empty:
            col_al1.warning(f"📅 **Hoje:** Você tem {len(df_agenda_hoje)} agendamento(s) para atender!")
        if not df_crm_pendente.empty:
            col_al2.error(f"⚠️ **CRM:** {len(df_crm_pendente)} cliente(s) precisam de contato (prazo vencido)!")
else:
    st.success("✅ Tudo em dia! Sem pendências para hoje.")

st.divider()

# ... (Manter o restante do código das abas a partir daqui)

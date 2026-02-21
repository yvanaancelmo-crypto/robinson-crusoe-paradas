import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time
from contextlib import contextmanager
import hashlib

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO GERAL
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Robinson Crusoe — Controle de Paradas",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  USUÁRIOS — edite senhas aqui (hash SHA-256)
#  Para gerar um hash: import hashlib; hashlib.sha256("suasenha".encode()).hexdigest()
# ─────────────────────────────────────────────
def _h(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

USERS = {
    # usuário : { senha_hash, perfil }
    "yvana":   { "hash": _h("yvana123"),   "perfil": "admin",    "display": "Yvana" },
    "felipe":  { "hash": _h("felipe123"),  "perfil": "admin",    "display": "Felipe" },
    "mecanico":{ "hash": _h("mec2024"),    "perfil": "mecanico", "display": "Mecânico" },
}

RESPONSAVEIS = ["Felipe", "Wagner", "Valiate", "Yvana", "Outro"]

MAQUINAS = [
    "Máquina 01", "Máquina 02", "Máquina 03",
    "Máquina 04", "Máquina 05", "Máquina 06",
    "Máquina 07", "Máquina 08", "Máquina 09",
]

TIPOS = {
    "MM": {"label": "MM — Mecânica",     "cor": "#1d6fa4"},
    "PO": {"label": "PO — Operacional",  "cor": "#d97706"},
    "ME": {"label": "ME — Elétrica",     "cor": "#7c3aed"},
}

DB_PATH = "robinson_paradas.db"

# ─────────────────────────────────────────────
#  CSS GLOBAL
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600;700&family=IBM+Plex+Mono:wght@500;700&display=swap');

:root {
    --navy:       #002147;
    --navy-light: #003a7a;
    --white:      #ffffff;
    --gray-50:    #f7f9fc;
    --gray-100:   #eef1f6;
    --gray-200:   #dde3ed;
    --gray-400:   #8fa3bf;
    --gray-600:   #4a6080;
    --red:        #c0392b;
    --red-soft:   #fff0ee;
    --yellow:     #d97706;
    --yellow-soft:#fffbeb;
    --green:      #16a34a;
    --green-soft: #f0fdf4;
    --blue-soft:  #eff6ff;
}

* { font-family: 'IBM Plex Sans', sans-serif !important; }
code, .mono { font-family: 'IBM Plex Mono', monospace !important; }

.stApp { background-color: var(--gray-50); }

/* ── Header ── */
.app-header {
    background: linear-gradient(120deg, var(--navy) 60%, var(--navy-light) 100%);
    color: white;
    padding: 1.6rem 2rem 1.2rem;
    border-radius: 14px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
}
.app-header .title  { font-size: 1.6rem; font-weight: 700; margin: 0; line-height: 1.2; }
.app-header .sub    { font-size: 0.82rem; color: #93c5fd; margin: 0.2rem 0 0; }

/* ── Login ── */
.login-wrap {
    max-width: 420px;
    margin: 4rem auto;
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    box-shadow: 0 4px 24px rgba(0,33,71,0.08);
}
.login-logo { text-align: center; margin-bottom: 1.5rem; }
.login-logo .icon { font-size: 3rem; }
.login-logo h2 { color: var(--navy); font-weight: 700; margin: 0.4rem 0 0.2rem; font-size: 1.4rem; }
.login-logo p  { color: var(--gray-400); font-size: 0.85rem; margin: 0; }

/* ── Cards ── */
.card {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 4px rgba(0,33,71,0.05);
}
.card-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: var(--gray-400);
    margin-bottom: 0.8rem;
}

/* ── Métricas ── */
.metric-box {
    background: white;
    border: 1px solid var(--gray-200);
    border-radius: 10px;
    padding: 1.1rem 1.2rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,33,71,0.04);
}
.metric-box .lbl { font-size: 0.68rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: var(--gray-400); }
.metric-box .val { font-size: 2rem; font-weight: 700; color: var(--navy); font-family: 'IBM Plex Mono', monospace; line-height: 1.1; margin: 0.2rem 0; }
.metric-box .hint{ font-size: 0.72rem; color: var(--gray-400); }

/* ── Alertas ── */
.alerta-critico {
    background: var(--red-soft);
    border: 2px solid var(--red);
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin: 0.6rem 0;
    color: #7f1d1d;
}
.alerta-critico .titulo { font-weight: 700; font-size: 1rem; margin-bottom: 0.4rem; }
.alerta-atencao {
    background: var(--yellow-soft);
    border-left: 4px solid var(--yellow);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    color: #78350f;
}
.alerta-ok {
    background: var(--green-soft);
    border-left: 4px solid var(--green);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    color: #14532d;
}

/* ── Badge tipo ── */
.badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    color: white;
}

/* ── Assinatura ── */
.assinatura-box {
    background: var(--blue-soft);
    border: 2px dashed #93c5fd;
    border-radius: 10px;
    padding: 1.2rem;
    text-align: center;
    margin: 0.8rem 0;
}
.assinatura-box.ok {
    background: var(--green-soft);
    border: 2px solid var(--green);
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 10px;
    padding: 5px;
    border: 1px solid var(--gray-200);
    gap: 4px;
    margin-bottom: 1rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px;
    font-weight: 600;
    font-size: 0.83rem;
    color: var(--gray-400);
    padding: 8px 18px;
}
.stTabs [aria-selected="true"] {
    background: var(--navy) !important;
    color: white !important;
}

/* ── Botões ── */
.stButton > button {
    background: var(--navy);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.88rem;
    padding: 0.6rem 1.4rem;
    width: 100%;
    transition: background 0.2s, transform 0.1s;
}
.stButton > button:hover  { background: var(--navy-light); color: white; }
.stButton > button:active { transform: scale(0.98); }

/* ── Tipo botões coloridos ── */
[data-testid="stHorizontalBlock"] .stButton > button { width: 100%; font-size: 0.95rem; padding: 0.7rem 0; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--navy); }
[data-testid="stSidebar"] * { color: white !important; }

/* Limpa rodapé e menu */
#MainMenu, footer { visibility: hidden; }

/* Inputs */
.stTextInput input, .stSelectbox select, .stTimeInput input, .stDateInput input {
    border-radius: 7px !important;
    border-color: var(--gray-200) !important;
}

div[data-testid="stForm"] { border: none !important; padding: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  BANCO DE DADOS
# ─────────────────────────────────────────────
def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS paradas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            data          TEXT NOT NULL,
            lote          TEXT NOT NULL,
            maquina       TEXT NOT NULL,
            hora_inicio   TEXT NOT NULL,
            hora_fim      TEXT NOT NULL,
            duracao_min   INTEGER NOT NULL,
            tipo          TEXT NOT NULL,
            descricao     TEXT NOT NULL,
            componente    TEXT,
            responsavel   TEXT NOT NULL,
            criado_por    TEXT NOT NULL,
            criado_em     TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

init_db()

@contextmanager
def get_con():
    con = sqlite3.connect(DB_PATH)
    try:
        yield con
    finally:
        con.close()

def load_data() -> pd.DataFrame:
    with get_con() as con:
        df = pd.read_sql_query(
            "SELECT * FROM paradas ORDER BY data DESC, hora_inicio DESC", con
        )
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
    return df

def insert_parada(data, lote, maquina, h_ini, h_fim, dur, tipo, desc, comp, resp, user):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_con() as con:
        con.execute("""
            INSERT INTO paradas
            (data,lote,maquina,hora_inicio,hora_fim,duracao_min,tipo,descricao,componente,responsavel,criado_por,criado_em)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (str(data), lote, maquina, str(h_ini), str(h_fim), dur, tipo, desc, comp, resp, user, agora))
        con.commit()

def delete_parada(pid: int):
    with get_con() as con:
        con.execute("DELETE FROM paradas WHERE id=?", (pid,))
        con.commit()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def calc_dur(h_ini: time, h_fim: time) -> int:
    delta = datetime.combine(date.today(), h_fim) - datetime.combine(date.today(), h_ini)
    return max(0, int(delta.total_seconds() // 60))

def badge(tipo: str) -> str:
    cores = {"MM": "#1d6fa4", "PO": "#d97706", "ME": "#7c3aed"}
    c = cores.get(tipo, "#64748b")
    return f'<span class="badge" style="background:{c}">{tipo}</span>'

def autenticar(usuario: str, senha: str):
    u = usuario.strip().lower()
    if u in USERS and USERS[u]["hash"] == _h(senha):
        return USERS[u]
    return None

# ─────────────────────────────────────────────
#  STATE INICIAL
# ─────────────────────────────────────────────
if "logado" not in st.session_state:
    st.session_state.logado     = False
    st.session_state.user_info  = {}
    st.session_state.tipo_sel   = None
    st.session_state.assinado   = False
    st.session_state.resp_sel   = ""

# ══════════════════════════════════════════════
#  TELA DE LOGIN
# ══════════════════════════════════════════════
if not st.session_state.logado:
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">
            <div class="icon">🏭</div>
            <h2>Robinson Crusoe</h2>
            <p>Sistema de Controle de Paradas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Centraliza o formulário
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Acesso ao Sistema</div>', unsafe_allow_html=True)
        login_user = st.text_input("Usuário", placeholder="seu usuário")
        login_pass = st.text_input("Senha",   placeholder="••••••••", type="password")
        if st.button("🔐  Entrar"):
            info = autenticar(login_user, login_pass)
            if info:
                st.session_state.logado    = True
                st.session_state.user_info = info
                st.session_state.username  = login_user.strip().lower()
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────
#  APP PRINCIPAL (pós-login)
# ─────────────────────────────────────────────
user_info = st.session_state.user_info
perfil     = user_info["perfil"]
display    = user_info["display"]

# ── Header ──
st.markdown(f"""
<div class="app-header">
    <div style="font-size:2.4rem">🏭</div>
    <div>
        <p class="title">Robinson Crusoe — Controle de Paradas</p>
        <p class="sub">Olá, <b>{display}</b> · Perfil: {perfil.upper()} · {date.today().strftime("%d/%m/%Y")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Logout no topo
col_sp, col_out = st.columns([5, 1])
with col_out:
    if st.button("↩ Sair"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── Abas ──
abas = ["➕ Registrar Parada", "📊 Dashboard Geral", "🔍 Por Máquina", "⚠️ Dano Real"]
if perfil == "admin":
    abas.append("🗂 Gerenciar Dados")

tabs = st.tabs(abas)

# ══════════════════════════════════════════════
#  ABA 1 — REGISTRAR
# ══════════════════════════════════════════════
with tabs[0]:
    st.markdown("### Novo Registro de Parada")

    # ── Bloco 1: Dados básicos ──
    st.markdown('<div class="card"><div class="card-title">📋 Identificação</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        f_data = st.date_input("Data", value=date.today())
    with c2:
        f_lote = st.text_input("Lote Juliano", placeholder="Ex: 25-187")
    with c3:
        f_maq  = st.selectbox("Máquina", MAQUINAS)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Bloco 2: Tempo ──
    st.markdown('<div class="card"><div class="card-title">⏱ Horário</div>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        f_ini = st.time_input("Hora Início", value=time(8, 0))
    with c5:
        f_fim = st.time_input("Hora Final",  value=time(8, 30))
    with c6:
        dur = calc_dur(f_ini, f_fim)
        st.markdown(f"""
        <div class="metric-box" style="margin-top:1.6rem">
            <div class="lbl">Duração Calculada</div>
            <div class="val">{dur}</div>
            <div class="hint">minutos</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Bloco 3: Tipo de parada (botões coloridos) ──
    st.markdown('<div class="card"><div class="card-title">🔧 Tipo de Parada</div>', unsafe_allow_html=True)
    bt1, bt2, bt3 = st.columns(3)
    with bt1:
        if st.button("🔵  MM — Mecânica"):
            st.session_state.tipo_sel = "MM"
    with bt2:
        if st.button("🟡  PO — Operacional"):
            st.session_state.tipo_sel = "PO"
    with bt3:
        if st.button("🟣  ME — Elétrica"):
            st.session_state.tipo_sel = "ME"

    tipo_atual = st.session_state.get("tipo_sel")
    if tipo_atual:
        cores = {"MM": "#1d6fa4", "PO": "#d97706", "ME": "#7c3aed"}
        st.markdown(f'<div style="margin-top:0.6rem;padding:0.6rem 1rem;background:{cores[tipo_atual]}18;border-left:4px solid {cores[tipo_atual]};border-radius:6px;font-weight:700;color:{cores[tipo_atual]};font-size:0.95rem">✅ Selecionado: {TIPOS[tipo_atual]["label"]}</div>', unsafe_allow_html=True)
    else:
        st.caption("Clique em um dos botões acima para selecionar o tipo.")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Bloco 4: Descrição ──
    st.markdown('<div class="card"><div class="card-title">📝 Detalhes da Ocorrência</div>', unsafe_allow_html=True)
    c7, c8 = st.columns([2, 1])
    with c7:
        f_desc = st.text_area("Descrição da Parada", placeholder="Ex: Lata arranhando no trilho de saída, causando rejeição.", height=90)
    with c8:
        f_comp = st.text_input("Componente Afetado", placeholder="Ex: Trilho guia, Sensor óptico")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Bloco 5: Assinatura Digital ──
    st.markdown('<div class="card"><div class="card-title">✍️ Assinatura Digital do Responsável</div>', unsafe_allow_html=True)

    resp_col, btn_col = st.columns([2, 1])
    with resp_col:
        resp = st.selectbox("Responsável pela validação", ["— selecione —"] + RESPONSAVEIS)
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅  Validar com Assinatura"):
            if resp == "— selecione —":
                st.error("Selecione um responsável.")
            else:
                st.session_state.assinado  = True
                st.session_state.resp_sel  = resp

    if st.session_state.assinado and st.session_state.resp_sel:
        st.markdown(f"""
        <div class="assinatura-box ok">
            <div style="font-size:1.5rem">✅</div>
            <div style="font-weight:700;color:#14532d;margin-top:0.3rem">Assinado por: {st.session_state.resp_sel}</div>
            <div style="font-size:0.75rem;color:#16a34a">{datetime.now().strftime("%d/%m/%Y às %H:%M")}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="assinatura-box">
            <div style="color:#3b82f6;font-size:0.85rem">Selecione o responsável e clique em <b>"Validar com Assinatura"</b> antes de salvar.</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Botão Salvar ──
    if st.button("💾  SALVAR REGISTRO DE PARADA"):
        erros = []
        if not f_lote.strip():            erros.append("Informe o Lote Juliano.")
        if dur == 0:                      erros.append("Hora Final deve ser maior que Hora Início.")
        if not tipo_atual:                erros.append("Selecione o Tipo de Parada.")
        if not f_desc.strip():            erros.append("Preencha a Descrição.")
        if not st.session_state.assinado: erros.append("Valide com Assinatura Digital antes de salvar.")

        if erros:
            for e in erros:
                st.error(f"⚠️ {e}")
        else:
            insert_parada(
                f_data, f_lote.strip(), f_maq,
                f_ini, f_fim, dur,
                tipo_atual, f_desc.strip(), f_comp.strip(),
                st.session_state.resp_sel, display
            )
            st.success(f"✅ Registro salvo com sucesso! Duração: **{dur} minutos**. Responsável: **{st.session_state.resp_sel}**")
            # Reset assinatura e tipo
            st.session_state.assinado = False
            st.session_state.resp_sel = ""
            st.session_state.tipo_sel = None
            st.balloons()

# ══════════════════════════════════════════════
#  ABA 2 — DASHBOARD GERAL
# ══════════════════════════════════════════════
with tabs[1]:
    df = load_data()

    if df.empty:
        st.markdown('<div class="alerta-ok">📭 Nenhum registro encontrado. Comece registrando paradas na primeira aba.</div>', unsafe_allow_html=True)
    else:
        # KPIs
        tot_min   = df["duracao_min"].sum()
        tot_reg   = len(df)
        media_dur = df["duracao_min"].mean()
        maq_crit  = df.groupby("maquina")["duracao_min"].sum().idxmax()
        tot_horas = tot_min / 60

        st.markdown("### Visão Geral da Fábrica")
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="metric-box"><div class="lbl">Total de Paradas</div><div class="val">{tot_reg}</div><div class="hint">registros</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="metric-box"><div class="lbl">Tempo Total Perdido</div><div class="val">{tot_min:,}</div><div class="hint">minutos · {tot_horas:.1f}h</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="metric-box"><div class="lbl">Média por Parada</div><div class="val">{media_dur:.0f}</div><div class="hint">minutos</div></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="metric-box"><div class="lbl">Máquina Crítica</div><div class="val" style="font-size:1rem;padding-top:0.4rem">{maq_crit}</div><div class="hint">maior tempo parado</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico de barras — todas as máquinas
        df_maq = df.groupby("maquina")["duracao_min"].sum().reset_index().sort_values("duracao_min", ascending=True)
        fig1 = px.bar(
            df_maq, x="duracao_min", y="maquina", orientation="h",
            title="⏱ Tempo Total de Parada por Máquina (min)",
            color="duracao_min",
            color_continuous_scale=["#bfdbfe", "#002147"],
            labels={"duracao_min": "Minutos Parados", "maquina": ""}
        )
        fig1.update_layout(
            showlegend=False, coloraxis_showscale=False,
            paper_bgcolor="white", plot_bgcolor="#f7f9fc",
            font_family="IBM Plex Sans", title_font_size=14,
            margin=dict(l=10, r=10, t=44, b=10), height=380
        )
        st.plotly_chart(fig1, use_container_width=True)

        # Linha + pizza
        cl, cr = st.columns(2)

        df_tipo = df.groupby("tipo")["duracao_min"].sum().reset_index()
        fig2 = px.pie(
            df_tipo, names="tipo", values="duracao_min",
            title="Distribuição por Tipo",
            color="tipo",
            color_discrete_map={"MM": "#1d6fa4", "PO": "#d97706", "ME": "#7c3aed"},
            hole=0.45
        )
        fig2.update_layout(paper_bgcolor="white", font_family="IBM Plex Sans",
                           title_font_size=14, margin=dict(t=44, b=10))
        cl.plotly_chart(fig2, use_container_width=True)

        df_time = df.groupby(df["data"].dt.date)["duracao_min"].sum().reset_index()
        df_time.columns = ["Data", "Minutos"]
        fig3 = px.area(
            df_time, x="Data", y="Minutos",
            title="Evolução Diária de Tempo Perdido",
        )
        fig3.update_traces(line_color="#002147", fillcolor="#bfdbfe")
        fig3.update_layout(paper_bgcolor="white", plot_bgcolor="#f7f9fc",
                           font_family="IBM Plex Sans", title_font_size=14,
                           margin=dict(t=44, b=10))
        cr.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════
#  ABA 3 — FILTRO POR MÁQUINA
# ══════════════════════════════════════════════
with tabs[2]:
    df = load_data()
    st.markdown("### Análise Individual por Máquina")

    maq_sel = st.selectbox("Selecione a Máquina para analisar:", MAQUINAS, key="maq_filtro")
    df_m = df[df["maquina"] == maq_sel].copy() if not df.empty else pd.DataFrame()

    if df_m.empty:
        st.markdown(f'<div class="alerta-ok">✅ <b>{maq_sel}</b> não possui paradas registradas.</div>', unsafe_allow_html=True)
    else:
        tot_m   = df_m["duracao_min"].sum()
        qtd_m   = len(df_m)
        med_m   = df_m["duracao_min"].mean()

        k1, k2, k3 = st.columns(3)
        k1.markdown(f'<div class="metric-box"><div class="lbl">Paradas Registradas</div><div class="val">{qtd_m}</div></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="metric-box"><div class="lbl">Tempo Total</div><div class="val">{tot_m}</div><div class="hint">minutos</div></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="metric-box"><div class="lbl">Duração Média</div><div class="val">{med_m:.0f}</div><div class="hint">min / parada</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico por tipo
        df_t = df_m.groupby("tipo")["duracao_min"].sum().reset_index()
        fig = px.bar(
            df_t, x="tipo", y="duracao_min",
            title=f"Tempo por Tipo — {maq_sel}",
            color="tipo",
            color_discrete_map={"MM": "#1d6fa4", "PO": "#d97706", "ME": "#7c3aed"},
            labels={"tipo": "Tipo", "duracao_min": "Minutos"},
            text="duracao_min"
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, paper_bgcolor="white",
                          plot_bgcolor="#f7f9fc", font_family="IBM Plex Sans",
                          title_font_size=14, margin=dict(t=44, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Histórico
        st.markdown(f"#### Histórico completo — {maq_sel}")
        df_show = df_m[["data","lote","hora_inicio","hora_fim","duracao_min","tipo","descricao","componente","responsavel"]].copy()
        df_show.columns = ["Data","Lote","Início","Fim","Min","Tipo","Descrição","Componente","Responsável"]
        df_show["Data"] = df_show["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
#  ABA 4 — DANO REAL
# ══════════════════════════════════════════════
with tabs[3]:
    df = load_data()
    st.markdown("### ⚠️ Contexto de Dano Real — Problemas Recorrentes")
    st.caption("Detecta falhas repetitivas que acumulam tempo de parada significativo.")

    if df.empty:
        st.info("Sem dados para análise.")
    else:
        # Filtro de lote
        lotes_disp = ["Todos"] + sorted(df["lote"].unique().tolist())
        lote_filtro = st.selectbox("Filtrar por Lote:", lotes_disp)
        df_ana = df if lote_filtro == "Todos" else df[df["lote"] == lote_filtro]

        LIMIAR_OCORR = 3  # ← Regra de Ouro: mais de 3x no mesmo lote

        if df_ana.empty:
            st.info("Nenhum dado para o lote selecionado.")
        else:
            df_ana = df_ana.copy()
            df_ana["desc_key"] = df_ana["descricao"].str.strip().str.lower()

            grupo = df_ana.groupby(["maquina", "desc_key", "tipo"]).agg(
                ocorrencias=("id", "count"),
                tempo_total=("duracao_min", "sum"),
                desc_orig=("descricao", "first"),
            ).reset_index()

            criticos = grupo[grupo["ocorrencias"] >= LIMIAR_OCORR].sort_values("tempo_total", ascending=False)
            outros   = grupo[grupo["ocorrencias"] < LIMIAR_OCORR].sort_values("ocorrencias", ascending=False)

            if criticos.empty:
                st.markdown('<div class="alerta-ok">✅ Nenhuma falha recorrente crítica detectada. Continue monitorando!</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"**{len(criticos)} problema(s) com recorrência crítica (≥ {LIMIAR_OCORR}x):**")
                for _, row in criticos.iterrows():
                    h  = row["tempo_total"] // 60
                    mn = row["tempo_total"] % 60
                    st.markdown(f"""
                    <div class="alerta-critico">
                        <div class="titulo">🚨 ALERTA DE DANO REAL</div>
                        <div style="font-size:1rem;margin-bottom:0.5rem">
                            <b>{row['maquina']}</b> · Tipo: <b>{row['tipo']}</b>
                        </div>
                        <div style="font-size:0.92rem;margin-bottom:0.6rem">
                            Problema: <i>"{row['desc_orig']}"</i>
                        </div>
                        <div style="display:flex;gap:1.5rem;font-size:0.88rem;flex-wrap:wrap">
                            <span>🔁 Ocorrências: <b>{row['ocorrencias']}x</b></span>
                            <span>⏱ Tempo perdido: <b>{row['tempo_total']} min ({h}h {mn}min)</b></span>
                            <span>📦 Lote: <b>{lote_filtro}</b></span>
                        </div>
                        <div style="margin-top:0.6rem;font-size:0.8rem;font-style:italic">
                            Esta falha recorrente já causou <b>{row['tempo_total']} minutos</b> de parada, impactando diretamente a meta deste lote.
                        </div>
                    </div>""", unsafe_allow_html=True)

            # Tabela de todos os padrões
            st.markdown("<br>")
            st.markdown("#### 📋 Ranking de Impacto — Todas as Ocorrências")
            df_rank = grupo.sort_values("tempo_total", ascending=False).head(20)
            df_rank_show = df_rank[["maquina","desc_orig","tipo","ocorrencias","tempo_total"]].copy()
            df_rank_show.columns = ["Máquina","Descrição","Tipo","Ocorrências","Min. Perdidos"]

            fig_r = px.bar(
                df_rank_show.sort_values("Min. Perdidos"),
                x="Min. Perdidos", y="Descrição", orientation="h",
                color="Tipo",
                color_discrete_map={"MM": "#1d6fa4", "PO": "#d97706", "ME": "#7c3aed"},
                title="Top 20 Causas por Tempo Perdido Acumulado"
            )
            fig_r.update_layout(paper_bgcolor="white", plot_bgcolor="#f7f9fc",
                                font_family="IBM Plex Sans", title_font_size=14,
                                margin=dict(l=10, r=10, t=44, b=10))
            st.plotly_chart(fig_r, use_container_width=True)
            st.dataframe(df_rank_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════
#  ABA 5 — GERENCIAR DADOS (admin only)
# ══════════════════════════════════════════════
if perfil == "admin" and len(tabs) > 4:
    with tabs[4]:
        df = load_data()
        st.markdown("### 🗂 Gerenciamento de Dados")
        st.caption("Área restrita — somente administradores.")

        if df.empty:
            st.info("Sem registros no banco de dados.")
        else:
            st.markdown(f"**Total de registros:** {len(df)}")
            df_full = df[["id","data","lote","maquina","hora_inicio","hora_fim",
                           "duracao_min","tipo","descricao","componente",
                           "responsavel","criado_por","criado_em"]].copy()
            df_full["data"] = df_full["data"].dt.strftime("%d/%m/%Y")
            df_full.columns = ["ID","Data","Lote","Máquina","Início","Fim","Min",
                                "Tipo","Descrição","Componente","Responsável","Criado Por","Criado Em"]
            st.dataframe(df_full, use_container_width=True, hide_index=True)

            # Export CSV
            csv = df_full.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Exportar CSV completo", csv, "paradas_robinson.csv", "text/csv")

            st.markdown("---")
            st.markdown("#### Excluir Registro")
            del_id = st.number_input("ID do registro a excluir:", min_value=1, step=1)
            if st.button("🗑 Confirmar Exclusão"):
                delete_parada(int(del_id))
                st.warning(f"Registro #{del_id} removido.")
                st.rerun()

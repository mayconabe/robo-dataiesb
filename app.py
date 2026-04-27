import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIA/SUS · Produção Ambulatorial",
    page_icon="⚕",
    layout="wide",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stMarkdown, .stText {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ─ Layout ─────────────────────────────────────────────────────────────── */
.main .block-container {
    padding: 1.75rem 2.5rem 4rem 2.5rem;
    max-width: 1480px;
}
/* ─ Page header ─────────────────────────────────────────────────────────── */
.page-header {
    padding: 0 0 1.5rem 0;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 0;
    animation: fadeDown 0.35s ease both;
}
.page-header .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    background: #EBF4FF;
    color: #1A56A0;
    font-size: 0.6875rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding: 0.25rem 0.625rem;
    border-radius: 20px;
    margin-bottom: 0.625rem;
}
.page-header h1 {
    font-size: 1.625rem !important;
    font-weight: 800 !important;
    color: #0D1F3C !important;
    letter-spacing: -0.03em !important;
    line-height: 1.15 !important;
    margin: 0 !important;
}
.page-header .sub {
    font-size: 0.8125rem;
    color: #64748B;
    margin-top: 0.375rem;
    font-weight: 400;
}

/* ─ KPI Grid ─────────────────────────────────────────────────────────────── */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.875rem;
    margin: 1.5rem 0 2rem 0;
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E8EFF7;
    border-radius: 12px;
    padding: 1.125rem 1.375rem 1rem;
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.18s ease, transform 0.18s ease;
    animation: fadeSlideUp 0.4s ease both;
}
.kpi-card:hover {
    box-shadow: 0 6px 20px rgba(13,31,60,0.09);
    transform: translateY(-2px);
}
.kpi-card::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 12px;
    box-shadow: inset 0 0 0 1px rgba(13,31,60,0.05);
    pointer-events: none;
}
.kpi-accent {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}
.kpi-card.c-blue   .kpi-accent { background: linear-gradient(90deg,#1A56A0,#4A90D9); }
.kpi-card.c-green  .kpi-accent { background: linear-gradient(90deg,#1A7F4B,#38A169); }
.kpi-card.c-slate  .kpi-accent { background: linear-gradient(90deg,#3D5A80,#64748B); }
.kpi-card.c-amber  .kpi-accent { background: linear-gradient(90deg,#B7791F,#D69E2E); }
.kpi-label {
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748B;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.875rem;
    font-weight: 800;
    color: #0D1F3C;
    line-height: 1;
    letter-spacing: -0.035em;
    font-variant-numeric: tabular-nums;
}
.kpi-unit {
    font-size: 0.875rem;
    font-weight: 600;
    color: #94A3B8;
    margin-left: 0.125rem;
    letter-spacing: 0;
}
.kpi-delta {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 0.5rem;
    padding: 0.2rem 0.5rem 0.2rem 0.4rem;
    border-radius: 20px;
}
.kpi-delta.pos { background: #F0FFF4; color: #276749; }
.kpi-delta.neu { background: #EDF2F7; color: #4A5568; }
.kpi-context {
    font-size: 0.6875rem;
    color: #94A3B8;
    margin-top: 0.25rem;
    font-weight: 400;
}

/* ─ Section headers ──────────────────────────────────────────────────────── */
.sec-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2.25rem 0 0.25rem;
}
.sec-bar {
    width: 4px;
    height: 1.125rem;
    border-radius: 2px;
    flex-shrink: 0;
    background: #1A56A0;
}
.sec-title {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #0D1F3C !important;
    letter-spacing: -0.015em !important;
    margin: 0 !important;
}
.sec-desc {
    font-size: 0.8rem;
    color: #64748B;
    margin: 0 0 1rem 0;
    padding-left: 1.25rem;
    line-height: 1.5;
}

/* ─ Chart wrapper ────────────────────────────────────────────────────────── */
.chart-wrap {
    background: #FFFFFF;
    border: 1px solid #E8EFF7;
    border-radius: 12px;
    padding: 0.25rem 0.25rem 0;
    overflow: hidden;
    animation: fadeSlideUp 0.5s ease both;
}

/* ─ Insight cards ────────────────────────────────────────────────────────── */
.insight-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.875rem;
    margin-top: 0.5rem;
}
.insight-card {
    background: #FFFFFF;
    border: 1px solid #E8EFF7;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    animation: fadeSlideUp 0.55s ease both;
}
.insight-card .i-head {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.875rem;
    padding-bottom: 0.625rem;
    border-bottom: 1px solid #F1F5F9;
}
.insight-card .i-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.insight-card .i-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.insight-card.ov .i-dot  { background: #1A56A0; }
.insight-card.ov .i-title { color: #1A56A0; }
.insight-card.tr .i-dot  { background: #276749; }
.insight-card.tr .i-title { color: #276749; }
.insight-card.al .i-dot  { background: #B7791F; }
.insight-card.al .i-title { color: #B7791F; }
.insight-card.ac .i-dot  { background: #4A5568; }
.insight-card.ac .i-title { color: #4A5568; }
.insight-card ul {
    list-style: none;
    margin: 0;
    padding: 0;
}
.insight-card li {
    font-size: 0.8125rem;
    color: #374151;
    padding: 0.275rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    line-height: 1.45;
}
.insight-card li .bullet { color: #CBD5E0; flex-shrink: 0; font-weight: 700; }
.insight-card li strong  { color: #0D1F3C; font-weight: 600; }

/* ─ Footer ───────────────────────────────────────────────────────────────── */
.dash-footer {
    margin-top: 3rem;
    padding-top: 1.25rem;
    border-top: 1px solid #E2E8F0;
    font-size: 0.75rem;
    color: #94A3B8;
    text-align: center;
    animation: fadeDown 0.5s ease 0.3s both;
}

/* ─ Animations ───────────────────────────────────────────────────────────── */
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.d1 { animation-delay: 0.05s; }
.d2 { animation-delay: 0.10s; }
.d3 { animation-delay: 0.15s; }
.d4 { animation-delay: 0.20s; }

/* ─ Filter bar ───────────────────────────────────────────────────────────── */
.filter-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin: 0 0 0.75rem 1.25rem;
}
.filter-row [data-baseweb="select"],
.filter-row [data-baseweb="input"] {
    min-width: 0;
}
/* Make filter widgets compact */
div[data-testid="stHorizontalBlock"] [data-testid="stSelectbox"] > label,
div[data-testid="stHorizontalBlock"] [data-testid="stSlider"] > label,
div[data-testid="stHorizontalBlock"] [data-testid="stMultiSelect"] > label {
    font-size: 0.6875rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #64748B !important;
    margin-bottom: 0.2rem !important;
}
div[data-testid="stHorizontalBlock"] [data-baseweb="select"] > div:first-child {
    min-height: 34px !important;
    font-size: 0.8125rem !important;
}
div[data-testid="stHorizontalBlock"] [data-testid="stSlider"] {
    padding-top: 0 !important;
}

/* ─ Streamlit overrides ──────────────────────────────────────────────────── */
[data-testid="stMetric"] { display: none !important; }
.stPlotlyChart { border-radius: 12px; }
div[data-testid="stExpander"] {
    border: 1px solid #E8EFF7 !important;
    border-radius: 10px !important;
    overflow: hidden;
}
div[data-testid="stExpander"] summary {
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
}
[data-testid="stDataFrameResizable"] { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Paleta e template de gráficos ─────────────────────────────────────────────
C_DEEP     = "#0D1F3C"
C_BLUE1    = "#1A56A0"
C_BLUE2    = "#2B7FD4"
C_BLUE3    = "#5BA3E8"
C_BLUE4    = "#93C5F5"
C_BLUE5    = "#C7E2FC"
C_GREEN    = "#276749"
C_GREEN2   = "#38A169"
C_AMBER    = "#B7791F"
C_RED      = "#9B2335"
C_SLATE    = "#64748B"
C_GRID     = "#F1F5F9"
C_BORDER   = "#E8EFF7"

BLUES_SEQ  = [C_BLUE1, C_BLUE2, C_BLUE3, C_BLUE4, C_BLUE5,
              "#B3D1F0", "#D8EAFB", "#1E3A6E", "#1565C0", "#90CAF9"]

def apply_theme(fig, height=460, show_legend=True, margin=None):
    m = margin or dict(l=12, r=12, t=44, b=12)
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, sans-serif", color="#374151", size=11),
        title_font=dict(family="Inter", size=12.5, color=C_DEEP),
        showlegend=show_legend,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(size=11),
            orientation="h",
            y=1.06,
            x=0,
        ),
        margin=m,
        hoverlabel=dict(
            bgcolor=C_DEEP,
            bordercolor=C_DEEP,
            font=dict(family="Inter", size=12, color="#FFFFFF"),
        ),
        hovermode="x unified",
    )
    fig.update_xaxes(
        gridcolor="rgba(0,0,0,0)",
        linecolor=C_BORDER,
        tickfont=dict(size=10.5, color=C_SLATE),
        ticklen=4,
        ticks="outside",
    )
    fig.update_yaxes(
        gridcolor=C_GRID,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=10.5, color=C_SLATE),
    )
    return fig

# ── Dados ─────────────────────────────────────────────────────────────────────
DADOS_DIR = Path("dados")

@st.cache_data(show_spinner="Carregando arquivos…")
def carregar_csvs(tipo: str) -> pd.DataFrame:
    arquivos = sorted(DADOS_DIR.glob(f"sia_{tipo}_*.csv"))
    return pd.concat(
        [pd.read_csv(a, sep=";", encoding="utf-8-sig", dtype=str) for a in arquivos],
        ignore_index=True,
    )

@st.cache_data(show_spinner="Processando…")
def limpar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().strip('"') for c in df.columns]
    col_mun = next(c for c in df.columns if "unic" in c.lower())
    df.rename(columns={col_mun: "municipio"}, inplace=True)
    df["cod_municipio"] = df["municipio"].str.extract(r"^(\d{6})")
    df["municipio"]     = df["municipio"].str.replace(r"^\d{6}\s*", "", regex=True).str.strip()
    df["periodo_dt"]    = pd.to_datetime(df["periodo"], format="%m/%Y")
    df["ano"]           = df["periodo_dt"].dt.year
    df["mes"]           = df["periodo_dt"].dt.month

    fixas = {"periodo","conteudo","municipio","cod_municipio","periodo_dt","ano","mes","Total"}
    subs  = [c for c in df.columns if c not in fixas]
    for col in subs + (["Total"] if "Total" in df.columns else []):
        df[col] = (
            df[col].astype(str).str.strip().str.strip('"')
            .replace("-","0")
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df = df[~df["municipio"].str.upper().str.contains(r"^TOTAL$", na=False)]
    return df

with st.spinner("Carregando dados do DATASUS…"):
    df_qtd   = limpar(carregar_csvs("qtd_aprovada"))
    df_valor = limpar(carregar_csvs("valor_aprovado"))

FIXAS    = {"periodo","conteudo","municipio","cod_municipio","periodo_dt","ano","mes","Total"}
SUBGRUPOS = [c for c in df_qtd.columns if c not in FIXAS]

# ── Métricas base ─────────────────────────────────────────────────────────────
resumo = (
    df_qtd.groupby("periodo_dt")["Total"].sum().reset_index()
    .rename(columns={"Total":"qtd_total"})
    .merge(
        df_valor.groupby("periodo_dt")["Total"].sum().reset_index()
        .rename(columns={"Total":"valor_total"}),
        on="periodo_dt",
    )
    .sort_values("periodo_dt")
)
resumo["periodo"] = resumo["periodo_dt"].dt.strftime("%m/%Y")

anual_qtd  = df_qtd.groupby("ano")["Total"].sum()
anual_val  = df_valor.groupby("ano")["Total"].sum()
cresc_pct  = (anual_qtd.get(2025,0) - anual_qtd.get(2024,0)) / anual_qtd.get(2024,1) * 100
qtd_total  = df_qtd["Total"].sum()
val_total  = df_valor["Total"].sum()
n_mun      = df_qtd["municipio"].nunique()
zeradas    = (df_qtd["Total"] == 0).mean() * 100

top_sub = (
    df_qtd[SUBGRUPOS].sum().sort_values(ascending=False).head(10)
    .reset_index()
)
top_sub.columns = ["subgrupo","qtd"]
top_sub["pct"]          = top_sub["qtd"] / top_sub["qtd"].sum() * 100
top_sub["subgrupo_curto"] = top_sub["subgrupo"].str.slice(5, 46)

top_mun = (
    df_qtd[df_qtd["municipio"].str.strip() != ""]
    .groupby("municipio")["Total"].sum().sort_values(ascending=False)
    .head(15).reset_index()
)
top_mun.columns = ["municipio","qtd_total"]
top_mun["pct"] = top_mun["qtd_total"] / qtd_total * 100

sub_2024   = df_qtd[df_qtd["ano"] == 2024][SUBGRUPOS].sum()
sub_2025   = df_qtd[df_qtd["ano"] == 2025][SUBGRUPOS].sum()
cresc_sub  = ((sub_2025 - sub_2024) / sub_2024.replace(0, np.nan) * 100).dropna().sort_values()

prod_mun = (
    df_qtd[df_qtd["municipio"].str.strip() != ""]
    .groupby("municipio")["Total"].sum()
)

df_qtd_f   = df_qtd
df_valor_f = df_valor
resumo_f   = resumo

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
    <div class="badge">⚕ DATASUS · SIA/SUS</div>
    <h1>Produção Ambulatorial do SUS</h1>
    <p class="sub">Por Local de Atendimento &nbsp;·&nbsp; Janeiro 2024 — Janeiro 2026 &nbsp;·&nbsp; Brasil (5.600 municípios)</p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-row">
  <div class="kpi-card c-blue d1">
    <div class="kpi-accent"></div>
    <div class="kpi-label">Qtd. Aprovada Total</div>
    <div class="kpi-value">{qtd_total/1e9:.2f}<span class="kpi-unit">Bi</span></div>
    <div class="kpi-delta neu">25 meses · {qtd_total/1e6/25:,.0f}M / mês</div>
  </div>
  <div class="kpi-card c-green d2">
    <div class="kpi-accent"></div>
    <div class="kpi-label">Valor Aprovado Total</div>
    <div class="kpi-value">R$ {val_total/1e9:.1f}<span class="kpi-unit">Bi</span></div>
    <div class="kpi-delta neu">Ticket médio R$ {val_total/qtd_total:.2f}</div>
  </div>
  <div class="kpi-card c-slate d3">
    <div class="kpi-accent"></div>
    <div class="kpi-label">Municípios Ativos</div>
    <div class="kpi-value">{n_mun:,}</div>
    <div class="kpi-delta neu">{zeradas:.1f}% sem produção</div>
  </div>
  <div class="kpi-card c-amber d4">
    <div class="kpi-accent"></div>
    <div class="kpi-label">Crescimento 2024→2025</div>
    <div class="kpi-value">+{cresc_pct:.1f}<span class="kpi-unit">%</span></div>
    <div class="kpi-delta pos">▲ Tendência de alta</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1. Série Temporal
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Série Temporal — Produção Mensal</p></div>
<p class="sec-desc">Evolução da quantidade e do valor aprovados mês a mês. Passe o mouse para ver os valores exatos de cada período.</p>
""", unsafe_allow_html=True)

_anos_ts = sorted(resumo["periodo_dt"].dt.year.unique().tolist())
_fc1, _fc2, _fc3 = st.columns([2, 2, 3])
with _fc1:
    ts_anos = st.multiselect(
        "Anos", _anos_ts, default=_anos_ts, key="ts_anos",
        help="Filtre um ou mais anos na série temporal",
    )
with _fc2:
    ts_metrica = st.selectbox(
        "Métrica", ["Quantidade e Valor", "Só Quantidade", "Só Valor"], key="ts_metrica",
    )

resumo_ts = resumo[resumo["periodo_dt"].dt.year.isin(ts_anos if ts_anos else _anos_ts)]

_n_rows = 1 if ts_metrica != "Quantidade e Valor" else 2
_subtitles = {
    "Quantidade e Valor": ("Quantidade Aprovada (milhões)", "Valor Aprovado (R$ bilhões)"),
    "Só Quantidade":      ("Quantidade Aprovada (milhões)",),
    "Só Valor":           ("Valor Aprovado (R$ bilhões)",),
}
fig_ts = make_subplots(
    rows=_n_rows, cols=1, shared_xaxes=True,
    subplot_titles=_subtitles[ts_metrica],
    vertical_spacing=0.10,
)

if ts_metrica in ("Quantidade e Valor", "Só Quantidade"):
    _r = 1
    fig_ts.add_trace(go.Bar(
        x=resumo_ts["periodo_dt"], y=resumo_ts["qtd_total"] / 1e6,
        name="Qtd (M)", marker_color=C_BLUE3, opacity=0.55,
        hovertemplate="<b>%{x|%b/%Y}</b><br>Qtd: %{y:,.1f}M<extra></extra>",
    ), row=_r, col=1)
    fig_ts.add_trace(go.Scatter(
        x=resumo_ts["periodo_dt"], y=resumo_ts["qtd_total"] / 1e6,
        name="Tendência Qtd", mode="lines+markers",
        line=dict(color=C_BLUE1, width=2.5),
        marker=dict(size=5, color=C_BLUE1, line=dict(color="white", width=1.5)),
        hovertemplate="<b>%{x|%b/%Y}</b><br>%{y:,.1f}M<extra></extra>",
    ), row=_r, col=1)
    if not resumo_ts.empty:
        pico_row = resumo_ts.loc[resumo_ts["qtd_total"].idxmax()]
        fig_ts.add_annotation(
            x=pico_row["periodo_dt"], y=pico_row["qtd_total"] / 1e6,
            text=f"Pico<br>{pico_row['qtd_total']/1e6:.0f}M",
            showarrow=True, arrowhead=2, arrowcolor=C_BLUE1, arrowsize=0.8,
            font=dict(size=10, color=C_BLUE1, family="Inter"),
            bgcolor="white", bordercolor=C_BORDER, borderwidth=1,
            ay=-36, row=_r, col=1,
        )
    fig_ts.update_yaxes(title_text="Milhões", tickformat=",.0f", row=_r, col=1, title_font_size=10)

if ts_metrica in ("Quantidade e Valor", "Só Valor"):
    _r = 2 if ts_metrica == "Quantidade e Valor" else 1
    fig_ts.add_trace(go.Bar(
        x=resumo_ts["periodo_dt"], y=resumo_ts["valor_total"] / 1e9,
        name="Valor (Bi)", marker_color=C_GREEN2, opacity=0.55,
        hovertemplate="<b>%{x|%b/%Y}</b><br>R$ %{y:,.2f}Bi<extra></extra>",
    ), row=_r, col=1)
    fig_ts.add_trace(go.Scatter(
        x=resumo_ts["periodo_dt"], y=resumo_ts["valor_total"] / 1e9,
        name="Tendência Valor", mode="lines+markers",
        line=dict(color=C_GREEN, width=2.5),
        marker=dict(size=5, color=C_GREEN, line=dict(color="white", width=1.5)),
        hovertemplate="<b>%{x|%b/%Y}</b><br>R$ %{y:,.2f}Bi<extra></extra>",
    ), row=_r, col=1)
    fig_ts.update_yaxes(title_text="R$ Bilhões", tickformat=",.1f", row=_r, col=1, title_font_size=10)

_h_ts = 380 if _n_rows == 1 else 520
apply_theme(fig_ts, height=_h_ts)
fig_ts.update_layout(title_text="", barmode="overlay")

st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
st.plotly_chart(fig_ts, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.expander("Ver tabela completa por período"):
    tbl = resumo_ts[["periodo","qtd_total","valor_total"]].copy()
    tbl["qtd_total"]   = tbl["qtd_total"].map("{:,.0f}".format)
    tbl["valor_total"] = tbl["valor_total"].map("R$ {:,.2f}".format)
    tbl.columns = ["Período","Qtd. Aprovada","Valor Aprovado"]
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. Top Subgrupos
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Top Subgrupos de Procedimento</p></div>
<p class="sec-desc">Subgrupos com maior volume de procedimentos aprovados. A fatia de Componente Especializado responde sozinha por um terço de toda a produção.</p>
""", unsafe_allow_html=True)

_anos_sub = ["Todos"] + sorted(df_qtd["ano"].unique().tolist())
_sc1, _sc2, _sc3 = st.columns([2, 2, 3])
with _sc1:
    sub_ano = st.selectbox("Ano", _anos_sub, key="sub_ano")
with _sc2:
    sub_n = st.slider("Exibir top", 5, 15, 10, key="sub_n")

_df_sub = df_qtd if sub_ano == "Todos" else df_qtd[df_qtd["ano"] == sub_ano]
top_sub_f = (
    _df_sub[SUBGRUPOS].sum().sort_values(ascending=False).head(sub_n).reset_index()
)
top_sub_f.columns = ["subgrupo","qtd"]
top_sub_f["pct"]           = top_sub_f["qtd"] / top_sub_f["qtd"].sum() * 100
top_sub_f["subgrupo_curto"] = top_sub_f["subgrupo"].str.slice(5, 46)

col_bar, col_pie = st.columns([3, 2], gap="medium")

with col_bar:
    ts_f = top_sub_f.sort_values("qtd")
    fig_bar = go.Figure(go.Bar(
        x=ts_f["qtd"],
        y=ts_f["subgrupo_curto"],
        orientation="h",
        marker=dict(
            color=ts_f["qtd"],
            colorscale=[[0, C_BLUE4], [1, C_BLUE1]],
            line=dict(color="rgba(0,0,0,0)"),
        ),
        text=[f"{v/1e9:.2f}Bi" for v in ts_f["qtd"]],
        textposition="outside",
        textfont=dict(size=10.5, color=C_SLATE, family="Inter"),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} procedimentos<extra></extra>",
    ))
    _titulo_sub = f"Quantidade por Subgrupo — {sub_ano}"
    _h_sub = max(320, sub_n * 36)
    apply_theme(fig_bar, height=_h_sub, show_legend=False)
    fig_bar.update_layout(title_text=_titulo_sub, margin=dict(l=8, r=80, t=44, b=8))
    fig_bar.update_xaxes(title_text="Qtd. Aprovada", tickformat=".2s")
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=top_sub_f["subgrupo_curto"],
        values=top_sub_f["pct"],
        hole=0.52,
        marker=dict(colors=BLUES_SEQ[:len(top_sub_f)], line=dict(color="white", width=1.5)),
        textinfo="percent",
        textfont=dict(size=10.5, family="Inter"),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        sort=False,
    ))
    fig_pie.add_annotation(
        text=f"Top {sub_n}<br><b>subgrupos</b>", x=0.5, y=0.5, showarrow=False,
        font=dict(size=11, color=C_DEEP, family="Inter"), align="center",
    )
    apply_theme(fig_pie, height=_h_sub, show_legend=False)
    fig_pie.update_layout(title_text="Participação Relativa (%)", margin=dict(l=0, r=0, t=44, b=0))
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 3. Top Municípios
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Top Municípios por Quantidade Aprovada</p></div>
<p class="sec-desc">São Paulo concentra 8,6% da produção nacional — mas a distribuição entre os maiores é relativamente equilibrada, indicando descentralização.</p>
""", unsafe_allow_html=True)

_anos_mun = ["Todos"] + sorted(df_qtd["ano"].unique().tolist())
_mc1, _mc2, _mc3 = st.columns([2, 2, 3])
with _mc1:
    mun_ano = st.selectbox("Ano", _anos_mun, key="mun_ano")
with _mc2:
    mun_n = st.slider("Exibir top", 5, 30, 15, key="mun_n")

_df_mun = df_qtd if mun_ano == "Todos" else df_qtd[df_qtd["ano"] == mun_ano]
_qtd_total_mun = _df_mun["Total"].sum()
top_mun_f = (
    _df_mun[_df_mun["municipio"].str.strip() != ""]
    .groupby("municipio")["Total"].sum()
    .sort_values(ascending=False)
    .head(mun_n).reset_index()
)
top_mun_f.columns = ["municipio","qtd_total"]
top_mun_f["pct"] = top_mun_f["qtd_total"] / _qtd_total_mun * 100

tm = top_mun_f.sort_values("qtd_total")
fig_mun = go.Figure(go.Bar(
    x=tm["qtd_total"],
    y=tm["municipio"],
    orientation="h",
    marker=dict(
        color=tm["qtd_total"],
        colorscale=[[0, C_BLUE5], [0.5, C_BLUE2], [1, C_BLUE1]],
        line=dict(color="rgba(0,0,0,0)"),
    ),
    text=[f"{v/1e6:.0f}M  ({p:.1f}%)" for v, p in zip(tm["qtd_total"], tm["pct"])],
    textposition="outside",
    textfont=dict(size=10.5, color=C_SLATE, family="Inter"),
    hovertemplate="<b>%{y}</b><br>%{x:,.0f} procedimentos<extra></extra>",
))
_periodo_mun = str(mun_ano) if mun_ano != "Todos" else "Jan/2024–Jan/2026"
_h_mun = max(360, mun_n * 30)
apply_theme(fig_mun, height=_h_mun, show_legend=False)
fig_mun.update_layout(
    title_text=f"Qtd. Aprovada Acumulada — {_periodo_mun}",
    margin=dict(l=8, r=90, t=44, b=8),
)
fig_mun.update_xaxes(title_text="Qtd. Aprovada", tickformat=".2s")
st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
st.plotly_chart(fig_mun, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. Variação Anual
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Variação Anual — 2024 vs 2025</p></div>
<p class="sec-desc">Comparação entre Janeiro e Dezembro de cada ano (12 meses completos). O ano de 2026 é excluído por conter apenas Janeiro.</p>
""", unsafe_allow_html=True)

# Restringe a comparação a 2024 e 2025 (anos com 12 meses completos)
_anos_var = [y for y in sorted(df_qtd["ano"].unique().tolist()) if y != 2026]
_vc1, _vc2, _vc3 = st.columns([2, 2, 3])
with _vc1:
    var_base = st.selectbox("Ano base", _anos_var, index=0, key="var_base")
with _vc2:
    _comp_opts = [y for y in _anos_var if y != var_base]
    var_comp = st.selectbox("Ano comparado", _comp_opts,
                            index=0, key="var_comp")
with _vc3:
    var_n = st.slider("Subgrupos no ranking", 4, 15, 8, key="var_n")

# Filtra estritamente Jan–Dez de cada ano (meses 1–12)
_df_base     = df_qtd[(df_qtd["ano"] == var_base)   & (df_qtd["mes"].between(1, 12))]
_df_comp     = df_qtd[(df_qtd["ano"] == var_comp)   & (df_qtd["mes"].between(1, 12))]
_df_base_val = df_valor[(df_valor["ano"] == var_base) & (df_valor["mes"].between(1, 12))]
_df_comp_val = df_valor[(df_valor["ano"] == var_comp) & (df_valor["mes"].between(1, 12))]

anual_qtd_v = {var_base: _df_base["Total"].sum(), var_comp: _df_comp["Total"].sum()}
anual_val_v = {var_base: _df_base_val["Total"].sum(), var_comp: _df_comp_val["Total"].sum()}
anos_sel_v  = sorted({var_base, var_comp})

_s_base = _df_base[SUBGRUPOS].sum()
_s_comp = _df_comp[SUBGRUPOS].sum()

# Só inclui subgrupos com 12 meses de dados em ambos os anos (evita distorção de subgrupos recém-criados)
_meses_ativos_base = (df_qtd[df_qtd["ano"] == var_base][SUBGRUPOS] > 0).any().pipe(
    lambda _: df_qtd[df_qtd["ano"] == var_base].groupby("mes")[SUBGRUPOS].sum().gt(0).sum()
)
_sub_12_base = set(_meses_ativos_base[_meses_ativos_base == 12].index)
_meses_ativos_comp = df_qtd[df_qtd["ano"] == var_comp].groupby("mes")[SUBGRUPOS].sum().gt(0).sum()
_sub_12_comp = set(_meses_ativos_comp[_meses_ativos_comp == 12].index)
_subs_validos = list(_sub_12_base & _sub_12_comp)

_n_excluidos = len(SUBGRUPOS) - len(_subs_validos)
cresc_sub_v = (
    (_s_comp[_subs_validos] - _s_base[_subs_validos])
    / _s_base[_subs_validos].replace(0, np.nan) * 100
).dropna().sort_values()

if _n_excluidos > 0:
    st.caption(
        f"ℹ️ {_n_excluidos} subgrupo(s) excluído(s) do ranking por não ter dados nos 12 meses "
        f"de {var_base} ou {var_comp} (subgrupos recém-implantados ou com registro irregular)."
    )

col_anual, col_cresc = st.columns(2, gap="medium")

with col_anual:
    _q_base = anual_qtd_v[var_base]
    _q_comp = anual_qtd_v[var_comp]
    _v_base = anual_val_v[var_base]
    _v_comp = anual_val_v[var_comp]
    _dq = (_q_comp - _q_base) / _q_base * 100
    _dv = (_v_comp - _v_base) / _v_base * 100

    _x_labels = [str(var_base), str(var_comp)]
    fig_anual = go.Figure()
    fig_anual.add_trace(go.Bar(
        name="Qtd. (Bi proc.)",
        x=_x_labels,
        y=[_q_base / 1e9, _q_comp / 1e9],
        marker_color=C_BLUE2,
        text=[f"{_q_base/1e9:.2f}Bi", f"{_q_comp/1e9:.2f}Bi"],
        textposition="outside",
        textfont=dict(size=11, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Qtd: %{y:.2f}Bi<extra></extra>",
    ))
    fig_anual.add_trace(go.Bar(
        name="Valor (R$ Bi)",
        x=_x_labels,
        y=[_v_base / 1e9, _v_comp / 1e9],
        marker_color=C_GREEN2,
        text=[f"R${_v_base/1e9:.1f}Bi", f"R${_v_comp/1e9:.1f}Bi"],
        textposition="outside",
        textfont=dict(size=11, family="Inter"),
        hovertemplate="<b>%{x}</b><br>Valor: R$%{y:.2f}Bi<extra></extra>",
    ))
    _cor_delta = C_GREEN if _dq >= 0 else C_RED
    fig_anual.add_annotation(
        xref="paper", yref="paper", x=0.5, y=1.18,
        text=f"{var_base}→{var_comp}: <b>{_dq:+.1f}%</b> Qtd · <b>{_dv:+.1f}%</b> Valor",
        showarrow=False,
        font=dict(size=11, color=_cor_delta, family="Inter"),
        bgcolor="white", bordercolor=C_BORDER, borderwidth=1, borderpad=5,
    )
    apply_theme(fig_anual, height=380)
    fig_anual.update_layout(
        title_text=f"Jan–Dez {var_base} vs Jan–Dez {var_comp}",
        barmode="group",
        hovermode="closest",
    )
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_anual, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_cresc:
    extremos = pd.concat([cresc_sub_v.head(var_n), cresc_sub_v.tail(var_n)])
    cores = [C_RED if v < 0 else C_BLUE1 for v in extremos.values]
    fig_cresc = go.Figure(go.Bar(
        x=extremos.values,
        y=[s[5:38] for s in extremos.index],
        orientation="h",
        marker=dict(color=cores, opacity=0.85, line=dict(color="rgba(0,0,0,0)")),
        text=[f"{v:+.0f}%" for v in extremos.values],
        textposition="outside",
        textfont=dict(size=10, family="Inter", color=C_SLATE),
        hovertemplate="<b>%{y}</b><br>%{x:+.1f}%<extra></extra>",
    ))
    fig_cresc.add_vline(x=0, line_width=1.5, line_color=C_DEEP, opacity=0.4)
    _h_cresc = max(380, len(extremos) * 28)
    apply_theme(fig_cresc, height=_h_cresc, show_legend=False)
    fig_cresc.update_layout(
        title_text=f"Altas e Quedas por Subgrupo — Jan–Dez {var_base}→{var_comp}",
        margin=dict(l=8, r=52, t=44, b=8),
    )
    fig_cresc.update_xaxes(title_text="Variação %", ticksuffix="%")
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_cresc, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 5. Distribuição de Municípios
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Distribuição dos Municípios por Volume de Produção</p></div>
<p class="sec-desc">A maioria dos municípios produz entre 1M e 10M de procedimentos. A cauda longa à direita revela a concentração nos grandes centros.</p>
""", unsafe_allow_html=True)

_anos_dist = ["Todos"] + sorted(df_qtd["ano"].unique().tolist())
_dc1, _dc2 = st.columns([2, 5])
with _dc1:
    dist_ano = st.selectbox("Ano", _anos_dist, key="dist_ano")

_df_dist = df_qtd if dist_ano == "Todos" else df_qtd[df_qtd["ano"] == dist_ano]
prod_mun_f = (
    _df_dist[_df_dist["municipio"].str.strip() != ""]
    .groupby("municipio")["Total"].sum()
)

faixas = pd.cut(
    prod_mun_f,
    bins=[0, 1_000, 100_000, 1_000_000, 10_000_000, 100_000_000, float("inf")],
    labels=["< 1K", "1K–100K", "100K–1M", "1M–10M", "10M–100M", "> 100M"],
)
dist = faixas.value_counts().sort_index().reset_index()
dist.columns = ["Faixa","Municípios"]
dist["Pct"] = dist["Municípios"] / len(prod_mun_f) * 100

col_dist, col_box = st.columns(2, gap="medium")

with col_dist:
    fig_dist = go.Figure(go.Bar(
        x=dist["Faixa"].astype(str),
        y=dist["Municípios"],
        marker=dict(
            color=dist["Municípios"],
            colorscale=[[0, C_BLUE4], [1, C_BLUE1]],
            line=dict(color="rgba(0,0,0,0)"),
        ),
        text=[f"{r.Municípios:,}<br><span style='font-size:9px'>{r.Pct:.1f}%</span>"
              for r in dist.itertuples()],
        textposition="outside",
        textfont=dict(size=10.5, family="Inter"),
        hovertemplate="<b>%{x}</b><br>%{y:,} municípios<extra></extra>",
    ))
    apply_theme(fig_dist, height=380, show_legend=False)
    fig_dist.update_layout(title_text="Municípios por Faixa de Produção Acumulada")
    fig_dist.update_yaxes(title_text="Nº de Municípios")
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_dist, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_box:
    prod_pos = prod_mun_f[prod_mun_f > 0]
    pctls    = np.percentile(prod_pos, [25, 50, 75, 90, 99])
    fig_box  = go.Figure()
    fig_box.add_trace(go.Box(
        y=prod_pos.values, name="Municípios",
        marker_color=C_BLUE2, line_color=C_BLUE1,
        fillcolor=C_BLUE5, opacity=0.9,
        boxmean=True, boxpoints=False,
        hoverinfo="y",
    ))
    colors_pct = [C_SLATE, C_BLUE1, C_BLUE1, C_AMBER, C_RED]
    for pv, lbl, col in zip(pctls, ["P25","P50","P75","P90","P99"], colors_pct):
        fig_box.add_hline(
            y=pv, line_dash="dot", line_color=col, line_width=1.5,
            annotation_text=f"<b>{lbl}</b> {pv:,.0f}",
            annotation_position="right",
            annotation_font=dict(size=9.5, color=col, family="Inter"),
        )
    apply_theme(fig_box, height=380, show_legend=False)
    fig_box.update_yaxes(type="log", title_text="Qtd. Aprovada (log)")
    fig_box.update_layout(title_text="Dispersão por Município (escala log)")
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig_box, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 6. Insights
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="sec-header"><div class="sec-bar"></div><p class="sec-title">Principais Achados e Recomendações</p></div>
<p class="sec-desc">Síntese analítica dos padrões identificados — base para decisões de monitoramento e planejamento.</p>
""", unsafe_allow_html=True)

top1_sub = top_sub.iloc[0]
top1_mun = top_mun.iloc[0]

st.markdown(f"""
<div class="insight-grid">
  <div class="insight-card ov">
    <div class="i-head">
      <div class="i-dot"></div>
      <span class="i-title">Visão Geral do Dataset</span>
    </div>
    <ul>
      <li><span class="bullet">—</span><span><strong>{n_mun:,} municípios</strong> com produção registrada</span></li>
      <li><span class="bullet">—</span><span><strong>{len(SUBGRUPOS)} subgrupos</strong> de procedimento</span></li>
      <li><span class="bullet">—</span><span>Qtd. total: <strong>{qtd_total/1e9:.2f} bilhões</strong> de procedimentos</span></li>
      <li><span class="bullet">—</span><span>Valor total: <strong>R$ {val_total/1e9:.2f} bilhões</strong></span></li>
      <li><span class="bullet">—</span><span>Apenas <strong>{zeradas:.1f}%</strong> das linhas sem produção — dados bem preenchidos</span></li>
    </ul>
  </div>
  <div class="insight-card tr">
    <div class="i-head">
      <div class="i-dot"></div>
      <span class="i-title">Tendência e Sazonalidade</span>
    </div>
    <ul>
      <li><span class="bullet">—</span><span>Crescimento de <strong>+{cresc_pct:.1f}%</strong> em quantidade (2024→2025)</span></li>
      <li><span class="bullet">—</span><span>Pico em <strong>Out/2025</strong> — maior mês da série histórica</span></li>
      <li><span class="bullet">—</span><span>Quedas sazonais em <strong>Dez/Jan</strong> (férias e feriados)</span></li>
      <li><span class="bullet">—</span><span>Tendência de alta sustentada ao longo dos 25 meses</span></li>
    </ul>
  </div>
  <div class="insight-card al">
    <div class="i-head">
      <div class="i-dot"></div>
      <span class="i-title">Concentração de Procedimentos</span>
    </div>
    <ul>
      <li><span class="bullet">—</span><span><strong>{top1_sub['subgrupo'][5:50]}</strong> lidera com {top1_sub['pct']:.1f}% do top-10</span></li>
      <li><span class="bullet">—</span><span>Consultas + Laboratório: <strong>~51,7%</strong> de toda a produção</span></li>
      <li><span class="bullet">—</span><span><strong>{top1_mun['municipio']}</strong> concentra {top1_mun['pct']:.1f}% da produção nacional</span></li>
      <li><span class="bullet">—</span><span>Distribuição geográfica relativamente descentralizada</span></li>
    </ul>
  </div>
  <div class="insight-card ac">
    <div class="i-head">
      <div class="i-dot"></div>
      <span class="i-title">Recomendações de Ação</span>
    </div>
    <ul>
      <li><span class="bullet">—</span><span>Monitorar subgrupos em queda para identificar problemas de <strong>acesso</strong></span></li>
      <li><span class="bullet">—</span><span>Investigar municípios com produção zero em múltiplos meses (<strong>subnotificação</strong>)</span></li>
      <li><span class="bullet">—</span><span>Usar sazonalidade Dez/Jan para <strong>planejamento de capacidade</strong></span></li>
      <li><span class="bullet">—</span><span>Cruzar com população IBGE para calcular <strong>cobertura per capita</strong></span></li>
    </ul>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="dash-footer">Desenvolvido com Streamlit + Plotly &nbsp;·&nbsp; '
    'Fonte: DATASUS TabNet / SIA/SUS &nbsp;·&nbsp; '
    'Dados: Janeiro 2024 — Janeiro 2026</div>',
    unsafe_allow_html=True,
)

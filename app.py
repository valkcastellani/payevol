import datetime
import streamlit as st
import pandas as pd
import altair as alt

from payevol.core.dates import add_months, first_day_current_month
from payevol.core.formatting import brl
from payevol.services.min_wage import fetch_min_wage_changes, min_wage_at
from payevol.services.ipca import fetch_ipca_number_index
from payevol.services.series import (
    build_equivalent_salary_series_sm,
    build_ipca_adjusted_series,
)
from payevol.services.inpc import fetch_inpc_number_index
from payevol.services.series import build_inpc_adjusted_series

APP_TITLE = "payEvol - Evolução Salarial"
MIN_REF = datetime.date(1994, 7, 1)

# ---------------- UI ----------------

st.set_page_config(page_title=APP_TITLE, page_icon="💸", layout="wide")

# container mais largo + inputs mais compactos
st.markdown(
    """
<style>
/* =========================
   payEvol - Clean Modern UI
   ========================= */

/* ---- layout base ---- */
.block-container{
  max-width: 1180px;
  padding-top: 1.2rem;
  padding-bottom: 2.0rem;
}

h1, h2, h3, h4{
  letter-spacing: -0.02em;
}

:root{
  /* neutros */
  --bg: #ffffff;
  --card: #ffffff;
  --muted: rgba(49,51,63,.62);
  --text: rgba(49,51,63,.92);

  /* bordas + sombras */
  --border: rgba(49,51,63,.12);
  --shadow: 0 8px 30px rgba(16,24,40,.06);

  /* acento (bem discreto) */
  --accent: #2f6fed; /* azul clean */
  --accent-weak: rgba(47,111,237,.12);
}

/* ---- remove “peso” de elementos padrão ---- */
hr{
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.0rem 0 1.0rem 0 !important;
}

[data-testid="stAppViewContainer"]{
  background: var(--bg);
}

/* ---- títulos/caption mais clean ---- */
[data-testid="stCaptionContainer"]{
  color: var(--muted);
  line-height: 1.35;
}

/* ---- Inputs como “cards” ---- */
div[data-testid="stNumberInput"],
div[data-testid="stSelectbox"]{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: none;
  padding: .60rem .70rem .55rem .70rem;
}

/* deixa o label mais suave */
div[data-testid="stNumberInput"] label,
div[data-testid="stSelectbox"] label{
  color: var(--muted);
  font-weight: 600;
  font-size: .88rem;
}

/* campos internos */
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] div[role="button"]{
  padding-top: .40rem !important;
  padding-bottom: .40rem !important;
  border-radius: 10px !important;
}

/* remove bordas internas “duplas” do baseweb */
div[data-testid="stSelectbox"] div[role="button"]{
  border: 1px solid transparent !important;
}

/* foco acessível */
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stSelectbox"] div[role="button"]:focus{
  outline: none !important;
  box-shadow: 0 0 0 3px var(--accent-weak) !important;
  border-color: rgba(47,111,237,.40) !important;
}

/* ---- Remover steppers do number_input (all browsers) ---- */
div[data-testid="stNumberInput"] input[type="number"]::-webkit-outer-spin-button,
div[data-testid="stNumberInput"] input[type="number"]::-webkit-inner-spin-button{
  -webkit-appearance: none;
  margin: 0;
}
div[data-testid="stNumberInput"] input[type="number"]{
  -moz-appearance: textfield;
}

/* ---- Métricas como cards ---- */
[data-testid="stMetric"]{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .85rem 1rem;
  box-shadow: none;
}

[data-testid="stMetricLabel"]{
  color: var(--muted);
  font-weight: 700;
}

[data-testid="stMetricValue"]{
  color: var(--text);
  letter-spacing: -0.015em;
}

/* delta (quando existir) mais sutil */
[data-testid="stMetricDelta"]{
  font-weight: 700;
}

/* ---- Dataframe / tabela clean ---- */
[data-testid="stDataFrame"]{
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}

/* ---- Expander como card ---- */
details[data-testid="stExpander"]{
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .25rem .60rem;
  background: var(--card);
}

details[data-testid="stExpander"] summary{
  font-weight: 700;
  color: var(--text);
}

/* ---- Gráfico: dá “respiro” ---- */
[data-testid="stVegaLiteChart"], 
[data-testid="stArrowVegaLiteChart"],
[data-testid="stLineChart"]{
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: .65rem .65rem .20rem .65rem;
  background: var(--card);
}

/* ---- Alertas (st.error etc) menos agressivos ---- */
div[data-testid="stAlert"]{
  border-radius: 14px;
  border: 1px solid var(--border);
  box-shadow: none;
}

/* ---- Tooltip padrão (quando houver) ---- */
[role="tooltip"]{
  border-radius: 12px !important;
}

/* ---- Pequenos ajustes de espaçamento ---- */
[data-testid="stVerticalBlock"] > div:has(> [data-testid="stMetric"]){
  gap: .85rem;
}

/* ---- Mobile: reduz padding ---- */
@media (max-width: 900px){
  .block-container{ padding-left: 1rem; padding-right: 1rem; }
}

div[data-testid="stNumberInputContainer"] { 
  background-color: #f0f2f6; /* cor de fundo mais clara */ 
}
[data-testid="stVegaLiteChart"], 
[data-testid="stArrowVegaLiteChart"],
[data-testid="stLineChart"]{
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--card);

  /* ajuste crítico */
  overflow: hidden;

  /* recomendo reduzir/remover o padding para não “empurrar” o SVG */
  padding: 0.35rem 0.35rem 0.10rem 0.35rem; /* ou até 0 */
}
</style>
""",
    unsafe_allow_html=True,
)

st.title("💸 payEvol — Evolução Salarial")
st.caption(
    "Entradas: mm/aaaa (mín. 07/1994) e salário na referência. "
    "O gráfico compara: (1) equivalente mantendo o mesmo nº de salários mínimos, (2) atualizado pelo IPCA, "
    "e (3) salário atual (opcional)."
)

st.divider()

# ---- Entradas em UMA LINHA ----

today_m1 = add_months(first_day_current_month(), -1)  # mês atual - 1

min_y, min_m = MIN_REF.year, MIN_REF.month
max_y, max_m = today_m1.year, today_m1.month
# anos em ordem decrescente
years = list(range(max_y, min_y - 1, -1))

default_ref = max(MIN_REF, today_m1)
default_y, default_m = default_ref.year, default_ref.month


c_y, c_m, c_sr, c_sc = st.columns([1.2, 1, 2, 2])

with c_y:
    year = st.selectbox("Ano (ref.)", years, index=years.index(default_y))

# meses válidos para o ano escolhido
if year == min_y and year == max_y:
    months = list(range(min_m, max_m + 1))
elif year == min_y:
    months = list(range(min_m, 13))
elif year == max_y:
    months = list(range(1, max_m + 1))
else:
    months = list(range(1, 13))

with c_m:
    default_month = default_m if default_m in months else months[0]
    month = st.selectbox("Mês (ref.)", months, index=months.index(default_month))

ref = datetime.date(year, month, 1)

with c_sr:
    salary_ref = st.number_input(
        "Salário (ref.) R$",
        min_value=0.00,
        step=100.00,
        value=0.00,
        format="%.2f",
    )

with c_sc:
    salary_current = st.number_input(
        "Salário atual R$ (opcional)",
        min_value=0.00,
        step=100.00,
        value=0.00,
        format="%.2f",
    )

# ---- Carrega fontes externas ----
with st.spinner("Carregando salário mínimo, IPCA e INPC..."):
    sm_changes = fetch_min_wage_changes()  # Previdenciarista
    ipca_index = fetch_ipca_number_index()  # IBGE/SIDRA (tabela 1737)
    inpc_index = fetch_inpc_number_index()  # IBGE/SIDRA (tabela 1738)


# ---- Métricas de referência ----
sm_ref = min_wage_at(ref, sm_changes)
k_sm = (float(salary_ref) / sm_ref) if sm_ref > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Referência", ref.strftime("%m/%Y"))
col2.metric("Salário (ref.)", brl(float(salary_ref)))
col3.metric("Salário mínimo (ref.)", brl(sm_ref))
col4.metric("Múltiplo na ref.", f"{k_sm:.4g} SM")

st.divider()

# ---- Séries mensais ----
st.subheader("📈 Evolução mensal: equivalente por SM, IPCA, INPC")

series_sm = build_equivalent_salary_series_sm(
    ref, float(salary_ref), sm_changes
)  # k×SM(m)
series_ipca = build_ipca_adjusted_series(
    ref, float(salary_ref), ipca_index
)  # salário_ref × I(m)/I(prev_ref)
try:
    series_inpc = build_inpc_adjusted_series(ref, float(salary_ref), inpc_index)
    inpc_ok = True
except Exception as e:
    inpc_ok = False
    st.error(f"INPC indisponível para esta referência: {e}")


# Junta para plot
plot_df = pd.DataFrame(index=series_sm["ref_date"])
plot_df["Equivalente (k×SM) R$"] = series_sm["equiv_brl"].values
plot_df["Atualizado pelo IPCA (R$)"] = (
    series_ipca.set_index("ref_date")["salary_ipca"].reindex(plot_df.index).values
)
if inpc_ok:
    plot_df["Atualizado pelo INPC (R$)"] = (
        series_inpc.set_index("ref_date")["salary_inpc"].reindex(plot_df.index).values
    )


if float(salary_current) > 0:
    plot_df["Salário atual (R$)"] = float(salary_current)

# st.line_chart(plot_df)
# --- Ajuste automático de eixo Y (min/max entre as séries exibidas) ---
# (remove colunas totalmente NaN, por exemplo INPC se não disponível)
plot_df2 = plot_df.copy()
# --- Ajuste automático de eixo Y (min/max entre as séries exibidas) ---
plot_df2 = plot_df.copy().dropna(axis=1, how="all")

y_min = float(plot_df2.min(numeric_only=True).min())
y_max = float(plot_df2.max(numeric_only=True).max())

pad = (y_max - y_min) * 0.03 if y_max > y_min else (y_max * 0.03 if y_max else 1.0)
y_domain = [y_min - pad, y_max + pad]

# --- calcula domínio X com folga (1 mês a mais) para o último ponto não sumir ---
x_min = plot_df2.index.min()
x_max = plot_df2.index.max()
x_max_plus = pd.Timestamp(add_months(x_max.date(), 1))  # +1 mês à direita

# Altair pede formato "longo"
long_df = (
    plot_df2.reset_index()
    .rename(columns={"index": "ref_date"})
    .melt(id_vars=["ref_date"], var_name="Série", value_name="Valor")
    .dropna()
)

ptBR_time_locale = {
    "dateTime": "%A, %e de %B de %Y %X",
    "date": "%d/%m/%Y",
    "time": "%H:%M:%S",
    "periods": ["AM", "PM"],
    "days": ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"],
    "shortDays": ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"],
    "months": [
        "janeiro",
        "fevereiro",
        "março",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    ],
    "shortMonths": [
        "jan",
        "fev",
        "mar",
        "abr",
        "mai",
        "jun",
        "jul",
        "ago",
        "set",
        "out",
        "nov",
        "dez",
    ],
}

chart = (
    alt.Chart(long_df)
    .mark_line(point=alt.OverlayMarkDef(filled=True, size=55))
    .encode(
        x=alt.X(
            "ref_date:T",
            title="Mês",
            scale=alt.Scale(domain=[x_min, x_max_plus]),
            # FORÇA o texto do label (não depende do locale do browser)
            axis=alt.Axis(labelExpr="timeFormat(datum.value, '%b/%Y')"),
        ),
        y=alt.Y("Valor:Q", title="R$", scale=alt.Scale(domain=y_domain)),
        color=alt.Color("Série:N", title="Séries", legend=alt.Legend(orient="bottom")),
        tooltip=[
            alt.Tooltip("ref_date:T", title="Mês", format="%B/%Y"),
            alt.Tooltip("Série:N"),
            alt.Tooltip("Valor:Q", format=",.2f", title="Valor (R$)"),
        ],
    )
    .properties(height=420, padding={"left": 8, "right": 22, "top": 6, "bottom": 6})
    .interactive()
)

spec = chart.to_dict()

# 1) locale no config do Vega-Lite
spec.setdefault("config", {})
spec["config"]["timeFormatLocale"] = ptBR_time_locale

# 2) locale também no embedOptions (Streamlit às vezes só respeita aqui)
spec.setdefault("usermeta", {})
spec["usermeta"].setdefault("embedOptions", {})
spec["usermeta"]["embedOptions"]["timeFormatLocale"] = ptBR_time_locale

# (opcional) evita sizing estranho em alguns layouts
spec.setdefault("autosize", {"type": "fit", "contains": "padding"})

st.vega_lite_chart(spec, use_container_width=True)

# ---- KPIs finais (último mês da série) ----
last_ref = series_sm["ref_date"].iloc[-1].date()
equiv_last_sm = float(series_sm["equiv_brl"].iloc[-1])
equiv_last_ipca = float(
    series_ipca.set_index("ref_date").loc[pd.Timestamp(last_ref), "salary_ipca"]
)
if inpc_ok:
    equiv_last_inpc = float(
        series_inpc.set_index("ref_date").loc[pd.Timestamp(last_ref), "salary_inpc"]
    )

m1, m2, m3, m4 = st.columns(4)
m1.metric("Último mês no gráfico", last_ref.strftime("%m/%Y"))
m2.metric("Equivalente (k×SM)", brl(equiv_last_sm))
m3.metric("Atualizado pelo IPCA", brl(equiv_last_ipca))
if inpc_ok:
    m4.metric("Atualizado pelo INPC", brl(equiv_last_inpc))

if float(salary_current) > 0:
    # comparações com salário atual
    n1, n2, n3, n4 = st.columns(4)
    n2.metric("Salário atual − (k×SM)", brl(float(salary_current) - equiv_last_sm))
    n3.metric(
        "Salário atual − Atualizado pelo IPCA",
        brl(float(salary_current) - equiv_last_ipca),
    )
    if inpc_ok:
        n4.metric(
            "Salário atual − Atualizado pelo INPC",
            brl(float(salary_current) - equiv_last_inpc),
        )

with st.expander("Ver tabela mensal"):
    tbl_dict = {
        "Mês/Ano": series_sm["mm_yyyy"],
        "Salário mínimo (R$)": series_sm["min_wage"].map(brl),
        "Equivalente (k×SM) (R$)": series_sm["equiv_brl"].map(brl),
        "Atualizado pelo IPCA (R$)": series_ipca.set_index("ref_date")["salary_ipca"]
        .reindex(series_sm["ref_date"])
        .map(brl)
        .values,
    }
    if inpc_ok:
        tbl_dict["Atualizado pelo INPC (R$)"] = (
            series_inpc.set_index("ref_date")["salary_inpc"]
            .reindex(series_sm["ref_date"])
            .map(brl)
            .values
        )
    tbl = pd.DataFrame(tbl_dict)
    st.dataframe(tbl, use_container_width=True)


st.caption(
    "Fontes: salário mínimo (Previdenciarista), IPCA (IBGE/SIDRA – tabela 1737) e INPC (IBGE/SIDRA – tabela 1738)."
)

# ---- Rodapé ----
import datetime
import streamlit as st
import streamlit.components.v1 as components

ano_atual = datetime.date.today().year
APP_NAME = "payEvol"
APP_VERSION = "v0.1.2"  # opcional

footer_html = f"""
<div style="margin-top:2.0rem;">
  <div style="
    border: 1px solid rgba(49,51,63,0.12);
    border-radius: 14px;
    padding: 0.95rem 1rem;
    background: #fff;
  ">
    <div style="
      display:flex;
      justify-content:space-between;
      align-items:center;
      flex-wrap:wrap;
      gap:0.5rem 1rem;
      font-size:0.92rem;
      color: rgba(49,51,63,0.85);
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    ">
      <div style="display:flex; align-items:center; gap:0.6rem; flex-wrap:wrap;">
        <span style="font-weight:800; color: rgba(49,51,63,0.95);">{APP_NAME}</span>
        <span style="opacity:0.70;">{APP_VERSION}</span>
        <span style="opacity:0.45;">•</span>
        <span>© 2025–{ano_atual} <b style="font-weight:800;">Valk Castellani</b></span>
      </div>

      <div style="display:flex; align-items:center; gap:0.85rem; flex-wrap:wrap;">
        <a href="https://www.linkedin.com/in/valkcastellani" target="_blank"
           style="text-decoration:none; font-weight:800; color: rgba(49,51,63,0.88);">
           LinkedIn</a>
        <span style="opacity:0.35;">|</span>
        <a href="https://github.com/valkcastellani" target="_blank"
           style="text-decoration:none; font-weight:800; color: rgba(49,51,63,0.88);">
           GitHub</a>
        <span style="opacity:0.35;">|</span>
        <a href="https://github.com/valkcastellani/payEvol" target="_blank"
           style="text-decoration:none; font-weight:800; color: rgba(49,51,63,0.88);">
           Repositório</a>
      </div>
    </div>

    <div style="margin-top:0.55rem; font-size:0.82rem; color: rgba(49,51,63,0.62); line-height:1.35;">
      Índices e cálculos: confira as fontes oficiais no README do projeto.
    </div>
  </div>
</div>
"""

# height: ajuste se você acrescentar mais linhas
components.html(footer_html, height=110)

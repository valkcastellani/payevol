from datetime import date
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
MIN_REF = date(1994, 7, 1)

# ---------------- UI ----------------

st.set_page_config(page_title=APP_TITLE, page_icon="💸", layout="wide")

# container mais largo + inputs mais compactos
st.markdown(
    """
    <style>
      .block-container { max-width: 1250px; padding-top: 1.2rem; }
      div[data-testid="stNumberInput"] input { padding-top: .25rem; padding-bottom: .25rem; }
      div[data-testid="stSelectbox"] div[role="button"] { padding-top: .25rem; padding-bottom: .25rem; }
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
years = list(range(min_y, max_y + 1))

default_ref = max(MIN_REF, today_m1)
default_y, default_m = default_ref.year, default_ref.month

c_m, c_y, c_sr, c_sc = st.columns([1, 1.2, 2, 2])

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

ref = date(year, month, 1)

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
st.subheader("📈 Evolução mensal: equivalente por SM vs IPCA")

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
plot_df2 = plot_df2.dropna(axis=1, how="all")

# calcula min/max global entre as séries
y_min = float(plot_df2.min(numeric_only=True).min())
y_max = float(plot_df2.max(numeric_only=True).max())

# pequena folga para não “colar” no topo/rodapé
pad = (y_max - y_min) * 0.03 if y_max > y_min else (y_max * 0.03 if y_max else 1.0)
y_domain = [y_min - pad, y_max + pad]

# Altair pede formato "longo"
long_df = (
    plot_df2.reset_index()
    .rename(columns={"index": "ref_date"})
    .melt(id_vars=["ref_date"], var_name="Série", value_name="Valor")
    .dropna()
)

chart = (
    alt.Chart(long_df)
    .mark_line()
    .encode(
        x=alt.X("ref_date:T", title="Mês"),
        y=alt.Y("Valor:Q", title="R$", scale=alt.Scale(domain=y_domain)),
        color=alt.Color("Série:N", title="Séries"),
        tooltip=[
            alt.Tooltip("ref_date:T", title="Mês"),
            alt.Tooltip("Série:N"),
            alt.Tooltip("Valor:Q", format=",.2f", title="Valor (R$)"),
        ],
    )
    .properties(height=420)
    .interactive()
)

st.altair_chart(chart, use_container_width=True)

# ---- KPIs finais (último mês da série) ----
last_ref = series_sm["ref_date"].iloc[-1].date()
equiv_last_sm = float(series_sm["equiv_brl"].iloc[-1])
equiv_last_ipca = float(
    series_ipca.set_index("ref_date").loc[pd.Timestamp(last_ref), "salary_ipca"]
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Último mês no gráfico", last_ref.strftime("%m/%Y"))
m2.metric("Equivalente (k×SM)", brl(equiv_last_sm))
m3.metric("Atualizado pelo IPCA", brl(equiv_last_ipca))

if float(salary_current) > 0:
    # comparações com salário atual
    m4.metric("Salário atual − (k×SM)", brl(float(salary_current) - equiv_last_sm))

with st.expander("Ver tabela mensal"):
    tbl = pd.DataFrame(
        {
            "Mês/Ano": series_sm["mm_yyyy"],
            "Salário mínimo (R$)": series_sm["min_wage"].map(brl),
            "Equivalente (k×SM) (R$)": series_sm["equiv_brl"].map(brl),
            "Atualizado pelo IPCA (R$)": series_ipca.set_index("ref_date")[
                "salary_ipca"
            ]
            .reindex(series_sm["ref_date"])
            .map(brl)
            .values,
            "Atualizado pelo INPC (R$)": series_inpc.set_index("ref_date")[
                "salary_inpc"
            ]
            .reindex(series_sm["ref_date"])
            .map(brl)
            .values,
        }
    )
    st.dataframe(tbl, use_container_width=True)


st.caption(
    "Fontes: salário mínimo (Previdenciarista), IPCA (IBGE/SIDRA – tabela 1737) e INPC (IBGE/SIDRA – tabela 1738)."
)

from __future__ import annotations

from datetime import date
import re
import pandas as pd
import requests
import streamlit as st

INPC_1736_ALL = "https://apisidra.ibge.gov.br/values/h/n/t/1736/p/all/n1/all/v/all"

_RX_DNC = re.compile(r"^D\d+N$")
_RX_DCC = re.compile(r"^D\d+C$")


def _to_float_ptbr(s: str) -> float:
    s = s.strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _find_period_yyyymm(item: dict) -> str | None:
    for k, v in item.items():
        if not _RX_DCC.match(str(k)):
            continue
        vv = str(v).strip()
        if vv.isdigit() and len(vv) == 6:
            return vv
    return None


def _pick_dim_names(item: dict) -> list[str]:
    out = []
    for k, v in item.items():
        if _RX_DNC.match(str(k)):
            out.append(str(v).strip())
    return out


def _is_numero_indice(dim_names: list[str]) -> bool:
    targets = {"número-índice", "numero-índice", "número índice", "numero indice"}
    return any(s.strip().lower() in targets for s in dim_names)


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def _fetch_inpc_index_from_1736() -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(INPC_1736_ALL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("INPC (SIDRA 1736): resposta inesperada.")

    rows = []
    for item in data[1:]:
        if not isinstance(item, dict):
            continue

        dim_names = _pick_dim_names(item)
        if not _is_numero_indice(dim_names):
            continue

        period = _find_period_yyyymm(item)
        val = str(item.get("V", "")).strip()
        if not (period and val):
            continue

        try:
            y = int(period[:4])
            m = int(period[4:])
            v = _to_float_ptbr(val)
        except Exception:
            continue

        rows.append((date(y, m, 1), v))

    df = pd.DataFrame(rows, columns=["ref_date", "inpc_index"]).drop_duplicates()
    df = df.sort_values("ref_date").reset_index(drop=True)

    if df.empty:
        raise RuntimeError("INPC (SIDRA 1736): não encontrei a série 'Número-índice'.")
    return df


def _build_chain_index_from_7063() -> pd.DataFrame:
    """
    Fallback: usa 7063 (variação mensal %) e reconstrói um índice encadeado.

    Se a série começar em X, cria um ponto-base no mês anterior a X com índice 100.
    Como o cálculo final usa razão I(m)/I(prev_ref), a base (100) cancela e serve perfeitamente.
    """
    from payevol.services.inpc_var_7063 import fetch_inpc_monthly_variation_7063

    var_df = fetch_inpc_monthly_variation_7063(item_name="Índice geral")
    var_df = var_df.sort_values("ref_date").reset_index(drop=True)

    if var_df.empty:
        raise RuntimeError("INPC (fallback 7063): sem dados de variação mensal.")

    first_month: date = var_df["ref_date"].iloc[0]
    base_month = _add_months(first_month, -1)

    idx_rows = [(base_month, 100.0)]
    current_index = 100.0

    for _, row in var_df.iterrows():
        m = row["ref_date"]
        var_pct = float(row["inpc_var_mensal_pct"])
        current_index = current_index * (1.0 + var_pct / 100.0)
        idx_rows.append((m, current_index))

    df = pd.DataFrame(idx_rows, columns=["ref_date", "inpc_index"])
    df = df.drop_duplicates().sort_values("ref_date").reset_index(drop=True)
    return df


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fetch_inpc_number_index() -> pd.DataFrame:
    """
    INPC mensal em número-índice:
      - tenta SIDRA 1736 (preferencial)
      - se falhar, fallback SIDRA 7063 (variação mensal %) encadeando um índice base
    """
    try:
        df = _fetch_inpc_index_from_1736()
        df["source"] = "sidra-1736"
        return df
    except Exception:
        df = _build_chain_index_from_7063()
        df["source"] = "sidra-7063-chain"
        return df

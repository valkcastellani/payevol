from __future__ import annotations

from datetime import date
import re
import pandas as pd
import requests
import streamlit as st

# Tabela 7063 (a partir de jan/2020): INPC - variações e peso mensal (índice geral e grupos etc.)
# Usamos v/all e filtramos por nome de variável e item/subitem (ex.: "Índice geral").
SIDRA_7063_ALL = "https://apisidra.ibge.gov.br/values/h/n/t/7063/p/all/n1/all/v/all"

_RX_DNC = re.compile(r"^D\d+N$")
_RX_DCC = re.compile(r"^D\d+C$")


def _to_float_ptbr(s: str) -> float:
    s = s.strip()
    # "1,23" -> 1.23 ; "-0,60" -> -0.60 ; "1.234,56" -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _find_period_yyyymm(item: dict) -> str | None:
    """
    A dimensão de período no SIDRA geralmente vem como D?C no formato YYYYMM.
    Ex.: "202001" (jan/2020).
    """
    for k, v in item.items():
        if not _RX_DCC.match(str(k)):
            continue
        vv = str(v).strip()
        if vv.isdigit() and len(vv) == 6:
            return vv
    return None


def _pick_dimension_names(item: dict) -> list[str]:
    """
    Retorna todos os D?N (nomes de dimensões) da linha, para filtragem por texto.
    """
    out = []
    for k, v in item.items():
        if _RX_DNC.match(str(k)):
            out.append(str(v).strip())
    return out


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def fetch_inpc_monthly_variation_7063(
    item_name: str = "Índice geral", variable_contains: str = "Variação mensal"
) -> pd.DataFrame:
    """
    Retorna INPC - Variação mensal (%) para:
      - Brasil (n1/all)
      - item/grupo: "Índice geral" (por padrão)
      - variável cujo nome contém "Variação mensal" (por padrão)
      - meses: todos (p/all) [a tabela 7063 começa em 2020-01]

    Saída:
      ref_date (date no 1º dia do mês)
      inpc_var_mensal_pct (float, em %)
      variable_name (str)
      item_name (str)
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(SIDRA_7063_ALL, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    if not isinstance(data, list) or len(data) < 2:
        raise RuntimeError("Resposta inesperada do SIDRA (tabela 7063).")

    rows = []
    item_name_norm = item_name.strip().lower()
    var_contains_norm = variable_contains.strip().lower()

    for item in data[1:]:
        if not isinstance(item, dict):
            continue

        # nome da variável vem como algum D?N. Vamos filtrar:
        dim_names = _pick_dimension_names(item)
        dim_names_norm = [s.lower() for s in dim_names]

        # precisa conter "Variação mensal" em algum D?N
        if not any(var_contains_norm in s for s in dim_names_norm):
            continue

        # precisa conter o item desejado (Índice geral) em algum D?N
        if not any(item_name_norm == s for s in dim_names_norm):
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

        # tenta capturar um "nome de variável" mais amigável, se existir
        # (se não achar, guarda vazio)
        var_name = next(
            (s for s in dim_names if variable_contains.lower() in s.lower()), ""
        )
        rows.append((date(y, m, 1), v, var_name, item_name))

    df = pd.DataFrame(
        rows, columns=["ref_date", "inpc_var_mensal_pct", "variable_name", "item_name"]
    )
    df = df.drop_duplicates().sort_values("ref_date").reset_index(drop=True)

    if df.empty:
        raise RuntimeError(
            "Não consegui filtrar a variação mensal do INPC na tabela 7063."
        )
    return df

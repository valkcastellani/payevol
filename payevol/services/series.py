from datetime import date
import pandas as pd

from payevol.core.dates import add_months, first_day_current_month
from payevol.services.min_wage import min_wage_at

def build_equivalent_salary_series_sm(ref: date, salary_ref: float, sm_changes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Série mensal ref -> (mês atual - 1) com:
      k = salary_ref / SM_ref
      equiv_brl(m) = k * SM(m)
    """
    end_ref = add_months(first_day_current_month(), -1)
    if ref > end_ref:
        end_ref = ref

    months = pd.date_range(start=ref, end=end_ref, freq="MS")
    base = pd.DataFrame({"ref_date": months}).sort_values("ref_date")

    changes = sm_changes_df.copy()
    changes["ref_date"] = pd.to_datetime(changes["ref_date"])
    changes = changes.sort_values("ref_date")

    out = pd.merge_asof(base, changes, on="ref_date", direction="backward")

    sm_ref = min_wage_at(ref, sm_changes_df)
    k = float(salary_ref) / float(sm_ref)

    out["salary_ref"] = float(salary_ref)
    out["sm_ref"] = float(sm_ref)
    out["k_sm"] = float(k)
    out["equiv_brl"] = out["k_sm"] * out["min_wage"]
    out["mm_yyyy"] = out["ref_date"].dt.strftime("%m/%Y")
    return out

def build_index_adjusted_series(ref: date, salary_ref: float, index_df: pd.DataFrame, index_col: str, out_col: str) -> pd.DataFrame:
    """
    Série mensal ref -> (mês atual - 1), usando número-índice:
      salary_adj(m) = salary_ref * I(m) / I(mês_anterior_ref)
    index_col: nome da coluna com número-índice no dataframe (ex.: ipca_index / inpc_index)
    out_col: nome da coluna de saída (ex.: salary_ipca / salary_inpc)
    """
    end_ref = add_months(first_day_current_month(), -1)
    if ref > end_ref:
        end_ref = ref

    months = pd.date_range(start=ref, end=end_ref, freq="MS")
    base = pd.DataFrame({"ref_date": months}).sort_values("ref_date")

    idx = index_df.copy()
    idx["ref_date"] = pd.to_datetime(idx["ref_date"])
    idx = idx.sort_values("ref_date")

    out = pd.merge_asof(base, idx, on="ref_date", direction="backward")
    out.rename(columns={index_col: "I_m"}, inplace=True)

    prev_ref = add_months(ref, -1)
    q = pd.DataFrame({"ref_date": [pd.to_datetime(prev_ref)]}).sort_values("ref_date")
    prev = pd.merge_asof(q, idx, on="ref_date", direction="backward")

    if prev.empty or pd.isna(prev.loc[0, index_col]):
        first_avail = idx["ref_date"].min().date()
        raise RuntimeError(
            f"{out_col}: não há índice disponível para {prev_ref.strftime('%m/%Y')} (mês anterior à referência). "
            f"Série disponível a partir de {first_avail.strftime('%m/%Y')}. "
            "Escolha uma referência igual ou posterior ao início da série."
        )

    I_prev = float(prev.loc[0, index_col])
    if I_prev <= 0:
        raise RuntimeError(
            f"{out_col}: índice inválido para {prev_ref.strftime('%m/%Y')}. "
            "Tente novamente mais tarde."
        )

    out["salary_ref"] = float(salary_ref)
    out["I_prev_ref"] = I_prev
    out[out_col] = float(salary_ref) * (out["I_m"] / I_prev)
    return out

def build_ipca_adjusted_series(ref: date, salary_ref: float, ipca_df: pd.DataFrame) -> pd.DataFrame:
    return build_index_adjusted_series(ref, salary_ref, ipca_df, "ipca_index", "salary_ipca")

def build_inpc_adjusted_series(ref: date, salary_ref: float, inpc_df: pd.DataFrame) -> pd.DataFrame:
    return build_index_adjusted_series(ref, salary_ref, inpc_df, "inpc_index", "salary_inpc")

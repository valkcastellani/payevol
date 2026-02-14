def brl(value: float) -> str:
    # Formatação pt-BR sem depender de locale do SO
    s = f"{value:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

import pandas as pd

def dataframe_to_records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []

    out = df.copy()

    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].astype(str)

    out = out.astype(object).where(pd.notnull(out), None)

    return out.to_dict(orient="records")

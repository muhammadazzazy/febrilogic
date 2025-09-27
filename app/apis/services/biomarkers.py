"""Service to handle biomarker statistics."""
from functools import lru_cache

import pandas as pd
from pandas import DataFrame


from apis.config import BIOMARKER_STATS_FILE


@lru_cache(maxsize=1)
def get_biomarker_stats() -> DataFrame:
    """Get cached biomarker statistics dataframe."""
    biomarker_df: DataFrame = pd.read_csv(BIOMARKER_STATS_FILE)
    biomarker_df['disease'] = biomarker_df['disease'].astype(str).str.strip()
    return biomarker_df

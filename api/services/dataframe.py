from typing import Dict
import os
import vaex
from vaex.dataframe import DataFrame
from fastapi.exceptions import HTTPException
from transformers import AutoModel

DF_PATH = f"{os.getcwd()}/dataframes"
os.makedirs(DF_PATH, exist_ok=True)


class DataFrameService:
    """A class for handling cold-start data, processing it, and investigating it"""
    def __init__(self) -> None:
        self.dataframes: Dict[str, DataFrame] = {}

    def _validate_file(self, name) -> bool:
        """Makes sure the file exists and is a csv"""
        return os.path.isfile(name) and os.path.splitext(name)[-1] == ".csv"

    def _get_text_length(self, df: DataFrame) -> DataFrame:
        df_copy = df.copy()
        df_copy["text_length"] = df["text"].str.len()
        return df_copy

    def process_upload_data(self, name: str) -> None:
        """processes a dataframe for handling"""
        if not self._validate_file(name):
            raise HTTPException(
                status_code=400,
                detail=f"File {name} is either not available or not a csv"
            )
        df = vaex.open(name)
        if "text" not in df.get_column_names():
            raise HTTPException(
                status_code=400,
                detail=f"File {name} has no 'text' column. Uploaded data must have text"
            )
        df = self._get_text_length(df)



# ./services/dataframe_store.py

import pandas as pd

class DataFrameStore:
    _instance = None # Armazena a única instância da classe
    _metadata_store = pd.DataFrame(columns=['table_name', 'column_name', 'data_type', 'source_file'])

    def __new__(cls):
        """
        Garante que apenas uma instância de DataFrameStore seja criada (Singleton).
        """
        if cls._instance is None:
            cls._instance = super(DataFrameStore, cls).__new__(cls)
        return cls._instance

    def add_metadata(self, table_name: str, metadata_df: pd.DataFrame):
        """
        Adiciona metadados de uma nova tabela ao store.
        Remove metadados existentes para a mesma table_name antes de adicionar novos,
        garantindo que os metadados estejam sempre atualizados.

        Args:
            table_name (str): O nome da tabela à qual os metadados pertencem.
            metadata_df (pd.DataFrame): Um DataFrame contendo as colunas:
                                        'column_name', 'data_type', 'table_name', 'source_file'.
        """
        # Garante que o DataFrame de entrada tenha as colunas esperadas
        expected_columns = ['column_name', 'data_type', 'table_name', 'source_file']
        if not all(col in metadata_df.columns for col in expected_columns):
            raise ValueError(f"metadata_df deve conter as colunas: {expected_columns}")

        # Remove entradas antigas para a mesma tabela
        self._metadata_store = self._metadata_store[self._metadata_store['table_name'] != table_name]

        # Concatena os novos metadados
        self._metadata_store = pd.concat([self._metadata_store, metadata_df], ignore_index=True)
        print(f"[DataFrameStore] Metadados para a tabela '{table_name}' adicionados/atualizados.")

    def get_all_metadata(self) -> pd.DataFrame:
        """
        Retorna um DataFrame consolidado com todos os metadados de todas as tabelas.

        Returns:
            pd.DataFrame: Um DataFrame contendo os metadados.
        """
        return self._metadata_store.copy() # Retorna uma cópia para evitar modificações externas diretas

    def get_metadata_by_table(self, table_name: str) -> pd.DataFrame:
        """
        Retorna os metadados de uma tabela específica.

        Args:
            table_name (str): O nome da tabela.

        Returns:
            pd.DataFrame: Um DataFrame com os metadados da tabela especificada.
        """
        return self._metadata_store[self._metadata_store['table_name'] == table_name].copy()

    def clear(self):
        """
        Limpa todos os metadados armazenados no store.
        Útil para reiniciar o estado entre diferentes uploads de ZIP.
        """
        self._metadata_store = pd.DataFrame(columns=['table_name', 'column_name', 'data_type', 'source_file'])
        print("[DataFrameStore] Todos os metadados foram limpos.")

    def get_table_names(self) -> list:
        """
        Retorna uma lista de todos os nomes de tabelas únicos atualmente armazenados.
        """
        return self._metadata_store['table_name'].unique().tolist()
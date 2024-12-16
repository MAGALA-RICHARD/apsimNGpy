"""
Custom-based exception handling for apsimNgpy package
"""


class TableNotFoundError(Exception):
    """Exception raised when the specified database cannot be found."""

    def __init__(self, dbname, message="Table not found"):
        self.dbname = dbname
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}: {self.dbname}"



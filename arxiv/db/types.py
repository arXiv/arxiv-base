from typing import Annotated
from sqlalchemy.orm import mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]
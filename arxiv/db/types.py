from typing import Annotated
from sqlalchemy.orm import mapped_column

str255 = Annotated[str, 255]
intpk = Annotated[int, mapped_column(primary_key=True)]
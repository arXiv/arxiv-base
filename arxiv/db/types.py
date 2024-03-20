"""
This file contains common database types. We have lots of integer 
primary keys in our db, so we can include a shorthand like intpk
to make annotating the column type in .models easier
"""

from typing import Annotated
from sqlalchemy.orm import mapped_column

intpk = Annotated[int, mapped_column(primary_key=True)]
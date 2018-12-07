"""
arXiv group, archive and category definitions.

arXiv categories are arranged in a hierarchy where there are archives
(astro-ph, cs, math, etc.) that contain subject classes (astro-ph has subject
classes CO, GA, etc.). We now use the term category to refer to any archive or
archive.subject_class that one can submit to (so hep-th and math.IT are both
categories). No subject class can be in more than one archive. However, our
scientific advisors identify some categories that should appear in more than
one archive because they bridge major subject areas. Examples include math.MP
== math-ph and stat.TH = math.ST. These are called category aliases and the
idea is that any article classified in one of the aliases categories also
appears in the other (canonical), but that most of the arXiv code for display,
search, etc. does not need to understand the break with hierarchy.

"""
from typing import Optional
from .definitions import CATEGORIES, CATEGORIES_ACTIVE, ARCHIVES, \
    ARCHIVES_ACTIVE, ARCHIVES_SUBSUMED, CATEGORY_ALIASES
from .category import Category

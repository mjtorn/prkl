# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import connection
from django.db.models.signals import post_syncdb

from prkl.web import models

QRY_CREATE_FUNCTION_LEVENSHTEIN = """\
CREATE OR REPLACE FUNCTION levenshtein (text,text) RETURNS int
AS '$libdir/fuzzystrmatch','levenshtein'
LANGUAGE C IMMUTABLE STRICT;
"""

def create_levenshtein(sender, **kwargs):
    """Create a levenshtein calculator
    """

    cursor = connection.cursor()
    cursor.execute(QRY_CREATE_FUNCTION_LEVENSHTEIN)
    cursor.connection.commit()

post_syncdb.connect(create_levenshtein, sender=models)

# EOF


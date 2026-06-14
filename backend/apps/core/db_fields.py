import uuid
from django.db import models


def new_guid_str():
    """Default for char(36) PK fields mapped to SQL Server uniqueidentifier columns."""
    return str(uuid.uuid4())


class GUIDField(models.UUIDField):
    """
    UUIDField for SQL Server `uniqueidentifier` columns.

    mssql-django treats UUIDField as char(32) and sends values as
    32-char hex (no dashes) in get_db_prep_value(), which SQL Server
    refuses to convert to uniqueidentifier. This field always sends
    the standard dashed string form instead.
    """

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None
        if not isinstance(value, uuid.UUID):
            value = self.to_python(value)
        return str(value)

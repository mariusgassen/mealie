import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID


class ServerThemeOverride(SqlAlchemyBase, BaseMixins):
    """
    A single server-wide theme color set by an admin (e.g. key `dark_primary`, value `#E58325`).

    Only values an admin has changed are stored; anything without a row falls back to the
    `THEME_*` environment variables and then to the built-in defaults.
    """

    __tablename__ = "server_theme_overrides"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    key: Mapped[str] = mapped_column(sa.String, nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(sa.String, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass

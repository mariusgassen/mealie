from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from .group import Group


class AIRequestLog(SqlAlchemyBase, BaseMixins):
    __tablename__ = "ai_request_logs"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    group: Mapped[Group] = orm.relationship("Group", back_populates="ai_request_logs")

    request_type: Mapped[str] = mapped_column(sa.String, nullable=False)
    model: Mapped[str] = mapped_column(sa.String, nullable=False)
    system_prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)
    user_message: Mapped[str] = mapped_column(sa.Text, nullable=False)
    raw_response: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass

from typing import TYPE_CHECKING

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from .group import Group


class AIPromptOverride(SqlAlchemyBase, BaseMixins):
    __tablename__ = "ai_prompt_overrides"
    __table_args__ = (sa.UniqueConstraint("group_id", "name", name="ai_prompt_overrides_group_id_name_key"),)
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    group_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    group: Mapped[Group] = orm.relationship("Group", back_populates="ai_prompt_overrides")

    name: Mapped[str] = mapped_column(sa.String, nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(sa.Text, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass

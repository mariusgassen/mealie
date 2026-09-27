from fastapi import APIRouter, HTTPException
from pydantic import UUID4

from mealie.repos.repository_factory import AllRepositories
from mealie.routes._base import BaseAdminController, controller
from mealie.routes._base.mixins import HttpRepo
from mealie.schema.group.ai_prompts import AIPromptOut, AIPromptOverrideUpdate
from mealie.schema.group.ai_providers import (
    AIProviderCreate,
    AIProviderOut,
    AIProviderUpdate,
)
from mealie.services.openai import OpenAIService

router = APIRouter(prefix="/groups/{group_id}/ai-providers")


@controller(router)
class AdminGroupAIProviderController(BaseAdminController):
    def _group_repos(self, group_id: UUID4) -> AllRepositories:
        """Return repos scoped to the target group."""
        return AllRepositories(self.session, group_id=group_id, household_id=None)

    def _mixins(self, group_id: UUID4) -> HttpRepo:
        return HttpRepo[AIProviderCreate, AIProviderOut, AIProviderUpdate](
            self._group_repos(group_id).group_ai_providers, self.logger
        )

    # =======================================================================
    # Provider CRUD

    @router.post("/providers", response_model=AIProviderOut, tags=["Admin: AI Providers"])
    def create_ai_provider(self, group_id: UUID4, data: AIProviderCreate):
        return self._mixins(group_id).create_one(data)

    @router.get("/providers/{provider_id}", response_model=AIProviderOut, tags=["Admin: AI Providers"])
    def get_ai_provider(self, group_id: UUID4, provider_id: UUID4):
        return self._mixins(group_id).get_one(provider_id)

    @router.put("/providers/{provider_id}", response_model=AIProviderOut, tags=["Admin: AI Providers"])
    def update_ai_provider(self, group_id: UUID4, provider_id: UUID4, data: AIProviderUpdate):
        return self._mixins(group_id).update_one(data, provider_id)

    @router.delete("/providers/{provider_id}", response_model=AIProviderOut, tags=["Admin: AI Providers"])
    def delete_ai_provider(self, group_id: UUID4, provider_id: UUID4):
        return self._mixins(group_id).delete_one(provider_id)

    # =======================================================================
    # Prompt Overrides

    @router.get("/prompts", response_model=list[AIPromptOut], tags=["Admin: AI Prompts"])
    def get_ai_prompts(self, group_id: UUID4):
        return OpenAIService(self._group_repos(group_id)).list_prompts()

    @router.get("/prompts/{name}", response_model=AIPromptOut, tags=["Admin: AI Prompts"])
    def get_ai_prompt(self, group_id: UUID4, name: str):
        service = OpenAIService(self._group_repos(group_id))
        if name not in service.list_prompt_names():
            raise HTTPException(status_code=404, detail=f"Unknown prompt '{name}'")

        return service.get_prompt_detail(name)

    @router.put("/prompts/{name}", response_model=AIPromptOut, tags=["Admin: AI Prompts"])
    def update_ai_prompt(self, group_id: UUID4, name: str, data: AIPromptOverrideUpdate):
        try:
            return OpenAIService(self._group_repos(group_id)).save_prompt_override(name, data.prompt)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @router.delete("/prompts/{name}", response_model=AIPromptOut, tags=["Admin: AI Prompts"])
    def reset_ai_prompt(self, group_id: UUID4, name: str):
        """Discards the group's override for this prompt, reverting it to the default."""
        try:
            return OpenAIService(self._group_repos(group_id)).reset_prompt(name)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

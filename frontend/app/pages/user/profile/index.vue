<template>
  <v-container v-if="user" class="mb-8">
    <section class="d-flex align-center ga-4 mt-4">
      <UserAvatar
        :tooltip="false"
        size="56"
        :user-id="user.id"
      />
      <div class="flex-grow-1 min-width-0">
        <h2 class="text-h5 font-weight-bold">
          {{ $t('profile.welcome-user', [user.fullName]) }}
        </h2>
        <p class="profile-description text-body-2 text-medium-emphasis mb-0">
          {{ $t('profile.description') }}
        </p>
      </div>
      <v-btn
        v-if="user.canInvite"
        variant="tonal"
        rounded
        :icon="$vuetify.display.xs"
        :prepend-icon="$vuetify.display.xs ? undefined : $globals.icons.createAlt"
        :text="$vuetify.display.xs ? undefined : $t('profile.get-invite-link')"
        :aria-label="$t('profile.get-invite-link')"
        @click="inviteDialog = true"
      >
        <v-icon v-if="$vuetify.display.xs">
          {{ $globals.icons.createAlt }}
        </v-icon>
      </v-btn>
      <UserInviteDialog v-model="inviteDialog" />
    </section>
    <section class="mt-6">
      <h3 class="text-caption font-weight-bold text-uppercase text-medium-emphasis mb-2">
        {{ $t('profile.household-statistics') }}
      </h3>
      <div class="stats-grid">
        <v-card
          v-for="(value, key) in filteredStats"
          :key="`${key}-${value}`"
          flat
          :to="getStatsTo(key)"
          class="stats-tile pa-3"
        >
          <div class="text-h6 font-weight-bold">
            {{ value }}
          </div>
          <div class="text-caption text-medium-emphasis">
            {{ getStatsTitle(key) }}
          </div>
        </v-card>
      </div>
    </section>
    <v-divider class="my-7" />
    <section>
      <div>
        <h3 class="text-h6">
          {{ $t('profile.personal') }}
        </h3>
        <p class="text-body-2 text-medium-emphasis">
          {{ $t('profile.personal-description') }}
        </p>
      </div>
      <v-row tag="section">
        <v-col
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.user"
            :link="{ text: $t('profile.manage-user-profile'), to: `/user/profile/edit` }"
          >
            <template #title>
              {{ $t('profile.user-settings') }}
            </template>
            {{ $t('profile.user-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :icon="$globals.icons.api"
              :link="{ text: $t('profile.manage-your-api-tokens'), to: `/user/profile/api-tokens` }"
            >
              <template #title>
                {{ $t('settings.token.api-tokens') }}
              </template>
              {{ $t('profile.api-tokens-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
    <v-divider class="my-7" />
    <section>
      <div>
        <h3 class="text-h6">
          {{ $t('household.household') }}
        </h3>
        <p class="text-body-2 text-medium-emphasis">
          {{ $t('profile.household-description') }}
        </p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManageHousehold"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.household"
            :link="{ text: $t('profile.household-settings'), to: `/household` }"
          >
            <template #title>
              {{ $t('profile.household-settings') }}
            </template>
            {{ $t('profile.household-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.book"
            :link="{ text: $t('profile.manage-cookbooks'), to: `/g/${groupSlug}/cookbooks` }"
          >
            <template #title>
              {{ $t('sidebar.cookbooks') }}
            </template>
            {{ $t('profile.cookbooks-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.user"
            :link="{ text: $t('profile.manage-members'), to: `/household/members` }"
          >
            <template #title>
              {{ $t('profile.members') }}
            </template>
            {{ $t('profile.members-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            v-if="user.advanced"
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :icon="$globals.icons.webhook"
              :link="{ text: $t('profile.manage-webhooks'), to: `/household/webhooks` }"
            >
              <template #title>
                {{ $t('settings.webhooks.webhooks') }}
              </template>
              {{ $t('profile.webhooks-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :icon="$globals.icons.bellPlus"
              :link="{ text: $t('profile.manage-notifiers'), to: `/household/notifiers` }"
            >
              <template #title>
                {{ $t('profile.notifiers') }}
              </template>
              {{ $t('profile.notifiers-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
    <v-divider class="my-7" />
    <section v-if="user.canManage || user.canOrganize || user.advanced">
      <div>
        <h3 class="text-h6">
          {{ $t('group.group') }}
        </h3>
        <p class="text-body-2 text-medium-emphasis">
          {{ $t('profile.group-description') }}
        </p>
      </div>
      <v-row tag="section">
        <v-col
          v-if="user.canManage"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.group"
            :link="{ text: $t('profile.group-settings'), to: `/group` }"
          >
            <template #title>
              {{ $t('profile.group-settings') }}
            </template>
            {{ $t('profile.group-settings-description') }}
          </UserProfileLinkCard>
        </v-col>
        <v-col
          v-if="user.canOrganize"
          cols="12"
          sm="12"
          md="6"
        >
          <UserProfileLinkCard
            :icon="$globals.icons.database"
            :link="{ text: $t('profile.manage-data'), to: `/group/data/foods` }"
          >
            <template #title>
              {{ $t('profile.manage-data') }}
            </template>
            {{ $t('profile.manage-data-description') }}
          </UserProfileLinkCard>
        </v-col>
        <AdvancedOnly>
          <v-col
            cols="12"
            sm="12"
            md="6"
          >
            <UserProfileLinkCard
              :icon="$globals.icons.import"
              :link="{ text: $t('profile.manage-data-migrations'), to: `/group/migrations` }"
            >
              <template #title>
                {{ $t('profile.data-migrations') }}
              </template>
              {{ $t('profile.data-migrations-description') }}
            </UserProfileLinkCard>
          </v-col>
        </AdvancedOnly>
      </v-row>
    </section>
  </v-container>
</template>

<script setup lang="ts">
import UserProfileLinkCard from "@/components/Domain/User/UserProfileLinkCard.vue";
import { useUserApi } from "~/composables/api";
import UserAvatar from "@/components/Domain/User/UserAvatar.vue";
import { useAsyncKey } from "~/composables/use-utils";
import type { UserOut } from "~/lib/api/types/user";
import UserInviteDialog from "~/components/Domain/User/UserInviteDialog.vue";

definePageMeta({
  name: "UserProfile",
  middleware: ["auth"],
  scrollToTop: true,
});

const i18n = useI18n();
const auth = useMealieAuth();
const { $appInfo } = useNuxtApp();
const route = useRoute();
const groupSlug = computed(() => route.params.groupSlug || auth.user.value?.groupSlug || "");

useSeoMeta({
  title: i18n.t("settings.profile"),
});

const user = computed<UserOut | null>(() => {
  const authUser = auth.user.value;
  if (!authUser) return null;

  // Override canInvite if password login is disabled
  const canInvite = !$appInfo.allowPasswordLogin ? false : authUser.canInvite;

  return {
    ...authUser,
    canInvite,
  };
});

const inviteDialog = ref(false);
const api = useUserApi();

const { data: stats } = useAsyncData(useAsyncKey(), async () => {
  const { data } = await api.households.statistics();

  if (data) {
    return data;
  }
});

const filteredStats = computed(() => {
  const statsData = stats.value;
  if (!statsData) return {};
  if (!user.value?.canManage) {
    const { totalUsers, ...rest } = statsData;
    return rest;
  }
  return statsData;
});

const statsText: { [key: string]: string } = {
  totalRecipes: i18n.t("general.recipes"),
  totalUsers: i18n.t("user.users"),
  totalCategories: i18n.t("sidebar.categories"),
  totalTags: i18n.t("sidebar.tags"),
  totalTools: i18n.t("tool.tools"),
};

function getStatsTitle(key: string) {
  return statsText[key] ?? "unknown";
}

const { $globals } = useNuxtApp();

const statsTo = computed<{ [key: string]: string }>(() => {
  return {
    totalRecipes: `/g/${groupSlug.value}/`,
    totalUsers: "/household/members",
    totalCategories: `/g/${groupSlug.value}/recipes/categories`,
    totalTags: `/g/${groupSlug.value}/recipes/tags`,
    totalTools: `/g/${groupSlug.value}/recipes/tools`,
  };
});

function getStatsTo(key: string) {
  return statsTo.value[key] ?? "unknown";
}
</script>

<style scoped>
.profile-description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.stats-tile {
  border-radius: 14px;
}
</style>

<template>
  <v-menu
    offset-y
    nudge-bottom="5"
    close-delay="50"
    nudge-right="15"
  >
    <template #activator="{ props: activatorProps }">
      <slot
        name="activator"
        :props="activatorProps"
      />
    </template>
    <v-list
      density="comfortable"
      class="mb-0 mt-1 py-0"
      variant="flat"
    >
      <template v-for="(item, index) in links">
        <div
          v-if="!item.hide"
          :key="item.title"
        >
          <v-divider
            v-if="item.insertDivider"
            :key="index"
            class="mx-2"
          />
          <v-list-item
            v-if="!item.restricted || isOwnGroup"
            :key="item.title"
            :to="item.to"
            exact
            class="my-1"
          >
            <template #prepend>
              <v-icon
                size="40"
                :icon="item.icon"
              />
            </template>
            <v-list-item-title class="font-weight-medium" style="font-size: small;">
              {{ item.title }}
            </v-list-item-title>
            <v-list-item-subtitle class="font-weight-medium" style="font-size: small;">
              {{ item.subtitle }}
            </v-list-item-subtitle>
          </v-list-item>
        </div>
      </template>
    </v-list>
  </v-menu>
</template>

<script setup lang="ts">
import { useLoggedInState } from "~/composables/use-logged-in-state";

interface CreateLink {
  insertDivider: boolean;
  icon: string;
  title: string;
  subtitle: string;
  to: string;
  restricted: boolean;
  hide: boolean;
}

defineProps<{ links: CreateLink[] }>();

const { isOwnGroup } = useLoggedInState();
</script>

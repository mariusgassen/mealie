<template>
  <v-card
    flat
    :to="link.to"
    height="100%"
    class="profile-link-card d-flex align-center ga-3 mt-3 pa-3"
  >
    <span class="profile-link-card__icon">
      <v-icon size="22">{{ icon }}</v-icon>
    </span>
    <div class="flex-grow-1 profile-link-card__text">
      <div class="text-subtitle-1 font-weight-medium">
        <slot name="title" />
      </div>
      <div class="text-body-2 text-medium-emphasis profile-link-card__description">
        <slot name="default" />
      </div>
    </div>
    <v-icon
      size="small"
      class="text-medium-emphasis"
    >
      {{ $globals.icons.chevronRight }}
    </v-icon>
  </v-card>
</template>

<script setup lang="ts">
interface LinkProp {
  text: string;
  url?: string;
  to: string;
}

defineProps({
  link: {
    type: Object as () => LinkProp,
    required: true,
  },
  icon: {
    type: String,
    default: "",
  },
});
</script>

<style scoped>
.profile-link-card {
  border-radius: 14px;
}

.profile-link-card__icon {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  color: rgb(var(--v-theme-on-primary));
  background: rgb(var(--v-theme-primary));
}

/* one line of context, not a paragraph */
.profile-link-card__description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
</style>

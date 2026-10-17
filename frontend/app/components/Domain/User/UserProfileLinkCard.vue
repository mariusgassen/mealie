<template>
  <v-card
    variant="outlined"
    style="border-color: lightgrey;"
    :to="link.to"
    height="100%"
    class="d-flex flex-column mt-4 pa-2"
  >
    <div class="d-flex justify-space-between">
      <div>
        <v-card-title class="text-subtitle-1 pb-0">
          <slot name="title" />
        </v-card-title>
        <div class="d-flex justify-center align-center">
          <v-card-text class="d-flex flex-row mb-auto">
            <slot name="default" />
          </v-card-text>
        </div>
      </div>
    </div>
    <v-spacer />
    <v-divider />
    <v-card-actions>
      <v-btn
        variant="text"
        color="info"
        :to="link.to"
      >
        {{ link.text }}
      </v-btn>
    </v-card-actions>
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
});
</script>

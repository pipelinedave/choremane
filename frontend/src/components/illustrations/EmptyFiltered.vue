<template>
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" fill-rule="evenodd">
      <!-- Background circle -->
      <circle cx="100" cy="100" r="80" fill="#f5f5f5" />
      
      <!-- Filter shape -->
      <path d="M60 60l30 40v40l20 10v-50l30-40z" fill="#ffffff" stroke="#6b7280" stroke-width="2" />
      
      <!-- Filtered items (crossed out) -->
      <path d="M70 130l60-60M70 70l60 60" stroke="var(--color-primary, #4338ca)" stroke-width="2" stroke-linecap="round" />
    </g>
  </svg>
</template>

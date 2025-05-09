<template>
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" fill-rule="evenodd">
      <!-- Background circle -->
      <circle cx="100" cy="100" r="80" fill="#f5f5f5" />
      
      <!-- Clipboard -->
      <path d="M70 50h60v100H70z" fill="#ffffff" stroke="#6b7280" stroke-width="2" />
      <path d="M85 40h30v20H85z" fill="#ffffff" stroke="#6b7280" stroke-width="2" rx="5" />
      
      <!-- Lines on clipboard -->
      <path d="M85 70h30" stroke="#d1d5db" stroke-width="2" stroke-linecap="round" />
      <path d="M85 90h30" stroke="#d1d5db" stroke-width="2" stroke-linecap="round" />
      <path d="M85 110h30" stroke="#d1d5db" stroke-width="2" stroke-linecap="round" />
      
      <!-- Plus sign for new chore -->
      <circle cx="140" cy="140" r="25" fill="var(--color-primary, #4338ca)" />
      <path d="M140 130v20M130 140h20" stroke="#ffffff" stroke-width="3" stroke-linecap="round" />
    </g>
  </svg>
</template>

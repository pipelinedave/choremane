<template>
  <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" fill-rule="evenodd">
      <!-- Background circle -->
      <circle cx="100" cy="100" r="80" fill="#f5f5f5" />
      
      <!-- Box/Archive -->
      <path d="M50 80h100v60H50z" fill="#ffffff" stroke="#6b7280" stroke-width="2" />
      <path d="M60 80v-10h80v10" stroke="#6b7280" stroke-width="2" />
      <path d="M75 100h50" stroke="#6b7280" stroke-width="2" stroke-dasharray="4" />
      
      <!-- Archive lid -->
      <path d="M50 80l10-20h80l10 20" fill="#ffffff" stroke="#6b7280" stroke-width="2" />
      
      <!-- Handle -->
      <path d="M95 90h10v10h-10z" fill="var(--color-primary, #4338ca)" stroke="#6b7280" />
    </g>
  </svg>
</template>

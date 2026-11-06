<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <GlobalLoading />
  <GlobalNotifications />
  <GlobalConfirm />
</template>

<style>
/*
  全站等比縮放：以 1536px 寬（1920 螢幕 125% 縮放）為基準 16px，
  更寬的螢幕按比例放大（所有 rem 尺寸一起變大），最大 28px；較窄螢幕維持 16px。
*/
html {
  font-size: clamp(16px, 1.0417vw, 28px);
}
</style>

// Script to clean up any problematic localStorage data
(() => {
  try {
    // List of potentially problematic storage keys
    const keysToRemove = [
      'choremane_current_version',
      'choremane_dismissed_update',
      'VERSION_STORAGE_KEY',
      'DISMISS_UNTIL_NEXT_VERSION_KEY',
      'appVersionInfo',
      'version_cleanup_performed'
    ];
    
    // Remove these keys from localStorage
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
    });
    
    // Log that the cleanup was performed
    localStorage.setItem('version_cleanup_performed_at', new Date().toISOString());
    
    console.log('Successfully cleaned up localStorage version data');
    return true;
  } catch (error) {
    console.error('Error cleaning localStorage:', error);
    return false;
  }
})();

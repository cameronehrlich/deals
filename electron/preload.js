const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Scrape a property URL locally using Puppeteer
  scrapeProperty: (url) => ipcRenderer.invoke('scrape-property', url),

  // Check if running in Electron
  isElectron: () => ipcRenderer.invoke('is-electron'),

  // Get the API URL
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),

  // Platform info
  platform: process.platform,
});

const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const { scrapeProperty } = require('./scraper');

// Keep a global reference of the window object
let mainWindow;

// API URL - use environment variable or default to Vercel
const API_URL = process.env.API_URL || 'https://deals-api-swart.vercel.app';

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // In development, load from Next.js dev server
  // In production, load from the bundled standalone server or Vercel
  const isDev = process.env.NODE_ENV === 'development';

  if (isDev) {
    // Development: load from local Next.js dev server
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load from Vercel deployment
    // (We could also bundle the Next.js standalone build, but Vercel is simpler)
    mainWindow.loadURL('https://deals-tau-seven.vercel.app');
  }

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC Handlers for local scraping
ipcMain.handle('scrape-property', async (event, url) => {
  try {
    console.log('Scraping property:', url);
    const result = await scrapeProperty(url);
    return { success: true, data: result };
  } catch (error) {
    console.error('Scraping error:', error);
    return { success: false, error: error.message };
  }
});

// Check if we're in Electron (renderer can call this)
ipcMain.handle('is-electron', () => true);

// Get API URL
ipcMain.handle('get-api-url', () => API_URL);

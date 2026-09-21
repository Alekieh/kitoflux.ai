const { app, BrowserWindow, globalShortcut, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');

let mainWindow = null;
let stealthActive = false;

function applyWindowsStealthAffinity(win) {
  if (process.platform !== 'win32') {
    console.log('[Stealth] Non-Windows platform detected; WDA_EXCLUDEFROMCAPTURE is Windows-specific.');
    stealthActive = true;
    return;
  }

  try {
    const handleBuffer = win.getNativeWindowHandle();
    const hwnd = handleBuffer.readInt32LE(0);
    
    // WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Decimal 17)
    // Invoked via zero-dependency inline PowerShell pinvoke
    const psCommand = `powershell -Command "$sig = '[DllImport(\\\"user32.dll\\\")] public static extern bool SetWindowDisplayAffinity(IntPtr hWnd, uint dwAffinity);'; $type = Add-Type -MemberDefinition $sig -Name Win32Utils -Namespace Kitoflux -PassThru; $type::SetWindowDisplayAffinity([IntPtr]${hwnd}, 17)"`;
    
    exec(psCommand, (err, stdout, stderr) => {
      if (err) {
        console.error('[Stealth Error] Failed to set display affinity:', err);
        stealthActive = false;
      } else {
        console.log('[Stealth Success] SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE) applied to HWND:', hwnd);
        stealthActive = true;
      }
    });
  } catch (err) {
    console.error('[Stealth Exception]:', err);
    stealthActive = false;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 820,
    height: 540,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    hasShadow: false,
    resizable: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Always keep on top across all workspaces
  mainWindow.setAlwaysOnTop(true, 'screen-saver');
  mainWindow.setVisibleOnAllWorkspaces(true);

  // Apply stealth exclusion
  mainWindow.webContents.on('did-finish-load', () => {
    applyWindowsStealthAffinity(mainWindow);
  });

  const devUrl = 'http://localhost:5173';
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL(devUrl);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html')).catch(() => {
      mainWindow.loadURL(devUrl);
    });
  }

  // Register Global Shortcuts
  // 1. Hotkey to trigger Autotyper
  globalShortcut.register('CommandOrControl+Shift+Space', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('hotkey-event', 'TRIGGER_AUTOTYPE');
    }
  });

  // 2. Emergency Panic Killswitch (Ctrl+Shift+X or Double Esc in UI)
  globalShortcut.register('CommandOrControl+Shift+X', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.hide();
    }
  });

  // 3. Toggle HUD visibility
  globalShortcut.register('Alt+H', () => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
      }
    }
  });
}

ipcMain.handle('get-stealth-status', () => {
  return stealthActive;
});

ipcMain.on('panic-hide', () => {
  if (mainWindow) mainWindow.hide();
});

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

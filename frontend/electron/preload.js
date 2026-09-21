const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('kitoflux', {
  triggerAutotype: (text) => ipcRenderer.send('trigger-autotype', text),
  panicHide: () => ipcRenderer.send('panic-hide'),
  toggleStealth: () => ipcRenderer.send('toggle-stealth'),
  getStealthStatus: () => ipcRenderer.invoke('get-stealth-status'),
  onGlobalHotkey: (callback) => ipcRenderer.on('hotkey-event', (_event, value) => callback(value))
});

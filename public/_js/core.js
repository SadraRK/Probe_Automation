'use strict';
let paApp = {windowLoaded: false};
window.addEventListener('load', () => paApp.windowLoaded = true);
window.paApp = paApp;

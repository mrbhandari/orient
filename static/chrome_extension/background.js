chrome.browserAction.onClicked.addListener(function(activeTab) {
    chrome.tabs.executeScript(null, {
        code: "javascript:(function(){var el=document.createElement('script');el.src='http://localhost:8000/static/chrome_extension/perfmap.js';document.body.appendChild(el);})();" //TODO: fix absolute path
    });
});

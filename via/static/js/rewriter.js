/* Javascript interceptions for rewriting HTML pages */
console.log('Initializing Via DOM API monkey-patching');

function staticProxyURL(url) {
  const absUrl = new URL(url, document.baseURI).toString();
  const proxyUrlTemplate = VIA_REWRITER_SETTINGS.urlTemplates.PROXY_STATIC;
  return proxyUrlTemplate.replace('__URL__', absUrl);
}

const origFetch = window.fetch;
window.fetch = (url, ...args) => {
  return origFetch.call(null, staticProxyURL(url), ...args);
};

const origOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url, ...args) {
  return origOpen.call(this, method, staticProxyURL(url), ...args);
};

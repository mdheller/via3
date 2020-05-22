/* Javascript interceptions for rewriting HTML pages */
console.log('Initializing Via DOM API monkey-patching');

function staticProxyURL(url) {
  console.log("Getting static proxy URL for", url);

  const absUrl = new URL(url, VIA_REWRITER_SETTINGS.baseUrl).toString();
  console.log("--- ABS URL", absUrl);

  const proxyUrlTemplate = VIA_REWRITER_SETTINGS.urlTemplates.PROXY_STATIC;
  const final = proxyUrlTemplate.replace('__URL__', absUrl);

  console.log("--- FINAL", final);
  return final;
}

const origFetch = window.fetch;
window.fetch = (url, ...args) => {
  return origFetch.call(null, staticProxyURL(url), ...args);
};

const origOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url, ...args) {
  return origOpen.call(this, method, staticProxyURL(url), ...args);
};

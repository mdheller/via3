/* Javascript interceptions for rewriting HTML pages */

class URLRewriter {
  // Partial port of via3.services.rewriter.url.URLRewriter

  constructor(settings) {
    this.baseUrl = settings.baseUrl;
    this.baseScheme = this._urlScheme(this.baseUrl);
    this.urlTemplates = settings.urlTemplates;
  }

  _urlScheme(url) {
    if (url.startsWith("https:")) {
      return "https";
    } else if (url.startsWith("http:")) {
      return "http";
    }
    return null;
  }

  makeAbsolute(url) {
    if (url.startsWith("//")) {
      return this.baseScheme + ":" + url;
    }

    return new URL(url, this.baseUrl).toString();
  }

  canProxy(url) {
    return url.startsWith("https:") || url.startsWith("http:");
  }

  proxyStatic(url) {
    // We don't URL escape the paths that go direct through NGINX
    return this._templateRewrite(url, this.urlTemplates.PROXY_STATIC, false);
  }

  rewriteJS(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_JS);
  }

  rewriteHTML(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_HTML);
  }

  rewriteCSS(url) {
    return this._templateRewrite(url, this.urlTemplates.REWRITE_CSS);
  }

  _templateRewrite(url, template, encode = true) {
    console.log("Rewrite incoming URL", url);

    let absoluteUrl = this.makeAbsolute(url);
    console.log("  > (absolute)", url);

    if (!this.canProxy(absoluteUrl)) {
      console.log("  > (can't proxy)");
      return absoluteUrl;
    }

    if (encode) {
      absoluteUrl = encodeURIComponent(absoluteUrl);
      console.log("  > (encoded)", absoluteUrl);
    }

    const finalUrl = template.replace("__URL__", absoluteUrl);
    console.log("  > (final)", finalUrl);

    return finalUrl;
  }
}

function monkeyPatch(urlRewriter) {
  console.log("Initializing Via DOM API monkey-patching");

  const origFetch = window.fetch;
  window.fetch = (url, ...args) => {
    console.log("Via: Triggered fetch patch", url, args);
    return origFetch.call(null, urlRewriter.proxyStatic(url), ...args);
  };

  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function(method, url, ...args) {
    console.log("Via: Triggered XMLHttpRequest patch", method, url, args);
    return origOpen.call(this, method, urlRewriter.proxyStatic(url), ...args);
  };

  const origReplaceState = history.replaceState;
  history.replaceState = function(state, title, url) {
    console.log("Via: Tried to replace history", state, title, url);
    origReplaceState.call(history, state, title, urlRewriter.rewriteHTML(url));
    //return pushState.apply(history, arguments);
  };
  const origPushState = history.pushState;
  history.pushState = function(state, title, url) {
    console.log("Via: Tried to change history", state, title, url);
    origPushState.call(history, state, title, urlRewriter.rewriteHTML(url));
    //return pushState.apply(history, arguments);
  };

  // Pretend to be an old browser that doesn't support ServiceWorker.
  delete Object.getPrototypeOf(navigator).serviceWorker;
}

const urlRewriter = new URLRewriter(VIA_REWRITER_SETTINGS);
monkeyPatch(urlRewriter);

// Initialize proxy for "unforgeable" DOM properties (`window.location`,
// `document.location` and various properties on `location`).
//
// Since these properties cannot be monkey-patched, we instead use server-side
// rewriting to replace references to this property with a different property
// which we can set.
const baseURL = new URL(VIA_REWRITER_SETTINGS.baseUrl);

const assignURL = url => {
  location.assign(urlRewriter.rewriteHTML(url));
};

const replaceURL = url => {
  location.replace(urlRewriter.rewriteHTML(url));
};

// nb. We don't use `location` as the target here because that prevents us from
// returning custom values for certain properties (eg. `location.replace`)
// which are not configurable.
const locationProxy = new Proxy(
  {},
  {
    get(target, prop, receiver) {
      if (prop in baseURL) {
        return baseURL[prop];
      }
      switch (prop) {
        case "assign":
          return assignURL;
        case "replace":
          return replaceURL;
      }

      const val = Reflect.get(location, prop);
      if (typeof val === "function") {
        return val.bind(location);
      }
      return val;
    },

    set(target, prop, value) {
      if (prop === "href") {
        value = urlRewriter.rewriteHTML(value);
      }
      return Reflect.set(location, prop, value);
    },

    has(target, prop) {
      return Reflect.has(location, prop);
    },

    ownKeys(target) {
      return Reflect.ownKeys(location);
    },

    deleteProperty(target, prop) {
      return Reflect.deleteProperty(location, prop);
    },

    defineProperty(target, prop, attrs) {
      return Reflect.defineProperty(location, prop, attrs);
    },

    getOwnPropertyDescriptor(target, prop) {
      const descriptor = Reflect.getOwnPropertyDescriptor(location, prop);
      if (descriptor) {
        // The proxy is constructed with a dummy target with no properties, but
        // the engine requires that any properties that don't exist on the target
        // are marked as configurable. Therefore report that any queried properties
        // are configurable.
        descriptor.configurable = true;
      }
      return descriptor;
    }
  }
);

const viaLocationDescriptor = {
  enumerable: true,
  configurable: true,

  get(value) {
    return locationProxy;
  },

  set(value) {
    locationProxy.href = value;
  }
};

Object.defineProperty(document, 'viaLocation', viaLocationDescriptor);
Object.defineProperty(window, 'viaLocation', viaLocationDescriptor);

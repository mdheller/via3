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

// Initialize proxy for "unforgeable" window properties (mainly `location`).
//
// Since these properties cannot be monkey-patched, we instead use server-side
// rewriting to wrap the page's JS in an IIFE which defines alternative `window`
// and `location` globals that refer to proxies set up here. These proxies
// can then intercept reads/writes to the unforgeable properties and modify
// their behavior.
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

// Build up a set of "native" properties of `window`, excluding any added by
// client code.
const nativeWindowProperties = new Set();
for (let prop in window) {
  nativeWindowProperties.add(prop);
}

// nb. We don't use `window` as the target here because that prevents us
// us from returning custom values for certain properties (eg. `window.window`)
// which are non-writable and non-configurable.
const windowProxy = new Proxy(
  {},
  {
    get(target, prop, receiver) {
      switch (prop) {
        case "location":
          return locationProxy;
        case "window":
          return windowProxy;
        default:
          break;
      }

      const val = Reflect.get(window, prop);

      // Calls to many `window` methods fail if `this` is a proxy rather than
      // the real window. Therefore we bind the returned function to the real `window`.
      //
      // We only apply this to functions which:
      //
      //  - Are "native" properties of the window (ie. not a custom added property)
      //  - Do not look like a constructor (eg. name beginning with capital letter)
      if (
        typeof val === "function" &&
        nativeWindowProperties.has(prop) &&
        val.name.match(/^[a-z]+/)
      ) {
        // A limitation of this is that any properties of `val` are not preserved
        // on the wrapped function.
        return val.bind(window);
      } else {
        return val;
      }
    },

    // Some `window` property setters fail if `this` is a proxy rather than the
    // real window. Therefore we set the property on the real `window`.
    set(target, prop, value) {
      // When using `window.location = <new URL>`, proxy the new URL.
      if (prop === "location") {
        value = urlRewriter.rewriteHTML(value);
      }
      return Reflect.set(window, prop, value);
    },

    has(target, prop) {
      return Reflect.has(window, prop);
    },

    ownKeys(target) {
      return Reflect.ownKeys(window);
    },

    deleteProperty(target, prop) {
      return Reflect.deleteProperty(window, prop);
    },

    defineProperty(target, prop, attrs) {
      return Reflect.defineProperty(window, prop, attrs);
    },

    getOwnPropertyDescriptor(target, prop) {
      const descriptor = Reflect.getOwnPropertyDescriptor(window, prop);
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

window.viaWindowProxy = windowProxy;

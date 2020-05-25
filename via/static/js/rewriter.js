/* Javascript interceptions for rewriting HTML pages */


class URLRewriter {
    // Partial port of via3.services.rewriter.url.URLRewriter

    constructor(settings) {
        this.baseUrl = settings.baseUrl;
        this.baseScheme = this._urlScheme(this.baseUrl);
        this.urlTemplates = settings.urlTemplates;
    }

    _urlScheme(url) {
        if (url.startsWith('https:')){
            return 'https'
        }
        else if (url.startsWith('http:')){
            return 'http'
        }
        return null;
    }

    makeAbsolute(url) {
        if (url.startsWith('//')) {
            return this.baseScheme + ':' + url;
        }

        return new URL(url, this.baseUrl).toString();
    }

    canProxy(url) {
        return url.startsWith('https:') || url.startsWith('http:')
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

    _templateRewrite(url, template, encode=true) {
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

        const finalUrl = template.replace('__URL__', absoluteUrl);
        console.log("  > (final)", finalUrl);

        return finalUrl;
    }
}


function monkeyPatch(urlRewriter) {
    console.log('Initializing Via DOM API monkey-patching');

    const origFetch = window.fetch;
    window.fetch = (url, ...args) => {
        console.log("Via: Triggered fetch patch", url, args);
        return origFetch.call(null, urlRewriter.proxyStatic(url), ...args);
    };

    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...args) {
        console.log("Via: Triggered XMLHttpRequest patch", method, url, args);
        return origOpen.call(this, method, urlRewriter.proxyStatic(url), ...args);
    };

    const origReplaceState = history.replaceState;
    history.replaceState = function (state) {
        console.log("Via: Tried to replace history (ignored)", state);
        //return pushState.apply(history, arguments);
    };
    const origPushState = history.pushState;
    history.pushState = function (state) {
        console.log("Via: Tried to change history (ignored)", state);
        //return pushState.apply(history, arguments);
    };
}


monkeyPatch(new URLRewriter(VIA_REWRITER_SETTINGS));
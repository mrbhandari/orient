/*
 * CONFIDENTIAL AND PROPRIETARY SOURCE CODE OF ORIENT, INC.
 *
 * Copyright (C) 2009-2011 Orient, Inc. All Rights Reserved.
 *
 * Use of this Source Code is subject to the terms of the applicable license
 * agreement from Orient, Inc.
 *
 * The copyright notice(s) in this Source Code does not indicate actual or
 * intended publication of this Source Code.
 */

/*
 * This is the tracking code for Orient. It tracks the browser by fetching
 * a pixel from a server.  The major tracking components are listed below.
 *   - Track page views by fetching pixel every time the page is loaded
 *   - Track link clicks by adding an event handler to the link so that mousedown on the link triggers a pixel fetch
 *   - Optionally, track time on page by periodically making pixel fetches
 *
 * See br-tracking-js.html for example usage.
 *
 *
 * Author: pradeep@orient.com
 */

/*global br_related_rid, s, escape, unescape */

(function(undefined) {
  var OrUtils = {
    getElementById: function(id) {
      if (document.getElementById) {
        return document.getElementById(id);
      } else if (document.all) {
        return document.all[id];
      } else if (document.layers) {
        return document.layers[id];
      }
      return null;
    },

    /**
     * Adds an event handler to obj.
     *
     * @param obj the element to which to add a handler
     * @param type the "type" of event to watch
     * @param callback the function to invoke
     */
    addEventHandler: function(obj, type, callback) {
      if (obj.addEventListener) {
        obj.addEventListener(type, callback, true);
      } else if (obj.attachEvent) {
        obj.attachEvent('on' + type, callback);
      } else {
        obj['on' + type] = callback;
      }
    },

    /**
     * Adds a handler to invoke when the document is considered "ready".
     * (This happens sooner than window load.)
     *
     * @param callback the function to invoke on document ready
     */
    addLoadHandler: function(callback) {

      // First check if the document has already been loaded in which case
      // execute the callback directly.
      if (document.readyState == "interactive" ||
          document.readyState == "complete" ||
          document.readyState == "loaded") {
        callback();
        return;
      }

      if (document.addEventListener) {
        document.addEventListener("DOMContentLoaded", callback, false);
      } else if (document.attachEvent) {
        document.attachEvent("onreadystatechange", function() {
          if (document.readyState === "complete") {
            callback();
          }
        });
      }
    },

    /**
     * Get domain name to set the cookie for.
     * www.domain.com goes to domain.com
     * domain.com remains unchanged
     */
    getBaseDomain: function(host) {
      var parts = host.split('.');
      var n = parts.length;
      if (n <= 2) {
        return host;
      }

      if (parts[n - 1].length <= 2 && parts[n - 2].length <= 3) {
        return parts[n - 3] + "." + parts[n - 2] + "." + parts[n - 1];
      } else {
        return parts[n - 2] + "." + parts[n - 1];
      }
    },

    /**
     * Sets a persistent cookie in the browser with cookieName and cookieValue.
     * @param cookieName name of the cookie
     * @param cookieValue value of the cookie
     * @return void
     */
    setPersistentCookie: function(cookieName, cookieValue, domain) {
      var expiryDate = new Date();
      expiryDate.setDate(expiryDate.getDate() + 365 * 100);
      var cookie = cookieName + "=" + escape(cookieValue) +
        "; expires=" + expiryDate.toGMTString() +
        "; path=/";
      if (domain) {
        cookie = cookie + "; domain=" + domain;
      }
      document.cookie = cookie;
    },

    /**
     * Gets the value of the cookie with name cookieName.
     * @param cookieName Name of the cookie.
     * @return value of the cookie, or empty string.
     */
    getCookie: function(cookieName) {
      if (document.cookie && (document.cookie.length > 0)) {
        var cookieIndex = document.cookie.indexOf(cookieName + "=");
        if (cookieIndex != -1) {
          cookieIndex = cookieIndex + cookieName.length + 1;
          var cookieEndIndex = document.cookie.indexOf(";", cookieIndex);
          if (cookieEndIndex == -1) {
            cookieEndIndex = document.cookie.length;
          }
          return unescape(document.cookie.substring(cookieIndex, cookieEndIndex));
        }
      }
      return "";
    },

    /**
     * Copies all properties from the source to the destination object.
     *
     * @param destination The object to receive the new properties.
     * @param source The object whose properties will be duplicated.
     * @return destination object
     */
    extend: function(destination, source) {
      for (var property in source) {
        if (source.hasOwnProperty(property)) {
          destination[property] = source[property];
        }
      }
      return destination;
    }
  };


  /**
   * Feature detection
   */
  var support = {
    'localStorage': typeof localStorage === 'object' && !!localStorage.removeItem,
    'jsonParsing': typeof JSON === 'object' && !!JSON.parse && !!JSON.stringify,
    'querySelector': typeof document.querySelector === 'function' && typeof document.querySelectorAll === 'function'
  };
  OrUtils.support = support;

  var browserDetect = {
    init: function () {
      this.browser = this.searchString(this.dataBrowser) || "An unknown browser";
      this.version = this.searchVersion(navigator.userAgent) || this.searchVersion(navigator.appVersion) || "an unknown version";
      this.OS = this.searchString(this.dataOS) || "an unknown OS";
      urlLength = 60000;
      subUrlLength = 30000;
      if (this.browser == "Explorer") {
        if (this.version <= 6) {
          urlLength = 1900;
          subUrlLength = 800;
        }
        else if(this.version <= 8) {
          urlLength = 4000;
          subUrlLength = 1800;
        }
      }
      this.urlLength = urlLength;
      this.subUrlLength = subUrlLength;
    },
    searchString: function (data) {
      for (var i = 0; i < data.length; i++) {
        var dataString = data[i].string;
        var dataProp = data[i].prop;
        this.versionSearchString = data[i].versionSearch || data[i].identity;
        if (dataString) {
          if (dataString.indexOf(data[i].subString) != -1)
            return data[i].identity;
        } else if (dataProp)
          return data[i].identity;
      }
    },
    searchVersion: function (dataString) {
      var index = dataString.indexOf(this.versionSearchString);
      if (index == -1) return;
      return parseFloat(dataString.substring(index + this.versionSearchString.length + 1));
    },
    dataBrowser: [{
      string: navigator.userAgent,
      subString: "Chrome",
      identity: "Chrome"
    }, {
      string: navigator.userAgent,
      subString: "OmniWeb",
      versionSearch: "OmniWeb/",
      identity: "OmniWeb"
    }, {
      string: navigator.vendor,
      subString: "Apple",
      identity: "Safari",
      versionSearch: "Version"
    }, {
      prop: window.opera,
      identity: "Opera",
      versionSearch: "Version"
    }, {
      string: navigator.vendor,
      subString: "iCab",
      identity: "iCab"
    }, {
      string: navigator.vendor,
      subString: "KDE",
      identity: "Konqueror"
    }, {
      string: navigator.userAgent,
      subString: "Firefox",
      identity: "Firefox"
    }, {
      string: navigator.vendor,
      subString: "Camino",
      identity: "Camino"
    }, { // for newer Netscapes (6+)
      string: navigator.userAgent,
      subString: "Netscape",
      identity: "Netscape"
    }, {
      string: navigator.userAgent,
      subString: "MSIE",
      identity: "Explorer",
      versionSearch: "MSIE"
    }, {
      string: navigator.userAgent,
      subString: "Gecko",
      identity: "Mozilla",
      versionSearch: "rv"
    }, { // for older Netscapes (4-)
      string: navigator.userAgent,
      subString: "Mozilla",
      identity: "Netscape",
      versionSearch: "Mozilla"
    }],
    dataOS: [{
      string: navigator.platform,
      subString: "Win",
      identity: "Windows"
    }, {
      string: navigator.platform,
      subString: "Mac",
      identity: "Mac"
    }, {
      string: navigator.userAgent,
      subString: "iPhone",
      identity: "iPhone/iPod"
    }, {
      string: navigator.platform,
      subString: "Linux",
      identity: "Linux"
    }]
  };
  browserDetect.init();
  OrUtils.browserDetect = browserDetect

  /**
   * This is the main tracker class.
   * @param version version of the tracking code.
   * @param data hash-map of the data that we want to log.
   * @return void
   */
  function OrTrkClass(version, data) {
    var pixelLocation = 'http://d3d6b97n2tsi13.cloudfront.net/pix.gif';

    // TODO We use cdns as that is the cert we currently have, but in the future we should
    // migrate this to another name and cert, say staticssl.brsrvr.com.
    // Also, leaving it on brsrvr.com (rather than brcdn.com) which is UltraDNS, as reliability
    // on SSL pages is particularly important.
    var sslPixelLocation = 'https://d3d6b97n2tsi13.cloudfront.net/pix.gif';
    var orCookieName = '_or_uid_1';
    var orCookieValue;

    var sid;
    var startTime;

    // Safeguarding enableTracking to only be executed at most once
    var hasEnabledTracking = false;

    // Legacy subdomain cookie support to be set in flags
    var setSubdomainCookie = OrTrk.options.setSubdomainCookie;
    // override point for unit testing
    var OrTrkConfig = window.OrTrkConfig;
    if (OrTrkConfig && typeof OrTrkConfig.setSubdomainCookie === 'boolean') {
      setSubdomainCookie = OrTrkConfig.setSubdomainCookie;
    }

	  var DEFERRED_PIXEL_KEY = 'br-trk.deferredPixel',
	      DEFERRED_DATA_KEY = 'br-trk.deferredData';

    /* Makes a shallow copy of the data object */
    function copyOf(obj) {
      var result = {};
      for (var key in obj) {
        if (obj.hasOwnProperty(key) &&
            (obj[key] !== undefined) &&
            (typeof obj[key] !== 'function')) {
          result[key] = obj[key];
        }
      }
      return result;
    }

    var version = version;
    // Make the copy of the external data to make sure we don't mess with it should the external
    // code rely on it being immutable. The data object is assumed to be flat, i.e. does not
    // contain any nested objects.
    var data = copyOf(data);
    /**
     * First this function checks if the user has the orient cookie, i.e. cookie with name orCookieName.
     * If so, then this function returns without doing anything. If not, then it sets a persistent cookie with name
     * orCookieName and value being a new randomly generated userId.
     *
     * Note: this function sets rCookieValue member variable to be the cookieValue. It is set to empty string if the
     * browser doesn't support cookies.
     *
     * We have two cookies. There is a legacy one that has the default domain (set to the subdomain) and a new
     * cookie where the domain is set to the actual domain (right now just dropping the first part of the subdomain). To allow
     * us to analyze the users which have both old and new cookies, we let the new cookie accumulate values
     * from the old cookie. The old UIDs are prepended with underscore (_).
     *
     * New cookie format is "uid=<user_id>:_uid=<old_id1>:_uid=<old_id2>:...:key1=val2:key2=val2:...:keyN=valN"
     * The new cookie has been in use for quite awhile now, and the legacy cookie should be retired. To that end, we
     * will make support for the legacy cookie optional, as well as chaining to the new cookie where it still exists.
     *
     * @return void
     */
    function setOrCookieIfNeededNew() {
      // Read the old cookie value.
      // Some old cookie values contain trailing colon that is removed here.
      var orCookie = OrUtils.getCookie(orCookieName).replace(/:$/g, "");
      //var brNewCookieValueCandidate = OrUtils.getCookie(brNewCookieName);
      var present = false;
      if (orCookie && orCookie.length > 0) {
        orCookieValue = orCookie;
        present = true;
      }
      //var newPresent = brNewCookieValueCandidate && brNewCookieValueCandidate.length > 0;

      var randUid = Math.round(Math.random() * 10E12);
      if (!present) {
        orCookieValue = "uid=" + randUid;
      }

      var uid;
      var cookieProps = {};

      if (!present) {
        uid = orCookieValue;
      } else {
        // Split the existing cookie values and extract the parameters
        var parts = orCookieValue.split(":");
        // Loop over the split parts (starting from index 1 since index 0 is the special user ID that always
        // comes first) and extract cookie values.
        uid = parts[0];
        for (var i = 1, len = parts.length; i < len; i++) {
          // Add the valid key-value pairs to the parameters map
          var kv = parts[i].split("=");
          if (kv[0] && kv[1]) {
            cookieProps[kv[0]] = kv[1];
          }
        }
      }

      // Update the mutable cookie properties and create the ones that are missing.

      // Script version (never changed once set)
      cookieProps.v = cookieProps.v || OrTrk.scriptVersion;
      // Creation timestamp (never changed once set)
      cookieProps.ts = cookieProps.ts || (new Date()).getTime();

      // Hit count (incremeted on every pageview)
      cookieProps.hc = Number(cookieProps.hc || 0) + 1;

      // Build the new cookie candidate string.
      var builder = [uid];
      for (var key in cookieProps) {
        builder.push(key + "=" + cookieProps[key]);
      }
      brNewCookieValue = builder.join(":");
      if (brNewCookieValue != orCookieValue &&
        // Sanity check to ensure that cookie length is not too large
        brNewCookieValue.length < 1000) {
        var cookieDomain = OrUtils.getBaseDomain(document.domain);
        OrUtils.setPersistentCookie(orCookieName, brNewCookieValue, cookieDomain);
        orCookieValue = OrUtils.getCookie(orCookieName); // Refetch cookie since the browser might not support cookies.
      }
    }

    /**
     * Finds the meta data associated with the passed in attribute name. If the resulting size of the data is
     * larger than maxLength, it trucates to maxLength.
     * @param metas List of meta data of the document obtained by document.getElementsByTagName("meta")
     * @param name The attribute name of the data we want to obtain.
     * @param maxLengh The maximum length of the data to be truncated.
     * @return The meta data associated with attribute-name name.
     */
    function getMetaTag(metas, name, maxLength) {
      var i, length = metas.length;
      for (i = 0; i < length; i++) {
        // '0' flag will make getAttribute case insenstive on IE < 8:
        var attrVal = metas[i].getAttribute('name', 0);
        if (attrVal) {
          if (attrVal.toLowerCase() === name) {
            return metas[i].getAttribute('content', 0).substr(0, maxLength);
          }
        }
      }
      return '';
    }

    /**
     * Finds meta keywords, meta description, truncates both to 200 characters each and returns
     * metaData object with mk and md set to hold these values.
     *
     * @param metaData The metaData object to which mk and md are added.
     * @return metaData object with mk and md values added.
     */
    function getMetaData(metaData) {
      var metas = document.getElementsByTagName("meta");
      metaData.mk = getMetaTag(metas, "keywords", 200);
      metaData.md = getMetaTag(metas, "description", 200);
      return metaData;
    }

    /**
     * Retrieves the canonical URL reference of the document (if set) from the "link" tags
     * of the document.
     *
     * @return canonical URL or null if not set.
     */
    function getCanonicalUrlRef() {
      var linkTags = document.getElementsByTagName("link");
      for (var i = 0, len = linkTags.length; i < len; i++) {
        if (linkTags[i].getAttribute("rel") == "canonical") {
          return linkTags[i].getAttribute("href");
        }
      }
      return '';
    }

    /**
     * Returns the referrer for the page, or empty string.
     * If the referrer has been explicitly passed in the data object then the provided
     * referrer is used, otherwise the document.referrer is used.
     * NOTE: It is also possible to use the Omniture referrer if avalable:
     * var referrer =  s.referrer;
     */
    function getReferrer(explicitReferrer) {
      if (explicitReferrer && explicitReferrer !== '') {
        return explicitReferrer;
      }
      return document.referrer || '';
    }

    /**
     * Combines the key and value into the "key=value" string. The value is urlencoded.
     * @param key param key.
     * @param value param value.
     */
    function makeParam(key, value) {
      return key + "=" + encodeURIComponent(value);
    }

    /**
     * Truncates the URL string if its length exceeds the limit and puts the double tilde
     * character (~~) at the end to indicate the URL has been truncated.
     */
    function truncateUrl(url) {
      var MAX_URL = OrUtils.browserDetect.subUrlLength; // sanity limit for URLs that are passed via pixel request.
      if (!url) {
        return ''; // sanity check
      }
      return url.length > MAX_URL ? url.substring(0, MAX_URL) + '~~' : url;
    }

    /**
     * Extracts the value from the data object and deletes the corresponding key from the object.
     * When the logging data params are appended to the query string in the priority order, they
     * need to be removed from the data object so they are not appended twice.
     * @param data The data object.
     * @param key The key to extract.
     * @return the value of the key or null if the key is undefined.
     */
    function extract(data, key) {
      var value = '';
      if (data[key]) {
        value = data[key];
        delete data[key];
      }
      return value;
    }

    /**
     * Generates a query string that is used for logging of all the
     * different types (pageview, linkclick, timespent).
     * @return query string in the ke2y=value2&key2=value2 form. All the values are urlencoded.
     */
    function generateQueryString(loggingData) {
      var params = [];

      // First come the most important params. The ones that come from the merchant data are
      // removed from the map so they are not appended twice.
      params.push(makeParam('acct_id', extract(loggingData, 'acct_id')));
      params.push(makeParam('cookie', orCookieValue));
      //params.push(makeParam('sid', sid));


      // If it is the conversion hit, push the flag and the basket value
      var isConversion = extract(loggingData, 'is_conversion');
      if (isConversion) {
        params.push(makeParam('is_conversion', isConversion));
      }
      var orderId = extract(loggingData, 'order_id');
      if (orderId) {
        params.push(makeParam('order_id', orderId));
      }
      var basketValue = extract(loggingData, 'basket_value');
      if (basketValue) {
        params.push(makeParam('basket_value', basketValue));
      }
      // push the referrer
      var explicitReferrer = extract(loggingData, 'explicit_referrer');
      params.push(makeParam('ref', truncateUrl(getReferrer(explicitReferrer))));

      params.push(makeParam('tzo', new Date().getTimezoneOffset()));

      // Push the random number to make sure the request goes through the caches
      params.push(makeParam('rand', Math.random()));
      
      // Append other params from the data object
      for (var key in loggingData) {
		if (key === "type" || key === "title" || key === "link" || 
			key === "path" || key === "time" || key == "href" ||
			key == "element_txt" || key == "element" || 
			key == "cssclass" || key == "img_src" || key == "label" ||
		   	key == "name") {
          params.push(makeParam(key, loggingData[key]));
		}
      }

      // Append the page URL and canonical URL at the end of the request.
      // URLs are always appended at the end of the query in order to sacrifice them
      // in case we hit the URL quota on IE (2k).
      var url = truncateUrl(location.href);
      params.push(makeParam('url', url));
      var can_url = truncateUrl(getCanonicalUrlRef());
      // Check if the rel canonical exists on the page
      if (can_url) {
        // set the rc flag which specifies the rel canonical exist on the page
        params.push(makeParam('rc', 1));
        // if the rel canonical is different from the page url, set it explicitly
        if (can_url != url) {
          params.push(makeParam('can_url', can_url));
        }
      }
      // Version is the legacy param not used on the server side so it goes in the end of the hit
      //params.push(makeParam('version', version));
      return params.join('&');
    }
    
    /**
     * Basket data should be passed in the following format:
     * 'basket': {
     *    'items': [
     *     {
     *       'prod_id' : 'pid123456',
     *       'sku': 'p3458755',
     *       'name': 'Cashmere Sweater',
     *       'quantity': '1',
     *       'price': '65.95', 
     *       'mod': 'sale'
     *    },
     *  }
     * Encodes a list of items in the extended basket data in the following format
     * 
     * <item_separator><attr_code><attr_value><attr_separator>
     * 
     * eg, !ip3458755'nCashemere Sweater'q1'p65.95'msale!ip35945786'q2'p9.55'mblue,XL
     *
     * @param items A list of items that are Javascript objects
     * @return encoded_items A string in the format described above.
     */
    function encodeExtendedBasketParams(items) {
      var ITEM_SEPARATOR = '!';
      var ATTR_SEPARATOR = '\'';
      var ATTR_CODE_MAP = {
        'prod_id' : 'i',
        'sku' : 's',
        'name' : 'n',
        'quantity' : 'q',
        'price' : 'p',
        'mod' : 'm'
      }
      var encoded_items = [];
      for (var idx = 0; idx < items.length; idx++) {
        var item_attrs = [];
        for (var key in items[idx]) {
          // Is this a valid key?
          if (key in ATTR_CODE_MAP) {
            item_attrs.push([ATTR_CODE_MAP[key], items[idx][key]].join(''));
          }
        }
        var encoded_item = item_attrs.join(ATTR_SEPARATOR);
        encoded_items.push(encoded_item);
      }
      var result = ITEM_SEPARATOR + encoded_items.join(ITEM_SEPARATOR);
      return result;
    }

    /**
     * Given a queryString, creates an Image object with the appropriate HTTP or HTTPS pixel location and attaches the
     * queryString to it.
     * 
     * @param queryString   the query string for pixel, without the '?'
     */
    function firePixel(queryString) {
      var img = new Image();
      var baseUrl = ("https:" === document.location.protocol) ? sslPixelLocation : pixelLocation;
      img.src = baseUrl + "?" + queryString;
    }

    /**
     * This is final call that logs the data by fetching a pixel from a orient server.
     * To improve support for other product- or customer-specific use cases, it looks for the presence of
     * pixelLogCallback within OrTrkConfig and calls it on loggingData to give the callback a chance to examine and/or
     * modify it.
     * 
     * @param loggingData Hashmap of all the data that needs to be logged.
     * @param deferred    (optional) true to queue up the pixel to fire with the next pageview.
     *                    This is necessary to make sure event pixels aren't lost when leaving the page.
     *                    Only works with HTML5 local storage-enabled browsers.
     * @return void
     */
    function pixelLog(loggingData, deferred) {
      // Since pixelLogCallback can be any function defined by the globally-accessible OrTrkConfig, we need to catch any
      // potential errors to make sure they don't stop the pixel from firing.
      try {
        var OrTrkConfig = window.OrTrkConfig;
        // Pickup all _br_m* and _br_mz* cookies if we include br-trk-visits.template.js
        if (window.OrTrk && window.OrTrk.BrmCookies && typeof window.OrTrk.BrmCookies.logCookies === 'function') {
          window.OrTrk.BrmCookies.logCookies(loggingData);
        }
        if (OrTrkConfig && typeof OrTrkConfig.pixelLogCallback === 'function') {
          OrTrkConfig.pixelLogCallback(loggingData);
        }
      } catch (err) {}

      loggingData["lang"] = navigator.language || navigator.browserLanguage;

      //log extra cookie items
      var extraCookies = OrTrk.options.extraCookies || [];
      for (var i=0; i<extraCookies.length; i++) {
        var cookie = extraCookies[i];
        var cookieValue = OrUtils.getCookie(cookie['name']);
        if(cookieValue || cookieValue === false || cookieValue === 0) {
          // "_ec_" is prefixed in key, so that it does not collide with other keys: ec = extracookie
          var cookieName = "_ec_"+cookie['name'];
          if(cookieValue.length <= cookie['maxLength']) {
            loggingData[cookieName] = cookieValue;
          } else {
            loggingData[cookieName] = cookieValue.substring(0, cookie['maxLength']);
          }
        }
      }

      var queryString = generateQueryString(loggingData);

      // TODO(max): Make the logic more intelligent (check the remaining length of the query, drop
      // the non-important params, truncate URLs etc).
      if (queryString.length > OrUtils.browserDetect.urlLength) {
        queryString = queryString.substr(0, OrUtils.browserDetect.urlLength) + "&tr=1";
      }
      if (deferred) {
        if (support.localStorage) {
          localStorage[DEFERRED_PIXEL_KEY] = queryString;
        }
      } else {
        firePixel(queryString);
      }
    }

    /**
     * This is the main function that logs all the data for the user viewing a page.
     * @param opt_pageViewType String value that dictates what we log
     * @return void
     */
    function logPageView(opt_pageViewType) {
      // Fire deferred pixels (if any).
      // These pixels should be fired before the current page's pageview pixel so that the clickstream order is
      // maintained.
      logDeferredPixels();

      var pageViewData = copyOf(data);
      opt_pageViewType = opt_pageViewType || 'pageview';
      pageViewData.type = opt_pageViewType;
      if (document.title) {
        pageViewData.title = document.title.substr(0, 200);
      }

     // BR Custom data should be parsed and passed in final query String as top level params
     // Example br_custom_data = { ‘sem’ :{ sem-key-1’ : ‘sem-value-1’}, 'project' : {  "key1' : 'value1', "key2' : 'value2' }}
     // add to the pageViewData following key:values project_key1=value1 | product_key2=value2 | sem-sem-key-1=sem-value-1 and so on
     if (typeof document.br_custom_data !== 'undefined') {
        var custom_data = document.br_custom_data;
        for (var key in custom_data) {
          for (var subkey in custom_data[key]) {
            pageViewData[key + "_" + subkey] = custom_data[key][subkey];
          }
        }
      }

      // Merge in deferred data (if any).
      // See logEvent() for deferred pixels.
      // If there are any conflicting parameters, pageViewData should override the deferred data.
      try {
        if (support.localStorage && support.jsonParsing && localStorage[DEFERRED_DATA_KEY]) {
          var deferredData = JSON.parse(localStorage[DEFERRED_DATA_KEY]);
          if (deferredData) {
            for (var key in deferredData) {
              if (deferredData.hasOwnProperty(key)) {
                var newKey = 'df_' + key;
                if (typeof pageViewData[newKey] === 'undefined') {
                  pageViewData[newKey] = deferredData[key];
                }
              }
            }
          }
          localStorage.removeItem(DEFERRED_DATA_KEY);
        }
      } catch (err) {}

      pixelLog(pageViewData);
    }

    /**
     * This is the main function that logs all the data for the user when (s)he clicks a link. Note that this is the
     * call that logs the link click -- not the function that decorates the links with callback.
     * @param link the URL of the link that was clicked (can be undefined if the clicked element was not a link)
     * @param path the DOM path from the root div to the clicked element. Format looks like this: "DIV.class|DIV.class2|A.class3"
     */
    function logLinkClick(link, path) {
      var linkClickData = copyOf(data);
      linkClickData.type = 'linkclick';
      if (link) {
        linkClickData.link = link;
      }
      if (path) {
        linkClickData.path = path;
      }
      linkClickData.time = (new Date()).getTime() - startTime;
      pixelLog(linkClickData);
    }
    
    
    function logAction(href, path, tag) { 
      var linkClickData = copyOf(data);
      linkClickData.type = 'linkclick';
      if (href) {
        linkClickData.href = href;
      }
      if (path) {
        linkClickData.path = path;
      }
      if (tag) {
        linkClickData.tag = tag;
      }
      linkClickData.time = (new Date()).getTime() - startTime;
      pixelLog(linkClickData);
    }

    
    setTimeout(
    function() {
        var arrayWithElements = new Array();
        
        function clickListener(e) 
        {   
            setOrCookieIfNeededNew();
            var clickedElement=(window.event)
                                ? window.event.srcElement
                                : e.target;
                var pathHref = getElementPathHref(document.body, clickedElement)
                
                parsedData = copyOf(data);
	
                parsedData.type = "click";
                parsedData.element = clickedElement.tagName;
                parsedData.cssclass = clickedElement.className;
                parsedData.path = pathHref.path;
                parsedData.name = clickedElement.getAttribute("name");
                parsedData.element_txt = clickedElement.textContent;

                if (clickedElement.tagName == "INPUT") {
                  parsedData.label = clickedElement.parentElement.innerText;
                  parsedData.input_type = clickedElement.getAttribute("type");
                  parsedData.value = clickedElement.getAttribute("value");
                  parsedData.element_txt = clickedElement.getAttribute("placeholder");
                }
                
                if (clickedElement.tagName == "BUTTON" || clickedElement.tagName ==  "SELECT" || clickedElement.tagName ==  "TEXTAREA" || clickedElement.tagName ==  "OPTION") {
                  parsedData.element_txt = clickedElement.getAttribute("value");
                }
                
                if (clickedElement.tagName == "IMG") {
                  parsedData.img_src = clickedElement.getAttribute("src");
                  parsedData.element_txt = clickedElement.getAttribute("alt");
                }
                
                if (clickedElement.tagName == "A") {
                  parsedData.element_txt = clickedElement.textContent;
                  parsedData.href = clickedElement.getAttribute("href");
                }
		
                pixelLog(parsedData);
        }
        
        document.onclick = clickListener;
    },1000);

    /**
     * The method triggers the tracking pixel request with the type 'event', 
     *   passing the parameters in the request query string.
     * The values of the parameters are URL-encoded
     *
     * @param group Name of the group the event belongs to. eg. 'Cart'
     * @param action Name of the event's action. eg. 'add' and 'remove' for 
     *   events in the 'Cart' group
     * @param opt_params (optional) Additional parameters to be passed with the event. 
     *   eg. Product ID, color and name of the product that was added to the cart. These are top level params in the OrTrk pixel request.
     * @param opt_value (optional) A numeric value associated with an event. The meaning 
     *   is event specific. eg, the price of the item added to the cart.
     * @param deferred (optional) see pixelLog()
     *                 Deferred event pixels will also have their data merged into the next pageview pixel, so that a
     *                 single pixel contains the data about the page and the action that led the visitor to the page.
     *                 This is needed for real-time pixel processing by Storm.
     *
     * Sample invocation
     *
     *   OrTrk.getTracker().logEvent('Cart', 'add', {'prod_id' : '348574', 'prod_color' : 'blue', 'prod_name' : 'Levi\'s Jeans Model 505'}, 
     *     {'key1' : 10});
     *
     */
    function logEvent(group, action, opt_params, opt_value, deferred) {
      var logEventData = copyOf(data);
      logEventData.group = group;
      logEventData.type = 'event';
      logEventData.etype = action;
      OrUtils.extend(logEventData, opt_params);
      OrUtils.extend(logEventData, opt_value);

      // If this is a deferred event, then save the data to be merged with the destination pageview.
      // Do this before pixelLog() because pixelLog() extracts data from logEventData.
      try {
        if (deferred && support.localStorage && support.jsonParsing) {
          localStorage[DEFERRED_DATA_KEY] = JSON.stringify(logEventData);
        }
      } catch (err) {}

      pixelLog(logEventData, deferred);
    }

    /**
     * Fires any deferred pixels in localStorage.
     * 
     * @return void
     */
    function logDeferredPixels() {
      if (support.localStorage) {
        var deferredPixel = localStorage[DEFERRED_PIXEL_KEY];
        if (deferredPixel) {
          localStorage.removeItem(DEFERRED_PIXEL_KEY);
          firePixel(deferredPixel);
        }
      }
    }

    /**
     * Returns the DOM path from the ancestor element to the target element, e.g. DIV.buttons|SPAN|A.addtocartbutton
     * If any of the nodes are HTML anchor elements, then the href is also returned.
     * 
     * @param ancestor               the element to stop at when walking up the DOM tree from the target element
     * @param target                 the element to start at when building the DOM path
     * @return {
     *           'path': 'string',   the DOM path from the ancestor to the target
     *           'href': 'string'    the lowest href attribute of any A tags in the path
     *         }
     */
    function getElementPathHref(ancestor, target) {
      var separator = '|',
          path = [],
          href;

      if (target) {
        while (target && (target !== ancestor.parentNode)) {
          var elem = target.tagName;
          if (target.id) {
            elem += '#' + target.id;
          } else if (target.className) {
            elem += '.' + target.className;
          }
          if (!href && target.tagName === 'A') {
            href = target.href;
          }
          path.splice(0, 0, elem);
          target = target.parentNode;
        }
      }

      return {
        'path': path.join(separator),
        'href': href || ''
      };
    }

    /**
     * Assigns a click tracker to the specified div. The click tracker reports all mousedowns
     * registered inside the div (i.e., on the div's subelements).
     * @param divId the ID of the div to track. An unknown div ID is ignored.
     * @param isClass a boolean flag indicating if divId is the name of a class instead of an ID
     *                If true, then a click tracker will be added to only the first element that matches that class.
     *                Note that this only happens for websites/browsers that define document.getElementsByClassName().
     * @return True if the handler was successfully assigned.
     */
    function addClickTracker(divId, isClass, callback) {
      var div = (isClass && typeof document.getElementsByClassName === 'function') ?
                    document.getElementsByClassName(divId)[0] : document.getElementById(divId);
      if (!div) {
        return false;
      }
      var clicked = function (e) {
        if (typeof callback === 'function') {
          callback(data);
        }
        var evt = e || window.event;
        var target = evt.target || evt.srcElement;
        if (!target) {
          return false;
        }
        var pathHref = getElementPathHref(div, target);
        logLinkClick(pathHref.href, pathHref.path);
      };
      OrUtils.addEventHandler(div, 'mousedown', clicked);
      return true;
    }

    /**
     * Assigns an event handler to every DOM element matched by the given selector, listening for the specified event.
     * The handler fires an event tracking pixel with the given event tracking data whenever the handler is triggered.
     * 
     * @param trackedElement   a data structure in the following format:
     *                         {
     *                           'id': 'elementID',             // }
     *                           'className': 'elementClass',   // }---exactly one of these should be given
     *                           'selector': 'cssSelector',     // }
     *                           'event': 'domEventName',       // required
     *                           'group': 'brEventGroup',       // required
     *                           'action': 'brEventAction',     // required
     *                           'deferred': true               // optional - see pixelLog()
     *                         }
     *                         Exactly one of the fields 'id', 'class', or 'selector' should be given.  If more than
     *                         one is provided, it uses only the first one it finds.  If none are provided, then this
     *                         function does nothing.
     *                         Note:
     *                         'id' should always work since document.getElementById() should be a built-in function.
     *                         'class' works only if document.getElementsByClassName() or document.querySelectorAll()
     *                             is implemented.
     *                         'selector' works only if document.querySelectorAll() is implemented.
     * @return True if the handler was successfully assigned.
     */
    function addEventTracker(trackedElement) {
      if (!trackedElement.event || !trackedElement.group || !trackedElement.action) {
        return false;
      }

      var matchedElements = [];

      if (trackedElement.id) {
        var element = document.getElementById(trackedElement.id);
        if (element) {
          matchedElements.push(element);
        }
      } else if (trackedElement.className) {
        var elements = [];

        if (typeof document.getElementsByClassName === 'function') {
          elements = document.getElementsByClassName(trackedElement.className);
        } else if (support.querySelector) {
          elements = document.querySelectorAll('.' + trackedElement.className);
        }

        if (elements.length) {
          matchedElements = elements;
        }
      } else if (trackedElement.selector && support.querySelector) {
        var elements = document.querySelectorAll(trackedElement.selector);
        if (elements.length) {
          matchedElements = elements;
        }
      }

      if (matchedElements.length) {
        var i = matchedElements.length;
        while (i--) {
          var eventHandler = (function (matchedElement) {
            return function (e) {
              var evt = e || window.event;
              var target = evt.target || evt.srcElement;
              if (!target) {
                return false;
              }
              var pathHref = getElementPathHref(matchedElement, target);
              logEvent(trackedElement.group, trackedElement.action, { 'path': pathHref.path }, {}, trackedElement.deferred);
            };
          })(matchedElements[i]);

          OrUtils.addEventHandler(matchedElements[i], trackedElement.event, eventHandler);
        }

        return true;
      }
    }

    /**
     * Assigns click trackers to the divs that are passed in. Divs that
     * aren't found are ignored.
     * @param [array of div IDs] one or more div IDs (e.g., ["div-related-searches", "div-search-found"])
     * @param isClass a boolean flag indicating if ids is an array of class names instead of IDs
     */
    function addClickTrackers(ids, isClass) {
      var i;
      for (i = 0; i < ids.length; i++) {
        addClickTracker(ids[i], isClass);
      }
    }

    /**
     * Assigns event handlers to the DOM elements that match the given selectors.
     * 
     * @param [array of events to track]  see addEventTracker() for the data model of each event
     */
    function addEventTrackers(trackedElements) {
      var i = trackedElements.length;
      while (i--) {
        addEventTracker(trackedElements[i]);
      }
    }

    /**
     * Enables link tracking on all Orient widgets (e.g., related searches and more results).
     */
    function enableLinkTracking() {
      if (!OrTrk.options.linkTracking) {
        return;
      }
      OrUtils.addLoadHandler(function () {
        addClickTrackers(OrTrk.options.linkTrackingIds);
        addClickTrackers(OrTrk.options.linkTrackingClasses, true);
      });
    }

    /**
     * Enables event tracking on the DOM elements configured for the customer.
     */
    function enableEventTracking() {
      if (!OrTrk.options.eventTracking) {
        return;
      }
      OrUtils.addLoadHandler(function () {
        addEventTrackers(OrTrk.options.eventTrackingSelectors.trackedElements);
      });
    }

    /**
     * Enables time tracking by pinging Orient at increasing time intervals up to
     * a max time.
     */
    function enableTimeTracking() {
      if (!OrTrk.options.timeTracking) {
        return;
      }

      // Times (in millis) at which we want to ping back a orient
      // server to log time spent on site.
      var timeOnSite = [5000, 25000, 75000, 150000];

      var logTimeOnSite = function(timeIndex) {
        var timeOnSiteData = copyOf(data);
        timeOnSiteData.type = 'sitetime';
        timeOnSiteData.time = timeOnSite[timeIndex];
        pixelLog(timeOnSiteData);
      };

      var i;
      for (i = 0; i < timeOnSite.length; ++i) {
        // Need the anonymous function to bind timeOnSite
        (function(timeIdx) {setTimeout(function() {logTimeOnSite(timeIdx); }, timeOnSite[timeIdx]); })(i);
      }
    }

    /**
     * This is the default tracking for orient.
     * @return void
     */
    function enableTracking() {
      if (hasEnabledTracking) {
        return;
      }
      logPageView();
      enableLinkTracking();
      enableEventTracking();
      enableTimeTracking();

      hasEnabledTracking = true;
    }

    function init() {
      startTime = (new Date()).getTime();
      setOrCookieIfNeededNew();
    }


    // Expose public functions below.
    // The default/primary tracking which we should have nearly all customers use.
    this.enableTracking = enableTracking;

    // Fine grained tracking functions below.
    this.logPageView = logPageView;
    this.logLinkClick = logLinkClick;
    this.enableLinkTracking = enableLinkTracking;
    this.logEvent = logEvent;
    // Dynamic registration of DOM elements to track.
    this.addClickTracker = addClickTracker;

    // various getters, these are used by br-social to send as query parameters for
    // the social widget.
    this.getCookie = OrUtils.getCookie;
    this.getReferrer = getReferrer;

    init(); // Initialization.
  }

  var tracker;
  window.OrTrk = {
    scriptVersion : "0.1",
    acctId : 1123,
    timestamp : 20150125,

    // set customer-specific options:
    options : {
      selfExecuting: true,
      linkTracking : true,
      linkTrackingIds : [''],
      linkTrackingClasses : [''],
      eventTracking : false,
      eventTrackingSelectors : {'trackedElements':[]},
      timeTracking : false,
      extraCookies : [],
      setSubdomainCookie : true
    },

    getTracker : function(version, data) {
      if (!tracker) {
        tracker = new OrTrkClass(version, data);
      }
      return tracker;
    },

    // orient internal functions.
    // ------------------------------

    /**
     * Used by br-social to get access to or_data and other information.
     * @return the singleton tracker if it has been created, or null.
     */
    _getTrackerIfExists : function() {
      return tracker || null;
    },

    OrUtils : OrUtils
  };

  // only defined in unit test environment:
  if (typeof testOrTrk !== "undefined") {
    window.OrUtils = OrUtils;
    window.OrTrkClass = OrTrkClass;
  }

  // For customers who lack the ability to serialize the loading of
  // the br-trk javascript and firing of the pixel, we provide this
  // self-executing option.
  //
  // Longer term, this should become the default since it requires
  // lesser lines of code for the merchant to integrate. For merchants
  // requiring finer control, we would simple disable the option.
  //
  // Requires: Global variable or_data.
  //
  if (OrTrk.options.selfExecuting && window.or_data) {
    try {
      var tracker = OrTrk.getTracker(0.1, or_data);
      tracker.enableTracking();
    } catch(err) {}
  }
}());

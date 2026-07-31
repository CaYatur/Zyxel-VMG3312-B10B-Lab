(function(window){
  'use strict';

  window.actionItemID = window.actionItemID || null;
  window.tabIndex = Number(window.tabIndex || 0);

  window.setPageIndex = function(menuIndex){
    window.actionItemID = menuIndex || null;
  };

  window.setTabIndex = function(index){
    window.tabIndex = Number(index || 0);
  };

  var jq = window.jQuery || window.$;
  if(!jq){return;}

  function resolveLegacyUrl(rawUrl){
    if(typeof rawUrl !== 'string' || !rawUrl){return rawUrl;}
    var separator = rawUrl.indexOf(' ');
    var urlPart = separator >= 0 ? rawUrl.slice(0, separator) : rawUrl;
    var selectorPart = separator >= 0 ? rawUrl.slice(separator) : '';
    if(/^(?:[a-z]+:)?\/\//i.test(urlPart) || urlPart.charAt(0) === '/' || urlPart.charAt(0) === '#'){
      return urlPart + selectorPart;
    }
    if(/^pages\//i.test(urlPart)){
      return '/' + urlPart + selectorPart;
    }
    var base = window.CAYA_BRIDGE_BASE || '/pages/';
    try{
      var resolved = new URL(urlPart, window.location.origin + base);
      return resolved.pathname + resolved.search + resolved.hash + selectorPart;
    }catch(error){
      return urlPart + selectorPart;
    }
  }

  if(jq.fn && jq.fn.load && !jq.fn.load.cayaWrapped){
    var originalLoad = jq.fn.load;
    var wrappedLoad = function(url, params, callback){
      return originalLoad.call(this, resolveLegacyUrl(url), params, callback);
    };
    wrappedLoad.cayaWrapped = true;
    jq.fn.load = wrappedLoad;
  }

  if(jq.ajax && !jq.ajax.cayaWrapped){
    var originalAjax = jq.ajax;
    var wrappedAjax = function(url, options){
      if(typeof url === 'string'){
        var directSettings = options && typeof options === 'object' && jq.extend ? jq.extend({}, options) : (options || {});
        directSettings.url = resolveLegacyUrl(url);
        return originalAjax.call(jq, directSettings);
      }
      if(url && typeof url === 'object' && typeof url.url === 'string'){
        var settings = jq.extend ? jq.extend({}, url) : url;
        settings.url = resolveLegacyUrl(settings.url);
        return originalAjax.call(jq, settings);
      }
      return originalAjax.apply(jq, arguments);
    };
    wrappedAjax.cayaWrapped = true;
    jq.ajax = wrappedAjax;
  }

  ['get','post','getJSON','getScript'].forEach(function(method){
    if(!jq[method] || jq[method].cayaWrapped){return;}
    var original = jq[method];
    var wrapped = function(url){
      var args = Array.prototype.slice.call(arguments);
      args[0] = resolveLegacyUrl(url);
      return original.apply(jq, args);
    };
    wrapped.cayaWrapped = true;
    jq[method] = wrapped;
  });

  window.CAYA_RESOLVE_LEGACY_URL = resolveLegacyUrl;

  jq.hciAlert = jq.hciAlert || function(message){
    var plain = String(message == null ? '' : message).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
    window.alert(plain || 'Modem işlemi tamamlanamadı.');
  };

  jq.closeLoadingMask = jq.closeLoadingMask || function(){};
  jq.openLoadingMask = jq.openLoadingMask || function(){};
  jq.zyMask = jq.zyMask || function(){};
  jq.closezyMask = jq.closezyMask || function(){};

  if(!jq.zyUiDialog){
    jq.zyUiDialog = function(options){
      var container = jq('<div class="dialogContener"></div>').appendTo('body');
      if(container.dialog){container.dialog(options || {});}
      container.setBtnAttr = function(){return container;};
      return container;
    };
  }

  var originalDialogFactory = jq.zyUiDialog;
  if(originalDialogFactory && !originalDialogFactory.cayaWrapped){
    var wrappedDialogFactory = function(options){
      var container = originalDialogFactory.call(jq, options || {});
      if(container && container.load && !container.load.cayaWrapped){
        var originalContainerLoad = container.load;
        var wrappedContainerLoad = function(url, params, callback){
          var normalizedUrl = resolveLegacyUrl(url);
          var userCallback = typeof params === 'function' ? params : callback;
          var requestData = typeof params === 'function' ? undefined : params;
          return originalContainerLoad.call(this, normalizedUrl, requestData, function(responseText, status, xhr){
            if(status === 'error'){
              container.html('<div class="caya-dialog-error"><strong>İçerik yüklenemedi.</strong><span>' + normalizedUrl + '</span></div>');
            }
            if(typeof userCallback === 'function'){
              userCallback.call(this, responseText, status, xhr);
            }
            window.setTimeout(refreshDialogState, 0);
          });
        };
        wrappedContainerLoad.cayaWrapped = true;
        container.load = wrappedContainerLoad;
      }
      window.setTimeout(refreshDialogState, 0);
      return container;
    };
    wrappedDialogFactory.cayaWrapped = true;
    jq.zyUiDialog = wrappedDialogFactory;
  }

  function normalizeDialog(dialog){
    if(!dialog || dialog.nodeType !== 1){return;}
    var content = dialog.querySelector('.dialogContener,.ui-dialog-content');
    if(!content){return;}

    dialog.classList.add('caya-stock-dialog');
    document.body.classList.add('caya-dialog-open');

    var title = dialog.querySelector('.ui-dialog-title');
    if(title){
      var normalizedTitle = String(title.textContent || '')
        .replace(/close/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
      title.textContent = normalizedTitle || 'Ayarları Düzenle';
    }

    var closeButton = dialog.querySelector('.ui-dialog-titlebar-close');
    if(closeButton){
      closeButton.setAttribute('aria-label', 'Kapat');
      closeButton.setAttribute('title', 'Kapat');
    }

    var buttons = dialog.querySelectorAll('.ui-dialog-buttonpane button');
    Array.prototype.forEach.call(buttons, function(button){
      var text = String(button.textContent || button.value || '').replace(/\s+/g, ' ').trim();
      if(/cancel|iptal/i.test(text)){button.textContent = 'İptal';}
      if(/apply|ok|save|uygula|kaydet/i.test(text)){button.textContent = 'Uygula';}
    });
  }

  function refreshDialogState(){
    var dialogs = document.querySelectorAll('.ui-dialog');
    var visibleCount = 0;
    Array.prototype.forEach.call(dialogs, function(dialog){
      var style = window.getComputedStyle ? window.getComputedStyle(dialog) : null;
      if(!style || style.display !== 'none'){
        normalizeDialog(dialog);
        visibleCount += 1;
      }
    });
    document.body.classList.toggle('caya-dialog-open', visibleCount > 0);
  }

  var observer = new MutationObserver(function(records){
    records.forEach(function(record){
      Array.prototype.forEach.call(record.addedNodes || [], function(node){
        if(!node || node.nodeType !== 1){return;}
        if(node.matches && node.matches('.ui-dialog')){normalizeDialog(node);}
        if(node.querySelectorAll){
          Array.prototype.forEach.call(node.querySelectorAll('.ui-dialog'), normalizeDialog);
        }
      });
    });
    window.setTimeout(refreshDialogState, 0);
  });

  function startDialogObserver(){
    if(!document.body){return;}
    observer.observe(document.body, {childList:true, subtree:true, attributes:true, attributeFilter:['style','class']});
    refreshDialogState();
    jq(document).bind('dialogopen.caya dialogclose.caya', function(){window.setTimeout(refreshDialogState, 0);});
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', startDialogObserver);
  }else{
    startDialogObserver();
  }
})(window);

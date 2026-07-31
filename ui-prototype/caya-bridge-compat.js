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

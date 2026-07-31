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
})(window);

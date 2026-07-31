(function(){
  'use strict';

  var modules = Array.isArray(window.CAYA_LIVE_MODULES) ? window.CAYA_LIVE_MODULES : [];
  var bridge = document.getElementById('bridgeFrame');
  var panel = document.getElementById('nativePanel');
  var tabs = document.getElementById('pageTabs');
  var statusBar = document.getElementById('statusBar');
  var title = document.getElementById('viewerTitle');
  var pathLabel = document.getElementById('viewerPath');
  var pageTitle = document.getElementById('pageTitle');
  var nav = document.getElementById('mainNav');
  var viewer = document.getElementById('viewer');
  var search = document.getElementById('moduleSearch');
  var liveBadge = document.getElementById('liveBadge');
  var activeModule = null;
  var activePage = null;
  var activePageIndex = 0;
  var controlLinks = [];
  var bridgePollToken = 0;

  var overview = {
    id: 'overview',
    title: 'Genel Bakış',
    category: 'Durum',
    risk: 'normal',
    pages: [{label: 'Durum', url: '/pages/connectionStatus/naviView_partialLoad.html', default: true}]
  };

  function str(value){return String(value == null ? '' : value);}
  function clean(value){return str(value).replace(/\s+/g, ' ').trim();}
  function setStatus(message, kind){
    statusBar.textContent = message;
    statusBar.className = 'status-bar' + (kind ? ' ' + kind : '');
    liveBadge.textContent = kind === 'error' ? 'Bağlantı hatası' : 'Canlı cihaz verisi';
    liveBadge.className = 'live-badge' + (kind === 'error' ? ' error' : '');
  }
  function resolvePage(module, page){
    var raw = page && page.url ? page.url : module.route;
    try{
      var resolved = new URL(raw, window.location.origin + '/pages/tabFW/');
      return resolved.pathname + resolved.search;
    }catch(error){return raw;}
  }
  function resolveBridge(module, page, pageIndex){
    if(module && module.tabJson && module.route){
      var route = module.route.replace(/tabIndex=\d+/, 'tabIndex=' + pageIndex);
      return route;
    }
    return resolvePage(module, page);
  }
  function pageList(module){
    var pages = Array.isArray(module.pages) && module.pages.length ? module.pages : [{label: module.title, url: module.route, default: true}];
    return pages.filter(function(page){return page && page.url;});
  }

  function openModule(module){
    if(!module){return;}
    if(module.risk === 'critical' && !window.confirm('Bu bölüm kritik bakım işlemleri içerir. Devam edilsin mi?')){return;}
    activeModule = module;
    pageTitle.textContent = module.title;
    title.textContent = module.title;
    viewer.hidden = false;
    Array.prototype.forEach.call(nav.querySelectorAll('.nav-button'), function(button){
      button.classList.toggle('active', button.getAttribute('data-module-id') === module.id);
    });
    buildPageTabs(module);
    var pages = pageList(module);
    var defaultIndex = Math.max(0, pages.findIndex(function(page){return page.default;}));
    openPage(pages[defaultIndex], defaultIndex);
    window.location.hash = encodeURIComponent(module.id);
  }

  function buildPageTabs(module){
    var pages = pageList(module);
    tabs.innerHTML = '';
    tabs.classList.toggle('has-pages', pages.length > 1);
    var activeButton = nav.querySelector('.nav-button.active');
    if(activeButton){activeButton.insertAdjacentElement('afterend', tabs);}
    pages.forEach(function(page, index){
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'page-tab';
      button.textContent = page.label || module.title;
      button.addEventListener('click', function(){openPage(page, index);});
      button.dataset.index = String(index);
      tabs.appendChild(button);
    });
  }

  function openPage(page, pageIndex){
    if(!activeModule || !page){return;}
    activePage = page;
    activePageIndex = Number(pageIndex || 0);
    var displayUrl = resolvePage(activeModule, page);
    var bridgeUrl = resolveBridge(activeModule, page, activePageIndex);
    pathLabel.textContent = displayUrl;
    Array.prototype.forEach.call(tabs.querySelectorAll('.page-tab'), function(button){button.classList.toggle('active', Number(button.dataset.index) === activePageIndex);});
    panel.innerHTML = '';
    controlLinks = [];
    bridgePollToken += 1;
    setStatus('Modemden canlı ayarlar okunuyor…');
    bridge.src = bridgeUrl + (bridgeUrl.indexOf('?') >= 0 ? '&' : '?') + '_cayaBridge=' + Date.now();
  }

  function labelFor(control, doc){
    if(control.id){
      var direct = doc.querySelector('label[for="' + CSS.escape(control.id) + '"]');
      if(direct && clean(direct.textContent)){return clean(direct.textContent);}
    }
    var wrapping = control.closest('label');
    if(wrapping && clean(wrapping.textContent)){return clean(wrapping.textContent);}
    var row = control.closest('tr');
    if(row){
      var cells = row.querySelectorAll('th,td');
      for(var i=0;i<cells.length;i++){
        if(!cells[i].contains(control) && clean(cells[i].textContent)){return clean(cells[i].textContent);}
      }
    }
    return control.getAttribute('title') || control.name || control.id || 'Ayar';
  }

  function proxyControl(source, doc){
    var type = (source.type || source.tagName || '').toLowerCase();
    if(type === 'hidden' || type === 'submit' || type === 'button' || type === 'reset' || type === 'image'){return null;}
    var field = document.createElement('div');
    field.className = 'native-field';
    var label = document.createElement('label');
    label.textContent = labelFor(source, doc);
    field.appendChild(label);
    var proxy;
    if(source.tagName === 'SELECT'){
      proxy = document.createElement('select');
      Array.prototype.forEach.call(source.options, function(option){
        var copy = document.createElement('option');
        copy.value = option.value;
        copy.textContent = clean(option.textContent) || option.value;
        copy.selected = option.selected;
        proxy.appendChild(copy);
      });
      proxy.multiple = source.multiple;
    }else if(source.tagName === 'TEXTAREA'){
      proxy = document.createElement('textarea');
      proxy.value = source.value;
      field.classList.add('full');
    }else if(type === 'checkbox' || type === 'radio'){
      var row = document.createElement('div');
      row.className = 'choice-row';
      proxy = document.createElement('input');
      proxy.type = type;
      proxy.checked = source.checked;
      proxy.value = source.value;
      row.appendChild(proxy);
      var state = document.createElement('span');
      state.textContent = source.checked ? 'Etkin' : 'Devre dışı';
      proxy.addEventListener('change', function(){state.textContent = proxy.checked ? 'Etkin' : 'Devre dışı';});
      row.appendChild(state);
      field.appendChild(row);
      proxy.disabled = source.disabled;
      controlLinks.push({source: source, proxy: proxy});
      return field;
    }else{
      proxy = document.createElement('input');
      proxy.type = type === 'password' ? 'password' : (type === 'number' ? 'number' : (type === 'file' ? 'file' : 'text'));
      if(type !== 'file'){proxy.value = source.value || '';}
      if(source.maxLength > 0){proxy.maxLength = source.maxLength;}
      if(source.placeholder){proxy.placeholder = source.placeholder;}
    }
    proxy.disabled = source.disabled;
    controlLinks.push({source: source, proxy: proxy});
    field.appendChild(proxy);
    return field;
  }

  function syncControls(){
    controlLinks.forEach(function(link){
      var source = link.source;
      var proxy = link.proxy;
      var type = (source.type || '').toLowerCase();
      if(type === 'checkbox' || type === 'radio'){
        source.checked = proxy.checked;
      }else if(source.tagName === 'SELECT'){
        Array.prototype.forEach.call(source.options, function(option, index){option.selected = proxy.options[index] ? proxy.options[index].selected : false;});
      }else if(type === 'file'){
        if(proxy.files && proxy.files.length){
          try{var transfer = new DataTransfer();Array.prototype.forEach.call(proxy.files, function(file){transfer.items.add(file);});source.files = transfer.files;}catch(error){throw new Error('Dosya alanı tarayıcı tarafından aktarılamadı.');}
        }
      }else{source.value = proxy.value;}
      try{source.dispatchEvent(new Event('change', {bubbles: true}));}catch(ignore){}
    });
  }

  function actionButton(source, moduleRisk){
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'native-action';
    var label = clean(source.value || source.textContent || source.title || 'Uygula');
    button.textContent = label;
    if(/sil|delete|reset|reboot|yeniden|fabrika/i.test(label)){button.classList.add('danger');}
    if(/cancel|iptal|geri/i.test(label)){button.classList.add('secondary');}
    button.addEventListener('click', function(){
      if((moduleRisk === 'critical' || button.classList.contains('danger')) && !window.confirm(label + ' işlemi gerçek modeme uygulanacak. Devam edilsin mi?')){return;}
      try{
        syncControls();
        setStatus('İşlem modeme gönderiliyor…');
        source.click();
        window.setTimeout(function(){if(bridge.contentDocument && bridge.contentDocument.readyState === 'complete'){renderBridge();}}, 1200);
      }catch(error){setStatus('Bu işlem stok JavaScript bağımlılığı nedeniyle çalıştırılamadı: ' + error.message, 'error');}
    });
    return button;
  }

  function renderTable(source){
    var wrap = document.createElement('div');
    wrap.className = 'native-table-wrap';
    var table = document.createElement('table');
    table.className = 'native-table';
    Array.prototype.forEach.call(source.querySelectorAll('tr'), function(row){
      var outRow = document.createElement('tr');
      Array.prototype.forEach.call(row.children, function(cell){
        if(cell.tagName !== 'TD' && cell.tagName !== 'TH'){return;}
        var outCell = document.createElement(cell.tagName.toLowerCase());
        outCell.textContent = clean(cell.textContent);
        outRow.appendChild(outCell);
      });
      if(outRow.children.length){table.appendChild(outRow);}
    });
    wrap.appendChild(table);
    return wrap;
  }

  function renderForm(form, doc, index){
    var card = document.createElement('section');
    card.className = 'native-card';
    var heading = document.createElement('h2');
    var legend = form.querySelector('legend,h1,h2,h3,.title,.step-title');
    heading.textContent = legend && clean(legend.textContent) ? clean(legend.textContent) : ('Ayar Grubu ' + (index + 1));
    card.appendChild(heading);
    var grid = document.createElement('div');
    grid.className = 'native-grid';
    Array.prototype.forEach.call(form.elements, function(control){
      var field = proxyControl(control, doc);
      if(field){grid.appendChild(field);}
    });
    card.appendChild(grid);
    var actions = document.createElement('div');
    actions.className = 'native-actions';
    var buttons = form.querySelectorAll('button,input[type=submit],input[type=button],input[type=reset],input[type=image]');
    Array.prototype.forEach.call(buttons, function(source){
      if(source.offsetParent === null && source.type !== 'hidden'){return;}
      actions.appendChild(actionButton(source, activeModule ? activeModule.risk : 'normal'));
    });
    if(!buttons.length){
      var submit = document.createElement('button');
      submit.type = 'button';submit.className = 'native-action';submit.textContent = 'Kaydet';
      submit.addEventListener('click', function(){try{syncControls();form.requestSubmit ? form.requestSubmit() : form.submit();setStatus('Ayarlar modeme gönderildi.', 'success');}catch(error){setStatus(error.message, 'error');}});
      actions.appendChild(submit);
    }
    card.appendChild(actions);
    return card;
  }

  function sourceDocument(){
    var outer = bridge.contentDocument || bridge.contentWindow.document;
    if(!outer || !outer.body){return null;}
    var inner = outer.querySelector('iframe#mainFrame,iframe[name="mainFrame"]');
    if(inner){
      try{
        var innerDoc = inner.contentDocument || inner.contentWindow.document;
        if(innerDoc && innerDoc.body && innerDoc.readyState !== 'loading'){
          if(!inner.dataset.cayaBound){
            inner.dataset.cayaBound = '1';
            inner.addEventListener('load', function(){window.setTimeout(renderBridge, 180);});
          }
          return innerDoc;
        }
      }catch(ignore){return null;}
    }
    return outer;
  }

  function waitForBridge(token, attempt){
    if(token !== bridgePollToken){return;}
    var doc = null;
    try{doc = sourceDocument();}catch(ignore){}
    if(doc && doc.body && clean(doc.body.textContent)){
      renderBridge();
      return;
    }
    if(attempt >= 30){setStatus('Modem sayfası zamanında yüklenmedi.', 'error');return;}
    window.setTimeout(function(){waitForBridge(token, attempt + 1);}, 180);
  }

  function renderBridge(){
    var doc;
    try{doc = sourceDocument();}catch(error){setStatus('Modem sayfasına erişilemedi: ' + error.message, 'error');return;}
    if(!doc || !doc.body){setStatus('Modem yanıtı boş.', 'error');return;}
    var bodyText = clean(doc.body.textContent);
    if(/login-page\.cgi|login\/login\.html/.test(doc.documentElement.innerHTML) || /kullanıcı adı.*parola/i.test(bodyText)){
      window.top.location.href = '/login/login.html';
      return;
    }
    panel.innerHTML = '';
    controlLinks = [];
    var forms = Array.prototype.slice.call(doc.forms || []);
    forms.forEach(function(form, index){panel.appendChild(renderForm(form, doc, index));});
    var tables = Array.prototype.slice.call(doc.querySelectorAll('table')).filter(function(table){return table.querySelectorAll('tr').length > 1 && !table.closest('form');});
    tables.slice(0, 12).forEach(function(table){
      var card = document.createElement('section');card.className = 'native-card';card.appendChild(renderTable(table));panel.appendChild(card);
    });
    if(!forms.length && !tables.length){
      var info = document.createElement('section');info.className = 'native-card';
      var text = document.createElement('div');text.className = 'native-info';text.textContent = bodyText || 'Bu modül görüntülenebilir veri döndürmedi.';info.appendChild(text);panel.appendChild(info);
    }
    setStatus(forms.length + ' ayar formu ve ' + tables.length + ' bilgi tablosu canlı cihazdan yüklendi.', 'success');
  }

  bridge.addEventListener('load', function(){
    var token = bridgePollToken;
    window.setTimeout(function(){waitForBridge(token, 0);}, 120);
  });

  function buttonFor(module){
    var button = document.createElement('button');button.type = 'button';button.className = 'nav-button';button.dataset.moduleId = module.id;button.textContent = module.title;button.addEventListener('click', function(){openModule(module);});return button;
  }
  function buildNavigation(){
    nav.innerHTML = '';nav.appendChild(buttonFor(overview));var groups = {};
    modules.forEach(function(module){var category = module.category || 'Diğer';(groups[category] || (groups[category] = [])).push(module);});
    Object.keys(groups).sort().forEach(function(category){var heading = document.createElement('div');heading.className = 'nav-section';heading.textContent = category;nav.appendChild(heading);groups[category].forEach(function(module){nav.appendChild(buttonFor(module));});});
  }
  function filterNavigation(query){
    var normalized = str(query).trim().toLocaleLowerCase('tr');
    Array.prototype.forEach.call(nav.querySelectorAll('.nav-button'), function(button){
      var matches = !normalized || button.textContent.toLocaleLowerCase('tr').indexOf(normalized) >= 0;
      button.hidden = !matches;
    });
    Array.prototype.forEach.call(nav.querySelectorAll('.nav-section'), function(section){
      var visible = false;
      var sibling = section.nextElementSibling;
      while(sibling && !sibling.classList.contains('nav-section')){
        if(sibling.classList.contains('nav-button') && !sibling.hidden){visible = true;break;}
        sibling = sibling.nextElementSibling;
      }
      section.hidden = !visible;
    });
    if(tabs.parentElement === nav){
      var activeButton = nav.querySelector('.nav-button.active');
      tabs.hidden = Boolean(normalized && (!activeButton || activeButton.hidden));
    }
  }

  search.addEventListener('input', function(){filterNavigation(search.value);});
  document.getElementById('reloadButton').addEventListener('click', function(){if(activePage){openPage(activePage, activePageIndex);}});
  document.getElementById('logoutButton').addEventListener('click', function(){window.top.location.href = '/login/logout.cgi';});

  buildNavigation();
  var requested = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
  openModule(requested === overview.id ? overview : (modules.find(function(module){return module.id === requested;}) || overview));
})();

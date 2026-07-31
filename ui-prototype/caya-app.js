(function(){
  'use strict';

  var modules = Array.isArray(window.CAYA_LIVE_MODULES) ? window.CAYA_LIVE_MODULES : [];
  var frame = document.getElementById('moduleFrame');
  var title = document.getElementById('viewerTitle');
  var pathLabel = document.getElementById('viewerPath');
  var pageTitle = document.getElementById('pageTitle');
  var nav = document.getElementById('mainNav');
  var catalog = document.getElementById('moduleCatalog');
  var viewer = document.getElementById('viewer');
  var search = document.getElementById('moduleSearch');

  var overview = {
    id: 'overview',
    title: 'Genel Bak\u0131\u015f',
    category: 'Durum',
    route: '/pages/connectionStatus/naviView_partialLoad.html',
    pages: [{label:'Durum'}],
    risk: 'normal'
  };

  function text(value){return String(value == null ? '' : value);}

  function openModule(module){
    if(!module){return;}
    if(module.risk === 'critical'){
      var approved = window.confirm('Bu b\u00f6l\u00fcm kritik bak\u0131m i\u015flemleri i\u00e7erir. Devam edilsin mi?');
      if(!approved){return;}
    }
    pageTitle.textContent = text(module.title);
    title.textContent = text(module.title);
    pathLabel.textContent = text(module.route);
    frame.src = module.route;
    viewer.hidden = false;
    catalog.hidden = true;
    Array.prototype.forEach.call(nav.querySelectorAll('.nav-button'), function(button){
      button.classList.toggle('active', button.getAttribute('data-module-id') === module.id);
    });
    window.location.hash = encodeURIComponent(module.id);
  }

  function buttonFor(module){
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'nav-button';
    button.setAttribute('data-module-id', module.id);
    button.textContent = module.title;
    button.addEventListener('click', function(){openModule(module);});
    return button;
  }

  function buildNavigation(){
    nav.innerHTML = '';
    nav.appendChild(buttonFor(overview));
    var groups = {};
    modules.forEach(function(module){
      var category = module.category || 'Di\u011fer';
      if(!groups[category]){groups[category] = [];}
      groups[category].push(module);
    });
    Object.keys(groups).sort().forEach(function(category){
      var heading = document.createElement('div');
      heading.className = 'nav-section';
      heading.textContent = category;
      nav.appendChild(heading);
      groups[category].forEach(function(module){nav.appendChild(buttonFor(module));});
    });
  }

  function buildCatalog(query){
    var normalized = text(query).toLocaleLowerCase('tr');
    var visible = modules.filter(function(module){
      return !normalized || text(module.title).toLocaleLowerCase('tr').indexOf(normalized) >= 0 || text(module.category).toLocaleLowerCase('tr').indexOf(normalized) >= 0;
    });
    var groups = {};
    visible.forEach(function(module){
      var category = module.category || 'Di\u011fer';
      if(!groups[category]){groups[category] = [];}
      groups[category].push(module);
    });
    catalog.innerHTML = '';
    if(!visible.length){
      var empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = 'E\u015fle\u015fen modem mod\u00fcl\u00fc bulunamad\u0131.';
      catalog.appendChild(empty);
      return;
    }
    Object.keys(groups).sort().forEach(function(category){
      var section = document.createElement('section');
      section.className = 'catalog-group';
      var heading = document.createElement('h2');
      heading.textContent = category;
      section.appendChild(heading);
      var grid = document.createElement('div');
      grid.className = 'module-grid';
      groups[category].forEach(function(module){
        var card = document.createElement('button');
        card.type = 'button';
        card.className = 'module-card';
        var strong = document.createElement('strong');
        strong.textContent = module.title;
        var small = document.createElement('small');
        small.textContent = String((module.pages || []).length) + ' ger\u00e7ek stok sayfas\u0131';
        card.appendChild(strong);
        card.appendChild(small);
        card.addEventListener('click', function(){openModule(module);});
        grid.appendChild(card);
      });
      section.appendChild(grid);
      catalog.appendChild(section);
    });
  }

  search.addEventListener('input', function(){
    var hasQuery = search.value.trim().length > 0;
    catalog.hidden = !hasQuery;
    viewer.hidden = hasQuery;
    if(hasQuery){buildCatalog(search.value); pageTitle.textContent = 'Mod\u00fcl Arama';}
  });

  document.getElementById('reloadButton').addEventListener('click', function(){
    var current = frame.getAttribute('src') || overview.route;
    var clean = current.replace(/([?&])_cayaReload=\d+/, '$1').replace(/[?&]$/, '');
    frame.src = clean + (clean.indexOf('?') >= 0 ? '&' : '?') + '_cayaReload=' + Date.now();
  });

  document.getElementById('logoutButton').addEventListener('click', function(){
    window.top.location.href = '/login/logout.cgi';
  });

  buildNavigation();
  buildCatalog('');
  var requested = decodeURIComponent((window.location.hash || '').replace(/^#/, ''));
  var initial = requested === overview.id ? overview : modules.find(function(module){return module.id === requested;});
  openModule(initial || overview);
})();

const icons = {
  dashboard: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>',
  globe: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 4 6 4 9s-1 6-4 9c-3-3-4-6-4-9s1-6 4-9Z"/></svg>',
  wifi: '<svg viewBox="0 0 24 24"><path d="M3 9a14 14 0 0 1 18 0M6 13a9 9 0 0 1 12 0M9.5 17a4 4 0 0 1 5 0"/><path d="M12 21h.01"/></svg>',
  devices: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="13" height="10" rx="2"/><path d="M7 20h10M10 14v6"/><rect x="17" y="8" width="4" height="9" rx="1"/></svg>',
  shield: '<svg viewBox="0 0 24 24"><path d="M12 3 4.5 6v5.5c0 4.7 3 7.8 7.5 9.5 4.5-1.7 7.5-4.8 7.5-9.5V6L12 3Z"/><path d="m9 12 2 2 4-4"/></svg>',
  settings: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3A1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z"/></svg>',
  menu: '<svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/></svg>',
  sun: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
  flask: '<svg viewBox="0 0 24 24"><path d="M9 3h6M10 3v6l-5 8.5A2.3 2.3 0 0 0 7 21h10a2.3 2.3 0 0 0 2-3.5L14 9V3"/><path d="M8 14h8"/></svg>',
  refresh: '<svg viewBox="0 0 24 24"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.6-2L20 8M4 16l2.3 2A7 7 0 0 0 18 16"/></svg>',
  download: '<svg viewBox="0 0 24 24"><path d="M12 3v13M7 11l5 5 5-5M5 21h14"/></svg>',
  upload: '<svg viewBox="0 0 24 24"><path d="M12 21V8M7 13l5-5 5 5M5 3h14"/></svg>',
  router: '<svg viewBox="0 0 24 24"><rect x="3" y="9" width="18" height="9" rx="3"/><path d="M7 13h.01M11 13h.01M17 13h.01M12 9V5M9 5a4 4 0 0 1 6 0"/></svg>',
  laptop: '<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="11" rx="2"/><path d="M2 20h20"/></svg>',
  phone: '<svg viewBox="0 0 24 24"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg>',
  tv: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="13" rx="2"/><path d="M8 22h8M12 18v4"/></svg>',
  users: '<svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/></svg>',
  lock: '<svg viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>',
  alert: '<svg viewBox="0 0 24 24"><path d="M10.3 3.7 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0Z"/><path d="M12 9v4M12 17h.01"/></svg>',
  backup: '<svg viewBox="0 0 24 24"><path d="M4 5h13l3 3v11H4Z"/><path d="M8 5v5h8V5M8 19v-5h8v5"/></svg>',
  update: '<svg viewBox="0 0 24 24"><path d="M12 3v12M8 7l4-4 4 4M5 21h14"/></svg>'
};

document.querySelectorAll('[data-icon]').forEach((node) => {
  const name = node.dataset.icon;
  if (icons[name]) node.innerHTML = icons[name];
});

const devices = [
  { name: 'CaYa-PC', type: 'laptop', connection: 'ethernet', ip: '192.168.1.2', activity: '18.4 Mbps', detail: 'Kablolu • LAN4' },
  { name: 'Cagan-iPhone', type: 'phone', connection: 'wifi', ip: '192.168.1.34', activity: '2.1 Mbps', detail: 'Wi‑Fi • Güçlü sinyal' },
  { name: 'Salon-TV', type: 'tv', connection: 'wifi', ip: '192.168.1.45', activity: '8.7 Mbps', detail: 'Wi‑Fi • Orta sinyal' },
  { name: 'Tablet', type: 'phone', connection: 'wifi', ip: '192.168.1.51', activity: '640 Kbps', detail: 'Wi‑Fi • Güçlü sinyal' },
  { name: 'Dizüstü', type: 'laptop', connection: 'wifi', ip: '192.168.1.62', activity: '1.3 Mbps', detail: 'Wi‑Fi • İyi sinyal' },
  { name: 'Akıllı-Priz', type: 'devices', connection: 'wifi', ip: '192.168.1.73', activity: '12 Kbps', detail: 'Wi‑Fi • Düşük trafik' }
];

const pageTitle = document.getElementById('pageTitle');
const pageEyebrow = document.getElementById('pageEyebrow');
const sidebar = document.getElementById('sidebar');
const toast = document.getElementById('toast');
let toastTimer;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

function openPage(pageName) {
  document.querySelectorAll('.page').forEach((page) => page.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.page === pageName));
  const target = document.getElementById(`page-${pageName}`);
  if (!target) return;
  target.classList.add('active');
  pageTitle.textContent = target.dataset.title;
  pageEyebrow.textContent = target.dataset.eyebrow;
  sidebar.classList.remove('open');
  history.replaceState(null, '', `#${pageName}`);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('[data-page], [data-page-link]').forEach((button) => {
  button.addEventListener('click', () => openPage(button.dataset.page || button.dataset.pageLink));
});

document.getElementById('menuButton').addEventListener('click', () => sidebar.classList.toggle('open'));

document.addEventListener('click', (event) => {
  if (window.innerWidth <= 820 && sidebar.classList.contains('open') && !sidebar.contains(event.target) && !event.target.closest('#menuButton')) {
    sidebar.classList.remove('open');
  }
});

const themeButton = document.getElementById('themeButton');
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('caya-theme', theme);
  themeButton.innerHTML = icons[theme === 'dark' ? 'sun' : 'moon'];
}
setTheme(localStorage.getItem('caya-theme') || 'light');
themeButton.addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));

document.getElementById('dismissBanner').addEventListener('click', (event) => event.currentTarget.closest('.demo-banner').remove());
document.getElementById('refreshOverview').addEventListener('click', (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.innerHTML = `${icons.refresh} Yenileniyor…`;
  setTimeout(() => {
    button.disabled = false;
    button.innerHTML = `${icons.refresh} Yenile`;
    showToast('Örnek ağ verileri yenilendi.');
  }, 900);
});

document.querySelectorAll('.demo-action, .switch input').forEach((element) => {
  element.addEventListener('click', (event) => {
    if (element.matches('.switch input')) {
      event.preventDefault();
      element.checked = !element.checked;
    }
    showToast('Prototip modunda ayar değişikliği yapılmaz.');
  });
});

function iconFor(type) {
  return icons[type] || icons.devices;
}

function renderOverviewDevices() {
  const target = document.getElementById('overviewDeviceList');
  target.innerHTML = devices.slice(0, 3).map((device) => `
    <div class="device-card">
      <span class="device-icon">${iconFor(device.type)}</span>
      <div><strong>${device.name}</strong><small>${device.detail}</small></div>
      <span class="device-activity">${device.activity}</span>
    </div>
  `).join('');
}

function renderDeviceTable() {
  const search = document.getElementById('deviceSearch').value.trim().toLocaleLowerCase('tr');
  const filter = document.getElementById('deviceFilter').value;
  const filtered = devices.filter((device) => {
    const matchesSearch = `${device.name} ${device.ip}`.toLocaleLowerCase('tr').includes(search);
    const matchesFilter = filter === 'all' || device.connection === filter;
    return matchesSearch && matchesFilter;
  });
  document.getElementById('deviceTableBody').innerHTML = filtered.map((device) => `
    <tr>
      <td><div class="table-device"><span>${iconFor(device.type)}</span><div><strong>${device.name}</strong><small>${device.detail}</small></div></div></td>
      <td>${device.connection === 'wifi' ? 'Wi‑Fi' : 'Ethernet'}</td>
      <td>${device.ip}</td>
      <td>${device.activity}</td>
      <td><button class="table-action" data-device="${device.name}">Ayrıntı</button></td>
    </tr>
  `).join('') || '<tr><td colspan="5">Eşleşen cihaz bulunamadı.</td></tr>';
  document.querySelectorAll('.table-action').forEach((button) => button.addEventListener('click', () => showToast(`${button.dataset.device} ayrıntıları demo modunda.`)));
}

document.getElementById('deviceSearch').addEventListener('input', renderDeviceTable);
document.getElementById('deviceFilter').addEventListener('change', renderDeviceTable);
renderOverviewDevices();
renderDeviceTable();

const initialPage = location.hash.replace('#', '');
if (initialPage && document.getElementById(`page-${initialPage}`)) openPage(initialPage);

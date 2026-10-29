const API_BASE = 'http://127.0.0.1:5002';

// 1. Auth & Token Management
const token = localStorage.getItem('factify_token');
const user = JSON.parse(localStorage.getItem('factify_user'));

if (!token || !user || user.role !== 'admin') {
  window.location.href = '/?error=unauthorized';
}

// Logout
document.getElementById('btn-logout').addEventListener('click', () => {
  localStorage.removeItem('factify_token');
  localStorage.removeItem('factify_user');
  window.location.href = '/';
});

// 2. Theme Toggle (Matches homepage logic)
const themeToggleBtn = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('factify_theme') || 'dark';
document.documentElement.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

themeToggleBtn.addEventListener('click', () => {
  let theme = document.documentElement.getAttribute('data-theme');
  if (theme === 'dark') {
    theme = 'light';
  } else {
    theme = 'dark';
  }
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('factify_theme', theme);
  updateThemeIcon(theme);
  updateChartsTheme();
});

function updateThemeIcon(theme) {
  const icon = themeToggleBtn.querySelector('.theme-icon');
  icon.textContent = theme === 'dark' ? '🌙' : '☀️';
}

// 3. Sidebar Navigation & Mobile Toggle
const sidebarLinks = document.querySelectorAll('.sidebar-link');
const sections = document.querySelectorAll('.admin-section-content');
const topbarTitle = document.getElementById('topbar-title');
const sidebar = document.getElementById('admin-sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebarClose = document.getElementById('sidebar-close');

const sectionTitles = {
  'dashboard': window.t('admin_title'),
  'users': window.t('user_mgmt'),
  'analyses': window.t('news_mgmt'),
  'feedbacks': window.t('sec_reviews_title'),
  'contacts': window.t('sec_contact_title'),
  'settings': window.t('sys_settings')
};

sidebarLinks.forEach(link => {
  link.addEventListener('click', () => {
    sidebarLinks.forEach(l => l.classList.remove('active'));
    link.classList.add('active');

    const target = link.getAttribute('data-target');
    sections.forEach(sec => sec.classList.remove('active'));
    document.getElementById(`sec-${target}`).classList.add('active');
    
    topbarTitle.textContent = sectionTitles[target];

    // On mobile, close sidebar after clicking
    if (window.innerWidth <= 768) {
      sidebar.classList.remove('active');
    }
    
    // Load specific data if needed
    if(target === 'users') loadUsers();
    else if(target === 'analyses') loadAnalyses();
    else if(target === 'feedbacks') loadFeedbacks();
    else if(target === 'contacts') loadContacts();
  });
});

sidebarToggle.addEventListener('click', () => {
  sidebar.classList.add('active');
});
sidebarClose.addEventListener('click', () => {
  sidebar.classList.remove('active');
});

// 4. Data Fetching & UI Population
let activityChartInstance = null;
let predictionChartInstance = null;

async function loadDashboard() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      document.getElementById('stat-users').textContent = data.users;
      document.getElementById('stat-analyses').textContent = data.analyses;
      document.getElementById('stat-feedbacks').textContent = data.feedbacks;
      document.getElementById('stat-contacts').textContent = data.contacts;
      
      initCharts(data);
    }
  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
  }
}

// Fetch tables (similar to original script.js but cleaner)
async function loadUsers() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/users`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (res.ok) {
      const users = await res.json();
      const tbody = document.getElementById('tbody-users');
      tbody.innerHTML = users.map(u => `
        <tr>
          <td>${u.name}</td>
          <td>${u.email}</td>
          <td><span class="badge ${u.role === 'admin' ? 'badge-admin' : 'badge-user'}">${u.role}</span></td>
          <td>${new Date(u.created_at).toLocaleDateString()}</td>
          <td>
            ${u.role !== 'admin' ? `<button class="action-btn" onclick="deleteRecord('user', '${u._id}')">Delete</button>` : 'Admin'}
          </td>
        </tr>
      `).join('');
    }
  } catch (e) { console.error(e); }
}

async function loadAnalyses() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/analyses`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (res.ok) {
      const analyses = await res.json();
      const tbody = document.getElementById('tbody-analyses');
      tbody.innerHTML = analyses.map(a => `
        <tr>
          <td>${a.user_id || 'Anonymous'}</td>
          <td>${a.type}</td>
          <td><div style="max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${a.input}">${a.input}</div></td>
          <td><span class="badge ${a.prediction === 'FAKE' ? 'badge-fake' : 'badge-real'}">${a.prediction}</span></td>
          <td>${a.confidence}%</td>
          <td>${new Date(a.created_at).toLocaleDateString()}</td>
        </tr>
      `).join('');
    }
  } catch (e) { console.error(e); }
}

async function loadFeedbacks() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/feedbacks`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (res.ok) {
      const fb = await res.json();
      const tbody = document.getElementById('tbody-feedbacks');
      tbody.innerHTML = fb.map(f => `
        <tr>
          <td>${f.name} <br><small style="color:var(--text-dim)">${f.email}</small></td>
          <td>${f.subject}</td>
          <td>${'⭐'.repeat(f.rating)}</td>
          <td>${new Date(f.created_at).toLocaleDateString()}</td>
          <td><button class="action-btn" onclick="deleteRecord('feedback', '${f._id}')">Delete</button></td>
        </tr>
      `).join('');
    }
  } catch (e) { console.error(e); }
}

async function loadContacts() {
  try {
    const res = await fetch(`${API_BASE}/api/admin/contacts`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (res.ok) {
      const contacts = await res.json();
      const tbody = document.getElementById('tbody-contacts');
      tbody.innerHTML = contacts.map(c => `
        <tr>
          <td>${c.name}</td>
          <td>${c.email}</td>
          <td>${c.subject}</td>
          <td><div style="max-width:250px; overflow:hidden; text-overflow:ellipsis;">${c.message}</div></td>
          <td>${new Date(c.created_at).toLocaleDateString()}</td>
          <td><button class="action-btn" onclick="deleteRecord('contact', '${c._id}')">Delete</button></td>
        </tr>
      `).join('');
    }
  } catch (e) { console.error(e); }
}

window.deleteRecord = async function(type, id) {
  if(!confirm(`Are you sure you want to delete this ${type}?`)) return;
  try {
    const res = await fetch(`${API_BASE}/api/admin/${type}/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if(res.ok) {
      if(type === 'user') loadUsers();
      if(type === 'feedback') loadFeedbacks();
      if(type === 'contact') loadContacts();
      loadDashboard();
    } else {
      alert("Failed to delete record.");
    }
  } catch (e) {
    console.error(e);
  }
}

// 5. Chart.js Initialization
function initCharts(data) {
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const textColor = isDark ? '#E6F1FF' : '#1a202c';
  const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';

  // Chart defaults for theme
  Chart.defaults.color = textColor;
  Chart.defaults.font.family = "'Inter', sans-serif";

  // Mocking last 7 days activity based on total data for visual effect
  // In a real scenario, the backend would supply daily breakdown
  const ctxActivity = document.getElementById('activityChart').getContext('2d');
  if (activityChartInstance) activityChartInstance.destroy();
  
  activityChartInstance = new Chart(ctxActivity, {
    type: 'line',
    data: {
      labels: ['6 Days Ago', '5 Days Ago', '4 Days Ago', '3 Days Ago', '2 Days Ago', 'Yesterday', 'Today'],
      datasets: [{
        label: 'Analyses Processed',
        data: [12, 19, 15, 25, 22, 30, data.analyses > 30 ? data.analyses : 45],
        borderColor: '#00F5FF',
        backgroundColor: 'rgba(0,245,255,0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, grid: { color: gridColor } },
        x: { grid: { display: false } }
      }
    }
  });

  const ctxPrediction = document.getElementById('predictionChart').getContext('2d');
  if (predictionChartInstance) predictionChartInstance.destroy();

  // Assuming an arbitrary split for the visual doughnut chart (Backend /stats currently doesn't split FAKE vs REAL)
  predictionChartInstance = new Chart(ctxPrediction, {
    type: 'doughnut',
    data: {
      labels: ['FAKE', 'REAL'],
      datasets: [{
        data: [data.analyses * 0.6 || 60, data.analyses * 0.4 || 40], // Mock split
        backgroundColor: ['#FF3D71', '#00FF88'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

function updateChartsTheme() {
  if (activityChartInstance && predictionChartInstance) {
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    const textColor = isDark ? '#E6F1FF' : '#1a202c';
    const gridColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)';
    
    Chart.defaults.color = textColor;
    
    activityChartInstance.options.scales.y.grid.color = gridColor;
    activityChartInstance.update();
    predictionChartInstance.update();
  }
}

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
});


window.addEventListener('languageChanged', () => {
  const activeLink = document.querySelector('.sidebar-link.active');
  if (activeLink) {
    const target = activeLink.getAttribute('data-target');
    const updatedTitles = {
      'dashboard': window.t('admin_title'),
      'users': window.t('user_mgmt'),
      'analyses': window.t('news_mgmt'),
      'feedbacks': window.t('sec_reviews_title'),
      'contacts': window.t('sec_contact_title'),
      'settings': window.t('sys_settings')
    };
    document.getElementById('topbar-title').textContent = updatedTitles[target];
  }
  
  if (activityChartInstance) {
    activityChartInstance.data.datasets[0].label = window.t('admin_stat_api');
    activityChartInstance.update();
  }
});

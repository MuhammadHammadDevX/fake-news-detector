// ============================================
// Factify - Main JavaScript
// Now with user authentication, feedback page, text check, and admin controls!
// ============================================
const API_BASE = (window.location.protocol === 'file:' || window.location.port !== '5002') ? 'http://127.0.0.1:5002' : '';

// ===== BACKGROUND PARTICLES =====
(function initParticles() {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * canvas.width, y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 0.5, o: Math.random() * 0.5 + 0.1
    });
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach((p, i) => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(0,245,255,${p.o})`; ctx.fill();
      for (let j = i + 1; j < particles.length; j++) {
        const dx = p.x - particles[j].x, dy = p.y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(0,245,255,${0.08 * (1 - dist / 120)})`; ctx.stroke();
        }
      }
    });
    requestAnimationFrame(draw);
  }
  draw();
})();

// ===== TYPING ANIMATION =====
(function initTyping() {
  const wordKeys = ['typed_detector', 'typed_analyzer', 'typed_shield', 'typed_guardian'];
  const el = document.getElementById('typed-text');
  if (!el) return;
  let wi = 0, ci = 0, deleting = false;
  function type() {
    const word = window.t(wordKeys[wi]);
    if (!deleting) {
      el.textContent = word.substring(0, ci + 1); ci++;
      if (ci === word.length) { deleting = true; setTimeout(type, 2000); return; }
    } else {
      el.textContent = word.substring(0, ci - 1); ci--;
      if (ci === 0) { deleting = false; wi = (wi + 1) % wordKeys.length; }
    }
    setTimeout(type, deleting ? 50 : 120);
  }
  type();
})();

// ===== STATS COUNTER =====
(function initCounters() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.querySelectorAll('.stat-number').forEach(el => {
          const target = parseInt(el.dataset.target);
          let current = 0;
          const step = Math.ceil(target / 60);
          const timer = setInterval(() => {
            current += step;
            if (current >= target) { current = target; clearInterval(timer); }
            el.textContent = current.toLocaleString();
          }, 30);
        });
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.5 });
  const stats = document.querySelector('.hero-stats');
  if (stats) observer.observe(stats);
})();

// ===== NAVBAR & THEME =====
const hamburger = document.getElementById('hamburger');
const navLinks = document.querySelector('.nav-links');
if (hamburger) {
  hamburger.addEventListener('click', () => navLinks.classList.toggle('open'));
}
document.querySelectorAll('.nav-link').forEach(l => {
  l.addEventListener('click', () => {
    if (navLinks) navLinks.classList.remove('open');
  });
});

window.addEventListener('scroll', () => {
  const sections = document.querySelectorAll('section[id]');
  let current = '';
  sections.forEach(s => { if (window.scrollY >= s.offsetTop - 200) current = s.id; });
  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.getAttribute('href') === `#${current}`);
  });
});

const themeBtn = document.getElementById('theme-toggle');
if (themeBtn) {
  themeBtn.addEventListener('click', () => {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    document.documentElement.setAttribute('data-theme', isLight ? 'dark' : 'light');
    themeBtn.querySelector('.theme-icon').textContent = isLight ? '🌙' : '☀️';
  });
}

// ===== TOAST NOTIFICATION SYSTEM =====
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ===== USER AUTHENTICATION STATE MANAGEMENT =====
function getToken() { return localStorage.getItem('factify_token'); }
function setToken(token) { localStorage.setItem('factify_token', token); }
function removeToken() { localStorage.removeItem('factify_token'); localStorage.removeItem('factify_user'); }
function getUser() {
  try {
    return JSON.parse(localStorage.getItem('factify_user'));
  } catch {
    return null;
  }
}
function setUser(user) { localStorage.setItem('factify_user', JSON.stringify(user)); }

function updateAuthUI() {
  const user = getUser();
  const token = getToken();
  const authBtns = document.getElementById('auth-buttons');
  const userMenu = document.getElementById('user-menu');
  const adminBtn = document.getElementById('btn-admin-nav');

  const isLoggedIn = !!(user && token);
  document.body.classList.toggle('logged-in', isLoggedIn);

  if (isLoggedIn) {
    if (authBtns) authBtns.style.display = 'none';
    if (userMenu) userMenu.style.display = 'block';
    const avatar = document.getElementById('user-avatar');
    if (avatar) avatar.textContent = user.name.charAt(0).toUpperCase();
    
    const uName = document.getElementById('dropdown-user-name');
    const uEmail = document.getElementById('dropdown-user-email');
    if (uName) uName.textContent = user.name;
    if (uEmail) uEmail.textContent = user.email;

    if (user.role === 'admin') {
      if (adminBtn) adminBtn.style.display = 'flex';
    } else {
      if (adminBtn) adminBtn.style.display = 'none';
    }

    // Fetch dynamic user history and global news when logged in
    renderDashboard();
    fetchNews();
  } else {
    if (authBtns) authBtns.style.display = 'flex';
    if (userMenu) userMenu.style.display = 'none';
    if (adminBtn) adminBtn.style.display = 'none';

    // Clear views for logged out state
    const dashboardSection = document.getElementById('user-dashboard');
    if (dashboardSection) dashboardSection.style.display = 'none';
    const grid = document.getElementById('news-grid');
    if (grid) grid.innerHTML = '';
    const resultsSection = document.getElementById('results-section');
    if (resultsSection) resultsSection.style.display = 'none';
  }
}

// Modal Toggle Logic
const loginModal = document.getElementById('login-modal');
const signupModal = document.getElementById('signup-modal');
const loginBtnNav = document.getElementById('btn-login-nav');
const signupBtnNav = document.getElementById('btn-signup-nav');
const loginClose = document.getElementById('login-modal-close');
const signupClose = document.getElementById('signup-modal-close');
const switchToSignup = document.getElementById('switch-to-signup');
const switchToLogin = document.getElementById('switch-to-login');

if (loginBtnNav) loginBtnNav.addEventListener('click', () => { loginModal.style.display = 'flex'; });
if (signupBtnNav) signupBtnNav.addEventListener('click', () => { signupModal.style.display = 'flex'; });
if (loginClose) loginClose.addEventListener('click', () => { loginModal.style.display = 'none'; });
if (signupClose) signupClose.addEventListener('click', () => { signupModal.style.display = 'none'; });

if (switchToSignup) switchToSignup.addEventListener('click', (e) => {
  e.preventDefault();
  loginModal.style.display = 'none';
  signupModal.style.display = 'flex';
});
if (switchToLogin) switchToLogin.addEventListener('click', (e) => {
  e.preventDefault();
  signupModal.style.display = 'none';
  loginModal.style.display = 'flex';
});

// Click outside modal to close
window.addEventListener('click', (e) => {
  if (e.target === loginModal) loginModal.style.display = 'none';
  if (e.target === signupModal) signupModal.style.display = 'none';
});

// Lock overlay button action listeners
document.querySelectorAll('.btn-lock-login').forEach(btn => {
  btn.addEventListener('click', () => { if (loginModal) loginModal.style.display = 'flex'; });
});
document.querySelectorAll('.btn-lock-signup').forEach(btn => {
  btn.addEventListener('click', () => { if (signupModal) signupModal.style.display = 'flex'; });
});

// Dropdown Toggle
const userAvatar = document.getElementById('user-avatar');
const userDropdown = document.getElementById('user-dropdown');
if (userAvatar) {
  userAvatar.addEventListener('click', (e) => {
    e.stopPropagation();
    userDropdown.style.display = userDropdown.style.display === 'none' ? 'block' : 'none';
  });
}
document.addEventListener('click', () => {
  if (userDropdown) userDropdown.style.display = 'none';
});

// Dashboard Nav Hook
const btnDashboardNav = document.getElementById('btn-user-dashboard-nav');
if (btnDashboardNav) {
  btnDashboardNav.addEventListener('click', () => {
    window.location.href = '/dashboard';
  });
}


// TRENDING FAKE NEWS ALERTS
async function fetchTrending() {
  const grid = document.getElementById('trending-grid');
  if (!grid) return;
  try {
    const res = await fetch(`${API_BASE}/api/trending`);
    if (res.ok) {
      const data = await res.json();
      if (data.length === 0) {
        grid.innerHTML = '<p>No trending misinformation alerts right now.</p>';
      } else {
        grid.innerHTML = data.map(t => `
          <div class="glass-card trending-card" style="padding: 1.5rem; border-left: 4px solid #ff4757; transition: transform 0.3s ease, box-shadow 0.3s ease; cursor: pointer;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <span style="background: rgba(255, 71, 87, 0.1); color: #ff4757; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">High Risk</span>
              <span style="color:var(--text-dim); font-size:0.8rem;">🚨 ${t.reports} reports</span>
            </div>
            <h4 style="margin-bottom: 15px; font-size: 1.1rem; line-height: 1.4;">${t.claim.substring(0, 80)}...</h4>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; align-items: center; border-top: 1px solid var(--glass-border); padding-top: 12px;">
              <span style="color:var(--text-dim); display:flex; align-items:center;"><span style="display:inline-block; width:8px; height:8px; background:#ff4757; border-radius:50%; margin-right:5px; animation: pulse 2s infinite;"></span>Live Status</span>
              <span style="color:#ff4757; font-weight:bold; background: rgba(255, 71, 87, 0.05); padding: 4px 8px; border-radius: 4px;">${t.confidence}% Fake Confidence</span>
            </div>
          </div>
        `).join('');
      }
    }
  } catch(e) {}
}
document.addEventListener('DOMContentLoaded', () => {
  fetchTrending();
});

// SIGNUP FORM SUBMISSION
const signupForm = document.getElementById('signup-form');
if (signupForm) {
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-signup-submit');
    const name = document.getElementById('signup-name').value.trim();
    const email = document.getElementById('signup-email').value.trim();
    const password = document.getElementById('signup-password').value;
    const confirmPassword = document.getElementById('signup-confirm-password').value;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showToast(window.t('toast_invalid_email'), 'error');
      return;
    }

    const passwordRegex = /^(?=.*[A-Z])(?=.*\d).{8,}$/;
    if (!passwordRegex.test(password)) {
      showToast(window.t('toast_pass_req'), 'error');
      return;
    }

    if (password !== confirmPassword) {
      showToast(window.t('toast_pass_mismatch'), 'error');
      return;
    }

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="display:inline-block; width:12px; height:12px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 1s linear infinite;"></span> Creating Account...';

    try {
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password })
      });
      const data = await res.ok ? await res.json() : null;
      if (res.ok && data) {
        setToken(data.token);
        setUser(data.user);
        window.location.href = '/dashboard';
      } else {
        const errData = await res.json();
        showToast(errData.error || window.t('toast_signup_failed'), 'error');
      }
    } catch (err) {
      showToast(window.t('toast_auth_err'), 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  });
}

// LOGIN FORM SUBMISSION
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-login-submit');
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner" style="display:inline-block; width:12px; height:12px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation:spin 1s linear infinite;"></span> Logging in...';

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.ok ? await res.json() : null;
      if (res.ok && data) {
        setToken(data.token);
        setUser(data.user);
        window.location.href = '/';
      } else {
        const errData = await res.json();
        showToast(errData.error || window.t('toast_invalid_cred'), 'error');
      }
    } catch (err) {
      showToast(window.t('toast_auth_err'), 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = originalText;
    }
  });
}

// PASSWORD VISIBILITY TOGGLE
document.querySelectorAll('.toggle-password').forEach(icon => {
  icon.addEventListener('click', function() {
    const input = this.previousElementSibling;
    if (input.type === 'password') {
      input.type = 'text';
      this.textContent = '🙈';
    } else {
      input.type = 'password';
      this.textContent = '👁️';
    }
  });
});

// LOGOUT ACTION
const logoutBtn = document.getElementById('btn-logout');
if (logoutBtn) {
  logoutBtn.addEventListener('click', () => {
    removeToken();
    updateAuthUI();
    document.getElementById('admin-panel').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    showToast(window.t('toast_logout'), 'info');
  });
}

// ===== ANALYZER MODE SWITCHER (URL vs TEXT vs IMAGE) =====
let analyzerMode = 'url';
const modeUrlBtn = document.getElementById('mode-url');
const modeTextBtn = document.getElementById('mode-text');
const modeImageBtn = document.getElementById('mode-image');
const urlContainer = document.getElementById('url-analysis-container');
const textContainer = document.getElementById('text-analysis-container');
const imageContainer = document.getElementById('image-analysis-container');

if (modeUrlBtn && modeTextBtn && modeImageBtn) {
  modeUrlBtn.addEventListener('click', () => {
    analyzerMode = 'url';
    modeUrlBtn.classList.add('active');
    modeTextBtn.classList.remove('active');
    modeImageBtn.classList.remove('active');
    urlContainer.style.display = 'block';
    textContainer.style.display = 'none';
    imageContainer.style.display = 'none';
  });

  modeTextBtn.addEventListener('click', () => {
    analyzerMode = 'text';
    modeTextBtn.classList.add('active');
    modeUrlBtn.classList.remove('active');
    modeImageBtn.classList.remove('active');
    urlContainer.style.display = 'none';
    textContainer.style.display = 'block';
    imageContainer.style.display = 'none';
  });

  modeImageBtn.addEventListener('click', () => {
    analyzerMode = 'image';
    modeImageBtn.classList.add('active');
    modeUrlBtn.classList.remove('active');
    modeTextBtn.classList.remove('active');
    urlContainer.style.display = 'none';
    textContainer.style.display = 'none';
    imageContainer.style.display = 'block';
  });
}

// ===== IMAGE UPLOAD LOGIC =====
let selectedImageFile = null;
const imageUploadWrapper = document.getElementById('image-upload-wrapper');
const imageInput = document.getElementById('image-input');
const imagePreview = document.getElementById('image-preview');

if (imageUploadWrapper && imageInput) {
  const imageUploadPrompt = document.getElementById('image-upload-prompt');
  const imagePreviewContainer = document.getElementById('image-preview-container');
  const btnRemoveImage = document.getElementById('btn-remove-image');

  imageUploadPrompt.addEventListener('click', () => imageInput.click());

  imageUploadWrapper.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (!selectedImageFile) imageUploadWrapper.classList.add('dragover');
  });

  imageUploadWrapper.addEventListener('dragleave', () => {
    imageUploadWrapper.classList.remove('dragover');
  });

  imageUploadWrapper.addEventListener('drop', (e) => {
    e.preventDefault();
    imageUploadWrapper.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleImageSelection(e.dataTransfer.files[0]);
    }
  });

  imageInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleImageSelection(e.target.files[0]);
    }
  });

  if (btnRemoveImage) {
    btnRemoveImage.addEventListener('click', (e) => {
      e.stopPropagation();
      selectedImageFile = null;
      imageInput.value = '';
      imagePreview.src = '';
      imagePreviewContainer.style.display = 'none';
      imageUploadPrompt.style.display = 'block';
    });
  }

  function handleImageSelection(file) {
    if (!file.type.startsWith('image/')) {
      showToast(window.t('toast_invalid_img'), 'error');
      return;
    }
    selectedImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imageUploadPrompt.style.display = 'none';
      imagePreviewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }
}

// ===== EXAMPLE URL =====
const btnExample = document.getElementById('btn-example');
if (btnExample) {
  btnExample.addEventListener('click', () => {
    if (analyzerMode === 'url') {
      document.getElementById('url-input').value = 'https://www.bbc.com/news/articles/c4gzge8nyero';
    } else {
      document.getElementById('text-input').value = 'A shocking leaked document reveals that a secret organization has banned reverse aging technology to protect big pharma profits. Scientists who discovered the miracle cure were reportedly silenced before the truth gets deleted.';
    }
  });
}

// ===== CLEAR INPUT =====
const btnClear = document.getElementById('btn-clear');
if (btnClear) {
  btnClear.addEventListener('click', () => {
    document.getElementById('url-input').value = '';
    document.getElementById('text-input').value = '';
    if (imageInput) imageInput.value = '';
    selectedImageFile = null;
    const imageUploadPrompt = document.getElementById('image-upload-prompt');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    if (imagePreview) imagePreview.src = '';
    if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
    if (imageUploadPrompt) imageUploadPrompt.style.display = 'block';
    
    document.getElementById('results-section').style.display = 'none';
  });
}

// ===== ANALYZE FUNCTION =====
const btnAnalyze = document.getElementById('btn-analyze');
if (btnAnalyze) {
  btnAnalyze.addEventListener('click', analyze);
}
const btnNewAnalysis = document.getElementById('btn-new-analysis');
if (btnNewAnalysis) {
  btnNewAnalysis.addEventListener('click', () => {
    document.getElementById('analyzer').scrollIntoView({ behavior: 'smooth' });
    if (analyzerMode === 'url') {
      document.getElementById('url-input').focus();
    } else {
      document.getElementById('text-input').focus();
    }
  });
}

async function analyze() {
  let endpoint = '';
  let payload = {};

  let isFormData = false;

  if (analyzerMode === 'url') {
    const url = document.getElementById('url-input').value.trim();
    if (!url || !url.startsWith('http')) {
      showToast(window.t('toast_invalid_url'), 'error');
      return;
    }
    endpoint = '/analyze-url';
    payload = { url };
  } else if (analyzerMode === 'text') {
    const text = document.getElementById('text-input').value.trim();
    if (!text || text.length < 50) {
      showToast(window.t('toast_short_text'), 'error');
      return;
    }
    endpoint = '/api/analyze-text';
    payload = { text };
  } else if (analyzerMode === 'image') {
    if (!selectedImageFile) {
      showToast(window.t('toast_no_img'), 'error');
      return;
    }
    endpoint = '/api/analyze-image';
    payload = new FormData();
    payload.append('image', selectedImageFile);
    isFormData = true;
  }

  showLoading(true);
  let statuses = [];
  if (analyzerMode === 'url') {
    statuses = [
      'Extracting platform content...',
      'Analyzing site metadata...',
      'Initiating real-time web search...',
      'Cross-referencing global fact-checkers...',
      'Scanning reputable news networks...',
      'Blending AI predictions & evidence...',
      'Compiling final integrity report...'
    ];
  } else if (analyzerMode === 'text') {
    statuses = [
      'Analyzing text structures...',
      'Evaluating emotional loads...',
      'Scanning for propaganda indicators...',
      'Initiating claims fact-check search...',
      'Comparing with verified databases...',
      'Blending linguistic scores...',
      'Compiling final integrity report...'
    ];
  } else {
    statuses = [
      'Extracting text and claims via Vision AI...',
      'Identifying news source and platform...',
      'Initiating claims fact-check search...',
      'Cross-referencing global fact-checkers...',
      'Evaluating image context and reasoning...',
      'Blending AI predictions & evidence...',
      'Compiling final integrity report...'
    ];
  }
  let si = 0;
  if (document.getElementById('loader-status')) {
    document.getElementById('loader-status').textContent = statuses[0];
  }
  const statusInterval = setInterval(() => {
    si = (si + 1) % statuses.length;
    const statusEl = document.getElementById('loader-status');
    if (statusEl) statusEl.textContent = statuses[si];
  }, 1200);

  try {
    const headers = {};
    if (!isFormData) {
      headers['Content-Type'] = 'application/json';
    }
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers,
      body: isFormData ? payload : JSON.stringify(payload)
    });
    
    if (res.status === 401) {
      clearInterval(statusInterval);
      showLoading(false);
      removeToken();
      updateAuthUI();
      document.getElementById('admin-panel').style.display = 'none';
      document.getElementById('results-section').style.display = 'none';
      showToast(window.t('toast_session_exp'), 'error');
      return;
    }
    
    const data = await res.json();
    clearInterval(statusInterval);
    showLoading(false);
    
    if (data.error) {
      showToast(data.error, 'error');
      return;
    }
    displayResults(data);
    showToast(window.t('toast_analysis_ok'), 'success');
  } catch (err) {
    clearInterval(statusInterval);
    showLoading(false);
    console.warn('Backend connection error:', err);
    showToast(window.t('toast_server_offline'), 'error');
  }
}

function showLoading(show) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.toggle('visible', show);
    overlay.style.display = show ? 'flex' : 'none';
  }
}

function displayResults(data) {
  const section = document.getElementById('results-section');
  if (!section) return;
  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  // 1. Verdict Badge
  const badge = document.getElementById('prediction-badge');
  const label = document.getElementById('prediction-label');
  const subtitle = document.getElementById('prediction-subtitle');
  if (badge && label) {
    badge.className = 'prediction-badge ' + (data.prediction || 'fake').toLowerCase();
    label.textContent = data.prediction || 'Unknown';
  }
  if (subtitle) {
    subtitle.textContent = data.metadata ? `Source Reputation: ${data.metadata.domain}` : 'Linguistic Text Audit';
  }

  // 2. Confidence Meter
  const pct = data.confidence || 0;
  const circumference = 2 * Math.PI * 85;
  const offset = circumference - (pct / 100) * circumference;
  const fill = document.getElementById('meter-fill');
  if (fill) {
    fill.style.strokeDasharray = circumference;
    setTimeout(() => { fill.style.strokeDashoffset = offset; }, 100);
  }
  const meterText = document.getElementById('meter-text');
  if (meterText) meterText.textContent = pct + '%';

  // 3. Trust Index
  const cred = data.credibility || 50;
  const trustFill = document.getElementById('trust-fill');
  const trustScore = document.getElementById('trust-score');
  const trustLabel = document.getElementById('trust-label');
  if (trustFill) trustFill.style.width = cred + '%';
  if (trustScore) trustScore.textContent = cred + '%';
  if (trustLabel) {
    trustLabel.textContent = cred > 75 ? 'Verified High Trust Index' : cred > 45 ? 'Exhibits Moderate Risks' : 'High Misinformation Threat';
  }

  // 4. Reasoning
  const rText = document.getElementById('reasoning-text');
  if (rText) rText.textContent = data.reason || 'No detailed review compiled.';
  
  const tagsEl = document.getElementById('manipulation-tags');
  if (tagsEl) {
    tagsEl.innerHTML = '';
    (data.manipulation || []).forEach(m => {
      const tag = document.createElement('span');
      tag.className = 'manip-tag emotion';
      tag.textContent = m;
      tagsEl.appendChild(tag);
    });
  }

  drawEmotionChart(data.emotions);

  // 5. Red Flags
  const hlEl = document.getElementById('highlighted-text');
  if (hlEl) {
    hlEl.innerHTML = '';
    (data.suspicious_sentences || []).forEach(s => {
      const p = document.createElement('p');
      p.className = 'suspicious-item';
      p.style.marginBottom = '0.5rem';
      p.innerHTML = `<span class="suspicious">${s}</span>`;
      hlEl.appendChild(p);
    });
  }

  // 6. Verification Path
  const fcList = document.getElementById('factcheck-list');
  if (fcList) {
    fcList.innerHTML = '';
    (data.suggestions || []).forEach(s => {
      const li = document.createElement('li');
      li.className = 'factcheck-item';
      li.innerHTML = `<span class="factcheck-icon">✓</span> <span>${s}</span>`;
      fcList.appendChild(li);
    });
  }

  // 7. Cross-Reference Sources
  const crossRefCard = document.getElementById('cross-reference-card');
  const crossRefList = document.getElementById('cross-reference-list');
  if (crossRefCard && crossRefList) {
    if (data.cross_references && data.cross_references.length > 0) {
      crossRefCard.style.display = 'block';
      crossRefList.innerHTML = '';
      data.cross_references.forEach(ref => {
        const item = document.createElement('div');
        item.className = 'cross-reference-item';
        
        let badgeClass = 'unverified';
        if (ref.category === 'Reputable News') badgeClass = 'news';
        else if (ref.category === 'Fact Check (Debunked)') badgeClass = 'fact-fake';
        else if (ref.category === 'Fact Check (Verified)') badgeClass = 'fact-real';
        
        item.innerHTML = `
          <div class="cross-reference-meta">
            <a href="${ref.url}" target="_blank" rel="noopener noreferrer" class="cross-reference-title">${ref.title}</a>
            <span class="cross-reference-badge ${badgeClass}">${ref.category}</span>
          </div>
          <p class="cross-reference-snippet">${ref.snippet}</p>
        `;
        crossRefList.appendChild(item);
      });
    } else {
      crossRefCard.style.display = 'none';
    }
  }

  // 8. Risk Gauge
  const riskGauge = document.getElementById('risk-gauge');
  const riskLabel = document.getElementById('risk-label');
  if (riskGauge && riskLabel) {
    riskGauge.style.display = 'block';
    const predUpper = (data.prediction || '').toUpperCase();
    if (predUpper === 'FAKE') {
        riskLabel.textContent = 'CRITICAL RISK';
        riskLabel.style.background = 'rgba(255,71,87,0.2)';
        riskLabel.style.color = '#ff4757';
    } else if (predUpper === 'REAL') {
        riskLabel.textContent = 'LOW RISK';
        riskLabel.style.background = 'rgba(46,213,115,0.2)';
        riskLabel.style.color = '#2ed573';
    } else {
        riskLabel.textContent = 'MEDIUM RISK (UNCERTAIN)';
        riskLabel.style.background = 'rgba(255,165,2,0.2)';
        riskLabel.style.color = '#ffa502';
    }
  }

  // 9. Deep LLM Evidence & Claims
  const evidenceCard = document.getElementById('evidence-card');
  const evidenceText = document.getElementById('evidence-text');
  const claimsCard = document.getElementById('claims-card');
  const claimsList = document.getElementById('claims-list');
  
  if (data.llm_analysis) {
    if (evidenceCard && evidenceText) {
      evidenceCard.style.display = 'block';
      evidenceText.textContent = data.llm_analysis.fact_check_summary || 'No summary provided.';
    }
    if (claimsCard && claimsList && data.llm_analysis.extracted_claims) {
      claimsCard.style.display = 'block';
      claimsList.innerHTML = '';
      data.llm_analysis.extracted_claims.forEach(c => {
        const li = document.createElement('li');
        li.style.padding = '8px';
        li.style.borderBottom = '1px solid var(--glass-border)';
        
        let color = '#ffa502';
        if (c.validity.toLowerCase().includes('true')) color = '#2ed573';
        if (c.validity.toLowerCase().includes('false')) color = '#ff4757';
        
        li.innerHTML = `<strong>Claim:</strong> ${c.claim} <br> <span style="color:${color}; font-weight:bold;">${c.validity}</span>`;
        claimsList.appendChild(li);
      });
    }
  } else {
    if (evidenceCard) evidenceCard.style.display = 'none';
    if (claimsCard) claimsCard.style.display = 'none';
  }

  // 9.5 Image Context
  const imgContextCard = document.getElementById('image-context-card');
  const imgSourceBadge = document.getElementById('img-source-badge');
  const imgPlatform = document.getElementById('img-platform');
  const imgAuthor = document.getElementById('img-author');
  const imgDate = document.getElementById('img-date');
  const imgQuality = document.getElementById('img-quality');
  const imgHeadline = document.getElementById('img-extracted-headline');
  const imgClaim = document.getElementById('img-extracted-claim');
  const imgContextSummary = document.getElementById('img-context-summary');
  const imgOcrText = document.getElementById('img-ocr-text');
  const imgResultPreview = document.getElementById('img-result-preview');
  
  if (data.image_analysis && imgContextCard) {
    imgContextCard.style.display = 'block';
    
    if (imgSourceBadge) {
      let source = data.image_analysis.source || 'Unknown';
      imgSourceBadge.textContent = source;
      
      // Color code by platform
      let sourceUpper = source.toUpperCase();
      if (sourceUpper.includes('FACEBOOK')) imgSourceBadge.style.background = '#1877F2';
      else if (sourceUpper.includes('TWITTER') || sourceUpper === 'X') imgSourceBadge.style.background = '#000000';
      else if (sourceUpper.includes('INSTAGRAM')) imgSourceBadge.style.background = '#E4405F';
      else if (sourceUpper.includes('WHATSAPP')) imgSourceBadge.style.background = '#25D366';
      else if (sourceUpper.includes('TIKTOK')) imgSourceBadge.style.background = '#000000';
      else if (sourceUpper.includes('BBC')) imgSourceBadge.style.background = '#B80000';
      else if (sourceUpper.includes('CNN')) imgSourceBadge.style.background = '#CC0000';
      else if (sourceUpper.includes('ARY') || sourceUpper.includes('GEO') || sourceUpper.includes('DAWN')) imgSourceBadge.style.background = '#006600';
      else imgSourceBadge.style.background = 'var(--text-dim)';
      imgSourceBadge.style.color = '#fff';
    }
    
    if (imgPlatform) imgPlatform.textContent = data.image_analysis.platform || 'Unknown';
    if (imgAuthor) imgAuthor.textContent = data.image_analysis.author || '—';
    if (imgDate) imgDate.textContent = data.image_analysis.date || '—';
    if (imgQuality) imgQuality.textContent = data.image_analysis.image_quality || '—';
    if (imgHeadline) imgHeadline.textContent = data.image_analysis.headline || 'None detected';
    if (imgClaim) imgClaim.textContent = data.image_analysis.claim_to_check || 'None extracted';
    if (imgContextSummary) imgContextSummary.textContent = data.image_analysis.context_summary || '—';
    if (imgOcrText) imgOcrText.textContent = data.image_analysis.ocr_text || 'No text detected';
    
    // Set the image result preview to the currently selected image preview
    if (imgResultPreview && selectedImageFile) {
      const reader = new FileReader();
      reader.onload = (e) => {
        imgResultPreview.src = e.target.result;
        imgResultPreview.style.display = 'block';
      };
      reader.readAsDataURL(selectedImageFile);
    } else if (imgResultPreview) {
      imgResultPreview.style.display = 'none';
    }
    
  } else if (imgContextCard) {
    imgContextCard.style.display = 'none';
  }

  // 10. Bookmark Button logic
  const bookmarkBtn = document.getElementById('btn-bookmark-analysis');
  if (bookmarkBtn) {
    if (getToken() && data.inserted_id) { // Wait, app.py doesn't return inserted_id yet! We need to fix app.py to return it.
      bookmarkBtn.style.display = 'inline-flex';
      bookmarkBtn.onclick = async () => {
        try {
          const res = await fetch(`${API_BASE}/api/user/bookmark`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
            body: JSON.stringify({ analysis_id: data.inserted_id })
          });
          if (res.ok) {
            showToast(window.t('toast_bookmark_ok'), 'success');
            renderDashboard();
          } else {
            showToast(window.t('toast_bookmark_err'), 'error');
          }
        } catch(e) { console.error(e); }
      };
    } else {
      bookmarkBtn.style.display = 'none';
    }
  }

  // Sync and render updated verification history from MongoDB
  renderDashboard();
}

// ===== DATABASE DASHBOARD SYNC =====
async function renderDashboard() {
  const token = getToken();
  if (!token) return;

  const dashboardSection = document.getElementById('user-dashboard');
  if (!dashboardSection) return;

  dashboardSection.style.display = 'block';

  try {
    // 1. Stats
    const statsRes = await fetch(`${API_BASE}/api/user/stats`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (statsRes.ok) {
      const stats = await statsRes.json();
      document.getElementById('stat-total').textContent = stats.total_analyses;
      document.getElementById('stat-fake').textContent = stats.fake_detected;
      document.getElementById('stat-bookmarks').textContent = stats.bookmarks_saved;
    }

    // 2. Bookmarks
    const bRes = await fetch(`${API_BASE}/api/user/bookmarks`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (bRes.ok) {
      const bList = await bRes.json();
      const bContainer = document.getElementById('bookmarks-list');
      if (bList.length === 0) {
        bContainer.innerHTML = '<p>No bookmarks yet.</p>';
      } else {
        bContainer.innerHTML = bList.map(item => `
          <div class="data-item">
            <div class="data-item-info">
              <span class="prediction-badge "></span>
              <div class="data-item-title"></div>
            </div>
            <button class="action-btn" style="background: rgba(255,61,113,0.1); color: var(--accent);" onclick="deleteBookmark('')">Remove</button>
          </div>
            <button class="btn btn-sm btn-ghost" onclick="deleteBookmark('${item._id}')">🗑️</button>
          </div>
        `).join('');
      }
    }

    // 3. History
    const hRes = await fetch(`${API_BASE}/api/user/analyses`, { headers: { 'Authorization': `Bearer ${token}` } });
    if (hRes.ok) {
      const history = await hRes.json();
      const hContainer = document.getElementById('history-list');
      if (history.length === 0) {
        hContainer.innerHTML = '<p>No audit trail yet.</p>';
      } else {
        hContainer.innerHTML = history.map(item => {
          const dateStr = new Date(item.created_at).toLocaleString();
          return `
            <div class="history-item glass-card" style="padding: 1rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap;">
              <div style="font-size: 0.8rem; color: var(--text-dim);">${dateStr}</div>
              <div><strong>Verdict: ${item.prediction}</strong> (${item.confidence}%)</div>
              <div class="hist-url" style="color: var(--primary); font-size: 0.85rem; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${item.input}">${item.input}</div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.warn('Failed to load user dashboard from DB:', err);
  }
}

async function deleteBookmark(id) {
  if (!confirm('Remove this bookmark?')) return;
  const token = getToken();
  try {
    await fetch(`${API_BASE}/api/user/bookmark/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }});
    renderDashboard();
  } catch(e) { console.error(e); }
}

const btnClearHistory = document.getElementById('btn-clear-history');
if (btnClearHistory) {
  btnClearHistory.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to clear your audit trail history?')) return;
    
    const token = getToken();
    if (!token) return;
    
    try {
      const res = await fetch(`${API_BASE}/api/user/analyses`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.status === 401) {
        removeToken();
        updateAuthUI();
        return;
      }
      
      if (res.ok) {
        renderHistory();
        showToast(window.t('toast_clear_audit'), 'info');
      } else {
        showToast(window.t('toast_clear_audit_err'), 'error');
      }
    } catch {
      showToast(window.t('toast_conn_err'), 'error');
    }
  });
}

// ===== CHART =====
function drawEmotionChart(emotions) {
  const canvas = document.getElementById('emotion-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const keys = Object.keys(emotions || {});
  if (!keys.length) return;
  const colors = ['#FF3D71', '#ff8c00', '#7B61FF', '#00F5FF', '#4ecdc4'];
  keys.forEach((key, i) => {
    const val = emotions[key];
    const barH = (val / 100) * (h - 60);
    const x = 20 + i * (w / keys.length);
    ctx.fillStyle = colors[i % colors.length];
    ctx.fillRect(x, h - 30 - barH, 35, barH);
    ctx.fillStyle = '#8892b0';
    ctx.font = '10px Inter';
    ctx.fillText(key.toUpperCase(), x, h - 10);
  });
}

// ===== NEWS FEED =====
window.currentNewsData = [];

async function fetchNews() {
  const token = getToken();
  if (!token) return;

  const loadingEl = document.getElementById('news-loading');
  const lockEl = document.getElementById('news-lock');
  if (lockEl) lockEl.style.display = 'none';
  if (loadingEl) loadingEl.style.display = 'flex';
  
  const categorySelect = document.getElementById('news-category');
  const category = categorySelect ? categorySelect.value : 'general';
  
  try {
    const url = `${API_BASE}/api/news?category=${category}`;
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (res.status === 401) {
      removeToken();
      updateAuthUI();
      return;
    }
    
    if (!res.ok) {
      const errData = await res.json();
      const grid = document.getElementById('news-grid');
      if (grid) grid.innerHTML = `<div class="news-error" style="grid-column: span 3; text-align: center; color: var(--accent); padding: 2rem;">${errData.error || 'Failed to sync news.'}</div>`;
      if (loadingEl) loadingEl.style.display = 'none';
      return;
    }
    
    window.currentNewsData = await res.json();
    if (loadingEl) loadingEl.style.display = 'none';
    
    renderNews();
  } catch (err) {
    if (loadingEl) loadingEl.style.display = 'none';
    console.warn('Could not load global news stream:', err);
    const grid = document.getElementById('news-grid');
    if (grid) grid.innerHTML = '<div class="news-error" style="grid-column: span 3; text-align: center; color: var(--accent); padding: 2rem;">Verification news node offline.</div>';
  }
}

function renderNews() {
  const grid = document.getElementById('news-grid');
  if (!grid) return;
  
  const searchInput = document.getElementById('news-search');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
  
  let filteredNews = window.currentNewsData || [];
  if (query) {
    filteredNews = filteredNews.filter(n => 
      (n.title && n.title.toLowerCase().includes(query)) || 
      (n.source && n.source.toLowerCase().includes(query))
    );
  }
  
  if (filteredNews.length === 0) {
    grid.innerHTML = '<div class="news-empty" style="grid-column: span 3; text-align: center; color: var(--text-dim); padding: 2rem;">No articles found matching your criteria.</div>';
    return;
  }
  
  grid.innerHTML = filteredNews.map(n => `
    <div class="news-card glass-card">
      <div class="news-card-body">
        <div class="news-card-source">${n.source}</div>
        <h4 class="news-card-title">${n.title}</h4>
        <div class="news-card-date">${n.pubDate || 'Updated recently'}</div>
      </div>
      <div class="news-card-footer" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <span class="trust-badge ${n.tag}">Trust Score: ${n.trust}%</span>
        <a href="${n.link}" target="_blank" rel="noopener noreferrer" class="btn btn-ghost" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; color: var(--primary);">Read ➔</a>
      </div>
    </div>
  `).join('');
}

// ===== CHATBOT =====
const chatToggle = document.getElementById('chatbot-toggle');
const chatWindow = document.getElementById('chatbot-window');
const chatInput = document.getElementById('chatbot-input');
const chatSend = document.getElementById('chatbot-send');
const chatMessages = document.getElementById('chatbot-messages');
const chatClose = document.getElementById('chatbot-close');
const chatSuggestions = document.getElementById('chatbot-suggestions');

const quickReplies = [
  "What is Factify?",
  "How do I verify a news article?",
  "Is Factify free to use?",
  "How accurate are the results?",
  "Can I verify social media posts?"
];

let chatHasStarted = false;
let chatHistory = [];

if (chatSuggestions) {
  chatSuggestions.innerHTML = '';
  quickReplies.forEach(reply => {
    const chip = document.createElement('div');
    chip.className = 'chatbot-suggestion-chip';
    chip.textContent = reply;
    chip.addEventListener('click', () => {
      chatInput.value = reply;
      handleChatbotSend();
      chatSuggestions.style.display = 'none';
      chatHasStarted = true;
    });
    chatSuggestions.appendChild(chip);
  });
}

if (chatToggle) {
  chatToggle.addEventListener('click', () => {
    chatWindow.style.display = chatWindow.style.display === 'none' ? 'flex' : 'none';
    if (!chatHasStarted && chatWindow.style.display === 'flex' && chatSuggestions) {
      chatSuggestions.style.display = 'flex';
    }
  });
}
if (chatClose) {
  chatClose.addEventListener('click', () => { chatWindow.style.display = 'none'; });
}

if (chatSend) {
  chatSend.addEventListener('click', handleChatbotSend);
}
if (chatInput) {
  chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleChatbotSend();
  });
}

async function handleChatbotSend() {
  const msg = chatInput.value.trim();
  if (!msg) return;
  
  chatHasStarted = true;
  if (chatSuggestions) chatSuggestions.style.display = 'none';
  
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.textContent = msg;
  chatMessages.appendChild(div);
  chatInput.value = '';
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Append user message to history
  chatHistory.push({ role: 'user', content: msg });

  // Add temporary typing animation indicator
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'chat-msg bot typing-indicator';
  loadingDiv.innerHTML = '<span></span><span></span><span></span>';
  chatMessages.appendChild(loadingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // Artificial human-like delay (minimum 1.5s)
  const delayPromise = new Promise(resolve => setTimeout(resolve, 1500));

  try {
    const fetchPromise = fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, history: chatHistory })
    });
    
    // Wait for both the network request AND the minimum human delay
    const [res] = await Promise.all([fetchPromise, delayPromise]);
    
    // Remove loading indicator
    if (loadingDiv.parentNode) {
      loadingDiv.parentNode.removeChild(loadingDiv);
    }
    
    if (res.ok) {
      const data = await res.json();
      const bdiv = document.createElement('div');
      bdiv.className = 'chat-msg bot';
      // Simple markdown parser for bold and newlines, with XSS escaping
      let safeReply = data.reply.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      let formattedReply = safeReply
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      bdiv.innerHTML = formattedReply;
      chatMessages.appendChild(bdiv);
      
      // Append assistant reply to history
      chatHistory.push({ role: 'assistant', content: data.reply });
    } else {
      chatHistory.pop(); // Remove user msg from history on error
      const bdiv = document.createElement('div');
      bdiv.className = 'chat-msg bot';
      bdiv.textContent = "Oops! I'm having trouble connecting to my brain right now. Please try again.";
      chatMessages.appendChild(bdiv);
    }
  } catch (e) {
    if (loadingDiv.parentNode) {
      loadingDiv.parentNode.removeChild(loadingDiv);
    }
    chatHistory.pop(); // Remove user msg from history on network error
    const bdiv = document.createElement('div');
    bdiv.className = 'chat-msg bot';
    bdiv.textContent = "Network error. Please check your connection and try again.";
    chatMessages.appendChild(bdiv);
  }
  
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== CONTACT / FEEDBACK SYSTEM =====
const starContainer = document.getElementById('star-rating');
const ratingInput = document.getElementById('feedback-rating');

if (starContainer) {
  const stars = starContainer.querySelectorAll('.star');
  stars.forEach(star => {
    star.addEventListener('click', () => {
      const val = parseInt(star.dataset.value);
      ratingInput.value = val;
      stars.forEach((s, idx) => {
        s.classList.toggle('active', idx < val);
      });
    });

    star.addEventListener('mouseover', () => {
      const val = parseInt(star.dataset.value);
      stars.forEach((s, idx) => {
        if (idx < val) s.style.color = '#ffc800';
      });
    });

    star.addEventListener('mouseout', () => {
      stars.forEach(s => s.style.color = '');
    });
  });
}

const feedbackForm = document.getElementById('feedback-form');
if (feedbackForm) {
  feedbackForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('feedback-name').value.trim();
    const email = document.getElementById('feedback-email').value.trim();
    const subject = document.getElementById('feedback-subject').value.trim();
    const message = document.getElementById('feedback-message').value.trim();
    const rating = parseInt(ratingInput.value);

    if (rating === 0) {
      showToast(window.t('toast_rate_exp'), 'error');
      return;
    }

    const fbToken = getToken();
    if (!fbToken) {
      showToast(window.t('toast_login_req'), 'error');
      if (loginModal) loginModal.style.display = 'flex';
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${fbToken}` },
        body: JSON.stringify({ name, email, subject, message, rating })
      });

      if (res.ok) {
        showToast(window.t('toast_feedback_ok'), 'success');
        feedbackForm.reset();
        ratingInput.value = 0;
        starContainer.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
        loadTestimonials();
      } else {
        const err = await res.json();
        showToast(err.error || window.t('toast_feedback_err'), 'error');
      }
    } catch {
      showToast(window.t('toast_conn_err'), 'error');
    }
  });
}

// ===== CONTACT FORM SUBMISSION =====
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById('contact-name').value,
      email: document.getElementById('contact-email').value,
      subject: document.getElementById('contact-subject').value,
      message: document.getElementById('contact-message').value
    };

    try {
      const res = await fetch(`${API_BASE}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        showToast(window.t('toast_msg_ok'), 'success');
        contactForm.reset();
      } else {
        const err = await res.json();
        showToast(err.error || window.t('toast_msg_err'), 'error');
      }
    } catch {
      showToast(window.t('toast_conn_err'), 'error');
    }
  });
}

async function loadTestimonials() {
  const list = document.getElementById('testimonials-list');
  if (!list) return;

  try {
    const res = await fetch(`${API_BASE}/api/feedback`);
    if (res.ok) {
      const feedbacks = await res.json();
      if (feedbacks.length === 0) {
        list.innerHTML = '<div class="testimonial-placeholder">No feedback yet. Be the first! 🚀</div>';
        return;
      }
      
      list.innerHTML = feedbacks.map(f => `
        <div class="testimonial-item">
          <div class="testimonial-name">${f.name}</div>
          <div class="testimonial-stars">${'★'.repeat(f.rating)}${'☆'.repeat(5 - f.rating)}</div>
          <p class="testimonial-message">${f.message}</p>
          <div class="testimonial-date">${new Date(f.created_at).toLocaleDateString()}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.warn('Could not load feedbacks stream:', err);
  }
}

// ===== ADMIN PANEL LOGIC =====
const btnAdminNav = document.getElementById('btn-admin-nav');
if (btnAdminNav) {
  btnAdminNav.addEventListener('click', () => {
    window.location.href = '/admin/dashboard';
  });
}

// Admin Tab Switching
document.querySelectorAll('.admin-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    
    document.querySelectorAll('.admin-tab-content').forEach(content => {
      content.style.display = 'none';
    });
    const activeTabId = tab.dataset.tab;
    document.getElementById(activeTabId).style.display = 'block';
    loadAdminTab(activeTabId);
  });
});



// ===== PDF EXPORT — ANALYSIS RESULTS ONLY =====
const btnExportPdf = document.getElementById('btn-export-pdf');
if (btnExportPdf) {
  btnExportPdf.addEventListener('click', async () => {
    const resultsSection = document.getElementById('results-section');
    if (!resultsSection || resultsSection.style.display === 'none') {
      showToast(window.t('toast_no_export'), 'error');
      return;
    }

    showToast(window.t('toast_pdf_gen'), 'info');

    try {
      // Capture website logo for PDF with forced colors for different backgrounds
      let watermarkLogoDataUrl = null;
      let headerLogoDataUrl = null;
      try {
        const logoEl = document.querySelector('.nav-logo');
        if (logoEl) {
          const cloneDark = logoEl.cloneNode(true);
          const cloneLight = logoEl.cloneNode(true);
          
          const tempContainer = document.createElement('div');
          // Use fixed positioning inside the viewport with zero opacity to prevent viewport cropping bugs in html2canvas
          tempContainer.style.position = 'fixed';
          tempContainer.style.top = '0';
          tempContainer.style.left = '0';
          tempContainer.style.opacity = '0';
          tempContainer.style.pointerEvents = 'none';
          tempContainer.style.zIndex = '-9999';
          document.body.appendChild(tempContainer);
          
          // Helper to style the clone to prevent cropping
          const prepClone = (clone) => {
            clone.style.display = 'inline-flex';
            clone.style.alignItems = 'center';
            clone.style.whiteSpace = 'nowrap';
            clone.style.padding = '10px 20px'; // Add padding to prevent bounds cropping
            clone.style.margin = '0';
            clone.style.textDecoration = 'none';
            clone.style.width = 'max-content';
          };

          // Force styles for watermark (dark text for white PDF background)
          prepClone(cloneDark);
          cloneDark.style.color = '#000000';
          const iconDark = cloneDark.querySelector('.logo-icon');
          if (iconDark) iconDark.style.color = '#00F5FF';
          const aiDark = cloneDark.querySelector('.logo-ai');
          if (aiDark) aiDark.style.color = '#00F5FF';
          
          // Force styles for header (white text for purple PDF background)
          prepClone(cloneLight);
          cloneLight.style.color = '#ffffff';
          const iconLight = cloneLight.querySelector('.logo-icon');
          if (iconLight) iconLight.style.color = '#00F5FF';
          const aiLight = cloneLight.querySelector('.logo-ai');
          if (aiLight) aiLight.style.color = '#00F5FF';
          
          tempContainer.appendChild(cloneDark);
          tempContainer.appendChild(cloneLight);
          
          const canvasDark = await html2canvas(cloneDark, { backgroundColor: null, scale: 3, logging: false });
          watermarkLogoDataUrl = canvasDark.toDataURL('image/png');
          
          const canvasLight = await html2canvas(cloneLight, { backgroundColor: null, scale: 3, logging: false });
          headerLogoDataUrl = canvasLight.toDataURL('image/png');

          document.body.removeChild(tempContainer);
        }
      } catch (e) {
        console.warn('Could not capture logo for PDF', e);
      }

      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF('p', 'pt', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin = 40;
      const contentWidth = pageWidth - 2 * margin;

      let yPos = 120;
      let pageNum = 1;

      // Function to check page overflow and add new page
      const checkPageBreak = (neededHeight) => {
        if (yPos + neededHeight > pageHeight - 60) {
          pdf.addPage();
          pageNum++;
          yPos = margin;
          drawWatermark();
          drawFooter();
        }
      };

      const drawWatermark = () => {
        if (watermarkLogoDataUrl) {
          // Draw the captured logo as a faint watermark in the center
          pdf.setGState(new pdf.GState({ opacity: 0.1 }));
          const logoWidth = 250;
          const logoHeight = 60; // Approximate ratio
          pdf.addImage(watermarkLogoDataUrl, 'PNG', (pageWidth - logoWidth) / 2, (pageHeight - logoHeight) / 2, logoWidth, logoHeight);
          pdf.setGState(new pdf.GState({ opacity: 1.0 }));
        }
      };

      const drawFooter = () => {
        pdf.setDrawColor(200, 200, 200);
        pdf.setLineWidth(1);
        pdf.line(margin, pageHeight - 60, pageWidth - margin, pageHeight - 60);
        pdf.setTextColor(100, 100, 100);
        pdf.setFontSize(10);
        pdf.text('Generated by Factify | Document ID: FG-' + Math.random().toString(36).substr(2, 9).toUpperCase(), margin, pageHeight - 40);
        pdf.text('www.factify.com | Page ' + pageNum, pageWidth - margin, pageHeight - 40, { align: 'right' });
      };

      // Extract Data
      const prediction = document.getElementById('prediction-label')?.textContent || 'Unknown';
      const riskLevel = document.getElementById('risk-label')?.textContent || '';
      const confidence = document.getElementById('meter-text')?.textContent || '0%';
      const trustScore = document.getElementById('trust-score')?.textContent || '0%';
      const reason = document.getElementById('reasoning-text')?.textContent || 'No detailed review compiled.';
      const evidence = document.getElementById('evidence-text')?.textContent || '';
      const claims = Array.from(document.querySelectorAll('#claims-list li')).map(el => el.textContent.trim());
      
      const manipTags = Array.from(document.querySelectorAll('#manipulation-tags .manip-tag')).map(el => el.textContent);
      const redFlags = Array.from(document.querySelectorAll('#highlighted-text .suspicious')).map(el => el.textContent);
      const verifications = Array.from(document.querySelectorAll('#factcheck-list li')).map(el => el.textContent.replace('✓', '').trim());

      const modeUrlBtn = document.getElementById('mode-url');
      const modeImageBtn = document.getElementById('mode-image');
      let inputMode = 'Text';
      if (modeUrlBtn && modeUrlBtn.classList.contains('active')) inputMode = 'URL';
      if (modeImageBtn && modeImageBtn.classList.contains('active')) inputMode = 'Image';
      
      let inputText = 'No input provided';
      if (inputMode === 'URL') {
        inputText = document.getElementById('url-input')?.value;
      } else if (inputMode === 'Text') {
        inputText = document.getElementById('text-input')?.value;
      } else if (inputMode === 'Image') {
        inputText = `Uploaded Image: ${selectedImageFile ? selectedImageFile.name : 'Unknown'}`;
      }
      if (!inputText) inputText = 'No input provided';

      // 1) HEADER & BRANDING (First Page Only)
      pdf.setFillColor(46, 21, 104);
      pdf.rect(0, 0, pageWidth, 80, 'F');
      
      if (headerLogoDataUrl) {
        // Draw the captured logo in the header (white/transparent)
        pdf.addImage(headerLogoDataUrl, 'PNG', margin, 20, 160, 40);
      } else {
        // Fallback text if logo fails to capture
        pdf.setTextColor(255, 255, 255);
        pdf.setFont("helvetica", "bold");
        pdf.setFontSize(28);
        pdf.text('Factify', margin, 50);
      }
      
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(12);
      pdf.setFont("helvetica", "normal");
      pdf.text('Official Verification Report', pageWidth - margin, 50, { align: 'right' });
      drawWatermark();
      drawFooter();

      // REPORT TITLE
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(20);
      pdf.setFont("helvetica", "bold");
      pdf.text('Comprehensive Content Analysis', margin, yPos);
      yPos += 20;
      pdf.setDrawColor(200, 200, 200);
      pdf.setLineWidth(1);
      pdf.line(margin, yPos, pageWidth - margin, yPos);
      yPos += 30;

      // 1. News Information (Analyzed Content)
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text(`1. Analyzed ${inputMode} (News Information):`, margin, yPos);
      yPos += 15;
      pdf.setFontSize(10);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(80, 80, 80);
      let textToPrint = inputText.length > 800 ? inputText.substring(0, 800) + '... [Truncated]' : inputText;
      let splitText = pdf.splitTextToSize(textToPrint, contentWidth);
      checkPageBreak(splitText.length * 12 + 20);
      pdf.text(splitText, margin, yPos);
      yPos += (splitText.length * 12) + 20;

      // Badges Container: 2. Verdict | 3. Confidence | 4. Trust Index
      checkPageBreak(60);
      pdf.setFontSize(12);
      pdf.setFont("helvetica", "bold");
      pdf.setTextColor(0, 0, 0);
      const isFake = prediction.toLowerCase() === 'fake';
      const statusColor = isFake ? [220, 53, 69] : [40, 167, 69];
      
      pdf.setFillColor(statusColor[0], statusColor[1], statusColor[2]);
      pdf.rect(margin, yPos, 160, 40, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.text(`2. Verdict: ${prediction.toUpperCase()}`, margin + 10, yPos + 25);

      pdf.setFillColor(0, 123, 255);
      pdf.rect(margin + 175, yPos, 160, 40, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.text(`3. Confidence: ${confidence}`, margin + 185, yPos + 25);

      pdf.setFillColor(108, 92, 231);
      pdf.rect(margin + 350, yPos, 160, 40, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.text(`4. Trust Index: ${trustScore}`, margin + 360, yPos + 25);
      yPos += 65;

      // 5. Evidence-Based Summary & Claims
      if (evidence) {
        pdf.setTextColor(0, 0, 0);
        pdf.setFontSize(14);
        pdf.setFont("helvetica", "bold");
        pdf.text('5. Evidence-Based Fact Check Summary:', margin, yPos);
        yPos += 15;
        pdf.setFontSize(11);
        pdf.setFont("helvetica", "normal");
        pdf.setTextColor(50, 50, 50);
        splitText = pdf.splitTextToSize(evidence, contentWidth);
        checkPageBreak(splitText.length * 15 + 20);
        pdf.text(splitText, margin, yPos);
        yPos += (splitText.length * 15) + 15;
        
        if (claims.length > 0) {
          pdf.setFontSize(12);
          pdf.setFont("helvetica", "bold");
          pdf.text('Extracted Claims:', margin, yPos);
          yPos += 15;
          pdf.setFontSize(10);
          pdf.setFont("helvetica", "normal");
          claims.forEach(c => {
             splitText = pdf.splitTextToSize('- ' + c, contentWidth);
             checkPageBreak(splitText.length * 12 + 10);
             pdf.text(splitText, margin, yPos);
             yPos += (splitText.length * 12) + 5;
          });
          yPos += 10;
        }
      }

      // 6. Structural Analysis
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('6. ML Structural Analysis:', margin, yPos);
      yPos += 15;
      pdf.setFontSize(11);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(50, 50, 50);
      splitText = pdf.splitTextToSize(reason, contentWidth);
      checkPageBreak(splitText.length * 15 + 20);
      pdf.text(splitText, margin, yPos);
      yPos += (splitText.length * 15) + 20;

      // 6. Linguistic Patterns Analysis
      checkPageBreak(50);
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('6. Linguistic Patterns Analysis:', margin, yPos);
      yPos += 15;
      pdf.setFontSize(11);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(80, 80, 80);
      let manipText = manipTags.length > 0 ? manipTags.join(' • ') : 'No specific manipulation patterns detected.';
      splitText = pdf.splitTextToSize(manipText, contentWidth);
      checkPageBreak(splitText.length * 15 + 20);
      pdf.text(splitText, margin, yPos);
      yPos += (splitText.length * 15) + 20;

      // 7. Emotional Load Assessment
      checkPageBreak(250);
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('7. Emotional Load Assessment:', margin, yPos);
      yPos += 15;
      const chartCanvas = document.getElementById('emotion-chart');
      if (chartCanvas) {
        try {
          const imgData = chartCanvas.toDataURL('image/png');
          pdf.addImage(imgData, 'PNG', margin, yPos, 300, 165);
          yPos += 180;
        } catch(e) {
          pdf.setFontSize(11);
          pdf.setFont("helvetica", "normal");
          pdf.text('Emotion chart unavailable.', margin, yPos);
          yPos += 20;
        }
      }

      // 8. Content Red Flags
      checkPageBreak(50);
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('8. Content Red Flags:', margin, yPos);
      yPos += 15;
      pdf.setFontSize(11);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(220, 53, 69); // Red text for red flags
      if (redFlags.length > 0) {
        redFlags.forEach(flag => {
          splitText = pdf.splitTextToSize('• ' + flag, contentWidth);
          checkPageBreak(splitText.length * 15 + 10);
          pdf.text(splitText, margin, yPos);
          yPos += (splitText.length * 15) + 5;
        });
      } else {
        pdf.setTextColor(40, 167, 69); // Green
        pdf.text('No critical red flags detected in content structure.', margin, yPos);
        yPos += 20;
      }
      yPos += 10;

      // 9. Verification Path
      checkPageBreak(50);
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('9. Verification Path & Suggestions:', margin, yPos);
      yPos += 15;
      pdf.setFontSize(11);
      pdf.setFont("helvetica", "normal");
      pdf.setTextColor(50, 50, 50);
      if (verifications.length > 0) {
        verifications.forEach(item => {
          splitText = pdf.splitTextToSize('✓ ' + item, contentWidth);
          checkPageBreak(splitText.length * 15 + 10);
          pdf.text(splitText, margin, yPos);
          yPos += (splitText.length * 15) + 5;
        });
      } else {
        pdf.text('No additional verification suggestions.', margin, yPos);
        yPos += 20;
      }
      yPos += 10;

      // 10. Final Conclusion
      checkPageBreak(80);
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(14);
      pdf.setFont("helvetica", "bold");
      pdf.text('10. Final Conclusion:', margin, yPos);
      yPos += 20;
      
      pdf.setFillColor(isFake ? 253 : 240, isFake ? 240 : 255, isFake ? 240 : 240); // Light red or light green bg
      pdf.rect(margin, yPos, contentWidth, 50, 'F');
      
      pdf.setFontSize(12);
      pdf.setTextColor(statusColor[0], statusColor[1], statusColor[2]);
      let conclusionText = isFake 
        ? `Based on a multi-vector AI analysis (Confidence: ${confidence}), this content exhibits high risk patterns associated with misinformation.`
        : `Based on a multi-vector AI analysis (Confidence: ${confidence}), this content appears credible with no significant manipulation detected.`;
      
      splitText = pdf.splitTextToSize(conclusionText, contentWidth - 20);
      pdf.text(splitText, margin + 10, yPos + 20);
      yPos += 70;

      // SAVE
      const safePrediction = prediction.trim().replace(/[^a-zA-Z0-9]/g, '');
      const filename = `Factify_${safePrediction}_Report.pdf`;
      pdf.save(filename);

      showToast(window.t('toast_pdf_ok'), 'success');

    } catch (err) {
      console.error('PDF generation error:', err);
      showToast(window.t('toast_pdf_err'), 'error');
    }
  });
}

// ===== INITIALIZE FEEDBACKS & AUTH STATE =====
document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  loadTestimonials();
  renderHistory();
  fetchNews();

  // News category dropdown select trigger
  const newsCategorySelect = document.getElementById('news-category');
  if (newsCategorySelect) {
    newsCategorySelect.addEventListener('change', () => fetchNews());
  }

  // News search dynamic query filter (frontend instantly)
  const newsSearchInput = document.getElementById('news-search');
  if (newsSearchInput) {
    newsSearchInput.addEventListener('input', () => {
      renderNews();
    });
  }
});

console.log('🛡️ Factify URL-Engine & Database Client initialized.');

// Dashboard Tab Switching Logic
document.addEventListener('DOMContentLoaded', () => {
  const sideTabs = document.querySelectorAll('.side-tab');
  const tabContents = document.querySelectorAll('.tab-content, .user-tab-content');
  
  sideTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      sideTabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      tabContents.forEach(c => c.style.display = 'none');
      
      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      const targetContent = document.getElementById('tab-' + targetId);
      if (targetContent) {
        targetContent.style.display = 'block';
        // slight delay to trigger animation
        setTimeout(() => targetContent.classList.add('active'), 10);
      }
    });
  });
});


// PROFILE UPDATE LOGIC
document.addEventListener('DOMContentLoaded', () => {
  const profileUpdateForm = document.getElementById('profile-update-form');
  if (profileUpdateForm) {
    profileUpdateForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('profile-name').value.trim();
      const btn = document.getElementById('btn-update-profile');
      const originalText = btn.textContent;
      btn.textContent = 'Saving...';
      btn.disabled = true;
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/user/profile`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({ name })
        });
        const data = await response.json();
        if (response.ok) {
          showToast(window.t('toast_profile_ok'), 'success');
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          user.name = data.name;
          localStorage.setItem('user', JSON.stringify(user));
          updateAuthUI();
        } else {
          showToast(data.error || window.t('toast_profile_err'), 'error');
        }
      } catch (err) {
        showToast(window.t('toast_profile_err'), 'error');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    });
  }

  const passwordUpdateForm = document.getElementById('password-update-form');
  if (passwordUpdateForm) {
    passwordUpdateForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const password = document.getElementById('profile-password').value;
      const confirmPassword = document.getElementById('profile-confirm-password').value;
      if (password !== confirmPassword) {
        showToast(window.t('toast_pass_mismatch'), 'error');
        return;
      }
      // Password validation rule
      const passRegex = /^(?=.*[A-Z])(?=.*\d).{8,}$/;
      if (!passRegex.test(password)) {
        showToast(window.t('toast_pass_req'), 'error');
        return;
      }

      const btn = document.getElementById('btn-update-password');
      const originalText = btn.textContent;
      btn.textContent = 'Updating...';
      btn.disabled = true;
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE}/api/user/password`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({ password })
        });
        const data = await response.json();
        if (response.ok) {
          showToast(window.t('toast_pass_ok'), 'success');
          passwordUpdateForm.reset();
        } else {
          showToast(data.error || window.t('toast_pass_err'), 'error');
        }
      } catch (err) {
        showToast(window.t('toast_pass_err'), 'error');
      } finally {
        btn.textContent = originalText;
        btn.disabled = false;
      }
    });
  }
});



// ===== USER DASHBOARD SIDEBAR TOGGLE =====
const userSidebar = document.getElementById('user-sidebar');
const userSidebarToggle = document.getElementById('user-sidebar-toggle');
const userSidebarClose = document.getElementById('user-sidebar-close');
const userSideTabsList = document.querySelectorAll('.user-sidebar-link');

if (userSidebarToggle && userSidebar) {
  userSidebarToggle.addEventListener('click', () => {
    userSidebar.classList.add('active');
  });
}
if (userSidebarClose && userSidebar) {
  userSidebarClose.addEventListener('click', () => {
    userSidebar.classList.remove('active');
  });
}
if (userSideTabsList) {
  userSideTabsList.forEach(tab => {
    tab.addEventListener('click', () => {
      if (window.innerWidth <= 900 && userSidebar) {
        userSidebar.classList.remove('active');
      }
    });
  });
}

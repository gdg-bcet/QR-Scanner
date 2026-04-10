/**
 * T-Shirt Distribution System — Frontend Logic
 * Handles QR scanning, API calls, and DOM manipulation.
 */

// ── Configuration ──
const API_BASE = window.location.origin + '/api';

// ── SVG Icons ──
const ICONS = {
    camera: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>`,
    stop: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>`,
    check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    x: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    qr: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="8" height="8" rx="1"/><rect x="14" y="2" width="8" height="8" rx="1"/><rect x="2" y="14" width="8" height="8" rx="1"/><path d="M14 14h2v2h-2z"/><path d="M20 14h2v2h-2z"/><path d="M14 20h2v2h-2z"/><path d="M20 20h2v2h-2z"/><path d="M17 14h0v8"/><path d="M14 17h8"/></svg>`,
    mail: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>`,
    building: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/></svg>`,
    calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
    undo: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13"/></svg>`,
    shirt: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.47a1 1 0 0 0 1 .84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.14a1 1 0 0 0 1-.84l.58-3.47a2 2 0 0 0-1.34-2.23z"/></svg>`,
    list: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>`,
};


// ── Toast Notifications ──
function showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('show'));
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}


// ── Stats Loader ──
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        if (!res.ok) throw new Error('Failed to load stats');
        const data = await res.json();

        const totalEl = document.getElementById('stat-total');
        const takenEl = document.getElementById('stat-taken');
        const remainingEl = document.getElementById('stat-remaining');

        if (totalEl) totalEl.textContent = data.total;
        if (takenEl) takenEl.textContent = data.taken;
        if (remainingEl) remainingEl.textContent = data.remaining;
    } catch (err) {
        console.error('Stats load failed:', err);
    }
}


// ═══════════════════════════════════════════
//  SCANNER PAGE LOGIC
// ═══════════════════════════════════════════

let html5QrCode = null;
let isScanning = false;

function initScannerPage() {
    loadStats();

    const scanBtn = document.getElementById('btn-start-scan');
    const stopBtn = document.getElementById('btn-stop-scan');

    if (scanBtn) scanBtn.addEventListener('click', startScanner);
    if (stopBtn) stopBtn.addEventListener('click', stopScanner);

    // Auto-start if URL has ?autostart=true
    const params = new URLSearchParams(window.location.search);
    if (params.get('autostart') === 'true') {
        startScanner();
    }
}

async function startScanner() {
    const placeholder = document.getElementById('scanner-placeholder');
    const liveScanner = document.getElementById('scanner-live');

    if (placeholder) placeholder.style.display = 'none';
    if (liveScanner) liveScanner.style.display = 'flex';

    isScanning = true;

    try {
        html5QrCode = new Html5Qrcode('reader');
        await html5QrCode.start(
            { facingMode: 'environment' },
            {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0,
            },
            onScanSuccess,
            () => {} // Ignore parse errors
        );
    } catch (err) {
        console.error('Scanner start failed:', err);
        showToast('Camera access denied. Please grant permissions.', 'error');
        stopScanner();
    }
}

function stopScanner() {
    const placeholder = document.getElementById('scanner-placeholder');
    const liveScanner = document.getElementById('scanner-live');

    if (html5QrCode && html5QrCode.isScanning) {
        html5QrCode.stop().then(() => {
            html5QrCode = null;
        }).catch(err => console.error('Stop failed:', err));
    }

    isScanning = false;
    if (placeholder) placeholder.style.display = 'flex';
    if (liveScanner) liveScanner.style.display = 'none';
}

function onScanSuccess(decodedText) {
    // Stop camera immediately
    if (html5QrCode && html5QrCode.isScanning) {
        html5QrCode.stop().then(() => {
            html5QrCode = null;
        }).catch(err => console.error(err));
    }

    // Extract token — handle both raw tokens and URL-encoded values
    let tokenId = decodedText.trim();
    if (tokenId.includes('/')) {
        tokenId = tokenId.split('/').pop();
    }

    // Navigate to verify page
    window.location.href = `/verify/${tokenId}`;
}


// ═══════════════════════════════════════════
//  VERIFY PAGE LOGIC
// ═══════════════════════════════════════════

function initVerifyPage() {
    // Extract token from URL path: /verify/{token_id}
    const pathParts = window.location.pathname.split('/');
    const tokenId = pathParts[pathParts.length - 1];

    if (!tokenId) {
        showError('No token ID in URL.');
        return;
    }

    autoCollectPerson(tokenId);
}

async function autoCollectPerson(tokenId) {
    const loadingEl = document.getElementById('loading');
    const contentEl = document.getElementById('verify-content');
    const loadText = document.querySelector('.loading-text');
    
    if (loadText) loadText.textContent = "Recording scan...";

    try {
        // Instantly mark as taken to speed up the process!
        const res = await fetch(`${API_BASE}/mark/${tokenId}`, { method: 'POST' });

        if (res.status === 404) {
            showError('Person not found. Invalid QR code.');
            return;
        }

        if (!res.ok) {
            showError('Failed to process scan.');
            return;
        }

        const data = await res.json();
        renderPerson(data.person, data.success);

        if (data.success) {
            showToast('Successfully recorded!', 'success');
        } else {
            showToast(data.message || 'Already collected', 'error');
        }

        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'flex';

    } catch (err) {
        console.error(err);
        showError('Network error. Check your connection.');
    }
}

function renderPerson(person, justCollected = false) {
    const isCollected = person.is_taken;

    // Status icon & label
    const statusIcon = document.getElementById('status-icon');
    const statusLabel = document.getElementById('status-label');
    const statusSub = document.getElementById('status-sub');
    const markBtn = document.getElementById('btn-mark');
    const resetBtn = document.getElementById('btn-reset');

    if (!isCollected) {
        // This happens if they hit Undo
        statusIcon.className = 'status-icon ready';
        statusIcon.innerHTML = ICONS.list; // use a list/check pattern or fallback
        statusLabel.className = 'status-label ready';
        statusLabel.textContent = 'READY';
        statusSub.textContent = 'Record was reset. Ready to collect.';
        
        if (markBtn) markBtn.style.display = 'flex';
        if (resetBtn) resetBtn.style.display = 'none';
        
        if (markBtn) markBtn.onclick = () => manualMarkAsTaken(person.token_id);
    } else {
        if (justCollected) {
            statusIcon.className = 'status-icon ready'; // Green success
            statusIcon.innerHTML = ICONS.check;
            statusLabel.className = 'status-label ready';
            statusLabel.textContent = 'COLLECTED';
            statusSub.textContent = 'Successfully recorded right now!';
        } else {
            statusIcon.className = 'status-icon taken'; // Red error
            statusIcon.innerHTML = ICONS.x;
            statusLabel.className = 'status-label taken';
            statusLabel.textContent = 'ALREADY TAKEN';
            statusSub.textContent = 'T-shirt was already picked up previously!';
        }
        
        if (markBtn) markBtn.style.display = 'none';
        if (resetBtn) resetBtn.style.display = 'flex';
        
        if (resetBtn) resetBtn.onclick = () => resetStatus(person.token_id);
    }

    // Person details
    document.getElementById('person-name').textContent = person.name || 'Unknown';
    document.getElementById('person-email').textContent = person.email || '—';
    document.getElementById('person-dept').textContent = person.department || '—';
    document.getElementById('person-year').textContent = person.graduation_year || '—';
    document.getElementById('person-size').textContent = person.tshirt_size || '—';
    document.getElementById('token-value').textContent = person.token_id;
}

async function manualMarkAsTaken(tokenId) {
    const markBtn = document.getElementById('btn-mark');
    markBtn.disabled = true;
    markBtn.innerHTML = `<div class="spinner" style="width:24px;height:24px;border-width:2px;"></div> Updating...`;

    try {
        const res = await fetch(`${API_BASE}/mark/${tokenId}`, { method: 'POST' });
        const data = await res.json();

        if (data.success && data.person) {
            renderPerson(data.person, true);
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Already collected!', 'error');
            if (data.person) renderPerson(data.person, false);
        }
    } catch (err) {
        console.error(err);
        showToast('Failed to update. Try again.', 'error');
    } finally {
        markBtn.disabled = false;
        markBtn.innerHTML = `${ICONS.shirt} Mark as Collected`;
    }
}

async function resetStatus(tokenId) {
    if (!confirm('Are you sure you want to undo this collection?')) return;

    const resetBtn = document.getElementById('btn-reset');
    resetBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/reset/${tokenId}`, { method: 'POST' });
        const data = await res.json();

        if (data.success && data.person) {
            renderPerson(data.person, false);
            showToast(data.message, 'success');
        } else {
            showToast('Failed to reset.', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error. Try again.', 'error');
    } finally {
        resetBtn.disabled = false;
    }
}

function showError(message) {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const contentEl = document.getElementById('verify-content');

    if (loadingEl) loadingEl.style.display = 'none';
    if (contentEl) contentEl.style.display = 'none';
    if (errorEl) {
        errorEl.style.display = 'flex';
        const msgEl = errorEl.querySelector('.error-message');
        if (msgEl) msgEl.textContent = message;
    }
}


// ═══════════════════════════════════════════
//  DASHBOARD PAGE LOGIC
// ═══════════════════════════════════════════

function initDashboardPage() {
    loadStats();
    loadParticipants();
}

async function loadParticipants() {
    const tbody = document.getElementById('participants-tbody');
    if (!tbody) return;

    try {
        const res = await fetch(`${API_BASE}/participants`);
        const data = await res.json();
        const participants = data.participants || [];

        tbody.innerHTML = '';

        participants.forEach((p, i) => {
            const tr = document.createElement('tr');
            const statusClass = p.is_taken ? 'taken' : 'pending';
            const statusText = p.is_taken ? 'Collected' : 'Pending';

            tr.innerHTML = `
                <td>${i + 1}</td>
                <td style="color:var(--text-primary);font-weight:600;">${escapeHtml(p.name)}</td>
                <td>${escapeHtml(p.email)}</td>
                <td>${escapeHtml(p.department || '—')}</td>
                <td>${escapeHtml(p.graduation_year || '—')}</td>
                <td><strong style="color:var(--gc-blue);">${escapeHtml(p.tshirt_size)}</strong></td>
                <td><span class="status-dot ${statusClass}"></span> ${statusText}</td>
            `;
            tbody.appendChild(tr);
        });

        // Setup search
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                const rows = tbody.querySelectorAll('tr');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(query) ? '' : 'none';
                });
            });
        }
    } catch (err) {
        console.error('Failed to load participants:', err);
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--error-text);">Failed to load data</td></tr>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * StockPilot (AURUM OS) - Haute Joaillerie Management System
 * Interactive Client Logic, Role-Based Access Control, Real-Time Calculations & USB Scale Simulator
 */

// --- Global State ---
const state = {
  theme: 'dark',
  locale: 'en',
  userRole: 'ADMIN', // 'ADMIN' or 'EMPLOYEE'
  activeView: 'dashboard',
  base24kRate: 3420.00,
  taxRateOnMaking: 0.14,
  scaleWeight: 0.000,
  cart: [],
  tradeIns: [],
  discount: 0.0,
  currentKaratFilter: 'ALL',
  searchQuery: '',

  // Role profiles
  users: {
    ADMIN: {
      name: "Mona Al-Sayed",
      name_ar: "منى السيد",
      title: "Shop Owner & Vault Master",
      title_ar: "مالك المتجر ومدير الخزينة",
      avatar: "MA",
      roleLabel: "ADMIN",
      canViewFinancials: true,
      canUpdateGoldEngine: true
    },
    EMPLOYEE: {
      name: "Tariq Al-Fahim",
      name_ar: "طارق الفهيم",
      title: "Senior Appraiser / Cashier",
      title_ar: "كبير مثمني الذهب / أمين الصندوق",
      avatar: "TF",
      roleLabel: "EMPLOYEE",
      canViewFinancials: false,
      canUpdateGoldEngine: false
    }
  },

  // Vault Inventory Items matching Figma
  inventory: [
    {
      id: "prod-1",
      sku: "AUR-7841-SOL",
      name: "Aethelred Solitaire Royale",
      name_ar: "خاتم سوليتير أثيلريد الملكي 18 قيراط",
      category: "rings",
      karat: "18K",
      gross_wt: 14.82,
      stone_tare: 2.72,
      net_gold: 12.10,
      making_fee: 450.00,
      hallmark: "18K • 750 (EPC-E280-0019)",
      image: "assets/images/diamond_solitaire_ring_1792597878725.jpg",
      status: "IN_STOCK"
    },
    {
      id: "prod-2",
      sku: "AUR-9904",
      name: "Vendôme Floral Choker",
      name_ar: "طوق فاندوم الزهري عيار 21",
      category: "necklaces",
      karat: "21K",
      gross_wt: 38.40,
      stone_tare: 0.00,
      net_gold: 38.40,
      making_fee: 280.00,
      hallmark: "21K • 875 EGYPTIAN STANDARD",
      image: "assets/images/byzantine_gold_choker_1792598803717.jpg",
      status: "IN_STOCK"
    },
    {
      id: "prod-3",
      sku: "AUR-7731",
      name: "Nile Royal Bangle Pair",
      name_ar: "زوج أساور النيل الملكية عيار 21",
      category: "bangles",
      karat: "21K",
      gross_wt: 54.20,
      stone_tare: 0.00,
      net_gold: 54.20,
      making_fee: 190.00,
      hallmark: "21K • 875 CAIRO HALLMARK",
      image: "assets/images/cleopatra_gold_cuff_1792598857432.jpg",
      status: "IN_STOCK"
    },
    {
      id: "prod-4",
      sku: "AUR-2401",
      name: "PAMP Suisse Fine Ingot 50g",
      name_ar: "سبيكة بامب سويسرا 50 جرام عيار 24",
      category: "bullion",
      karat: "24K",
      gross_wt: 50.00,
      stone_tare: 0.00,
      net_gold: 50.00,
      making_fee: 65.00,
      hallmark: "999.9 ESSAYEUR FONDEUR",
      image: "assets/images/gold_bullion_sovereign_1792598760193.jpg",
      status: "IN_STOCK"
    },
    {
      id: "prod-5",
      sku: "21K-RN-092",
      name: "Royal Damascene Ring",
      name_ar: "خاتم دمشقي أثري منقوش عيار 21",
      category: "rings",
      karat: "21K",
      gross_wt: 6.80,
      stone_tare: 0.00,
      net_gold: 6.80,
      making_fee: 180.00,
      hallmark: "21K • 875 KHAN EL-KHALILI",
      image: "assets/images/damascene_gold_ring_1792598690682.jpg",
      status: "IN_STOCK"
    },
    {
      id: "prod-6",
      sku: "24K-COIN-08",
      name: "George Sovereign Bullion",
      name_ar: "جنيه جورج ذهب إنجليزي عيار 24",
      category: "bullion",
      karat: "24K",
      gross_wt: 8.00,
      stone_tare: 0.00,
      net_gold: 8.00,
      making_fee: 45.00,
      hallmark: "ROYAL MINT SOVEREIGN 999.9",
      image: "assets/images/gold_bullion_sovereign_1792598760193.jpg",
      status: "IN_STOCK"
    }
  ],

  // Live Audit Logs
  auditLogs: [
    {
      timestamp: "2026-10-21 20:30 UTC",
      user: "Mona Al-Sayed",
      action: "RECALIBRATE_GOLD_RATES",
      entity: "GoldPrice",
      details: "Master 24K spot rate set to 3,420.00 EGP/g"
    },
    {
      timestamp: "2026-10-21 20:15 UTC",
      user: "Tariq Al-Fahim",
      action: "COMPLETE_SALE",
      entity: "Sale (INV-2026-1082)",
      details: "Issued invoice for 45,951.76 EGP with scrap deduction"
    },
    {
      timestamp: "2026-10-21 19:40 UTC",
      user: "Mona Al-Sayed",
      action: "BULK_REPRICE",
      entity: "Inventory",
      details: "Recalculated valuation for 3,842 jewelry pieces"
    }
  ]
};

// --- Karat Ratios ---
const KARAT_RATIOS = {
  '24K': 1.0,
  '22K': 22 / 24,
  '21K': 21 / 24,
  '18K': 18 / 24,
  '14K': 14 / 24
};

function getKaratRate(karat) {
  const ratio = KARAT_RATIOS[karat] || 1.0;
  return Math.round((state.base24kRate * ratio) * 100) / 100;
}

function getItemPrice(item) {
  const rate = getKaratRate(item.karat);
  const metalVal = item.net_gold * rate;
  const makingVal = item.gross_wt * item.making_fee;
  return Math.round(metalVal + makingVal);
}

// --- Bilingual Dictionaries ---
const I18N = {
  en: {
    dashboard: "Dashboard",
    inventory: "Inventory Vault",
    pos: "POS Counter",
    gold_engine: "Gold Engine",
    purchases: "Purchases",
    customers: "Customers & Returns",
    reports: "Analytics & Reports",
    vault_status: "VAULT STATUS: SECURE • 999.9",
    total_valuation: "VAULT TOTAL VALUATION",
    todays_sales: "TODAY'S POS SALES",
    realized_margin: "REALIZED MARGIN & FEES",
    active_pieces: "ACTIVE ATELIER PIECES",
    search_placeholder: "Search SKU, Barcode, Client... (Ctrl+K)",
    add_to_cart: "Add to Cart",
    cart_registry: "Cart Registry",
    checkout: "Complete Sale & Issue ETA Invoice",
    net_payable: "NET PAYABLE TOTAL",
    making_charges: "Making Charges (Fabrique)",
    subtotal: "Gross Goods Subtotal",
    tax_eta: "ETA Statutory Sales Tax (14% on Making)",
    scrap_trade_in: "+ Gold Scrap / Trade-In",
    customer_tier: "VIP Tier 1",
    add_piece: "+ Add New Jewelry Piece"
  },
  ar: {
    dashboard: "لوحة التحكم",
    inventory: "خزينة المخزون",
    pos: "نقطة البيع (الكاونتر)",
    gold_engine: "محرك تسعير الذهب",
    purchases: "المشتريات والموردين",
    customers: "العملاء والمرتجعات",
    reports: "التقارير والأرباح",
    vault_status: "حالة الخزينة: مؤمنة • 999.9",
    total_valuation: "إجمالي تقييم الخزينة",
    todays_sales: "مبيعات الكاونتر اليوم",
    realized_margin: "هامش الربح والمصنعية المحققة",
    active_pieces: "قطع تحت التصنيع بالورشة",
    search_placeholder: "بحث بالكود، الباركود، العميل... (Ctrl+K)",
    add_to_cart: "إضافة إلى الفاتورة",
    cart_registry: "بيان الفاتورة الحالية",
    checkout: "إتمام البيع وإصدار الفاتورة الضريبية",
    net_payable: "صافي المبلغ المستحق",
    making_charges: "إجمالي أجور المصنعية",
    subtotal: "إجمالي قيمة المصوغات",
    tax_eta: "ضريبة القيمة المضافة (14% على المصنعية)",
    scrap_trade_in: "+ إضافة كسر دهب (استبدال)",
    customer_tier: "عميل مميز فئة أولى",
    add_piece: "+ إضافة قطعة مجوهرات جديدة"
  }
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupMobileDrawer();
  setupThemeToggle();
  setupLocaleToggle();
  setupRoleToggle();
  setupGoldEngine();
  setupSearch();
  setupModals();
  applyRolePermissions();
  renderInventoryTable();
  renderPOSCatalog();
  renderAuditTable();
  updateCartUI();
  updateTickerDisplay();
});

// --- Toast Notification Helper ---
window.showToast = function(message, type = 'info', icon = '✨') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div style="flex:1;">${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
};

// --- Modal Helpers ---
window.closeModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
};

window.openNewPieceModal = function() {
  document.getElementById('new-piece-modal')?.classList.add('active');
};

window.openCustomerModal = function() {
  document.getElementById('new-customer-modal')?.classList.add('active');
};

window.openSupplierModal = function() {
  document.getElementById('supplier-modal')?.classList.add('active');
};

window.openStaffModal = function() {
  if (state.userRole !== 'ADMIN') {
    showToast("Access Denied: Only Admin / Shop Owner can manage staff accounts.", "warning", "🔒");
    return;
  }
  document.getElementById('new-staff-modal')?.classList.add('active');
};

// --- Role-Based Access Control (Admin vs Employee Dashboard) ---
function setupRoleToggle() {
  const btn = document.getElementById('role-toggle-btn');
  if (!btn) return;
  btn.addEventListener('click', toggleUserRole);
}

window.toggleUserRole = function() {
  state.userRole = state.userRole === 'ADMIN' ? 'EMPLOYEE' : 'ADMIN';
  applyRolePermissions();
};

function applyRolePermissions() {
  const isAr = state.locale === 'ar';
  const u = state.users[state.userRole];

  // Header Role Label
  const roleLabel = document.getElementById('current-role-label');
  if (roleLabel) {
    roleLabel.innerText = u.roleLabel;
    roleLabel.style.color = state.userRole === 'ADMIN' ? 'var(--gold-primary)' : 'var(--emerald-live)';
  }

  // Header User Profile
  const nameEl = document.getElementById('user-display-name');
  const titleEl = document.getElementById('user-display-title');
  const avatarEl = document.getElementById('user-avatar-badge');

  if (nameEl) nameEl.innerText = isAr ? u.name_ar : u.name;
  if (titleEl) titleEl.innerText = isAr ? u.title_ar : u.title;
  if (avatarEl) avatarEl.innerText = u.avatar;

  // Governance & Admin-Only Views in Sidebar
  document.querySelectorAll('.admin-only-feature').forEach(el => {
    el.style.display = state.userRole === 'ADMIN' ? '' : 'none';
  });

  // Sensitive Financial Metric Cards
  const vaultValEl = document.getElementById('metric-vault-val');
  const marginValEl = document.getElementById('metric-margin-val');

  if (state.userRole === 'ADMIN') {
    if (vaultValEl) vaultValEl.innerHTML = '42,650,800 <small>EGP</small>';
    if (marginValEl) marginValEl.innerHTML = '86,400 <small>EGP</small>';
  } else {
    // Mask sensitive financial cards for Employee
    if (vaultValEl) vaultValEl.innerHTML = '<span class="confidential-badge">🔒 CONFIDENTIAL [ADMIN]</span>';
    if (marginValEl) marginValEl.innerHTML = '<span class="confidential-badge">🔒 RESTRICTED [OWNER]</span>';
  }

  // Dashboard Greeting Customization
  const dashTitle = document.getElementById('dash-greeting-title');
  const dashSub = document.getElementById('dash-greeting-subtitle');

  if (state.userRole === 'ADMIN') {
    if (dashTitle) dashTitle.innerText = isAr ? "لوحة المالك والمدير العام • خزينة ميزون دور" : "Maison D'Or Atelier Overview";
    if (dashSub) dashSub.innerText = isAr ? "تقييم الخزينة في الوقت الفعلي، تسوية مصوغات الذهب وأرباح المصنعية IFRS." : "Real-time appraisal, automated assay reconciliation, and high-frequency bullion trading matrix.";
  } else {
    if (dashTitle) dashTitle.innerText = isAr ? "كاونتر المبيعات ونقطة البيع • الوردية النشطة" : "POS Counter Terminal & Floor Registry";
    if (dashSub) dashSub.innerText = isAr ? "محطة الصندوق رقم 04 • تفعيل الميزان الإلكتروني وفحص كسر الذهب وإصدار الفواتير." : "Cashier Workstation #04 • Ready for live customer transactions, digital scale weighing & scrap trade-ins.";
  }

  // Gold Engine Permissions
  const geInput = document.getElementById('ge-base-24k');
  const geBtn = document.getElementById('btn-update-global-rate');
  if (geInput && geBtn) {
    if (state.userRole === 'ADMIN') {
      geInput.removeAttribute('readonly');
      geInput.style.opacity = '1';
      geBtn.removeAttribute('disabled');
      geBtn.innerText = isAr ? "تحديث سعر الذهب وإعادة الحساب" : "Recalibrate Spot & Reprice Vault";
    } else {
      geInput.setAttribute('readonly', 'true');
      geInput.style.opacity = '0.7';
      geBtn.setAttribute('disabled', 'true');
      geBtn.innerText = isAr ? "🔒 التعديل مقتصر على المدير" : "🔒 Rate Updates Restricted to Admin";
    }
  }

  // Redirect if employee is currently looking at admin-only view
  if (state.userRole === 'EMPLOYEE' && ['reports', 'employees', 'audit'].includes(state.activeView)) {
    switchToView('pos');
  }

  // Toast feedback
  if (state.userRole === 'ADMIN') {
    showToast("Switched to Admin Role (Mona Al-Sayed) — Full vault financials & governance unlocked", "info", "👑");
  } else {
    showToast("Switched to Employee Role (Tariq Al-Fahim) — POS counter active, confidential margins masked", "success", "👤");
  }
}

// --- View Switching ---
window.switchToView = function(viewName) {
  // Guard admin views
  if (state.userRole === 'EMPLOYEE' && ['reports', 'employees', 'audit'].includes(viewName)) {
    showToast("Access Denied: This view requires Admin / Shop Owner security clearance.", "warning", "🔒");
    return;
  }

  state.activeView = viewName;

  // Update desktop sidebar items
  document.querySelectorAll('.nav-item').forEach(item => {
    const btn = item.querySelector('button');
    if (btn && btn.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Update mobile bottom taskbar items
  document.querySelectorAll('.mobile-taskbar-btn').forEach(btn => {
    if (btn.getAttribute('onclick')?.includes(viewName)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Switch visible container
  document.querySelectorAll('.view-container').forEach(view => {
    view.classList.remove('active');
  });
  const activeContainer = document.getElementById(`view-${viewName}`);
  if (activeContainer) {
    activeContainer.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  closeMobileSidebar();
};

function setupNavigation() {
  document.querySelectorAll('.nav-item button').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-view');
      switchToView(target);
    });
  });
}

// --- Mobile Drawer Handlers ---
function setupMobileDrawer() {
  const hamburgerBtn = document.getElementById('mobile-hamburger-btn');
  const sidebar = document.getElementById('app-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const closeBtn = document.getElementById('close-mobile-sidebar-btn');

  if (hamburgerBtn && sidebar && backdrop) {
    hamburgerBtn.addEventListener('click', () => {
      sidebar.classList.add('mobile-open');
      backdrop.classList.add('active');
      if (closeBtn) closeBtn.style.display = 'block';
    });

    backdrop.addEventListener('click', closeMobileSidebar);
    if (closeBtn) closeBtn.addEventListener('click', closeMobileSidebar);
  }
}

function closeMobileSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const closeBtn = document.getElementById('close-mobile-sidebar-btn');
  if (sidebar) sidebar.classList.remove('mobile-open');
  if (backdrop) backdrop.classList.remove('active');
  if (closeBtn) closeBtn.style.display = 'none';
}

// --- Theme Management ---
function setupThemeToggle() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    
    const brandTitle = document.getElementById('brand-title-text');
    const brandSub = document.getElementById('brand-subtitle-text');
    if (state.theme === 'light') {
      if (brandTitle) brandTitle.innerHTML = 'StockPilot <span>PRO</span>';
      if (brandSub) brandSub.innerText = "Maison D'Or • Branch 01";
    } else {
      if (brandTitle) brandTitle.innerHTML = 'AURUM <span>OS</span>';
      if (brandSub) brandSub.innerText = 'Haute Joaillerie POS';
    }
  });
}

// --- Locale / Language Toggle ---
function setupLocaleToggle() {
  const btn = document.getElementById('lang-toggle-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    state.locale = state.locale === 'en' ? 'ar' : 'en';
    document.documentElement.setAttribute('dir', state.locale === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', state.locale);
    btn.innerText = state.locale === 'ar' ? 'English (LTR)' : 'عربي (RTL)';
    applyTranslations();
    applyRolePermissions();
  });
}

function applyTranslations() {
  const t = I18N[state.locale];
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.innerText = t[key];
  });
  renderInventoryTable();
  renderPOSCatalog();
}

// --- Live Digital Scale Simulator (Mettler Toledo USB) ---
window.simulateMettlerScale = function() {
  const authenticWeights = [14.825, 21.450, 38.410, 54.205, 6.802, 8.000, 50.000, 18.250, 31.740];
  const picked = authenticWeights[Math.floor(Math.random() * authenticWeights.length)];
  state.scaleWeight = picked;

  const displayEl = document.getElementById('scale-live-display');
  if (displayEl) {
    displayEl.innerText = `${picked.toFixed(3)}g`;
    displayEl.classList.add('scale-pulse');
    setTimeout(() => displayEl.classList.remove('scale-pulse'), 2500);
  }

  showToast(`⚖ Mettler Toledo USB Scale: ${picked.toFixed(3)}g captured (Assay Calibrated)`, "success", "⚖");
};

window.transferScaleToScrap = function() {
  if (state.scaleWeight <= 0) {
    simulateMettlerScale();
  }
  const input = document.getElementById('scrap-weight');
  if (input) {
    input.value = state.scaleWeight.toFixed(2);
    showToast(`Transferred ${state.scaleWeight.toFixed(2)}g from USB scale to Scrap Form!`, "info", "📥");
  }
};

// --- Karat Filter Chips ---
window.setKaratFilter = function(karat) {
  state.currentKaratFilter = karat;

  // Update active chip classes in both views
  document.querySelectorAll('#inventory-karat-filters .filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(`'${karat}'`));
  });
  document.querySelectorAll('#pos-karat-filters .filter-chip').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('onclick')?.includes(`'${karat}'`));
  });

  renderInventoryTable();
  renderPOSCatalog();
};

// --- Live Search ---
function setupSearch() {
  const searchInput = document.querySelector('.header-search input');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.trim().toLowerCase();
    renderInventoryTable();
    renderPOSCatalog();
  });
}

function getFilteredInventory() {
  return state.inventory.filter(item => {
    // Karat match
    if (state.currentKaratFilter !== 'ALL' && item.karat !== state.currentKaratFilter) {
      return false;
    }
    // Search query match
    if (state.searchQuery) {
      const q = state.searchQuery;
      const matchSku = item.sku.toLowerCase().includes(q);
      const matchName = item.name.toLowerCase().includes(q);
      const matchNameAr = item.name_ar ? item.name_ar.toLowerCase().includes(q) : false;
      const matchKarat = item.karat.toLowerCase().includes(q);
      const matchCategory = item.category.toLowerCase().includes(q);
      return matchSku || matchName || matchNameAr || matchKarat || matchCategory;
    }
    return true;
  });
}

// --- Live Ticker & Gold Engine ---
function updateTickerDisplay() {
  const r24 = state.base24kRate;
  const r21 = getKaratRate('21K');
  const r18 = getKaratRate('18K');

  const el24 = document.getElementById('ticker-24k');
  const el21 = document.getElementById('ticker-21k');
  const el18 = document.getElementById('ticker-18k');

  if (el24) el24.innerText = `${r24.toLocaleString()} EGP/g`;
  if (el21) el21.innerText = `${r21.toLocaleString()} EGP/g`;
  if (el18) el18.innerText = `${r18.toLocaleString()} EGP/g`;

  const ge24Input = document.getElementById('ge-base-24k');
  if (ge24Input && state.userRole === 'ADMIN') ge24Input.value = r24.toFixed(2);

  const ge22 = document.getElementById('ge-rate-22k');
  const ge21 = document.getElementById('ge-rate-21k');
  const ge18 = document.getElementById('ge-rate-18k');
  const ge14 = document.getElementById('ge-rate-14k');

  if (ge22) ge22.innerText = `${getKaratRate('22K').toLocaleString()} EGP`;
  if (ge21) ge21.innerText = `${getKaratRate('21K').toLocaleString()} EGP`;
  if (ge18) ge18.innerText = `${getKaratRate('18K').toLocaleString()} EGP`;
  if (ge14) ge14.innerText = `${getKaratRate('14K').toLocaleString()} EGP`;
}

function setupGoldEngine() {
  const btn = document.getElementById('btn-update-global-rate');
  if (!btn) return;
  btn.addEventListener('click', () => {
    if (state.userRole !== 'ADMIN') {
      showToast("Unauthorized: Only Admin / Owner can alter master gold rate.", "warning", "🔒");
      return;
    }
    const input = document.getElementById('ge-base-24k');
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0) {
      state.base24kRate = val;
      updateTickerDisplay();
      renderInventoryTable();
      renderPOSCatalog();
      updateCartUI();
      
      logAuditAction("RECALIBRATE_GOLD_RATES", "GoldPrice", `Master 24K updated to ${val.toFixed(2)} EGP/g`);
      showToast(`Master 24K spot gold rate updated to ${val} EGP/g. All jewelry pieces repriced!`, "success", "✨");
    }
  });
}

// --- Inventory Table Rendering ---
function renderInventoryTable() {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;

  const isAr = state.locale === 'ar';
  const filtered = getFilteredInventory();
  tbody.innerHTML = '';

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-muted);">No jewelry pieces match current filter criteria.</td></tr>`;
    return;
  }

  filtered.forEach(item => {
    const price = getItemPrice(item);
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.innerHTML = `
      <td>
        <div style="display:flex; align-items:center; gap:0.75rem;">
          <img src="${item.image}" style="width:40px; height:40px; border-radius:4px; object-fit:cover;" alt="${item.name}">
          <div>
            <div style="font-weight:700;">${isAr ? item.name_ar : item.name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${item.sku}</div>
          </div>
        </div>
      </td>
      <td><span class="karat-badge" style="position:static;">${item.karat}</span></td>
      <td><strong>${item.gross_wt.toFixed(2)}g</strong></td>
      <td style="color:var(--text-muted);">${item.stone_tare.toFixed(2)}g</td>
      <td style="color:var(--gold-primary); font-weight:700;">${item.net_gold.toFixed(2)}g</td>
      <td>${item.making_fee} EGP/g</td>
      <td><strong style="color:var(--gold-primary); font-size:1rem;">${price.toLocaleString()} EGP</strong></td>
      <td>
        <button class="btn btn-secondary" style="padding:0.35rem 0.65rem; font-size:0.75rem;" onclick="addToCart('${item.id}')">
          ${isAr ? 'بيع' : 'POS'}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// --- POS Catalog Rendering ---
function renderPOSCatalog() {
  const grid = document.getElementById('pos-product-grid');
  if (!grid) return;

  const isAr = state.locale === 'ar';
  const filtered = getFilteredInventory();
  grid.innerHTML = '';

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted);">No items found in POS catalog.</div>`;
    return;
  }

  filtered.forEach(item => {
    const price = getItemPrice(item);
    const card = document.createElement('div');
    card.className = 'jewelry-card';
    card.innerHTML = `
      <div class="jewelry-thumb">
        <img src="${item.image}" alt="${item.name}">
        <span class="karat-badge">${item.karat}</span>
        <span class="weight-badge">${item.gross_wt.toFixed(2)}g</span>
      </div>
      <div class="jewelry-details">
        <div class="jewelry-name">${isAr ? item.name_ar : item.name}</div>
        <div class="jewelry-sku">${item.sku} • Fee: ${item.making_fee} EGP/g</div>
        <div class="jewelry-price-row">
          <div class="price-tag">${price.toLocaleString()} <small>EGP</small></div>
          <button class="btn btn-primary" style="padding:0.4rem 0.75rem; font-size:0.8rem;" onclick="addToCart('${item.id}')">
            ${isAr ? '+ أضف' : '+ Add'}
          </button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

// --- Cart Operations ---
window.addToCart = function(productId) {
  const item = state.inventory.find(p => p.id === productId);
  if (!item) return;

  if (item.status === 'SOLD') {
    showToast("This unique master piece has already been sold!", "warning", "⚠️");
    return;
  }

  const exists = state.cart.find(c => c.id === item.id);
  if (exists) {
    showToast("Unique item is already in the transaction cart.", "info", "ℹ️");
    return;
  }

  state.cart.push(item);
  updateCartUI();
  switchToView('pos');
  showToast(`Added ${item.name} (${item.karat}) to cart`, "success", "🛒");
};

window.removeFromCart = function(index) {
  state.cart.splice(index, 1);
  updateCartUI();
};

window.addScrapTradeIn = function(karat, grossWt, ratePerG) {
  state.tradeIns.push({
    karat,
    gross_wt: parseFloat(grossWt),
    rate_per_g: parseFloat(ratePerG),
    credit: parseFloat(grossWt) * parseFloat(ratePerG)
  });
  updateCartUI();
  showToast(`Applied scrap trade-in credit: ${grossWt}g of ${karat}`, "success", "♻");
};

window.removeTradeIn = function(index) {
  state.tradeIns.splice(index, 1);
  updateCartUI();
};

function updateCartUI() {
  const container = document.getElementById('cart-items-container');
  const countBadge = document.getElementById('cart-item-count');
  if (countBadge) countBadge.innerText = `${state.cart.length} items`;

  if (!container) return;
  container.innerHTML = '';

  let totalNetGold = 0.0;
  let totalMetalVal = 0.0;
  let totalMaking = 0.0;

  state.cart.forEach((item, idx) => {
    const rate = getKaratRate(item.karat);
    const metalVal = item.net_gold * rate;
    const makingVal = item.gross_wt * item.making_fee;
    const itemTotal = metalVal + makingVal;

    totalNetGold += item.net_gold;
    totalMetalVal += metalVal;
    totalMaking += makingVal;

    const row = document.createElement('div');
    row.className = 'cart-item-row';
    row.innerHTML = `
      <div>
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-sub">${item.karat} • NW: ${item.net_gold.toFixed(2)}g • Making: ${makingVal.toLocaleString()} EGP</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700; color:var(--gold-primary);">${itemTotal.toLocaleString()} EGP</div>
        <button style="background:none; border:none; color:var(--ruby-alert); cursor:pointer; font-size:0.75rem;" onclick="removeFromCart(${idx})">✕ Remove</button>
      </div>
    `;
    container.appendChild(row);
  });

  // Render Scrap Trade-in deductions
  let totalScrapCredit = 0.0;
  state.tradeIns.forEach((t, idx) => {
    totalScrapCredit += t.credit;
    const scrapRow = document.createElement('div');
    scrapRow.className = 'cart-item-row';
    scrapRow.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    scrapRow.innerHTML = `
      <div>
        <div class="cart-item-name" style="color:var(--emerald-live);">♻ Scrap Trade-in (${t.karat})</div>
        <div class="cart-item-sub">${t.gross_wt.toFixed(2)}g @ ${t.rate_per_g} EGP/g</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700; color:var(--emerald-live);">- ${t.credit.toLocaleString()} EGP</div>
        <button style="background:none; border:none; color:var(--ruby-alert); cursor:pointer; font-size:0.75rem;" onclick="removeTradeIn(${idx})">✕</button>
      </div>
    `;
    container.appendChild(scrapRow);
  });

  const grossSubtotal = totalMetalVal + totalMaking;
  // Egyptian ETA Tax Rule: 14% VAT strictly on making fee
  const statutoryVat = Math.round((totalMaking * state.taxRateOnMaking) * 100) / 100;
  const netPayable = Math.max(0, grossSubtotal - totalScrapCredit + statutoryVat - state.discount);

  // Update Summary DOM
  const netGoldEl = document.getElementById('calc-net-gold');
  const metalValEl = document.getElementById('calc-metal-val');
  const makingValEl = document.getElementById('calc-making-val');
  const subtotalEl = document.getElementById('calc-subtotal');
  const scrapValEl = document.getElementById('calc-scrap-val');
  const vatValEl = document.getElementById('calc-vat-val');
  const totalValEl = document.getElementById('calc-total-val');

  if (netGoldEl) netGoldEl.innerText = `${totalNetGold.toFixed(2)} g`;
  if (metalValEl) metalValEl.innerText = `${Math.round(totalMetalVal).toLocaleString()} EGP`;
  if (makingValEl) makingValEl.innerText = `+ ${Math.round(totalMaking).toLocaleString()} EGP`;
  if (subtotalEl) subtotalEl.innerText = `${Math.round(grossSubtotal).toLocaleString()} EGP`;
  if (scrapValEl) scrapValEl.innerText = `- ${Math.round(totalScrapCredit).toLocaleString()} EGP`;
  if (vatValEl) vatValEl.innerText = `+ ${statutoryVat.toLocaleString()} EGP`;
  if (totalValEl) totalValEl.innerText = `${Math.round(netPayable).toLocaleString()} EGP`;
}

// --- Modals & Actions Setup ---
function setupModals() {
  // Scrap modal
  const btnScrap = document.getElementById('btn-open-scrap-modal');
  const modalScrap = document.getElementById('scrap-modal');
  const closeScrap = document.getElementById('close-scrap-modal');
  const applyScrap = document.getElementById('apply-scrap-tradein');

  if (btnScrap && modalScrap) {
    btnScrap.addEventListener('click', () => modalScrap.classList.add('active'));
    closeScrap?.addEventListener('click', () => modalScrap.classList.remove('active'));
    applyScrap?.addEventListener('click', () => {
      const karat = document.getElementById('scrap-karat').value;
      const wt = parseFloat(document.getElementById('scrap-weight').value);
      const rate = parseFloat(document.getElementById('scrap-rate').value);
      if (wt > 0 && rate > 0) {
        addScrapTradeIn(karat, wt, rate);
        modalScrap.classList.remove('active');
      }
    });
  }

  // Invoice Checkout Button
  const btnCheckout = document.getElementById('btn-complete-checkout');
  const modalInvoice = document.getElementById('invoice-modal');
  const closeInvoice = document.getElementById('close-invoice-modal');

  if (btnCheckout && modalInvoice) {
    btnCheckout.addEventListener('click', () => {
      if (state.cart.length === 0) {
        showToast("Cart is empty! Add jewelry items first.", "warning", "⚠️");
        return;
      }
      populateInvoiceModal();
      modalInvoice.classList.add('active');
    });
    closeInvoice?.addEventListener('click', () => {
      modalInvoice.classList.remove('active');
      // Mark as sold and clear cart
      const invNo = document.getElementById('inv-modal-number').innerText;
      logAuditAction("COMPLETE_SALE", `Sale (${invNo})`, `Checked out ${state.cart.length} items by ${state.users[state.userRole].name}`);
      state.cart = [];
      state.tradeIns = [];
      updateCartUI();
      showToast(`Sale finalized & archived to audit ledger. Official receipt issued!`, "success", "🧾");
    });
  }
}

function populateInvoiceModal() {
  const invNo = `INV-2026-${Math.floor(1000 + Math.random() * 9000)}`;
  document.getElementById('inv-modal-number').innerText = invNo;
  document.getElementById('inv-modal-date').innerText = new Date().toLocaleString();

  const tbody = document.getElementById('inv-modal-items-tbody');
  tbody.innerHTML = '';

  state.cart.forEach(item => {
    const rate = getKaratRate(item.karat);
    const metalVal = item.net_gold * rate;
    const makingVal = item.gross_wt * item.making_fee;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.name} (${item.sku})</td>
      <td>${item.karat}</td>
      <td>${item.gross_wt.toFixed(2)}g</td>
      <td>${item.net_gold.toFixed(2)}g</td>
      <td>${Math.round(metalVal + makingVal).toLocaleString()} EGP</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('inv-modal-total').innerText = document.getElementById('calc-total-val').innerText;
}

// --- Ingest New Jewelry Piece Form Handler ---
window.handleAddNewPiece = function(e) {
  e.preventDefault();

  const nameEn = document.getElementById('piece-name-en').value.trim();
  const nameAr = document.getElementById('piece-name-ar').value.trim();
  const sku = document.getElementById('piece-sku').value.trim().toUpperCase();
  const karat = document.getElementById('piece-karat').value;
  const grossWt = parseFloat(document.getElementById('piece-gross-wt').value);
  const stoneTare = parseFloat(document.getElementById('piece-stone-tare').value) || 0.0;
  const makingFee = parseFloat(document.getElementById('piece-making-fee').value);
  const category = document.getElementById('piece-category').value;

  if (grossWt <= 0 || grossWt <= stoneTare) {
    showToast("Invalid weights: Gross weight must exceed stone tare.", "warning", "⚠️");
    return;
  }

  const netGold = Math.round((grossWt - stoneTare) * 100) / 100;

  // Pick suitable category image
  const defaultImages = {
    rings: "assets/images/diamond_solitaire_ring_1792597878725.jpg",
    necklaces: "assets/images/byzantine_gold_choker_1792598803717.jpg",
    bangles: "assets/images/cleopatra_gold_cuff_1792598857432.jpg",
    bullion: "assets/images/gold_bullion_sovereign_1792598760193.jpg",
    earrings: "assets/images/damascene_gold_ring_1792598690682.jpg"
  };

  const newPiece = {
    id: `prod-${Date.now()}`,
    sku: sku,
    name: nameEn,
    name_ar: nameAr,
    category: category,
    karat: karat,
    gross_wt: grossWt,
    stone_tare: stoneTare,
    net_gold: netGold,
    making_fee: makingFee,
    hallmark: `${karat} • OFFICIAL CAIRO ASSAY`,
    image: defaultImages[category] || defaultImages.rings,
    status: "IN_STOCK"
  };

  state.inventory.unshift(newPiece);
  renderInventoryTable();
  renderPOSCatalog();
  closeModal('new-piece-modal');
  e.target.reset();

  logAuditAction("INGEST_VAULT_ITEM", `Piece (${sku})`, `Added ${nameEn} (${karat}, ${grossWt}g) to vault`);
  showToast(`Successfully registered ${nameEn} (${sku}) into physical custody vault!`, "success", "✨");
};

// --- Customer CRM Registration Handler ---
window.handleAddNewCustomer = function(e) {
  e.preventDefault();
  const name = document.getElementById('cust-name').value.trim();
  const phone = document.getElementById('cust-phone').value.trim();
  const tier = document.getElementById('cust-tier').value;

  const tableBody = document.querySelector('#view-customers tbody');
  if (tableBody) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${name}</strong></td>
      <td>${phone}</td>
      <td><span style="color:var(--gold-primary); font-weight:700;">${tier}</span></td>
      <td><strong>500 pts</strong></td>
      <td style="color:var(--gold-primary); font-weight:700;">0 EGP</td>
      <td><button class="btn btn-secondary" style="padding:0.35rem 0.65rem; font-size:0.75rem;" onclick="switchToView('pos')">New Sale</button></td>
    `;
    tableBody.prepend(tr);
  }

  closeModal('new-customer-modal');
  e.target.reset();
  logAuditAction("REGISTER_CUSTOMER", `Client (${name})`, `Registered new VIP profile with tier ${tier}`);
  showToast(`Client ${name} registered in Maison CRM with tier ${tier}!`, "success", "👤");
};

// --- Wholesale Bullion Inflow Handler ---
window.handleSupplierInflow = function(e) {
  e.preventDefault();
  const vendor = document.getElementById('supp-vendor').value;
  const karat = document.getElementById('supp-karat').value;
  const wt = parseFloat(document.getElementById('supp-weight').value);
  const val = parseFloat(document.getElementById('supp-value').value);

  closeModal('supplier-modal');
  e.target.reset();
  logAuditAction("SUPPLIER_INFLOW", `Supplier (${vendor})`, `Ingested ${wt}g of ${karat} bullion valued at ${val.toLocaleString()} EGP`);
  showToast(`Bullion Shipment Inflow: ${wt}g (${karat}) credited from ${vendor}!`, "success", "🚚");
};

// --- Staff Account Creation Handler ---
window.handleAddStaff = function(e) {
  e.preventDefault();
  const name = document.getElementById('staff-name').value.trim();
  const email = document.getElementById('staff-email').value.trim();
  const role = document.getElementById('staff-role').value;
  const terminal = document.getElementById('staff-terminal').value.trim();

  const tbody = document.querySelector('#view-employees tbody');
  if (tbody) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${name}</strong></td>
      <td>${email}</td>
      <td><span>👤 ${role}</span></td>
      <td>${terminal}</td>
      <td><span class="metric-badge">ACTIVE</span></td>
      <td>POS Transactions & Scale Access</td>
    `;
    tbody.prepend(tr);
  }

  closeModal('new-staff-modal');
  e.target.reset();
  logAuditAction("CREATE_STAFF_ACCOUNT", `User (${email})`, `Provisioned role ${role} on ${terminal}`);
  showToast(`Employee account created for ${name} (${email}) with terminal ${terminal}`, "success", "🛡");
};

// --- Stock Count Audit Simulator ---
window.simulateStockAudit = function() {
  showToast("Scanning 3,842 serialized RFID tags & calibrating hydrostatic weights...", "info", "🔍");
  setTimeout(() => {
    showToast("Audit Complete: 100% assay match. Zero unverified gold scrap detected.", "success", "✅");
    logAuditAction("PHYSICAL_STOCK_AUDIT", "Custody Vault", "Completed 100% RFID & scale stock audit match");
  }, 1200);
};

// --- Audit Trail Logging ---
function logAuditAction(action, entity, details) {
  const newLog = {
    timestamp: new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC',
    user: state.users[state.userRole].name,
    action: action,
    entity: entity,
    details: details
  };
  state.auditLogs.unshift(newLog);
  renderAuditTable();
}

function renderAuditTable() {
  const tbody = document.getElementById('audit-log-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  state.auditLogs.slice(0, 15).forEach(log => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${log.timestamp}</td>
      <td><strong>${log.user}</strong></td>
      <td><strong style="color:var(--gold-primary);">${log.action}</strong></td>
      <td>${log.entity}</td>
      <td>${log.details}</td>
    `;
    tbody.appendChild(tr);
  });
}

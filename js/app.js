/**
 * StockPilot (AURUM OS) - Haute Joaillerie Management System
 * Interactive Client Logic & Real-Time Calculation Engine
 */

// --- Global State ---
const state = {
  theme: 'dark',
  locale: 'en',
  activeView: 'dashboard',
  base24kRate: 3420.00,
  taxRateOnMaking: 0.14,
  scaleWeight: 0.000,
  cart: [],
  tradeIns: [],
  discount: 0.0,
  currentKaratFilter: 'ALL',
  
  // Real inventory items matching Figma
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
  setupThemeToggle();
  setupLocaleToggle();
  setupGoldEngine();
  renderInventoryTable();
  renderPOSCatalog();
  updateCartUI();
  updateTickerDisplay();
  setupModals();
});

// --- Theme Management ---
function setupThemeToggle() {
  const btn = document.getElementById('theme-toggle-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', state.theme);
    
    // Update logo text based on theme to match Figma
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

// --- Navigation ---
function setupNavigation() {
  document.querySelectorAll('.nav-item button').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
      btn.parentElement.classList.add('active');

      const target = btn.getAttribute('data-view');
      state.activeView = target;

      document.querySelectorAll('.view-container').forEach(view => {
        view.classList.remove('active');
      });
      const activeContainer = document.getElementById(`view-${target}`);
      if (activeContainer) activeContainer.classList.add('active');
    });
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

  // Gold Engine rates display
  const ge24Input = document.getElementById('ge-base-24k');
  if (ge24Input) ge24Input.value = r24.toFixed(2);

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
    const input = document.getElementById('ge-base-24k');
    const val = parseFloat(input.value);
    if (!isNaN(val) && val > 0) {
      state.base24kRate = val;
      updateTickerDisplay();
      renderInventoryTable();
      renderPOSCatalog();
      updateCartUI();
      alert(`Master 24K rate updated to ${val} EGP/g. All karats and prices recalculated!`);
    }
  });
}

// --- Inventory Table Rendering ---
function renderInventoryTable() {
  const tbody = document.getElementById('inventory-table-body');
  if (!tbody) return;

  const isAr = state.locale === 'ar';
  tbody.innerHTML = '';

  state.inventory.forEach(item => {
    const price = getItemPrice(item);
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.innerHTML = `
      <td>
        <div style="display:flex; align-items:center; gap:0.75rem;">
          <img src="${item.image}" style="width:40px; height:40px; border-radius:4px; object-fit:cover;">
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
  grid.innerHTML = '';

  state.inventory.forEach(item => {
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
    alert("This piece is unique and has already been sold!");
    return;
  }

  // Check if unique piece already in cart
  const exists = state.cart.find(c => c.id === item.id);
  if (exists) {
    alert("Item is already in the current transaction cart.");
    return;
  }

  state.cart.push(item);
  updateCartUI();
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
  const statutoryVat = Math.round((totalMaking * state.taxRateOnMaking) * 100) / 100;
  const netPayable = Math.max(0, grossSubtotal - totalScrapCredit + statutoryVat - state.discount);

  // Update Summary DOM
  document.getElementById('calc-net-gold').innerText = `${totalNetGold.toFixed(2)} g`;
  document.getElementById('calc-metal-val').innerText = `${Math.round(totalMetalVal).toLocaleString()} EGP`;
  document.getElementById('calc-making-val').innerText = `+ ${Math.round(totalMaking).toLocaleString()} EGP`;
  document.getElementById('calc-subtotal').innerText = `${Math.round(grossSubtotal).toLocaleString()} EGP`;
  document.getElementById('calc-scrap-val').innerText = `- ${Math.round(totalScrapCredit).toLocaleString()} EGP`;
  document.getElementById('calc-vat-val').innerText = `+ ${statutoryVat.toLocaleString()} EGP`;
  document.getElementById('calc-total-val').innerText = `${Math.round(netPayable).toLocaleString()} EGP`;
}

// --- Modals & Actions ---
function setupModals() {
  // Scrap modal
  const btnScrap = document.getElementById('btn-open-scrap-modal');
  const modalScrap = document.getElementById('scrap-modal');
  const closeScrap = document.getElementById('close-scrap-modal');
  const applyScrap = document.getElementById('apply-scrap-tradein');

  if (btnScrap && modalScrap) {
    btnScrap.addEventListener('click', () => modalScrap.classList.add('active'));
    closeScrap.addEventListener('click', () => modalScrap.classList.remove('active'));
    applyScrap.addEventListener('click', () => {
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
        alert("Cart is empty! Add jewelry items first.");
        return;
      }
      populateInvoiceModal();
      modalInvoice.classList.add('active');
    });
    closeInvoice.addEventListener('click', () => {
      modalInvoice.classList.remove('active');
      state.cart = [];
      state.tradeIns = [];
      updateCartUI();
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

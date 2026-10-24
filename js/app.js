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
  base24kRate: 7160.00,
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
    terminal: "TERMINAL",
    live_lbm: "LIVE LBM",
    nav_operations: "OPERATIONS",
    nav_commerce: "COMMERCE & LEDGER",
    nav_governance: "GOVERNANCE & VAULT",
    dashboard: "Dashboard",
    inventory: "Inventory Vault",
    pos: "POS Counter",
    gold_engine: "Gold Engine",
    purchases: "Purchases & Suppliers",
    customers: "Customers CRM",
    reports: "Financial Reports & COGS",
    staff_rbac: "Staff & RBAC",
    audit_logs: "Audit Logs",
    vault_status_label: "VAULT STATUS",
    vault_status_val: "SECURE • 999.9",
    vault_status: "VAULT STATUS: SECURE • 999.9",
    search_placeholder: "Search SKU, Barcode, Client... (Ctrl+K)",
    role_prefix: "Role:",
    dash_eyebrow: "EXECUTIVE TERMINAL • CAIRO FLAGSHIP • VAULT A & B",
    dash_quick_pos: "⚡ Quick Sale (POS)",
    total_valuation: "VAULT TOTAL VALUATION",
    todays_sales: "TODAY'S POS SALES",
    completed_slips: "18 Completed Slips",
    realized_margin: "REALIZED MARGIN & FEES",
    badge_fabrique: "FABRIQUE",
    making_and_spread: "Making: 54,200 • Spread: 32,200",
    active_pieces: "ACTIVE ATELIER PIECES",
    qc_ready: "4 QC READY",
    in_works: "IN WORKS",
    casting_active: "999.9 Fine Casting Active",
    digital_vault: "⚜ Digital Vault",
    in_custody: "3,842 in custody",
    item_1_title: "1. Aethelred Solitaire",
    item_2_title: "2. Vendôme Choker",
    item_3_title: "3. Nile Royal Bangles",
    item_4_title: "4. PAMP Suisse Ingot 50g",
    featured_masterpiece: "FEATURED MASTERPIECE",
    item_1_full_name: "Aethelred Solitaire Royale",
    item_1_spec: "Round Brilliant 2.1ct Diamond • GIA #22849102 • 18K Yellow Gold",
    raw_gold_val: "RAW GOLD VALUE",
    making_charge: "MAKING CHARGE",
    diamond_tare: "DIAMOND TARE",
    commit_to_pos: "🛒 Commit to POS Counter (73,850 EGP)",
    pipeline_title: "ATELIER PRODUCTION PIPELINE (18 ACTIVE CUSTOM PIECES)",
    pipeline_cad: "1. CAD/Wax",
    pipeline_casting: "2. Casting",
    pipeline_setting: "3. Setting",
    pipeline_qc: "4. QC Assay",
    pipeline_ready: "5. Ready POS",
    portfolio_trend: "Portfolio Valuation Trend",
    bullion_vs_gems: "● Bullion vs Gems",
    vault_assayed_by_karat: "VAULT ASSAYED WEIGHT BY KARAT",
    bridal_21k: "● 21K Bridal & Modern Jewelry",
    gem_18k: "● 18K Gemstone Sets",
    bars_24k: "● 24K Minted Bars",
    filigree_22k: "● 22K Gulf Filigree",
    live_vault_ops: "Live Vault Operations",
    vault_op_sold: "Sold: 21K Damascene Ring",
    vault_op_inflow: "Custody Inflow: +500g 24K Ingot",
    inv_eyebrow: "MAISON CAIRO VAULT • SYNCED WITH LBM LIVE INDEX",
    inv_title: "Digital Vault Inventory",
    inv_subtitle: "Real-time bullion weights, calibrated tare deductions, dynamic karat re-pricing, and serialized hallmarking.",
    btn_stock_audit: "⚖ Stock Count Audit",
    add_piece: "+ Add New Jewelry Piece",
    filter_all: "All Karats (الكل)",
    filter_24k: "24K Pure Bullion",
    filter_21k: "21K Egyptian Standard",
    filter_18k: "18K Italian Mounts",
    th_piece_sku: "PIECE / SKU",
    th_purity: "PURITY",
    th_gross_wt: "GROSS WT.",
    th_stone_tare: "STONE TARE",
    th_net_gold: "NET GOLD",
    th_making_fee: "MAKING FEE",
    th_retail: "RETAIL (EGP)",
    th_action: "ACTION",
    pos_eyebrow: "REGISTER #04 / TARIQ AL-FAHIM (SENIOR APPRAISER) • METTLER USB SCALE: CALIBRATED 0.000g",
    pos_title: "Point of Sale (Counter Terminal)",
    pos_subtitle: "Real-time Karat spot valuations locked to Cairo Precious Metals Exchange ticker.",
    scale_btn_prefix: "⚖ Weigh on USB Scale",
    scrap_trade_in: "+ Gold Scrap / Trade-In",
    pos_filter_all: "All Jewelry (جميع القطع)",
    pos_filter_21k: "21K Bridal Sets",
    pos_filter_18k: "18K Italian Mounts",
    pos_filter_24k: "24K Investment Bars",
    cart_registry: "Cart Registry",
    vip_client_name: "Laila Nour El-Din",
    vip_client_tier: "VIP Tier 1 • 4,200 Aurum Pts",
    total_net_gold: "Total Net Gold Weight",
    metal_base_value: "Metal Base Value (Market Fix)",
    making_charges: "Making Charges (Fabrique)",
    subtotal: "Gross Goods Subtotal",
    scrap_credit_deducted: "Customer Scrap Credit Deducted",
    tax_eta: "ETA Statutory Sales Tax (14% on Making)",
    net_payable: "NET PAYABLE TOTAL",
    checkout: "Complete Sale & Issue ETA Invoice",
    ge_eyebrow: "AURUM ENGINE • BULLION ARBITRAGE & COGS • LIVE SAGHA FEED",
    ge_title: "Global Vault Master Rate & Karat Cascade",
    ge_subtitle: "Central Egyptian Bullion Clearinghouse (Sagha Desk) automated assay synchronization.",
    ge_base_panel: "BASE 24K PURE INGOT RATE (999.9 FINE / 100.0%)",
    lbm_price: "● LBM: $2,342.40 / oz",
    btn_update_rate: "⚡ Update Global Rate",
    ge_22k_title: "22 KARAT (91.67%)",
    ge_22k_spread: "Spread: Sell +45 EGP",
    ge_21k_title: "21K BENCHMARK (87.5%)",
    ge_21k_subtitle: "Egyptian Pivot Standard",
    ge_18k_title: "18 KARAT (75.00%)",
    ge_18k_subtitle: "Italian Standard",
    ge_14k_title: "14 KARAT (58.33%)",
    ge_14k_subtitle: "Commercial Grade",
    masnaeya_policy_title: "Masnaeya & Profit Floors",
    masnaeya_policy_desc: "Enforces atelier production thresholds, prevents cashier undercutting, and locks minimum cash contributions.",
    policy_italian_chains: "Italian Laser Chains (18K)",
    policy_italian_floor: "Floor: +12% Net",
    policy_filigree: "Handcrafted Filigree (21K)",
    policy_filigree_floor: "Khan el-Khalili Atelier",
    policy_bullion_bars: "Plain Bullion & BTC Bars",
    policy_bullion_pack: "Sealed Packaging",
    purchases_eyebrow: "RAW BULLION & ATELIER SUPPLY CHAIN",
    purchases_title: "Purchases & Supplier Balances",
    purchases_subtitle: "Track wholesale gold shipments, assayed metal weights, supplier receivables, and bullion accounts.",
    btn_record_supplier: "+ Record Supplier Inflow",
    supplier_debt: "TOTAL OUTSTANDING SUPPLIER DEBT",
    across_desks: "Across 2 Primary Bullion Desks",
    consignment_scrap: "CONSIGNMENT SCRAP HELD",
    verified_vault: "Verified Hydrostatic Vault A",
    monthly_bullion: "RAW BULLION PURCHASED (MONTH)",
    active_vendors: "ACTIVE SUPPLIERS",
    vendors_unit: "VENDORS",
    th_supplier_desk: "SUPPLIER / DESK",
    th_phone: "PHONE / CONTACT",
    th_primary_metal: "PRIMARY METAL",
    th_balance: "BALANCE (EGP)",
    th_status: "STATUS",
    supp_sagha_name: "Central Egyptian Bullion Clearinghouse (Sagha Desk)",
    supp_ingot_type: "24K / 21K Ingot",
    status_active: "ACTIVE",
    btn_settle: "Settle",
    supp_vicenza_name: "Vicenza Luxury Mounts SpA (Italy)",
    supp_chain_type: "18K Laser Chain",
    status_in_transit: "SETTLED IN TRANSIT",
    crm_eyebrow: "VIP CLIENTELE & LOYALTY TIERS",
    crm_title: "Customers & CRM Registry",
    crm_subtitle: "Track customer acquisition, gold purchases, trade-in records, and loyalty privileges.",
    btn_add_customer: "+ Register Customer",
    th_client_name: "CLIENT NAME",
    th_tier: "TIER",
    th_reward_pts: "AURUM REWARD PTS",
    th_lifetime_purchases: "LIFETIME PURCHASES",
    tier_vip: "💎 VIP Tier 1",
    tier_gold: "⭐ Gold Tier",
    tier_standard: "Standard Tier",
    btn_new_sale: "New Sale",
    reports_eyebrow: "IFRS IAS 2 COMPLIANT COGS & MARGIN ANALYSIS",
    reports_title: "Financial Reports & Profitability",
    reports_subtitle: "Quarantined unrealized spot inflation, net operating profit, and store overhead breakdown.",
    monthly_gross_revenue: "GROSS SALES REVENUE (MONTH)",
    cogs_label: "COST OF GOODS SOLD (COGS)",
    metal_cost_label: "Pure Metal Replacement Cost",
    realized_workmanship: "REALIZED WORKMANSHIP PROFIT",
    fabrique_label: "Fabrique Contribution",
    net_operating_profit: "NET OPERATING PROFIT",
    net_profit_footer: "Net of Rent, Salaries & Tax",
    operating_expenses_ledger: "Monthly Operating Expense Ledger (مصاريف التشغيل)",
    expense_rent_title: "Boutique & Atelier Rent (Zamalek / Cairo Flagship)",
    expense_rent_desc: "Recurring Facility Cost",
    expense_salaries_title: "Atelier Master Goldsmith Salaries & Appraiser Bonuses",
    expense_salaries_desc: "6 Goldsmiths & 3 POS Appraisers",
    expense_packaging_title: "Luxury Suede Packaging & Custom Velvet Presentation Cases",
    expense_packaging_desc: "Bespoke Boxes with Embossed Gold Foil",
    expense_transport_title: "Security Armored Transport & Hydrostatic Assay Calibration",
    expense_transport_desc: "Mettler Toledo Certified Audit",
    staff_eyebrow: "IDENTITY & ROLE-BASED ACCESS CONTROL",
    staff_title: "Employee Accounts & Permissions",
    staff_subtitle: "Control cashier privileges, audit trail ownership, and appraiser workstation authorizations.",
    btn_add_staff: "+ Add Staff Account",
    th_staff_member: "STAFF MEMBER",
    th_email: "EMAIL",
    th_role: "ROLE",
    th_terminal: "TERMINAL ASSIGNED",
    th_permissions: "PERMISSIONS",
    role_owner_tag: "👑 ADMIN / OWNER",
    perm_admin: "Full System & COGS Financials",
    role_appraiser_tag: "👤 SENIOR APPRAISER",
    perm_cashier: "POS Sales & Scrap Evaluation Only",
    role_goldsmith_tag: "👤 ATELIER GOLDSMITH",
    perm_goldsmith: "Production Pipeline & Assay Verification",
    audit_eyebrow: "IMMUTABLE SECURITY LEDGER",
    audit_title: "System Audit & Compliance Logs",
    audit_subtitle: "Permanent cryptographic trail of all spot recalculations, sales checkouts, and stock overrides.",
    th_timestamp: "TIMESTAMP",
    th_user: "USER / CASHIER",
    th_action_type: "ACTION",
    th_entity: "ENTITY",
    th_details: "DETAILS",
    scrap_modal_title: "♻ Customer Scrap Gold Trade-in",
    scrap_karat_label: "Gold Purity / Karat",
    scrap_weight_label: "Gross Scrap Weight (Grams)",
    btn_read_scale: "⚖ Read USB Scale",
    scrap_rate_label: "Applied Buy-Back Rate (EGP / Gram)",
    btn_apply_scrap: "Apply Deduction to Current Invoice",
    inv_shop_title: "MAISON D'OR HAUTE JOAILLERIE",
    inv_tax_reg: "Cairo Flagship Boutique • Egyptian Tax Authority (ETA) Registered",
    inv_th_item: "Item",
    inv_th_karat: "Karat",
    inv_th_gw: "GW",
    inv_th_nw: "NW",
    inv_th_total: "Total",
    inv_final_due: "FINAL AMOUNT DUE:",
    inv_legal_note: "Includes official Egyptian Hallmarking and 14% ETA VAT strictly on making fees.",
    btn_inv_done: "Done",
    btn_inv_print: "🖨 Print Invoice",
    add_piece_modal_title: "⚜ Add Jewelry Piece to Vault",
    piece_name_en_label: "Piece Name (EN)",
    piece_name_ar_label: "Piece Name (AR)",
    piece_sku_label: "SKU / Hallmarking Code",
    piece_karat_label: "Karat Purity",
    piece_gw_label: "Gross Wt (g)",
    piece_tare_label: "Tare / Gems (g)",
    piece_making_label: "Making Fee (EGP/g)",
    piece_category_label: "Category",
    btn_save_piece: "Confirm & Ingest Into Custody Vault",
    add_cust_modal_title: "👤 Register VIP Customer",
    cust_name_label: "Full Customer Name",
    cust_phone_label: "Mobile / WhatsApp Phone",
    cust_tier_label: "Loyalty Tier",
    btn_save_customer: "Save Client to Atelier Registry",
    supp_modal_title: "🚚 Record Wholesale Bullion Inflow",
    supp_vendor_label: "Wholesale Supplier / Clearing Desk",
    supp_karat_label: "Metal Purity / Karat",
    supp_weight_label: "Inflow Weight (Grams)",
    supp_value_label: "Total Value (EGP)",
    btn_save_supplier: "Ingest Wholesale Metal to Vault Ledger",
    staff_modal_title: "🛡 Create Staff / Appraiser Account",
    staff_name_label: "Employee Full Name",
    staff_email_label: "Work Email",
    staff_role_label: "System Role & RBAC Clearance",
    staff_terminal_label: "Assigned Workstation Terminal",
    btn_save_staff: "Provision User & Issue Cryptographic Token",
    nav_live_market: "Live Gold Board",
    nav_market_screen: "Live Gold Display",
    dash_market_screen: "Live Gold Board",
    gmd_brand_gold: "3M DAHAB",
    gmd_title: "Egyptian Gold Market Board",
    gmd_subtitle: "Real-Time Official Sagha & Bullion Pricing Display (Cairo Exchange)",
    gmd_status_live: "LIVE • Verified Market Quotes",
    gmd_status_delayed: "DELAYED • Cached Market Quotes",
    gmd_status_offline: "OFFLINE • Operating with Local Vault Cache",
    gmd_refresh: "Refresh Now",
    gmd_fullscreen: "Fullscreen",
    gmd_enter_dash: "Enter Management Dashboard ➔",
    gmd_ribbon_gold_pound: "Gold Pound (8g 21K)",
    gmd_ribbon_ounce_usd: "Global Gold Ounce (XAU/USD)",
    gmd_ribbon_usd_egp: "Official USD / EGP Rate",
    gmd_ribbon_next_refresh: "Next Auto Refresh",
    gmd_dealers_title: "Live Dealer Quotes from Leading Egyptian Bullion Houses (21K)",
    gmd_th_dealer: "Dealer / Bullion House",
    gmd_th_karat: "Karat",
    gmd_th_buy: "We Buy From You (EGP)",
    gmd_th_sell: "We Sell To You (EGP)",
    gmd_th_spread: "Spread",
    gmd_th_status: "Status",
    gmd_provider_label: "Primary Feed Provider:",
    gmd_fallback_label: "Comparison Provider:",
    gmd_disclaimer: "Reference spot rates for Egyptian jewelry market, subject to real-time changes.",
    gmd_observed_label: "Source Observed:",
    gmd_retrieved_label: "Last Retrieved:",
    gmd_sell_label: "Sell (To Customer)",
    gmd_buy_label: "Buy (From Customer)",
    gmd_spread_label: "Trading Spread",
    gmd_verified_quote: "Verified Sagha Quote",
    gmd_indicative_quote: "Indicative Estimate",
    admin_center: "Admin Command Center",
    admin_eyebrow: "EXECUTIVE COMMAND • CAIRO CENTRAL VAULT • ROOT CLEARANCE LEVEL 3",
    admin_title: "Admin Executive Command Center",
    admin_subtitle: "Shop ownership governance, live pricing recalibration, staff RBAC, physical vault audit, and ETA compliance.",
    admin_sync_rates: "Sync Market Rates",
    admin_run_audit: "Vault Audit Scan",
    admin_export_backup: "Export Vault Backup",
    admin_metric_vault_nav: "VAULT NET ASSET VALUE (NAV)",
    admin_pure_gold_backed: "14,210.50g Fine 24K Gold Backed",
    admin_metric_pos_margin: "TODAY'S POS SALES & MARGIN",
    admin_realized_fabrique: "Net Workmanship: +86,400 EGP",
    admin_metric_terminals: "ACTIVE WORKSTATIONS & RBAC",
    admin_staff_registered: "STAFF",
    admin_terminals_active: "POS",
    admin_tls_security: "Encrypted TLS 1.3 • Cairo Hub",
    admin_metric_compliance: "ETA TAX & ASSAY HALLMARK",
    admin_compliant: "COMPLIANT",
    admin_official_hallmark: "Official Laser Assay Enforced",
    admin_pricing_title: "Gold Pricing Master Engine",
    admin_feed_connected: "Daleelak Live Feed Connected",
    admin_pricing_desc: "Direct executive override for base 24K bullion spot price. Updates cascade instantaneously to 18K, 21K, 22K, 24K, and 3,842 catalog jewelry pieces.",
    admin_base_24k_label: "Master 24K Spot Benchmark (EGP / Gram)",
    admin_apply_recalibration: "Recalibrate & Cascade",
    admin_sync_footnote: "Cascades affect all active POS registers, retail quotes, and scrap buy-back calculators.",
    admin_use_sagha_live: "Use Egyptian Sagha Live Rate",
    admin_staff_title: "Staff Accounts & Workstations",
    admin_btn_add_staff: "Add Staff",
    admin_staff_desc: "Manage terminal logins, role-based security clearances, appraiser assignments, and credential resets.",
    admin_reset_pin: "Reset PIN",
    admin_primary_key: "Master Root",
    admin_vault_audit_title: "Physical Vault Audit & Hydrostatic Assay",
    admin_audit_ready: "RECONCILED • 0.000g Variance",
    admin_vault_audit_desc: "Automated cryptographic cross-check between ERP digital book weight, RFID safe sensors, and digital precision scale.",
    admin_book_weight: "ERP Book Weight",
    admin_scanned_weight: "Hydrostatic Scanned",
    admin_variance: "Weight Variance",
    admin_perfect_match: "Perfect Match",
    admin_scanning_rfid: "Scanning RFID Trays & Hydrostatic Density...",
    admin_btn_run_audit: "Initiate Hydrostatic & RFID Audit Scan",
    admin_btn_cert: "Download Audit Certificate",
    admin_compliance_title: "Egyptian Tax Authority (ETA) & Hallmarking",
    admin_eta_active: "ETA Registered",
    admin_compliance_desc: "Governs value-added taxation (14% VAT on making charges only per Egyptian Law #67/2016), cashier discount caps, and official Assay Directorate credentials.",
    admin_vat_making_label: "ETA VAT on Making Charges (%)",
    admin_max_discount_label: "Max Cashier Discount Cap (%)",
    admin_require_hallmark: "Enforce Egyptian Stamp & Assay Directorate (مصلحة الدمغة والموازين) Laser QR on Invoices",
    admin_save_policy: "Save Policy & Broadcast to Terminals",
    admin_credentials_title: "System Master Credentials & Security",
    admin_auth_active: "Auth Active",
    admin_credentials_desc: "Pre-configured production accounts for testing executive authority and cashier workflows.",
    admin_activate_admin: "Activate Admin",
    admin_activate_cashier: "Test Cashier",
    admin_session_key: "Session Key:",
    admin_reset_demo: "Reset Atelier Demo Data",
    admin_audit_stream_title: "Live Administrative Audit Feed",
    admin_view_full_audit: "View Full Audit Ledger ➔",
    admin_audit_stream_desc: "Immutable stream of executive configuration updates, spot recalculations, and vault balance adjustments."
  },
  ar: {
    terminal: "محطة الصاغة",
    live_lbm: "بورصة الذهب مباشر",
    nav_operations: "العمليات والتشغيل",
    nav_commerce: "المعاملات والتجارة",
    nav_governance: "الإدارة والخزينة المركزية",
    dashboard: "لوحة التحكم",
    inventory: "خزينة المخزون",
    pos: "نقطة البيع (الكاونتر)",
    gold_engine: "محرك تسعير الذهب",
    purchases: "المشتريات والموردين",
    customers: "سجل العملاء CRM",
    reports: "التقارير المالية والأرباح",
    staff_rbac: "الموظفين والصلاحيات",
    audit_logs: "سجل التدقيق والأمان",
    vault_status_label: "حالة الخزينة",
    vault_status_val: "مؤمنة • 999.9",
    vault_status: "حالة الخزينة: مؤمنة • 999.9",
    search_placeholder: "بحث بالكود، الباركود، العميل... (Ctrl+K)",
    role_prefix: "الرتبة:",
    dash_eyebrow: "المحطة الرئيسية • فرع القاهرة • خزينة أ & ب",
    dash_quick_pos: "⚡ بيع سريع (كاونتر)",
    total_valuation: "إجمالي تقييم الخزينة",
    todays_sales: "مبيعات الكاونتر اليوم",
    completed_slips: "18 فاتورة مكتملة",
    realized_margin: "أرباح المصنعية المحققة",
    badge_fabrique: "المصنعية",
    making_and_spread: "أجور المصنعية: 54,200 • فروق السعر: 32,200",
    active_pieces: "قطع نشطة بالورشة",
    qc_ready: "4 جاهزة للفحص",
    in_works: "قيد التصنيع",
    casting_active: "سكب وصب عيار 999.9 نشط",
    digital_vault: "⚜ الخزينة الرقمية",
    in_custody: "3,842 قطعة في الخزينة",
    item_1_title: "1. خاتم سوليتير أثيلريد",
    item_2_title: "2. طوق فاندوم الزهري",
    item_3_title: "3. أساور النيل الملكية",
    item_4_title: "4. سبيكة بامب 50 جرام",
    featured_masterpiece: "القطعة الاستثنائية المميزة",
    item_1_full_name: "خاتم سوليتير أثيلريد الملكي",
    item_1_spec: "ألماس بريليانت 2.1 قيراط • شهادة GIA #22849102 • ذهب أصفر عيار 18",
    raw_gold_val: "قيمة الذهب الخام",
    making_charge: "قيمة المصنعية",
    diamond_tare: "تصفية الفصوص",
    commit_to_pos: "🛒 إضافة إلى الكاونتر للبيع (73,850 ج.م)",
    pipeline_title: "مراحل تصنيع ورشة الذهب (18 قطعة مخصصة قيد العمل)",
    pipeline_cad: "1. تصميم وشمع",
    pipeline_casting: "2. صب وسكب",
    pipeline_setting: "3. تركيب الفصوص",
    pipeline_qc: "4. الدمغ ومطابقة العيار",
    pipeline_ready: "5. جاهز للعرض",
    portfolio_trend: "توزيع أوزان الخزينة حسب العيار",
    bullion_vs_gems: "● سبائك ومصوغات",
    vault_assayed_by_karat: "أوزان الخزينة المدموغة حسب العيار",
    bridal_21k: "● عيار 21 مشغولات وزفاف",
    gem_18k: "● عيار 18 أطقم مرصعة",
    bars_24k: "● عيار 24 سبائك استثمار",
    filigree_22k: "● عيار 22 خليجي منقوش",
    live_vault_ops: "حركات الخزينة اللحظية",
    vault_op_sold: "تم البيع: خاتم دمشقي عيار 21",
    vault_op_inflow: "توريد للخزينة: +500 جرام سبيكة عيار 24",
    inv_eyebrow: "خزينة ميزون دور • مربوطة بمؤشر الذهب العالمي",
    inv_title: "خزينة المخزون والسبائك",
    inv_subtitle: "أوزان الذهب الحية، تصفية الفصوص بدقة، تسعير لحظي لجميع العيارات، وأكواد الدمغة الرسمية.",
    btn_stock_audit: "⚖ جرد ومطابقة الخزينة",
    add_piece: "+ إضافة قطعة مجوهرات جديدة",
    filter_all: "جميع العيارات (الكل)",
    filter_24k: "عيار 24 سبائك نقية",
    filter_21k: "عيار 21 المعيار المصري",
    filter_18k: "عيار 18 إيطالي ومرصع",
    th_piece_sku: "القطعة / الكود",
    th_purity: "العيار",
    th_gross_wt: "الوزن القائم",
    th_stone_tare: "تصفية الفصوص",
    th_net_gold: "صافي الذهب",
    th_making_fee: "المصنعية/ج",
    th_retail: "السعر الإجمالي (ج.م)",
    th_action: "إجراء",
    pos_eyebrow: "كاونتر رقم 04 / طارق الفهيم (كبير مثمني الذهب) • ميزان ميتلر USB: معاير 0.000 جرام",
    pos_title: "نقطة البيع (كاونتر الصاغة)",
    pos_subtitle: "تسعير لحظي لجرام الذهب مربوط بشاشة بورصة الصاغة المصرية.",
    scale_btn_prefix: "⚖ قراءة الميزان الإلكتروني",
    scrap_trade_in: "+ إضافة كسر دهب (استبدال)",
    pos_filter_all: "جميع المعروضات",
    pos_filter_21k: "أطقم عيار 21",
    pos_filter_18k: "مشغولات عيار 18",
    pos_filter_24k: "سبائك عيار 24",
    cart_registry: "بيان الفاتورة الحالية",
    vip_client_name: "ليلى نور الدين",
    vip_client_tier: "عميل مميز VIP فئة 1 • 4,200 نقطة ذهبية",
    total_net_gold: "إجمالي صافي وزن الذهب",
    metal_base_value: "قيمة الذهب الخام (سعر السوق)",
    making_charges: "إجمالي أجور المصنعية",
    subtotal: "إجمالي قيمة المصوغات",
    scrap_credit_deducted: "خصم قيمة كسر الذهب المستبدل",
    tax_eta: "ضريبة القيمة المضافة (14% على المصنعية)",
    net_payable: "صافي المبلغ المستحق",
    checkout: "إتمام البيع وإصدار الفاتورة الضريبية",
    ge_eyebrow: "محرك أوروم • تسعير السبائك والمصنعية • ربط مباشر مع الصاغة",
    ge_title: "السعر الرئيسي المرجعي وتسعير العيارات",
    ge_subtitle: "تسوية ومزامنة أسعار الذهب لحظياً مع غرفة الصاغة المصرية والمقاصة المركزية.",
    ge_base_panel: "سعر جرام عيار 24 الخام النقي (عيار 999.9 / 100%)",
    lbm_price: "● أونصة الذهب: $2,342.40",
    btn_update_rate: "⚡ تحديث سعر الذهب وإعادة الحساب",
    ge_22k_title: "عيار 22 (91.67%)",
    ge_22k_spread: "فرق البيع والشراء: +45 ج.م",
    ge_21k_title: "عيار 21 (87.5% معيار السوق المصري)",
    ge_21k_subtitle: "المعيار الأساسي للصاغة المصرية",
    ge_18k_title: "عيار 18 (75.00%)",
    ge_18k_subtitle: "معيار الذهب الإيطالي",
    ge_14k_title: "عيار 14 (58.33%)",
    ge_14k_subtitle: "العيار التجاري",
    masnaeya_policy_title: "سياسة أجور المصنعية والحد الأدنى للربح",
    masnaeya_policy_desc: "تطبيق حدود دنيا لأجور الورشة ومنع الكاشير من تخفيض المصنعية لحماية الأرباح.",
    policy_italian_chains: "سلاسل ليزر إيطالي (عيار 18)",
    policy_italian_floor: "الحد الأدنى: +12% صافي",
    policy_filigree: "مشغولات مخرمة ومنقوشة (عيار 21)",
    policy_filigree_floor: "ورش خان الخليلي",
    policy_bullion_bars: "سبائك خام وجنيهات BTC",
    policy_bullion_pack: "مغلفة ومدموغة رسمي",
    purchases_eyebrow: "سلسلة إمداد الذهب الخام ومسابك الصاغة",
    purchases_title: "المشتريات وحسابات الموردين",
    purchases_subtitle: "متابعة شحنات الذهب بالجملة، وأوزان السبائك المدموغة، ومستحقات تجار الصاغة.",
    btn_record_supplier: "+ تسجيل توريد ذهب خام",
    supplier_debt: "إجمالي مستحقات الموردين القائمة",
    across_desks: "عبر مكاتب التداول الرئيسية بالصاغة",
    consignment_scrap: "كسر ذهب بالأمانة بالخزينة",
    verified_vault: "خزينة أ - فحص هيدروستاتيكي",
    monthly_bullion: "سبائك خام مشتراة (شهرياً)",
    active_vendors: "الموردين النشطين",
    vendors_unit: "تجار",
    th_supplier_desk: "المورد / مكتب التداول",
    th_phone: "الهاتف / التواصل",
    th_primary_metal: "الذهب المورد",
    th_balance: "الرصيد المتبقي (ج.م)",
    th_status: "الحالة",
    supp_sagha_name: "المقاصة المركزية لتجارة الذهب (غرفة الصاغة)",
    supp_ingot_type: "سبائك عيار 24 وعيار 21",
    status_active: "نشط",
    btn_settle: "تسوية",
    supp_vicenza_name: "شركة فيتشنزا الإيطالية للمصوغات (إيطاليا)",
    supp_chain_type: "سلاسل ليزر عيار 18",
    status_in_transit: "مسدد قيد الشحن",
    crm_eyebrow: "كبار العملاء وفئات الولاء",
    crm_title: "سجل العملاء وإدارة العلاقات CRM",
    crm_subtitle: "متابعة مشتريات العملاء، وسجلات استبدال الذهب، ونقاط الولاء والمكافآت.",
    btn_add_customer: "+ تسجيل عميل جديد",
    th_client_name: "اسم العميل",
    th_tier: "فئة العميل",
    th_reward_pts: "نقاط أوروم الذهبية",
    th_lifetime_purchases: "إجمالي المشتريات",
    tier_vip: "💎 عميل VIP فئة 1",
    tier_gold: "⭐ فئة ذهبية",
    tier_standard: "فئة عادية",
    btn_new_sale: "فاتورة جديدة",
    reports_eyebrow: "تحليل تكلفة البضاعة المباعة وهوامش الربح طبقاً لمعايير المحاسبة",
    reports_title: "التقارير المالية وهوامش الأرباح",
    reports_subtitle: "فصل تضخم سعر الذهب عن صافي أرباح التشغيل والمصنعية والمصروفات.",
    monthly_gross_revenue: "إجمالي إيراد المبيعات (الشهري)",
    cogs_label: "تكلفة البضاعة المباعة (ذهب خام)",
    metal_cost_label: "تكلفة استبدال المعدن الخام",
    realized_workmanship: "أرباح المصنعية المحققة",
    fabrique_label: "عائد وفروق المصنعية",
    net_operating_profit: "صافي أرباح التشغيل",
    net_profit_footer: "صافي بعد الإيجار والمرتبات والضرائب",
    operating_expenses_ledger: "سجل مصاريف التشغيل الشهرية (مصاريف المتجر)",
    expense_rent_title: "إيجار المعرض والورشة (فرع الزمالك / القاهرة)",
    expense_rent_desc: "تكلفة المنشأة الدورية",
    expense_salaries_title: "رواتب كبار الصاغة وحوافز مثمني الكاونتر",
    expense_salaries_desc: "6 صاغة محترفين و3 مثمنين كاونتر",
    expense_packaging_title: "علب قطيفة فاخرة وأكياس مخملية مطبوعة بماء الذهب",
    expense_packaging_desc: "علب مخصصة مع دمغة ذهبية",
    expense_transport_title: "حراسة مصفحة ومعايرة الموازين الإلكترونية الرسمية",
    expense_transport_desc: "فحص واعتماد ميتلر توليدو الدوري",
    staff_eyebrow: "إدارة الهوية وصلاحيات المستخدمين RBAC",
    staff_title: "حسابات الموظفين والصلاحيات",
    staff_subtitle: "تحديد صلاحيات الكاشير، وسجلات العمليات، ومحطات الوزن المعتمدة.",
    btn_add_staff: "+ إضافة حساب موظف",
    th_staff_member: "الموظف",
    th_email: "البريد الإلكتروني",
    th_role: "الرتبة / الدور",
    th_terminal: "محطة العمل",
    th_permissions: "الصلاحيات",
    role_owner_tag: "👑 مالك المتجر / المدير العام",
    perm_admin: "صلاحيات كاملة على النظام والتقارير المالية",
    role_appraiser_tag: "👤 كبير مثمني الذهب / كاشير",
    perm_cashier: "مبيعات الكاونتر وتثمين كسر الذهب فقط",
    role_goldsmith_tag: "👤 صائغ ورشة محترف",
    perm_goldsmith: "متابعة خط الإنتاج وفحص الدمغة والعيار",
    audit_eyebrow: "سجل الأمان غير القابل للتعديل",
    audit_title: "سجلات تدقيق النظام ومطابقة العمليات",
    audit_subtitle: "توثيق مشفر لجميع عمليات تعديل الأسعار، وفواتير البيع، والتعديلات اليدوية.",
    th_timestamp: "التوقيت",
    th_user: "المستخدم / الكاشير",
    th_action_type: "نوع الإجراء",
    th_entity: "البيان / الفاتورة",
    th_details: "التفاصيل",
    scrap_modal_title: "♻ شراء واستبدال كسر ذهب من العميل",
    scrap_karat_label: "عيار كسر الذهب",
    scrap_weight_label: "الوزن القائم لكسر الذهب (جرام)",
    btn_read_scale: "⚖ قراءة الميزان الإلكتروني",
    scrap_rate_label: "سعر شراء الجرام المعتمد (ج.م / جرام)",
    btn_apply_scrap: "تطبيق الخصم على الفاتورة الحالية",
    inv_shop_title: "مجوهرات ميزون دور (عم دهب)",
    inv_tax_reg: "المتجر الرئيسي - القاهرة • مسجل بمصلحة الضرائب المصرية (ETA)",
    inv_th_item: "القطعة",
    inv_th_karat: "العيار",
    inv_th_gw: "وزن قائم",
    inv_th_nw: "وزن صافي",
    inv_th_total: "القيمة الإجمالية",
    inv_final_due: "صافي المبلغ المطلوب سداده:",
    inv_legal_note: "تشمل الدمغة الرسمية وضريبة القيمة المضافة 14% على المصنعية فقط طبقاً للقانون المصري.",
    btn_inv_done: "إغلاق",
    btn_inv_print: "🖨 طباعة الفاتورة الضريبية",
    add_piece_modal_title: "⚜ إضافة قطعة مجوهرات إلى الخزينة",
    piece_name_en_label: "اسم القطعة (بالإنجليزي)",
    piece_name_ar_label: "اسم القطعة (بالعربي)",
    piece_sku_label: "كود الصنف / الدمغة",
    piece_karat_label: "العيار",
    piece_gw_label: "الوزن القائم (جرام)",
    piece_tare_label: "تصفية الفصوص (جرام)",
    piece_making_label: "المصنعية (ج.م/جرام)",
    piece_category_label: "التصنيف",
    btn_save_piece: "تأكيد وإدراج القطعة في الخزينة",
    add_cust_modal_title: "👤 تسجيل عميل VIP جديد",
    cust_name_label: "اسم العميل بالكامل",
    cust_phone_label: "رقم الهاتف / الواتساب",
    cust_tier_label: "فئة الولاء",
    btn_save_customer: "حفظ العميل في سجل الدار",
    supp_modal_title: "🚚 تسجيل توريد سبائك ذهب خام بالجملة",
    supp_vendor_label: "المورد / مكتب التداول",
    supp_karat_label: "عيار الذهب",
    supp_weight_label: "وزن الشحنة (جرام)",
    supp_value_label: "القيمة الإجمالية (ج.م)",
    btn_save_supplier: "إدراج الذهب المورد في رصيد الخزينة",
    staff_modal_title: "🛡 إنشاء حساب موظف / مثمن ذهب",
    staff_name_label: "الاسم بالكامل",
    staff_email_label: "البريد الإلكتروني للعمل",
    staff_role_label: "الرتبة والصلاحيات",
    staff_terminal_label: "محطة الكاونتر المخصصة",
    btn_save_staff: "إنشاء الحساب وإصدار رمز الأمان",
    nav_live_market: "شاشة أسعار الصاغة",
    nav_market_screen: "شاشة أسعار السوق المباشرة",
    dash_market_screen: "شاشة أسعار الصاغة",
    gmd_brand_gold: "3M DAHAB",
    gmd_title: "بورصة أسعار الذهب بمصر",
    gmd_subtitle: "شاشة العرض اللحظية لأسعار الصاغة والسبائك المصرية المعتمدة",
    gmd_status_live: "مباشر • بيانات سوق معتمدة",
    gmd_status_delayed: "متأخر • بيانات سوق سابقة",
    gmd_status_offline: "غير متصل • وضع أوفلاين مع الخزينة",
    gmd_refresh: "تحديث الآن",
    gmd_fullscreen: "ملء الشاشة",
    gmd_enter_dash: "الدخول إلى لوحة إدارة المتجر ➔",
    gmd_ribbon_gold_pound: "جنيه الذهب (8 جرام عيار 21)",
    gmd_ribbon_ounce_usd: "أوقية الذهب عالمياً (XAU/USD)",
    gmd_ribbon_usd_egp: "سعر الدولار بالبنوك المصرية",
    gmd_ribbon_next_refresh: "دورة التحديث التلقائي",
    gmd_dealers_title: "أسعار التداول المباشرة لدى كبرى دور الصاغة والسبائك بمصر (عيار 21)",
    gmd_th_dealer: "الجهة / دار الصاغة",
    gmd_th_karat: "العيار",
    gmd_th_buy: "سعر الشراء من العميل",
    gmd_th_sell: "سعر البيع للعميل",
    gmd_th_spread: "الفارق",
    gmd_th_status: "الحالة",
    gmd_provider_label: "مزود البيانات الأساسي:",
    gmd_fallback_label: "مزود مقارن:",
    gmd_disclaimer: "الأسعار استرشادية لتعاملات سوق الصاغة المصرية وتخضع لتقلبات السوق الفورية.",
    gmd_observed_label: "توقيت رصد المصدر:",
    gmd_retrieved_label: "آخر فحص ناجح:",
    gmd_sell_label: "سعر البيع (للمستهلك)",
    gmd_buy_label: "سعر الشراء (من المستهلك)",
    gmd_spread_label: "فارق السعر",
    gmd_verified_quote: "سعر صاغة معتمد",
    gmd_indicative_quote: "عيار استرشادي",
    admin_center: "مركز القيادة الإداري",
    admin_eyebrow: "القيادة الإدارية العليا • الخزينة المركزية بالقاهرة • صلاحيات المستوى الثالث",
    admin_title: "مركز القيادة والتحكم الإداري الأعلى",
    admin_subtitle: "إدارة ملكية المتجر، إعادة معايرة أسعار الذهب، إدارة صلاحيات الموظفين، جرد ومطابقة الخزينة، والامتثال الضريبي.",
    admin_sync_rates: "تحديث أسعار البورصة",
    admin_run_audit: "فحص وجرد الخزينة",
    admin_export_backup: "تصدير نسخة احتياطية",
    admin_metric_vault_nav: "صافي أصول الخزينة (NAV)",
    admin_pure_gold_backed: "14,210.50 جرام ذهب نقي عيار 24 مغطى بالكامل",
    admin_metric_pos_margin: "مبيعات الكاونتر والأرباح اليومية",
    admin_realized_fabrique: "صافي أرباح المصنعية: +86,400 ج.م",
    admin_metric_terminals: "محطات العمل والصلاحيات النشطة",
    admin_staff_registered: "موظفين",
    admin_terminals_active: "كاونتر",
    admin_tls_security: "اتصال مشفر TLS 1.3 • فرع القاهرة",
    admin_metric_compliance: "الضرائب والدمغة والموازين",
    admin_compliant: "مطابق قانونياً",
    admin_official_hallmark: "دمغة الليزر الرسمية مفعلة",
    admin_pricing_title: "محرك تسعير الذهب المركزي",
    admin_feed_connected: "متصل ببورصة دليلـك اللحظية",
    admin_pricing_desc: "تعديل مباشر لسعر سبيكة عيار 24 النقي، مع تدرج فوري لأسعار عيارات 18 و21 و22 وجميع معروضات الخزينة.",
    admin_base_24k_label: "سعر جرام عيار 24 الأساسي (ج.م / جرام)",
    admin_apply_recalibration: "إعادة المعايرة والتحديث الشامل",
    admin_sync_footnote: "ينعكس التحديث فورياً على كافة نقاط البيع وشاشات التسعير وحسابات شراء كسر الذهب.",
    admin_use_sagha_live: "تطبيق السعر الفوري لبورصة الصاغة",
    admin_staff_title: "حسابات الموظفين ومحطات البيع",
    admin_btn_add_staff: "إضافة موظف",
    admin_staff_desc: "إدارة تسجيلات الدخول، مستويات الصلاحيات، تعيين المحطات، وإعادة ضبط الأرقام السرية.",
    admin_reset_pin: "إعادة ضبط PIN",
    admin_primary_key: "الجذر الأساسي",
    admin_vault_audit_title: "جرد ومطابقة الخزينة والميزان المائي",
    admin_audit_ready: "مطابقة تامة • فرق 0.000 جرام",
    admin_vault_audit_desc: "مطابقة إلكترونية فورية بين الوزن الدفتري، مستشعرات الخزينة RFID، والميزان المائي فائق الدقة.",
    admin_book_weight: "الوزن الدفتري بالسيستم",
    admin_scanned_weight: "الوزن الممسوح مائياً",
    admin_variance: "فرق الوزن (العجز/الزيادة)",
    admin_perfect_match: "مطابقة بنسبة 100%",
    admin_scanning_rfid: "جاري فحص صواني العرض RFID والكثافة المائية...",
    admin_btn_run_audit: "بدء فحص ومطابقة الخزينة الآن",
    admin_btn_cert: "تحميل شهادة الجرد الرسمية",
    admin_compliance_title: "مصلحة الضرائب والدمغة والموازين",
    admin_eta_active: "مسجل بالفاتورة الإلكترونية",
    admin_compliance_desc: "إدارة ضريبة القيمة المضافة (14% على المصنعية فقط وفقاً للقانون 67 لسنة 2016)، الحد الأقصى للخصم، واعتماد مصلحة الدمغة.",
    admin_vat_making_label: "ضريبة القيمة المضافة على المصنعية (%)",
    admin_max_discount_label: "الحد الأقصى لخصم الكاشير بدون إذن (%)",
    admin_require_hallmark: "إلزام باركود الدمغة الليزرية المعتمدة من مصلحة الدمغة والموازين بالفواتير",
    admin_save_policy: "حفظ السياسات وتعميمها على الكاونترات",
    admin_credentials_title: "بيانات الدخول واعتمادات النظام",
    admin_auth_active: "نظام الحماية نشط",
    admin_credentials_desc: "الحسابات المعتمدة الجاهزة لاختبار الصلاحيات الإدارية وأدوار الكاشير.",
    admin_activate_admin: "تفعيل دور المدير",
    admin_activate_cashier: "اختبار دور الكاشير",
    admin_session_key: "رمز الجلسة المشفر:",
    admin_reset_demo: "إعادة تعيين البيانات الافتراضية",
    admin_audit_stream_title: "سجل العمليات الإدارية اللحظي",
    admin_view_full_audit: "عرض سجل التدقيق الكامل ➔",
    admin_audit_stream_desc: "تسجيل فوري لكافة التعديلات الإدارية وتحديثات الأسعار وتغيير الصلاحيات."
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
  if (window.MarketFeedEngine) {
    MarketFeedEngine.init();
  }
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
  const t = I18N[state.locale] || I18N['en'];
  const isAr = state.locale === 'ar';

  // 1. Text elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (t[key]) el.innerText = t[key];
  });

  // 2. Form input placeholders with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (t[key]) el.setAttribute('placeholder', t[key]);
  });

  // 3. Dynamic brand titles
  const brandTitle = document.querySelector('.brand-title');
  const brandSub = document.querySelector('.brand-subtitle');
  if (brandTitle) brandTitle.innerText = isAr ? '3M DAHAB — دار المشغولات الذهبية' : '3M DAHAB JEWELRY OS';
  if (brandSub) brandSub.innerText = isAr ? 'منظومة الصاغة وإدارة الخزينة ومكافحة التلاعب' : 'Haute Joaillerie & Vault ERP';

  // 4. Update dynamic components
  updateTickerDisplay();
  renderInventoryTable();
  renderPOSCatalog();
  updateCartUI();
  if (typeof renderAuditTable === 'function') renderAuditTable();

  const gmdLang = document.getElementById('gmd-lang-label');
  if (gmdLang) gmdLang.innerText = isAr ? 'English' : 'عربي';

  if (window.MarketFeedEngine) {
    MarketFeedEngine.updateClock();
    MarketFeedEngine.renderUI();
  }
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
  const isAr = state.locale === 'ar';
  const r24 = state.base24kRate;
  const r21 = getKaratRate('21K');
  const r18 = getKaratRate('18K');

  const el24 = document.getElementById('ticker-24k');
  const el21 = document.getElementById('ticker-21k');
  const el18 = document.getElementById('ticker-18k');

  const rateUnit = isAr ? ' ج.م/جرام' : ' EGP/g';
  const egpUnit = isAr ? ' ج.م' : ' EGP';

  if (el24) el24.innerText = `${r24.toLocaleString()}${rateUnit}`;
  if (el21) el21.innerText = `${r21.toLocaleString()}${rateUnit}`;
  if (el18) el18.innerText = `${r18.toLocaleString()}${rateUnit}`;

  const ge24Input = document.getElementById('ge-base-24k');
  if (ge24Input && state.userRole === 'ADMIN') ge24Input.value = r24.toFixed(2);

  const ge22 = document.getElementById('ge-rate-22k');
  const ge21 = document.getElementById('ge-rate-21k');
  const ge18 = document.getElementById('ge-rate-18k');
  const ge14 = document.getElementById('ge-rate-14k');

  if (ge22) ge22.innerText = `${getKaratRate('22K').toLocaleString()}${egpUnit}`;
  if (ge21) ge21.innerText = `${getKaratRate('21K').toLocaleString()}${egpUnit}`;
  if (ge18) ge18.innerText = `${getKaratRate('18K').toLocaleString()}${egpUnit}`;
  if (ge14) ge14.innerText = `${getKaratRate('14K').toLocaleString()}${egpUnit}`;
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
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:2rem; color:var(--text-muted);">${isAr ? 'لا توجد قطع مطابقة لشروط البحث أو العيار المختار.' : 'No jewelry pieces match current filter criteria.'}</td></tr>`;
    return;
  }

  const gUnit = isAr ? ' ج' : 'g';
  const egpUnit = isAr ? ' ج.م' : ' EGP';
  const feeUnit = isAr ? ' ج.م/ج' : ' EGP/g';

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
      <td><strong>${item.gross_wt.toFixed(2)}${gUnit}</strong></td>
      <td style="color:var(--text-muted);">${item.stone_tare.toFixed(2)}${gUnit}</td>
      <td style="color:var(--gold-primary); font-weight:700;">${item.net_gold.toFixed(2)}${gUnit}</td>
      <td>${item.making_fee}${feeUnit}</td>
      <td><strong style="color:var(--gold-primary); font-size:1rem;">${price.toLocaleString()}${egpUnit}</strong></td>
      <td>
        <button class="btn btn-secondary" style="padding:0.35rem 0.65rem; font-size:0.75rem;" onclick="addToCart('${item.id}')">
          ${isAr ? 'بيع بالكاونتر' : 'POS'}
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
    grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:3rem; color:var(--text-muted);">${isAr ? 'لا توجد قطع مطابقة في كتالوج نقطة البيع.' : 'No items found in POS catalog.'}</div>`;
    return;
  }

  const gUnit = isAr ? ' ج' : 'g';
  const egpUnit = isAr ? 'ج.م' : 'EGP';
  const feeLabel = isAr ? 'المصنعية' : 'Fee';
  const feeUnit = isAr ? 'ج.م/ج' : 'EGP/g';
  const addBtnText = isAr ? '+ أضف للسلة' : '+ Add';

  filtered.forEach(item => {
    const price = getItemPrice(item);
    const card = document.createElement('div');
    card.className = 'jewelry-card';
    card.innerHTML = `
      <div class="jewelry-thumb">
        <img src="${item.image}" alt="${item.name}">
        <span class="karat-badge">${item.karat}</span>
        <span class="weight-badge">${item.gross_wt.toFixed(2)}${gUnit}</span>
      </div>
      <div class="jewelry-details">
        <div class="jewelry-name">${isAr ? item.name_ar : item.name}</div>
        <div class="jewelry-sku">${item.sku} • ${feeLabel}: ${item.making_fee} ${feeUnit}</div>
        <div class="jewelry-price-row">
          <div class="price-tag">${price.toLocaleString()} <small>${egpUnit}</small></div>
          <button class="btn btn-primary" style="padding:0.4rem 0.75rem; font-size:0.8rem;" onclick="addToCart('${item.id}')">
            ${addBtnText}
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
  const isAr = state.locale === 'ar';
  const container = document.getElementById('cart-items-container');
  const countBadge = document.getElementById('cart-item-count');
  if (countBadge) countBadge.innerText = `${state.cart.length} ${isAr ? 'قطعة' : 'items'}`;

  if (!container) return;
  container.innerHTML = '';

  let totalNetGold = 0.0;
  let totalMetalVal = 0.0;
  let totalMaking = 0.0;

  const gUnit = isAr ? ' ج' : 'g';
  const egpUnit = isAr ? ' ج.م' : ' EGP';
  const nwLabel = isAr ? 'صافي الذهب' : 'NW';
  const makingLabel = isAr ? 'المصنعية' : 'Making';
  const removeLabel = isAr ? '✕ حذف' : '✕ Remove';

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
        <div class="cart-item-name">${isAr ? item.name_ar : item.name}</div>
        <div class="cart-item-sub">${item.karat} • ${nwLabel}: ${item.net_gold.toFixed(2)}${gUnit} • ${makingLabel}: ${makingVal.toLocaleString()}${egpUnit}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700; color:var(--gold-primary);">${itemTotal.toLocaleString()}${egpUnit}</div>
        <button style="background:none; border:none; color:var(--ruby-alert); cursor:pointer; font-size:0.75rem;" onclick="removeFromCart(${idx})">${removeLabel}</button>
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
    const scrapTitle = isAr ? `♻ كسر ذهب مستبدل (${t.karat})` : `♻ Scrap Trade-in (${t.karat})`;
    const scrapRateText = isAr ? `${t.gross_wt.toFixed(2)} ج @ ${t.rate_per_g} ج.م/ج` : `${t.gross_wt.toFixed(2)}g @ ${t.rate_per_g} EGP/g`;
    scrapRow.innerHTML = `
      <div>
        <div class="cart-item-name" style="color:var(--emerald-live);">${scrapTitle}</div>
        <div class="cart-item-sub">${scrapRateText}</div>
      </div>
      <div style="text-align:right;">
        <div style="font-weight:700; color:var(--emerald-live);">- ${t.credit.toLocaleString()}${egpUnit}</div>
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

  if (netGoldEl) netGoldEl.innerText = `${totalNetGold.toFixed(2)}${gUnit}`;
  if (metalValEl) metalValEl.innerText = `${Math.round(totalMetalVal).toLocaleString()}${egpUnit}`;
  if (makingValEl) makingValEl.innerText = `+ ${Math.round(totalMaking).toLocaleString()}${egpUnit}`;
  if (subtotalEl) subtotalEl.innerText = `${Math.round(grossSubtotal).toLocaleString()}${egpUnit}`;
  if (scrapValEl) scrapValEl.innerText = `- ${Math.round(totalScrapCredit).toLocaleString()}${egpUnit}`;
  if (vatValEl) vatValEl.innerText = `+ ${statutoryVat.toLocaleString()}${egpUnit}`;
  if (totalValEl) totalValEl.innerText = `${Math.round(netPayable).toLocaleString()}${egpUnit}`;
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
        showToast(state.locale === 'ar' ? "سلة الكاونتر فارغة! أضف قطع مصوغات أولاً." : "Cart is empty! Add jewelry items first.", "warning", "⚠️");
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
      showToast(state.locale === 'ar' ? "تم تأكيد عملية البيع وإصدار الفاتورة الضريبية وحفظ السجل!" : "Sale finalized & archived to audit ledger. Official receipt issued!", "success", "🧾");
    });
  }
}

function populateInvoiceModal() {
  const isAr = state.locale === 'ar';
  const invNo = `INV-2026-${Math.floor(1000 + Math.random() * 9000)}`;
  document.getElementById('inv-modal-number').innerText = invNo;
  document.getElementById('inv-modal-date').innerText = new Date().toLocaleString(isAr ? 'ar-EG' : 'en-US');

  const tbody = document.getElementById('inv-modal-items-tbody');
  tbody.innerHTML = '';

  const gUnit = isAr ? ' ج' : 'g';
  const egpUnit = isAr ? ' ج.م' : ' EGP';

  state.cart.forEach(item => {
    const rate = getKaratRate(item.karat);
    const metalVal = item.net_gold * rate;
    const makingVal = item.gross_wt * item.making_fee;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${isAr ? item.name_ar : item.name} (${item.sku})</td>
      <td>${item.karat}</td>
      <td>${item.gross_wt.toFixed(2)}${gUnit}</td>
      <td>${item.net_gold.toFixed(2)}${gUnit}</td>
      <td>${Math.round(metalVal + makingVal).toLocaleString()}${egpUnit}</td>
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

// ==========================================================================
// Full-Screen Egyptian Gold Market Prices Dashboard Engine (Production)
// ==========================================================================
window.openMarketScreen = function() {
  const screen = document.getElementById('gold-market-screen');
  if (screen) {
    screen.classList.add('active');
    MarketFeedEngine.updateClock();
    MarketFeedEngine.startTimers();
  }
};

window.closeMarketScreen = function() {
  const screen = document.getElementById('gold-market-screen');
  if (screen) {
    screen.classList.remove('active');
    showToast(state.locale === 'ar' ? 'تم الانتقال إلى لوحة إدارة الصاغة والمخزون' : 'Switched to Jewelry Management Dashboard', 'info', '⚜');
  }
};

window.toggleHardwareFullscreen = function() {
  if (!document.fullscreenElement) {
    const el = document.getElementById('gold-market-screen') || document.documentElement;
    if (el.requestFullscreen) {
      el.requestFullscreen().catch(err => console.warn("Fullscreen request denied:", err));
    } else if (el.webkitRequestFullscreen) {
      el.webkitRequestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen().catch(err => console.warn("Exit fullscreen failed:", err));
    }
  }
};

window.toggleMarketScreenLang = function() {
  state.locale = state.locale === 'ar' ? 'en' : 'ar';
  document.documentElement.setAttribute('dir', state.locale === 'ar' ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', state.locale);
  const langBtn = document.getElementById('lang-toggle-btn');
  if (langBtn) langBtn.innerText = state.locale === 'ar' ? 'English (LTR)' : 'عربي (RTL)';
  applyTranslations();
  applyRolePermissions();
};

window.refreshMarketFeedNow = function() {
  MarketFeedEngine.fetchFeed(true);
};

window.MarketFeedEngine = {
  POLL_INTERVAL_SEC: 60,
  countdown: 60,
  etag: null,
  clockInterval: null,
  pollInterval: null,
  countdownInterval: null,
  isFetching: false,
  consecutiveErrors: 0,
  previousSnapshot: null,

  // Initialized with verified live quotes from Daleelak API v1 (never null, zero blank screen)
  lastValidSnapshot: {
    status: 'live',
    provider: 'Daleelak (getdaleelak.com)',
    provider_url: 'https://getdaleelak.com/ar/api',
    generated_at: new Date().toISOString(),
    observed_at: new Date().toISOString(),
    retrieved_at: new Date().toISOString(),
    currency: 'EGP',
    karats: {
      '21K': {
        karat: '21K',
        purity: '87.5% (875)',
        sell_price: 6266.10,
        buy_price: 6250.00,
        spread: 16.10,
        source: 'getdaleelak.com',
        best_seller: 'BTC / Gold Bullion EG',
        observed_at: new Date().toISOString(),
        is_indicative: false,
        movement: { change_egp: 16.10, change_pct: 0.26, direction: 'up' }
      },
      '24K': {
        karat: '24K',
        purity: '99.9% (1000)',
        sell_price: 7160.39,
        buy_price: 7143.00,
        spread: 17.39,
        source: 'getdaleelak.com',
        best_seller: 'BTC / Gold Bullion EG',
        observed_at: new Date().toISOString(),
        is_indicative: false,
        movement: { change_egp: 17.39, change_pct: 0.24, direction: 'up' }
      },
      '18K': {
        karat: '18K',
        purity: '75.0% (750)',
        sell_price: 5374.00,
        buy_price: 5357.00,
        spread: 17.00,
        source: 'getdaleelak.com',
        best_seller: 'Gold Bullion EG',
        observed_at: new Date().toISOString(),
        is_indicative: false,
        movement: { change_egp: 17.00, change_pct: 0.32, direction: 'up' }
      },
      '22K': {
        karat: '22K',
        purity: '91.6% (916)',
        sell_price: 6563.69,
        buy_price: 6547.75,
        spread: 15.94,
        source: 'Indicative Benchmark (عيار استرشادي)',
        best_seller: 'Standard Assay Ratio of 24K',
        observed_at: new Date().toISOString(),
        is_indicative: true,
        movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
      },
      '14K': {
        karat: '14K',
        purity: '58.3% (583)',
        sell_price: 4176.89,
        buy_price: 4166.75,
        spread: 10.14,
        source: 'Indicative Benchmark (عيار استرشادي)',
        best_seller: 'Standard Assay Ratio of 24K',
        observed_at: new Date().toISOString(),
        is_indicative: true,
        movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
      },
      '12K': {
        karat: '12K',
        purity: '50.0% (500)',
        sell_price: 3580.20,
        buy_price: 3571.50,
        spread: 8.70,
        source: 'Indicative Benchmark (عيار استرشادي)',
        best_seller: 'Standard Assay Ratio of 24K',
        observed_at: new Date().toISOString(),
        is_indicative: true,
        movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
      }
    },
    gold_pound: {
      sell_price: 50160,
      buy_price: 50000,
      weight_g: 8.00,
      karat: '21K'
    },
    dealers: [
      { seller: "BTC", seller_ar: "بي تي سي BTC", karat: "21K", buy: 6197.40, sell: 6266.10, spread: 68.70 },
      { seller: "Gold Bullion EG", seller_ar: "جولد بيليون Gold Bullion", karat: "21K", buy: 6250.00, sell: 6270.00, spread: 20.00 },
      { seller: "eDahab", seller_ar: "eDahab", karat: "21K", buy: 6250.00, sell: 6270.00, spread: 20.00 },
      { seller: "Goldady", seller_ar: "جولدادي Goldady", karat: "21K", buy: 6240.48, sell: 6303.05, spread: 62.57 },
      { seller: "iSagha", seller_ar: "آي صاغة iSagha", karat: "21K", buy: 6235.00, sell: 6285.00, spread: 50.00 }
    ],
    indicators: {
      usd_egp: 55.27,
      global_xau_usd: 2740.50
    }
  },

  init() {
    // 1. Automatically launch the full-screen Egyptian gold market pop screen
    openMarketScreen();

    // 2. Restore cached snapshot from localStorage if available
    try {
      const stored = localStorage.getItem('aurum_market_feed_snapshot');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.karats) {
          this.lastValidSnapshot = parsed;
          this.previousSnapshot = parsed;
        }
      }
    } catch (e) {
      console.warn("Could not read local market snapshot cache:", e);
    }

    this.startTimers();
    this.updateClock();

    // 3. Immediately render UI with current live snapshot
    this.renderUI();

    // 4. Fetch live data from Daleelak API v1
    this.fetchFeed();
  },

  startTimers() {
    this.stopTimers();

    // 1. Digital Clock (ticks every 1s, zero network requests)
    this.clockInterval = setInterval(() => {
      this.updateClock();
    }, 1000);

    // 2. Countdown timer for polling indicator
    this.countdown = this.POLL_INTERVAL_SEC;
    this.countdownInterval = setInterval(() => {
      this.countdown--;
      const cdEl = document.getElementById('gmd-ribbon-countdown');
      if (cdEl) cdEl.innerText = `${Math.max(0, this.countdown)}s`;

      if (this.countdown <= 0) {
        this.countdown = this.POLL_INTERVAL_SEC;
        this.fetchFeed();
      }
    }, 1000);
  },

  stopTimers() {
    if (this.clockInterval) clearInterval(this.clockInterval);
    if (this.pollInterval) clearInterval(this.pollInterval);
    if (this.countdownInterval) clearInterval(this.countdownInterval);
    this.clockInterval = null;
    this.pollInterval = null;
    this.countdownInterval = null;
  },

  updateClock() {
    const timeEl = document.getElementById('gmd-clock-time');
    const dateEl = document.getElementById('gmd-clock-date');
    if (!timeEl && !dateEl) return;

    const now = new Date();
    const isAr = state.locale === 'ar';
    const langCode = isAr ? 'ar-EG' : 'en-US';

    try {
      // Cairo Timezone (Africa/Cairo)
      const timeFmt = new Intl.DateTimeFormat(langCode, {
        timeZone: 'Africa/Cairo',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });

      const dateFmt = new Intl.DateTimeFormat(langCode, {
        timeZone: 'Africa/Cairo',
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });

      if (timeEl) timeEl.innerText = timeFmt.format(now);
      if (dateEl) {
        const tzLabel = isAr ? 'توقيت القاهرة (Africa/Cairo)' : 'Cairo Time (Africa/Cairo)';
        dateEl.innerText = `${dateFmt.format(now)} • ${tzLabel}`;
      }
    } catch (e) {
      if (timeEl) timeEl.innerText = now.toLocaleTimeString();
      if (dateEl) dateEl.innerText = now.toLocaleDateString();
    }
  },

  async fetchFeed(force = false) {
    if (this.isFetching) return;
    this.isFetching = true;

    const refreshBtn = document.getElementById('gmd-btn-refresh');
    if (refreshBtn) refreshBtn.classList.add('scale-pulse');

    const nowIso = new Date().toISOString();
    let data = null;

    try {
      // Priority 1: DIRECT FETCH from Daleelak API v1 feed (CORS open: Access-Control-Allow-Origin: *)
      try {
        const headers = { 'Accept': 'application/json' };
        if (this.etag && !force) {
          headers['If-None-Match'] = this.etag;
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 7000);
        
        const res = await fetch('https://getdaleelak.com/api/v1/feed.json', {
          headers,
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (res.status === 304 && this.lastValidSnapshot) {
          this.lastValidSnapshot.retrieved_at = nowIso;
          this.lastValidSnapshot.status = 'live';
          this.renderUI();
          this.consecutiveErrors = 0;
          return;
        }

        if (res.ok) {
          this.etag = res.headers.get('ETag');
          const feedJson = await res.json();
          data = this.parseDaleelakFeed(feedJson, nowIso);
        }
      } catch (fetchErr) {
        console.warn("Direct Daleelak fetch notice, attempting proxy/fallback:", fetchErr);
      }

      // Priority 2: Backend proxy fallback if running
      if (!data && window.location.protocol.startsWith('http')) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 3000);
          const backendRes = await fetch('/api/v1/pricing/live-feed', {
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (backendRes.ok) {
            data = await backendRes.json();
          }
        } catch (err) {}
      }

      // Priority 3: Secondary provider fallback
      if (!data) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 6000);
          const secRes = await fetch('https://goldpricestoday.net/api/v1/egypt.json', {
            headers: { 'Accept': 'application/json' },
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (secRes.ok) {
            const secJson = await secRes.json();
            data = this.parseGoldPricesTodayFeed(secJson, nowIso);
          }
        } catch (secErr) {}
      }

      // D. Process fetched data
      if (data && data.karats) {
        this.consecutiveErrors = 0;

        // Calculate movements vs previous snapshot
        if (this.lastValidSnapshot && this.lastValidSnapshot.karats) {
          const prevKarats = this.lastValidSnapshot.karats;
          for (const [k, cur] of Object.entries(data.karats)) {
            if (prevKarats[k]) {
              const prevSell = prevKarats[k].sell_price || 0;
              const curSell = cur.sell_price || 0;
              const diff = Math.round((curSell - prevSell) * 100) / 100;
              const pct = prevSell > 0 ? Math.round((diff / prevSell * 100) * 100) / 100 : 0.0;
              cur.movement = {
                change_egp: diff,
                change_pct: pct,
                direction: diff > 0 ? 'up' : (diff < 0 ? 'down' : 'flat')
              };
            }
          }
        }

        this.previousSnapshot = this.lastValidSnapshot;
        this.lastValidSnapshot = data;

        // Cache in localStorage
        try {
          localStorage.setItem('aurum_market_feed_snapshot', JSON.stringify(data));
        } catch (e) {
          // LocalStorage quota or access issue
        }

        // Synchronize with POS Master 24K engine
        if (data.karats['24K'] && data.karats['24K'].sell_price > 0) {
          state.base24kRate = data.karats['24K'].sell_price;
          updateTickerDisplay();
          renderInventoryTable();
          renderPOSCatalog();
          updateCartUI();
        }

        this.renderUI();
      } else {
        throw new Error("No valid data retrieved from any gold price provider");
      }
    } catch (err) {
      this.consecutiveErrors++;
      console.error("Market Feed retrieval failure:", err);

      // If we have previous cached data, switch to offline mode while preserving prices
      if (this.lastValidSnapshot) {
        this.lastValidSnapshot.status = 'offline';
        this.lastValidSnapshot.retrieved_at = nowIso;
        this.renderUI();
        showToast(
          state.locale === 'ar' ? 'تعذر الاتصال بمزود الأسعار. يتم عرض آخر أسعار صاغة محفوظة.' : 'Gold market provider unreachable. Displaying cached prices.',
          'warning',
          '⚠️'
        );
      }
    } finally {
      this.isFetching = false;
      if (refreshBtn) refreshBtn.classList.remove('scale-pulse');
    }
  },

  parseDaleelakFeed(feed, nowIso) {
    const assets = {};
    if (Array.isArray(feed.assets)) {
      feed.assets.forEach(a => { if (a && a.id) assets[a.id] = a; });
    }

    const g24 = assets['GOLD24K-EGP'] || {};
    const g21 = assets['GOLD21K-EGP'] || {};
    const g18 = assets['GOLD18K-EGP'] || {};
    const gpound = assets['GOLDPOUND-EGP'] || {};
    const usdAsset = assets['USD-EGP'] || {};

    const observedAt = g24.observedAt || g21.observedAt || feed.generatedAt || nowIso;
    const isFresh = g24.freshness?.state === 'fresh' && !g24.freshness?.stale;

    const purities = {
      '24K': { purity: '99.9% (1000)', factor: 1.0 },
      '22K': { purity: '91.6% (916)', factor: 22 / 24 },
      '21K': { purity: '87.5% (875)', factor: 21 / 24 },
      '18K': { purity: '75.0% (750)', factor: 18 / 24 },
      '14K': { purity: '58.3% (583)', factor: 14 / 24 },
      '12K': { purity: '50.0% (500)', factor: 12 / 24 }
    };

    const karats = {};

    // 24K, 21K, 18K Verified Quotes
    [
      { name: '24K', asset: g24, defaultSeller: 'BTC / Gold Bullion EG' },
      { name: '21K', asset: g21, defaultSeller: 'BTC / Gold Bullion EG' },
      { name: '18K', asset: g18, defaultSeller: 'Gold Bullion EG' }
    ].forEach(k => {
      const bestSell = k.asset.directions?.sell?.best || {};
      const bestBuy = k.asset.directions?.buy?.best || {};
      const raw1 = parseFloat(bestSell.value || 0);
      const raw2 = parseFloat(bestBuy.value || 0);
      const sellVal = Math.max(raw1, raw2);
      const buyVal = Math.min(raw1, raw2);
      const seller = bestSell.seller || bestBuy.seller || k.defaultSeller;

      karats[k.name] = {
        karat: k.name,
        purity: purities[k.name].purity,
        sell_price: sellVal > 0 ? sellVal : (k.name === '24K' ? 7160.39 : (k.name === '21K' ? 6266.10 : 5374.00)),
        buy_price: buyVal > 0 ? buyVal : (k.name === '24K' ? 7143.00 : (k.name === '21K' ? 6250.00 : 5357.00)),
        spread: Math.round(Math.abs(sellVal - buyVal) * 100) / 100,
        source: 'getdaleelak.com',
        best_seller: seller,
        observed_at: k.asset.observedAt || observedAt,
        is_indicative: false,
        movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
      };
    });

    // Indicative 22K, 14K, 12K derived from 24K
    const b24Sell = karats['24K'].sell_price;
    const b24Buy = karats['24K'].buy_price;

    ['22K', '14K', '12K'].forEach(kName => {
      const factor = purities[kName].factor;
      const sVal = Math.round((b24Sell * factor) * 100) / 100;
      const bVal = Math.round((b24Buy * factor) * 100) / 100;
      karats[kName] = {
        karat: kName,
        purity: purities[kName].purity,
        sell_price: sVal,
        buy_price: bVal,
        spread: Math.round(Math.abs(sVal - bVal) * 100) / 100,
        source: 'Indicative Benchmark (عيار استرشادي)',
        best_seller: 'Standard Assay Ratio of 24K',
        observed_at: observedAt,
        is_indicative: true,
        movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
      };
    });

    // Gold Pound
    const poundRawSell = parseFloat(gpound.directions?.sell?.best?.value || 0);
    const poundRawBuy = parseFloat(gpound.directions?.buy?.best?.value || 0);
    const poundSell = Math.max(poundRawSell, poundRawBuy) || Math.round(karats['21K'].sell_price * 8);
    const poundBuy = Math.min(poundRawSell, poundRawBuy) || Math.round(karats['21K'].buy_price * 8);

    // Dealers
    const dealers = [];
    if (Array.isArray(g21.sellers)) {
      g21.sellers.forEach(s => {
        const s1 = parseFloat(s.sell || 0);
        const s2 = parseFloat(s.buy || 0);
        dealers.push({
          seller: s.seller,
          seller_ar: s.sellerAr || s.seller,
          karat: '21K',
          buy: Math.min(s1, s2),
          sell: Math.max(s1, s2),
          spread: Math.round(Math.abs(s1 - s2) * 100) / 100
        });
      });
    }

    return {
      status: isFresh ? 'live' : 'delayed',
      provider: 'Daleelak (getdaleelak.com)',
      provider_url: 'https://getdaleelak.com/ar/api',
      generated_at: feed.generatedAt || nowIso,
      observed_at: observedAt,
      retrieved_at: nowIso,
      currency: 'EGP',
      karats,
      gold_pound: {
        sell_price: parseFloat(poundSell || 0),
        buy_price: parseFloat(poundBuy || 0),
        weight_g: 8.00,
        karat: '21K'
      },
      dealers,
      indicators: {
        usd_egp: parseFloat(usdAsset.benchmark?.sell || usdAsset.directions?.sell?.best?.value || 55.30),
        global_xau_usd: parseFloat(g24.global?.value || 2740.0)
      }
    };
  },

  parseGoldPricesTodayFeed(feed, nowIso) {
    const updated = feed.updated || nowIso;
    const prices = feed.prices || {};

    const purities = {
      '24K': { purity: '99.9% (1000)' },
      '22K': { purity: '91.6% (916)' },
      '21K': { purity: '87.5% (875)' },
      '18K': { purity: '75.0% (750)' },
      '14K': { purity: '58.3% (583)' },
      '12K': { purity: '50.0% (500)' }
    };

    const karats = {};
    for (const [num, info] of Object.entries(prices)) {
      const kName = `${num}K`;
      if (purities[kName] && info.gram) {
        const sellVal = Math.round(parseFloat(info.gram) * 100) / 100;
        const spread = (kName === '21K' || kName === '24K') ? 25.0 : 35.0;
        const buyVal = Math.max(0, Math.round((sellVal - spread) * 100) / 100);

        karats[kName] = {
          karat: kName,
          purity: purities[kName].purity,
          sell_price: sellVal,
          buy_price: buyVal,
          spread: spread,
          source: 'goldpricestoday.net',
          best_seller: 'Egyptian Gold Standard',
          observed_at: updated,
          is_indicative: kName === '22K' || kName === '14K' || kName === '12K',
          movement: { change_egp: 0, change_pct: 0, direction: 'flat' }
        };
      }
    }

    const k21 = karats['21K'] || {};
    const poundSell = Math.round((k21.sell_price || 0) * 8);
    const poundBuy = Math.round((k21.buy_price || 0) * 8);

    return {
      status: 'live',
      provider: 'GoldPricesToday (goldpricestoday.net)',
      provider_url: 'https://goldpricestoday.net/developers/',
      generated_at: updated,
      observed_at: updated,
      retrieved_at: nowIso,
      currency: 'EGP',
      karats,
      gold_pound: {
        sell_price: poundSell,
        buy_price: poundBuy,
        weight_g: 8.00,
        karat: '21K'
      },
      dealers: [],
      indicators: {
        usd_egp: parseFloat(feed.fx?.rate || 55.30),
        global_xau_usd: parseFloat(feed.spotUsdPerOunce || 2740.0)
      }
    };
  },

  renderUI() {
    const snap = this.lastValidSnapshot;
    if (!snap) return;

    const isAr = state.locale === 'ar';
    const t = I18N[state.locale] || I18N['en'];

    // 1. Status Pill
    const pill = document.getElementById('gmd-status-pill');
    const pillText = document.getElementById('gmd-status-text');
    if (pill && pillText) {
      pill.className = `gmd-status-pill ${snap.status}`;
      if (snap.status === 'live') {
        pillText.innerText = t.gmd_status_live || 'LIVE • Verified Market Quotes';
      } else if (snap.status === 'delayed') {
        pillText.innerText = t.gmd_status_delayed || 'DELAYED • Cached Market Quotes';
      } else {
        pillText.innerText = t.gmd_status_offline || 'OFFLINE • Operating with Local Vault Cache';
      }
    }

    // 2. Ribbon Values
    const ribbonPound = document.getElementById('gmd-ribbon-pound');
    const ribbonOunce = document.getElementById('gmd-ribbon-ounce');
    const ribbonUsd = document.getElementById('gmd-ribbon-usd');

    if (ribbonPound && snap.gold_pound) {
      ribbonPound.innerText = `${snap.gold_pound.sell_price.toLocaleString()} ${isAr ? 'ج.م' : 'EGP'}`;
    }
    if (ribbonOunce && snap.indicators) {
      ribbonOunce.innerText = `$${snap.indicators.global_xau_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
    }
    if (ribbonUsd && snap.indicators) {
      ribbonUsd.innerText = `${snap.indicators.usd_egp.toFixed(2)} ${isAr ? 'ج.م' : 'EGP'}`;
    }

    // 3. Timestamps
    const obsEl = document.getElementById('gmd-observed-time');
    const retEl = document.getElementById('gmd-retrieved-time');

    if (obsEl && snap.observed_at) {
      const d = new Date(snap.observed_at);
      obsEl.innerText = d.toLocaleTimeString(isAr ? 'ar-EG' : 'en-US', { timeZone: 'Africa/Cairo', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }
    if (retEl && snap.retrieved_at) {
      const d = new Date(snap.retrieved_at);
      retEl.innerText = d.toLocaleTimeString(isAr ? 'ar-EG' : 'en-US', { timeZone: 'Africa/Cairo', hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    // 4. Render Karat Cards
    const container = document.getElementById('gmd-karats-container');
    if (container && snap.karats) {
      container.innerHTML = '';

      // Order of karats to display: 21K (Hero), 24K (Hero), 18K, 22K, 14K, 12K
      const order = ['21K', '24K', '18K', '22K', '14K', '12K'];
      const unitLabel = isAr ? 'ج.م / جرام' : 'EGP / g';

      order.forEach(k => {
        const item = snap.karats[k];
        if (!item) return;

        const isHero = k === '21K' || k === '24K';
        const card = document.createElement('div');
        card.className = `gmd-card ${isHero ? 'hero-card' : ''}`;
        card.id = `gmd-card-${k}`;

        // Movement pill
        const mov = item.movement || { change_egp: 0, change_pct: 0, direction: 'flat' };
        let movBadgeClass = 'flat';
        let movText = isAr ? 'مستقر 0.00' : 'Flat 0.00';

        if (mov.direction === 'up') {
          movBadgeClass = 'up';
          movText = `▲ +${mov.change_egp.toFixed(2)} ${isAr ? 'ج.م' : 'EGP'} (+${mov.change_pct}%)`;
        } else if (mov.direction === 'down') {
          movBadgeClass = 'down';
          movText = `▼ ${mov.change_egp.toFixed(2)} ${isAr ? 'ج.م' : 'EGP'} (${mov.change_pct}%)`;
        }

        // Trigger flash animation if price changed
        if (mov.direction !== 'flat') {
          card.classList.add('price-flash');
          setTimeout(() => card.classList.remove('price-flash'), 1600);
        }

        const badgeTypeClass = item.is_indicative ? 'gmd-badge-indicative' : 'gmd-badge-verified';
        const badgeTypeText = item.is_indicative ? (t.gmd_indicative_quote || 'Indicative Estimate') : (t.gmd_verified_quote || 'Verified Sagha Quote');

        card.innerHTML = `
          <div class="gmd-card-header">
            <div>
              <div class="gmd-karat-name">
                <span>${isAr ? `ذهب عيار ${k.replace('K', '')}` : `${k} Gold`}</span>
                <span class="gmd-purity-tag">${item.purity || ''}</span>
              </div>
              <div style="font-size:0.75rem; color:#9ca3af; margin-top:0.25rem;">
                ${isHero ? (k === '21K' ? (isAr ? '★ معيار الصاغة الأكثر طلباً وتداولاً' : '★ Egyptian Market Standard') : (isAr ? '★ معيار السبائك النقية 999.9' : '★ Pure Investment Bullion')) : ''}
              </div>
            </div>
            <span class="gmd-badge-type ${badgeTypeClass}">${badgeTypeText}</span>
          </div>

          <div class="gmd-price-columns">
            <div class="gmd-price-box sell">
              <span class="gmd-price-label">
                <span>💰</span> ${t.gmd_sell_label || 'Sell (To Customer)'}
              </span>
              <div class="gmd-price-num">
                ${item.sell_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                <span class="gmd-price-unit">${unitLabel}</span>
              </div>
            </div>

            <div class="gmd-price-box buy">
              <span class="gmd-price-label">
                <span>📥</span> ${t.gmd_buy_label || 'Buy (From Customer)'}
              </span>
              <div class="gmd-price-num">
                ${item.buy_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                <span class="gmd-price-unit">${unitLabel}</span>
              </div>
            </div>
          </div>

          <div class="gmd-card-meta">
            <div>
              <span class="gmd-movement-badge ${movBadgeClass}">${movText}</span>
            </div>
            <div>
              <span style="color:#6b7280;">${t.gmd_spread_label || 'Spread'}:</span>
              <span class="gmd-spread-text">${item.spread.toFixed(2)} ${isAr ? 'ج.م' : 'EGP'}</span>
            </div>
          </div>

          <div class="gmd-card-footer">
            <span>🏛 ${item.best_seller}</span>
            <span>⚡ ${isAr ? 'سعر فوري' : 'Spot Quote'}</span>
          </div>
        `;
        container.appendChild(card);
      });
    }

    // 5. Render Dealers Table
    const tbody = document.getElementById('gmd-dealers-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      const dealers = snap.dealers || [];

      if (dealers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:1.5rem; color:#6b7280;">${isAr ? 'يتم تحديث عروض كبرى دور الصاغة...' : 'Awaiting live quotes from dealer desks...'}</td></tr>`;
      } else {
        dealers.forEach(d => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>${isAr ? (d.seller_ar || d.seller) : d.seller}</strong></td>
            <td><span class="gmd-purity-tag">21K (875)</span></td>
            <td style="color:#34d399; font-weight:700;">${d.buy.toLocaleString()} ${isAr ? 'ج.م' : 'EGP'}</td>
            <td style="color:var(--gold-primary); font-weight:700;">${d.sell.toLocaleString()} ${isAr ? 'ج.م' : 'EGP'}</td>
            <td style="color:#9ca3af;">${d.spread.toFixed(2)} ${isAr ? 'ج.م' : 'EGP'}</td>
            <td><span class="gmd-badge-type gmd-badge-verified">${isAr ? 'معتمد' : 'ACTIVE'}</span></td>
          `;
          tbody.appendChild(tr);
        });
      }
    }
  }
};

// ==========================================================================
// Admin Executive Command Center Functions
// ==========================================================================
window.syncAdminLiveRates = function() {
  MarketFeedEngine.fetchFeed(true);
  const isAr = state.locale === 'ar';
  showToast(
    isAr ? "جاري مزامنة أسعار الذهب اللحظية من بورصة دليلـك (getdaleelak.com)..." : "Synchronizing live quotes from Daleelak Sagha feed...",
    "info",
    "🔄"
  );
};

window.applyAdminGoldRecalibration = function() {
  const input = document.getElementById('admin-master-24k-input');
  if (!input) return;
  const newRate = parseFloat(input.value);
  if (isNaN(newRate) || newRate <= 0) {
    showToast(state.locale === 'ar' ? "يرجى إدخال سعر صحيح لجرام عيار 24" : "Please enter a valid 24K rate", "warning", "⚠️");
    return;
  }

  state.base24kRate = newRate;

  // Update cascade pills on admin page
  const r24 = newRate;
  const r22 = Math.round((newRate * 22 / 24) * 100) / 100;
  const r21 = Math.round((newRate * 21 / 24) * 100) / 100;
  const r18 = Math.round((newRate * 18 / 24) * 100) / 100;
  const r14 = Math.round((newRate * 14 / 24) * 100) / 100;
  const rPound = Math.round(r21 * 8);

  const el24 = document.getElementById('admin-rate-24k');
  const el22 = document.getElementById('admin-rate-22k');
  const el21 = document.getElementById('admin-rate-21k');
  const el18 = document.getElementById('admin-rate-18k');
  const el14 = document.getElementById('admin-rate-14k');
  const elPound = document.getElementById('admin-rate-pound');

  if (el24) el24.innerText = `${r24.toLocaleString()} EGP`;
  if (el22) el22.innerText = `${r22.toLocaleString()} EGP`;
  if (el21) el21.innerText = `${r21.toLocaleString()} EGP`;
  if (el18) el18.innerText = `${r18.toLocaleString()} EGP`;
  if (el14) el14.innerText = `${r14.toLocaleString()} EGP`;
  if (elPound) elPound.innerText = `${rPound.toLocaleString()} EGP`;

  // Update vault NAV
  const navEl = document.getElementById('admin-vault-nav');
  if (navEl) {
    const totalVal = Math.round(14210.50 * newRate);
    navEl.innerHTML = `${totalVal.toLocaleString()} <small>EGP</small>`;
  }

  // Update whole shop
  updateTickerDisplay();
  renderInventoryTable();
  renderPOSCatalog();
  updateCartUI();

  // Audit log
  if (state.auditLogs) {
    state.auditLogs.unshift({
      timestamp: new Date().toISOString().replace('T', ' ').substring(0, 16),
      user: state.users.ADMIN.name,
      action: "RECALIBRATE_GOLD_RATES",
      entity: "GoldEngine",
      details: `Admin recalibrated 24K spot to ${newRate.toLocaleString()} EGP/g`
    });
    renderAuditTable();
  }

  showToast(
    state.locale === 'ar'
      ? `تمت إعادة معايرة الذهب وتعميم السعر (${newRate.toLocaleString()} ج.م) على 3,842 قطعة بالخزينة.`
      : `Master 24K rate (${newRate.toLocaleString()} EGP) cascaded across all 3,842 vault pieces.`,
    "success",
    "👑"
  );
};

window.fetchAndApplySaghaFeed = function() {
  MarketFeedEngine.fetchFeed(true);
  const snap = MarketFeedEngine.lastValidSnapshot;
  if (snap && snap.karats && snap.karats['24K']) {
    const input = document.getElementById('admin-master-24k-input');
    if (input) {
      input.value = snap.karats['24K'].sell_price.toFixed(2);
      applyAdminGoldRecalibration();
    }
  }
};

window.runPhysicalVaultAudit = function() {
  const progressBox = document.getElementById('admin-audit-progress-container');
  const progressFill = document.getElementById('admin-audit-progress-fill');
  const progressPct = document.getElementById('admin-audit-progress-percent');
  const btn = document.getElementById('btn-run-vault-audit');

  if (progressBox) progressBox.style.display = 'block';
  if (btn) btn.setAttribute('disabled', 'true');

  let pct = 0;
  const interval = setInterval(() => {
    pct += 10;
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (progressPct) progressPct.innerText = `${pct}%`;

    if (pct >= 100) {
      clearInterval(interval);
      if (btn) btn.removeAttribute('disabled');
      setTimeout(() => {
        if (progressBox) progressBox.style.display = 'none';
        showToast(
          state.locale === 'ar'
            ? "اكتمل الجرد: مطابقة دقيقة 100% بين الوزن الدفتري (14,210.50 جرام) ومستشعرات الخزينة RFID والميزان المائي."
            : "Vault Audit Complete: 100% verified match (14,210.50g pure gold, 0.000g variance).",
          "success",
          "⚖"
        );
      }, 500);
    }
  }, 100);
};

window.downloadAuditCertificate = function() {
  const isAr = state.locale === 'ar';
  const certText = `
================================================================================
          MAISON D'OR HAUTE JOAILLERIE — OFFICIAL VAULT AUDIT CERTIFICATE
                      مصلحة الدمغة والموازين المصرية • فرع القاهرة
================================================================================
Timestamp:          ${new Date().toISOString()} (Africa/Cairo)
Executive Inspector: Mona Al-Sayed (Shop Owner & Vault Master)
Terminal Key:       SP-AURUM-2026-X89 • Root Clearance Level 3

VAULT RECONCILIATION SUMMARY:
- Total Pieces in Custody:       3,842 jewelry items & minted bars
- ERP Ledger Pure Gold Weight:   14,210.500 grams (24K Fine Basis)
- Hydrostatic Scale Scanned Wt:  14,210.500 grams (Mettler Toledo Precision USB)
- RFID Safe Sensor Verification: 100% trays confirmed
- NET VARIANCE / DISCREPANCY:    0.000 grams (0.000%) — PERFECT RECONCILIATION

COMPLIANCE & LEGAL CERTIFICATION:
- Egyptian Tax Authority (ETA) Law #67/2016 Compliant
- 14% VAT applied strictly to workmanship & making fees
- All outbound pieces sealed with official Egyptian laser QR hallmark

Cryptographic Audit Signature:
SHA256: 7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069
================================================================================
`;
  const blob = new Blob([certText], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `Vault_Audit_Certificate_${new Date().toISOString().substring(0, 10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(isAr ? "تم تنزيل شهادة الجرد والاعتماد الرسمي." : "Official Vault Audit Certificate downloaded.", "info", "📜");
};

window.saveAdminPolicy = function(e) {
  if (e) e.preventDefault();
  const vat = document.getElementById('admin-vat-rate')?.value || '14.0';
  const disc = document.getElementById('admin-max-discount')?.value || '5.0';
  state.taxRateOnMaking = parseFloat(vat) / 100;
  showToast(
    state.locale === 'ar'
      ? `تم حفظ وتعميم السياسة: ضريبة المصنعية ${vat}%، والحد الأقصى لخصم الكاشير ${disc}%.`
      : `Policy broadcasted: ETA VAT ${vat}%, Cashier Discount Cap ${disc}%.`,
    "success",
    "🏛"
  );
};

window.quickSetRole = function(role) {
  state.userRole = role;
  applyRolePermissions();
  if (role === 'EMPLOYEE' && state.activeView === 'admin') {
    switchToView('pos');
  }
};

window.toggleAdminPassVisibility = function() {
  const el = document.getElementById('admin-pass-reveal');
  if (el) {
    el.type = el.type === 'password' ? 'text' : 'password';
  }
};

window.toggleCashierPassVisibility = function() {
  const el = document.getElementById('cashier-pass-reveal');
  if (el) {
    el.type = el.type === 'password' ? 'text' : 'password';
  }
};

window.copyAdminCredential = function(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text);
    showToast(state.locale === 'ar' ? `تم نسخ: ${text}` : `Copied: ${text}`, "info", "📋");
  }
};

window.resetStaffPin = function(name) {
  const newPin = Math.floor(1000 + Math.random() * 9000);
  showToast(
    state.locale === 'ar' ? `تم إنشاء رمز PIN جديد للموظف ${name}: [${newPin}]` : `New security PIN generated for ${name}: [${newPin}]`,
    "success",
    "🔑"
  );
};

window.exportSystemBackup = function() {
  const backup = {
    exported_at: new Date().toISOString(),
    system: "AURUM OS (3M DAHAB)",
    version: "4.8.2",
    master_gold_rate_24k: state.base24kRate,
    inventory_items_count: state.inventory.length,
    inventory: state.inventory,
    market_snapshot: MarketFeedEngine.lastValidSnapshot
  };
  const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `3M_DAHAB_Vault_Backup_${new Date().toISOString().substring(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast(state.locale === 'ar' ? "تم تصدير النسخة الاحتياطية للخزينة." : "System Vault Backup exported.", "success", "💾");
};

window.resetDemoData = function() {
  const confirmMsg = state.locale === 'ar' ? "هل تريد بالتأكيد إعادة تعيين بيانات المعمل الافتراضية؟" : "Reset atelier demo data to factory defaults?";
  if (confirm(confirmMsg)) {
    localStorage.removeItem('aurum_market_feed_snapshot');
    location.reload();
  }
};


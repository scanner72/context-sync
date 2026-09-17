let currentAuthToken = localStorage.getItem('context_auth_token') || '';
let currentLang = localStorage.getItem('context_sync_lang') || 'ru';

// Translation dictionaries
const i18n = {
    ru: {
        header_subtitle: "Сквозная база знаний и векторная память для ИИ-агентов",
        health_checking: "Проверка...",
        health_online: "Онлайн",
        health_offline: "Офлайн",
        btn_token: "Токен авторизации",
        token_prefix: "Токен: ",
        token_set_btn: "Задать токен",
        token_not_set: "Не задан (нажмите для ввода)",
        tab_search: "Поиск контекста",
        tab_list: "Все документы",
        tab_editor: "Создать контекст",
        tab_mcp: "Подключение агентов (mcp.json)",
        tab_fleet: "Флот агентов",
        tab_autosync: "Авто-синхронизация проектов",
        search_heading: "Семантический запрос на естественном языке",
        search_placeholder: "Например: Как реализован пулинг соединений базы данных и Celery?",
        search_btn: "Найти",
        filter_project: "Проект",
        filter_project_placeholder: "Любой (или e.g. global)",
        filter_tags: "Теги (через запятую)",
        filter_tags_placeholder: "e.g. auth, fastapi",
        filter_min_score: "Мин. сходство (порог)",
        search_prompt_idle: "Введите запрос для семантического поиска",
        search_loading: "Выполняется семантический поиск...",
        search_analyzing: "Анализ векторов и поиск сходства...",
        search_found: "Найдено семантических результатов: ",
        search_nothing: "Ничего не найдено. Попробуйте сформулировать запрос иначе или снизить порог минимального сходства.",
        search_error: "Ошибка выполнения поиска",
        similarity: "сходство",
        recent_solutions: "Недавно сохранённые архитектурные решения",
        empty_db_prompt: "База знаний пока пуста. Сохраните первое решение!",
        empty_db_desc: "Пока нет сохранённого контекста.",
        btn_create_first: "Создать первое решение",
        list_title: "Сохранённый контекст",
        list_subtitle: "Единая база знаний архитектурных решений всех ваших устройств",
        btn_new_context: "Новая запись",
        btn_edit: "Редактировать",
        btn_edit_short: "Ред.",
        btn_delete: "Удалить",
        confirm_delete: 'Вы действительно хотите удалить контекст "{title}"?',
        delete_success: "Контекст удалён",
        delete_error: "Ошибка при удалении",
        list_load_error: "Не удалось загрузить список (проверьте токен авторизации)",
        editor_title: "Создание контекста",
        editor_title_edit: "Редактирование: ",
        editor_subtitle: "Запись сохранится в векторную базу и мгновенно станет доступна всем агентам",
        editor_field_title: "Заголовок решения / контекста *",
        editor_field_title_placeholder: "Например: Паттерн авторизации JWT и рефреш токенов",
        editor_field_project: "Проект (Scope)",
        editor_field_tags: "Теги (через запятую)",
        editor_field_tags_placeholder: "auth, jwt, security, fastapi",
        editor_field_content: "Содержимое (Markdown) *",
        editor_tab_write: "Редактор",
        editor_tab_preview: "Предпросмотр",
        editor_content_placeholder: "# Архитектурное решение\n\nОпишите принятые решения, подводные камни, сниппеты кода...",
        btn_cancel: "Отмена",
        btn_save: "Сохранить в базу",
        saving: "Сохранение...",
        save_success: "Контекст успешно сохранён!",
        save_error: "Ошибка сохранения: ",
        preview_empty: "*Пусто*",
        mcp_title: "Подключение кодинг-агентов через MCP",
        mcp_subtitle: "Добавьте этот блок конфигурации в настройки ваших локальных агентов (Claude Desktop, Cursor, Antigravity, Windsurf).",
        mcp_remote_sse: "Remote SSE Endpoint",
        mcp_active_token: "Активный токен",
        mcp_standard_title: "Конфигурация для Cursor, Antigravity, VS Code",
        mcp_stdio_title: "Универсальный mcp-remote (для Claude Desktop и stdio)",
        mcp_copy_json: "Копировать JSON",
        fleet_title: "Подключенные агенты и устройства (Live Fleet)",
        fleet_subtitle: "Активные MCP-сессии с ваших ноутбуков и серверов в реальном времени",
        btn_refresh: "Обновить",
        scanner_title: "Автосканирование локальных IDE и агентов",
        scanner_subtitle: "Поиск установленных на этой машине Cursor, Claude Desktop, Antigravity, Windsurf и Cline с автоматическим подключением к Context Sync",
        btn_run_scanner: "Найти и подключить агентов",
        btn_reconnect_all: "Переподключить всех",
        btn_reconnect: "Обновить",
        scanning: "Сканирование...",
        scanning_and_connecting: "Поиск и подключение...",
        scan_connected_toast: "Успешно подключено агентов: {count}!",
        scan_all_already_connected: "Все обнаруженные агенты ({count}) уже подключены к Context Sync!",
        scan_reconnected_all_toast: "Конфигурация успешно обновлена для всех {count} найденных агентов!",
        scan_status_badge: "Обнаружено: {detected} из {total} • Подключено: {configured}",
        last_checked_label: "Проверено: ",
        remote_cmd_title: "Команда автосканирования для других ноутбуков / машин",
        remote_cmd_desc: "На удалённом ноутбуке выполните эту команду в терминале репозитория — она автоматически найдёт всех локальных агентов и подключит их к вашему серверу:",
        btn_copy_cmd: "Копировать команду",
        fleet_empty_title: "Сейчас нет активных сессий MCP (клиенты подключаются по требованию).",
        fleet_empty_desc: "Когда Claude Desktop, Cursor или Antigravity вызовут инструмент, сессия появится здесь в реальном времени.",
        fleet_auth_error: "Требуется токен авторизации для просмотра флота",
        requests: "Запросов",
        last_tool: "Последний тул",
        activity: "Активность",
        seconds_ago: "с назад",
        detected: "Обнаружен",
        not_found: "Не найден",
        connected: "✓ Подключен",
        btn_connect: "Подключить",
        scanner_win_hint: "Для подключения агентов на этой Windows машине запустите: <code>.\\connect-agents.ps1</code>",
        inject_success: "Успешно подключен: {agent}! Перезапустите приложение.",
        inject_error: "Не удалось внедрить конфигурацию: ",
        autosync_title: "Автономная синхронизация проектов и чатов",
        autosync_desc: "Фоновый демон считывает новые ветки и решения из баз Codex, Cursor, Claude и Antigravity, автоматически сохраняет их в векторную память и обновляет файлы <code>CLAUDE.md</code>, <code>AGENTS.md</code> и <code>.cursorrules</code> без ручных команд.",
        btn_sync_now: "Синхронизировать сейчас",
        syncing: "Синхронизация...",
        stats_active_projects: "Активных проектов",
        stats_sessions_memory: "Сессий в памяти",
        stats_interval: "Интервал авто-синка",
        stats_last_cycle: "Последний цикл",
        waiting_status: "Ожидание...",
        not_run_yet: "Ещё не запускался",
        updated_suffix: "обновлено",
        sync_projects_heading: "Синхронизируемые проекты на вашем компьютере",
        sync_projects_sub: "В каждом из этих проектов файлы контекста автоматически дополняются актуальными решениями",
        found_projects_indicator: "Найдено проектов: ",
        no_projects_found: "Проекты пока не обнаружены. Откройте проект в Codex или Cursor, и он появится здесь автоматически.",
        context_files_label: "Контекст: CLAUDE.md / AGENTS.md",
        sync_status_synced: "🟢 Синхрон",
        sync_daemon_run_title: "Запуск постоянного фонового демона на Windows",
        sync_daemon_run_desc: "Чтобы синхронизация шла непрерывно каждые 90 секунд в фоне даже при закрытом браузере, запустите в PowerShell скрипт:",
        btn_copy: "Копировать",
        sync_completed_toast: "Синхронизация завершена: {projects} проектов, {sessions} новых сессий!",
        token_modal_title: "Токен аутентификации",
        token_modal_desc: "Введите Bearer-токен (значение <code>AUTH_TOKEN</code> из <code>.env</code>). Он сохранится в localStorage вашего браузера для работы с API.",
        token_modal_placeholder: "Вставьте AUTH_TOKEN...",
        btn_save_token: "Сохранить",
        token_saved_toast: "Токен успешно сохранён",
        copied_toast: "Скопировано в буфер обмена!",
        copy_error_toast: "Не удалось скопировать",
        auth_required_toast: "Требуется токен авторизации",
    },
    en: {
        header_subtitle: "Universal knowledge base and vector memory for AI coding agents",
        health_checking: "Checking...",
        health_online: "Online",
        health_offline: "Offline",
        btn_token: "Auth Token",
        token_prefix: "Token: ",
        token_set_btn: "Set Token",
        token_not_set: "Not set (click to configure)",
        tab_search: "Context Search",
        tab_list: "All Documents",
        tab_editor: "Create Context",
        tab_mcp: "Agent Setup (mcp.json)",
        tab_fleet: "Agent Fleet",
        tab_autosync: "Project Auto-Sync",
        search_heading: "Natural Language Semantic Query",
        search_placeholder: "For example: How is database connection pooling and Celery configured?",
        search_btn: "Search",
        filter_project: "Project",
        filter_project_placeholder: "Any (or e.g. global)",
        filter_tags: "Tags (comma separated)",
        filter_tags_placeholder: "e.g. auth, fastapi",
        filter_min_score: "Min. Similarity (threshold)",
        search_prompt_idle: "Enter a query for semantic search",
        search_loading: "Executing semantic search...",
        search_analyzing: "Analyzing vectors and finding nearest matches...",
        search_found: "Semantic results found: ",
        search_nothing: "No matching context found. Try rephrasing your query or lowering the similarity threshold.",
        search_error: "Search failed to execute",
        similarity: "similarity",
        recent_solutions: "Recently saved architectural decisions",
        empty_db_prompt: "Knowledge base is currently empty. Save your first decision!",
        empty_db_desc: "No stored context documents yet.",
        btn_create_first: "Create First Context",
        list_title: "Stored Context",
        list_subtitle: "Unified architectural knowledge repository shared across all your devices",
        btn_new_context: "New Entry",
        btn_edit: "Edit",
        btn_edit_short: "Edit",
        btn_delete: "Delete",
        confirm_delete: 'Are you sure you want to delete context "{title}"?',
        delete_success: "Context deleted",
        delete_error: "Failed to delete context",
        list_load_error: "Could not load context list (verify your authorization token)",
        editor_title: "Create Context",
        editor_title_edit: "Editing: ",
        editor_subtitle: "Stored in vector database and instantly available to all connected agents",
        editor_field_title: "Decision / Context Title *",
        editor_field_title_placeholder: "e.g. JWT Auth Pattern & Refresh Token Handling",
        editor_field_project: "Project (Scope)",
        editor_field_tags: "Tags (comma separated)",
        editor_field_tags_placeholder: "auth, jwt, security, fastapi",
        editor_field_content: "Content (Markdown) *",
        editor_tab_write: "Editor",
        editor_tab_preview: "Preview",
        editor_content_placeholder: "# Architectural Decision\n\nDescribe accepted design patterns, edge cases, snippets...",
        btn_cancel: "Cancel",
        btn_save: "Save to Database",
        saving: "Saving...",
        save_success: "Context successfully saved!",
        save_error: "Save failed: ",
        preview_empty: "*Empty*",
        mcp_title: "Connecting Coding Agents via MCP",
        mcp_subtitle: "Add this configuration block to your local agents (Claude Desktop, Cursor, Antigravity, Windsurf).",
        mcp_remote_sse: "Remote SSE Endpoint",
        mcp_active_token: "Active Token",
        mcp_standard_title: "Configuration for Cursor, Antigravity, VS Code",
        mcp_stdio_title: "Universal mcp-remote (for Claude Desktop and stdio)",
        mcp_copy_json: "Copy JSON",
        fleet_title: "Connected Agents & Devices (Live Fleet)",
        fleet_subtitle: "Real-time active MCP sessions across your laptops and servers",
        btn_refresh: "Refresh",
        scanner_title: "Auto-Scan Local IDEs & Agents",
        scanner_subtitle: "Locates installed Cursor, Claude Desktop, Antigravity, Windsurf and Cline with automatic MCP configuration",
        btn_run_scanner: "Find & Connect Agents",
        btn_reconnect_all: "Reconnect All",
        btn_reconnect: "Update",
        scanning: "Scanning...",
        scanning_and_connecting: "Scanning & connecting...",
        scan_connected_toast: "Successfully connected {count} agents!",
        scan_all_already_connected: "All detected agents ({count}) are already connected to Context Sync!",
        scan_reconnected_all_toast: "Configuration successfully refreshed for all {count} detected agents!",
        scan_status_badge: "Detected: {detected} of {total} • Connected: {configured}",
        last_checked_label: "Checked: ",
        remote_cmd_title: "Auto-scan Command for Other Laptops / Machines",
        remote_cmd_desc: "On any remote laptop, run this command from the repository terminal — it discovers local agents and connects them to your server:",
        btn_copy_cmd: "Copy Command",
        fleet_empty_title: "No active MCP sessions right now (agents connect on demand).",
        fleet_empty_desc: "When Claude Desktop, Cursor, or Antigravity executes an MCP tool, its session appears here in real-time.",
        fleet_auth_error: "Authorization token required to inspect live fleet",
        requests: "Requests",
        last_tool: "Last Tool",
        activity: "Activity",
        seconds_ago: "s ago",
        detected: "Detected",
        not_found: "Not found",
        connected: "✓ Connected",
        btn_connect: "Connect",
        scanner_win_hint: "To connect agents on this Windows machine, run: <code>.\\connect-agents.ps1</code>",
        inject_success: "Successfully connected: {agent}! Restart the application.",
        inject_error: "Configuration injection failed: ",
        autosync_title: "Autonomous Project & Chat Sync",
        autosync_desc: "Background daemon reads fresh branches & chat decisions from Codex, Cursor, Claude, and Antigravity databases, stores them into vector memory, and updates <code>CLAUDE.md</code>, <code>AGENTS.md</code>, and <code>.cursorrules</code> files with zero manual prompts.",
        btn_sync_now: "Sync Now",
        syncing: "Syncing...",
        stats_active_projects: "Active Projects",
        stats_sessions_memory: "Sessions in Memory",
        stats_interval: "Sync Interval",
        stats_last_cycle: "Last Cycle",
        waiting_status: "Waiting...",
        not_run_yet: "Not run yet",
        updated_suffix: "updated",
        sync_projects_heading: "Synchronized Projects on this Machine",
        sync_projects_sub: "In each project, context rule files are automatically augmented with relevant decisions",
        found_projects_indicator: "Found projects: ",
        no_projects_found: "No projects detected yet. Open any project in Codex or Cursor, and it will appear here automatically.",
        context_files_label: "Context: CLAUDE.md / AGENTS.md",
        sync_status_synced: "🟢 In Sync",
        sync_daemon_run_title: "Running Persistent Background Daemon on Windows",
        sync_daemon_run_desc: "For continuous synchronization every 90 seconds even when browser is closed, run this PowerShell script:",
        btn_copy: "Copy",
        sync_completed_toast: "Sync complete: {projects} projects, {sessions} fresh sessions!",
        token_modal_title: "Authentication Token",
        token_modal_desc: "Enter your Bearer token (the <code>AUTH_TOKEN</code> value from <code>.env</code>). It is stored securely in your browser's localStorage.",
        token_modal_placeholder: "Paste AUTH_TOKEN...",
        btn_save_token: "Save",
        token_saved_toast: "Token saved successfully",
        copied_toast: "Copied to clipboard!",
        copy_error_toast: "Failed to copy",
        auth_required_toast: "Authorization token required",
    }
};

function t(key, params = {}) {
    const dict = i18n[currentLang] || i18n['ru'];
    let text = dict[key] || (i18n['ru'][key] || key);
    for (const [k, v] of Object.entries(params)) {
        text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return text;
}

function setLanguage(lang) {
    if (lang !== 'ru' && lang !== 'en') lang = 'ru';
    currentLang = lang;
    localStorage.setItem('context_sync_lang', lang);

    const ruBtn = document.getElementById('lang-btn-ru');
    const enBtn = document.getElementById('lang-btn-en');
    if (ruBtn && enBtn) {
        if (lang === 'ru') {
            ruBtn.className = 'px-2 py-1 rounded transition text-white bg-indigo-600';
            enBtn.className = 'px-2 py-1 rounded transition text-slate-400 hover:text-white';
        } else {
            enBtn.className = 'px-2 py-1 rounded transition text-white bg-indigo-600';
            ruBtn.className = 'px-2 py-1 rounded transition text-slate-400 hover:text-white';
        }
    }

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (key && (i18n[currentLang][key] || i18n['ru'][key])) {
            el.innerHTML = t(key);
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (key && (i18n[currentLang][key] || i18n['ru'][key])) {
            el.setAttribute('placeholder', t(key));
        }
    });

    updateTokenDisplay();
    renderMcpConfigs();
    checkHealth();

    const activeTab = ['search', 'list', 'editor', 'mcp', 'fleet', 'autosync'].find(name => {
        const tabEl = document.getElementById(`tab-${name}`);
        return tabEl && !tabEl.classList.contains('hidden');
    });

    if (activeTab === 'search') {
        const query = document.getElementById('searchQuery')?.value.trim();
        if (!query) loadRecentContexts();
    } else if (activeTab === 'list') {
        loadContextsList();
    } else if (activeTab === 'fleet') {
        loadFleet();
        runLocalScanner();
    } else if (activeTab === 'autosync') {
        loadAutoSyncView();
    }

    safeCreateIcons();
}

function safeCreateIcons() {
    if (typeof lucide !== 'undefined' && lucide.createIcons) {
        try {
            lucide.createIcons();
        } catch (e) {
            console.warn('Lucide icon render warning:', e);
        }
    }
}

function safeRenderMarkdown(text) {
    if (typeof marked !== 'undefined' && marked.parse) {
        try {
            return marked.parse(text || '');
        } catch (e) {
            console.warn('Marked parse warning:', e);
        }
    }
    // Reliable fallback parser
    return (text || '')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/`([^`]+)`/g, '<code class="bg-slate-800 text-indigo-300 px-1 py-0.5 rounded font-mono text-xs">$1</code>')
        .replace(/\n/g, '<br/>');
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
    safeCreateIcons();
    await initAuth();
    setLanguage(currentLang);
    checkHealth();
    loadRecentContexts();
    loadContextsList();
    loadFleet();
    renderMcpConfigs();

    // Markdown preview live sync if editing
    const contentArea = document.getElementById('ctxContent');
    if (contentArea) {
        contentArea.addEventListener('input', () => {
            const preview = document.getElementById('editorPreviewContainer');
            if (preview && !preview.classList.contains('hidden')) {
                preview.innerHTML = safeRenderMarkdown(contentArea.value || t('preview_empty'));
            }
        });
    }
});

// Auto-authentication for localhost or query param
async function initAuth() {
    // 1. Check URL query param ?token=...
    const urlParams = new URLSearchParams(window.location.search);
    const paramToken = urlParams.get('token');
    if (paramToken) {
        currentAuthToken = paramToken;
        localStorage.setItem('context_auth_token', currentAuthToken);
    }

    // 2. If no token in localStorage, auto-fetch from server if on localhost
    if (!currentAuthToken) {
        try {
            const resp = await fetch('/api/v1/system/info');
            if (resp.ok) {
                const info = await resp.json();
                if (info.auth_token) {
                    currentAuthToken = info.auth_token;
                    localStorage.setItem('context_auth_token', currentAuthToken);
                    console.log('Auto-authenticated on localhost');
                }
            }
        } catch (e) {
            console.warn('System info auto-auth unavailable', e);
        }
    }
    updateTokenDisplay();
}

// Toast Notification
function showToast(msg, isError = false) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toastMsg');
    if (!toast || !toastMsg) return;

    toastMsg.innerText = msg;
    toast.className = `fixed bottom-5 right-5 z-50 transform translate-y-0 opacity-100 transition-all duration-300 ${
        isError ? 'bg-red-600' : 'bg-indigo-600'
    } text-white px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium flex items-center space-x-2`;
    
    setTimeout(() => {
        toast.className = toast.className.replace('translate-y-0 opacity-100', 'translate-y-20 opacity-0');
    }, 3500);
}

// Token Modal
function openTokenModal() {
    const input = document.getElementById('inputAuthToken');
    if (input) input.value = currentAuthToken;
    const modal = document.getElementById('tokenModal');
    if (modal) modal.classList.remove('hidden');
}

function closeTokenModal() {
    const modal = document.getElementById('tokenModal');
    if (modal) modal.classList.add('hidden');
}

function saveToken() {
    const input = document.getElementById('inputAuthToken');
    const val = input ? input.value.trim() : '';
    currentAuthToken = val;
    localStorage.setItem('context_auth_token', val);
    closeTokenModal();
    updateTokenDisplay();
    renderMcpConfigs();
    showToast(t('token_saved_toast'));
    loadRecentContexts();
    loadContextsList();
    loadFleet();
}

function updateTokenDisplay() {
    const label = document.getElementById('tokenBtnLabel');
    const displayVal = document.getElementById('displayTokenVal');
    if (label) {
        if (currentAuthToken) {
            label.innerText = t('token_prefix') + currentAuthToken.substring(0, 8) + '...';
        } else {
            label.innerText = t('token_set_btn');
        }
    }
    if (displayVal) {
        displayVal.innerText = currentAuthToken || t('token_not_set');
    }
}

// Health Check
async function checkHealth() {
    const badge = document.getElementById('healthBadge');
    const text = document.getElementById('healthText');
    if (!badge || !text) return;

    try {
        const resp = await fetch('/health');
        if (resp.ok) {
            const data = await resp.json();
            badge.className = 'flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800 text-xs text-emerald-300';
            text.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 mr-1 inline-block"></span>${t('health_online')} (${data.embedding_provider})`;
        } else {
            throw new Error('Server returned ' + resp.status);
        }
    } catch (err) {
        badge.className = 'flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-red-950/60 border border-red-800 text-xs text-red-300';
        text.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-400 mr-1 inline-block"></span>${t('health_offline')}`;
    }
}

// Switch Tabs
function switchTab(tab) {
    ['search', 'list', 'editor', 'mcp', 'fleet', 'autosync'].forEach(t => {
        const tabEl = document.getElementById(`tab-${t}`);
        const btnEl = document.getElementById(`tab-btn-${t}`);
        if (!tabEl || !btnEl) return;
        if (t === tab) {
            tabEl.classList.remove('hidden');
            btnEl.className = 'tab-btn py-3.5 px-1 border-b-2 border-indigo-500 text-indigo-400 font-medium text-sm flex items-center space-x-2';
            if (t === 'fleet') {
                loadFleet();
                runLocalScanner();
            } else if (t === 'list') {
                loadContextsList();
            } else if (t === 'autosync') {
                loadAutoSyncView();
            }
        } else {
            tabEl.classList.add('hidden');
            btnEl.className = 'tab-btn py-3.5 px-1 border-b-2 border-transparent text-slate-400 hover:text-slate-200 font-medium text-sm flex items-center space-x-2';
        }
    });
    safeCreateIcons();
}

// API Helper
async function apiFetch(endpoint, options = {}) {
    options.headers = options.headers || {};
    if (currentAuthToken) {
        options.headers['Authorization'] = `Bearer ${currentAuthToken}`;
    }
    options.headers['Content-Type'] = 'application/json';

    const resp = await fetch(endpoint, options);
    if (resp.status === 401) {
        showToast(t('auth_required_toast'), true);
        openTokenModal();
        throw new Error('Unauthorized');
    }
    return resp;
}

// Load Recent Contexts on the Search Page immediately so it's never blank
async function loadRecentContexts() {
    const countLabel = document.getElementById('searchResultsCount');
    const list = document.getElementById('searchResultsList');
    if (!list) return;

    try {
        const resp = await apiFetch('/api/v1/contexts?limit=10');
        if (!resp.ok) return;
        const data = await resp.json();
        const items = data.contexts || [];

        if (items.length === 0) {
            if (countLabel) countLabel.innerText = t('empty_db_prompt');
            list.innerHTML = `
                <div class="bg-[#161b22] border border-[#30363d] rounded-xl p-8 text-center text-slate-400 text-xs space-y-3">
                    <p>${t('empty_db_desc')}</p>
                    <button onclick="switchTab('editor'); prepareNewContext();" class="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs">${t('btn_create_first')}</button>
                </div>
            `;
            return;
        }

        if (countLabel) countLabel.innerText = `${t('recent_solutions')} (${items.length}):`;

        const locale = currentLang === 'ru' ? 'ru-RU' : 'en-US';

        list.innerHTML = items.map(item => {
            const tagsHtml = (item.tags || []).map(t => 
                `<span class="px-2 py-0.5 rounded text-[11px] bg-slate-800 border border-slate-700 text-slate-300 font-mono">#${t}</span>`
            ).join(' ');

            const parsedContent = safeRenderMarkdown(item.content || '');
            const dateStr = item.updated_at ? new Date(item.updated_at).toLocaleDateString(locale) : '';

            return `
                <div class="bg-[#161b22] border border-[#30363d] hover:border-slate-600 rounded-xl p-5 space-y-3 transition shadow-sm">
                    <div class="flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <h3 class="text-sm font-semibold text-white hover:text-indigo-400 transition cursor-pointer" onclick="editExistingContext('${item.id}')">${item.title}</h3>
                                <span class="px-2 py-0.5 rounded text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-mono">${item.project || 'global'}</span>
                            </div>
                            <span class="text-[11px] text-slate-500 mt-0.5 block">${dateStr}</span>
                        </div>
                    </div>

                    <div class="markdown-body text-xs bg-[#0d1117] p-3.5 rounded-lg border border-[#30363d]">
                        ${parsedContent}
                    </div>

                    <div class="flex items-center justify-between pt-1">
                        <div class="flex flex-wrap gap-1.5">${tagsHtml}</div>
                        <button onclick="editExistingContext('${item.id}')" class="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1">
                            <span>${t('btn_edit')}</span>
                            <span class="ml-1">→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();
    } catch (e) {
        console.warn('Could not load recent contexts:', e);
    }
}

// Search
async function handleSearch(e) {
    if (e) e.preventDefault();
    const queryInput = document.getElementById('searchQuery');
    const query = queryInput ? queryInput.value.trim() : '';
    if (!query) {
        loadRecentContexts();
        return;
    }

    const projectInput = document.getElementById('searchProject');
    const project = projectInput && projectInput.value.trim() ? projectInput.value.trim() : undefined;
    const tagsInput = document.getElementById('searchTags');
    const tagsVal = tagsInput ? tagsInput.value.trim() : '';
    const tags = tagsVal ? tagsVal.split(',').map(t => t.trim()).filter(Boolean) : undefined;
    const scoreSlider = document.getElementById('searchMinScore');
    const minScore = scoreSlider ? parseFloat(scoreSlider.value) : 0.25;

    const countLabel = document.getElementById('searchResultsCount');
    const list = document.getElementById('searchResultsList');
    if (countLabel) countLabel.innerText = t('search_loading');
    if (list) list.innerHTML = `<div class="p-6 text-center text-slate-500 text-xs">${t('search_analyzing')}</div>`;

    try {
        const resp = await apiFetch('/api/v1/contexts/search', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                project: project,
                tags: tags,
                limit: 10,
                min_score: minScore,
            }),
        });

        if (!resp.ok) throw new Error('Search failed: ' + resp.status);
        const data = await resp.json();
        const results = data.results || [];

        if (countLabel) countLabel.innerText = `${t('search_found')}${results.length}`;

        if (results.length === 0) {
            list.innerHTML = `
                <div class="bg-[#161b22] border border-[#30363d] rounded-lg p-8 text-center text-slate-400 text-xs">
                    ${t('search_nothing')}
                </div>
            `;
            return;
        }

        list.innerHTML = results.map(item => {
            const scorePercent = Math.round((item.score || 0) * 100);
            const badgeColor = scorePercent >= 70 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 
                               scorePercent >= 40 ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' : 
                               'bg-slate-500/10 text-slate-400 border-slate-500/30';

            const tagsHtml = (item.tags || []).map(t => 
                `<span class="px-2 py-0.5 rounded text-[11px] bg-slate-800 border border-slate-700 text-slate-300 font-mono">#${t}</span>`
            ).join(' ');

            const parsedContent = safeRenderMarkdown(item.content || '');

            return `
                <div class="bg-[#161b22] border border-[#30363d] hover:border-slate-600 rounded-xl p-5 space-y-3 transition shadow-sm">
                    <div class="flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <h3 class="text-sm font-semibold text-white hover:text-indigo-400 transition cursor-pointer" onclick="editExistingContext('${item.id}')">${item.title}</h3>
                                <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono">${item.project || 'global'}</span>
                            </div>
                        </div>
                        <span class="px-2.5 py-1 rounded-full border text-xs font-semibold ${badgeColor}">
                            ${scorePercent}% ${t('similarity')}
                        </span>
                    </div>

                    <div class="markdown-body text-xs bg-[#0d1117] p-3.5 rounded-lg border border-[#30363d]">
                        ${parsedContent}
                    </div>

                    <div class="flex items-center justify-between pt-1">
                        <div class="flex flex-wrap gap-1.5">${tagsHtml}</div>
                        <button onclick="editExistingContext('${item.id}')" class="text-xs text-indigo-400 hover:text-indigo-300 flex items-center space-x-1">
                            <span>${t('btn_edit')}</span>
                            <span class="ml-1">→</span>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();

    } catch (err) {
        if (countLabel) countLabel.innerText = t('search_error');
        if (list) list.innerHTML = `<div class="p-6 text-center text-red-400 text-xs">Error: ${err.message}</div>`;
    }
}

// Load Contexts List
async function loadContextsList() {
    const grid = document.getElementById('contextsGrid');
    const countBadge = document.getElementById('contextsCountBadge');
    if (!grid) return;

    try {
        const resp = await apiFetch('/api/v1/contexts?limit=50');
        if (!resp.ok) throw new Error('Status: ' + resp.status);
        const data = await resp.json();
        const items = data.contexts || [];
        if (countBadge) countBadge.innerText = items.length;

        if (items.length === 0) {
            grid.innerHTML = `
                <div class="col-span-2 bg-[#161b22] border border-[#30363d] rounded-xl p-8 text-center text-slate-400 text-xs space-y-3">
                    <p>${t('empty_db_desc')}</p>
                    <button onclick="switchTab('editor'); prepareNewContext();" class="px-3.5 py-1.5 bg-indigo-600 rounded text-white text-xs">${t('btn_create_first')}</button>
                </div>
            `;
            return;
        }

        const locale = currentLang === 'ru' ? 'ru-RU' : 'en-US';

        grid.innerHTML = items.map(item => {
            const dateStr = item.updated_at ? new Date(item.updated_at).toLocaleDateString(locale) : '';
            const tagsHtml = (item.tags || []).map(t => 
                `<span class="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300">#${t}</span>`
            ).join(' ');

            return `
                <div class="bg-[#161b22] border border-[#30363d] hover:border-slate-600 rounded-xl p-4 flex flex-col justify-between space-y-3 transition">
                    <div>
                        <div class="flex items-center justify-between mb-1.5">
                            <span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-indigo-400 font-mono">${item.project || 'global'}</span>
                            <span class="text-[11px] text-slate-500">${dateStr}</span>
                        </div>
                        <h3 class="text-sm font-semibold text-white">${item.title}</h3>
                        <p class="text-xs text-slate-400 line-clamp-3 mt-1.5">${(item.content || '').replace(/#/g, '')}</p>
                    </div>

                    <div class="pt-2 border-t border-[#30363d] flex items-center justify-between">
                        <div class="flex flex-wrap gap-1">${tagsHtml}</div>
                        <div class="flex items-center space-x-2">
                            <button onclick="editExistingContext('${item.id}')" class="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] rounded text-xs text-slate-300">${t('btn_edit_short')}</button>
                            <button onclick="deleteContextItem('${item.id}', '${item.title}')" class="px-2 py-1 bg-red-950/40 hover:bg-red-900/60 text-red-300 rounded text-xs">${t('btn_delete')}</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();
    } catch (err) {
        grid.innerHTML = `<div class="col-span-2 text-center text-red-400 py-8 text-xs">${t('list_load_error')}</div>`;
    }
}

// Prepare New Context
function prepareNewContext() {
    document.getElementById('editContextId').value = '';
    document.getElementById('editorTitle').innerText = t('editor_title');
    document.getElementById('ctxTitle').value = '';
    document.getElementById('ctxProject').value = 'global';
    document.getElementById('ctxTags').value = '';
    document.getElementById('ctxContent').value = '';
    setEditorPreview(false);
}

// Edit Existing Context
async function editExistingContext(id) {
    try {
        const resp = await apiFetch(`/api/v1/contexts/${id}`);
        if (!resp.ok) throw new Error('Not found');
        const doc = await resp.json();

        document.getElementById('editContextId').value = doc.id;
        document.getElementById('editorTitle').innerText = t('editor_title_edit') + doc.title;
        document.getElementById('ctxTitle').value = doc.title;
        document.getElementById('ctxProject').value = doc.project || 'global';
        document.getElementById('ctxTags').value = (doc.tags || []).join(', ');
        document.getElementById('ctxContent').value = doc.content || '';

        setEditorPreview(false);
        switchTab('editor');
    } catch (err) {
        showToast('Failed to load context: ' + err.message, true);
    }
}

// Save / Update Context
async function handleSaveContext(e) {
    e.preventDefault();
    const title = document.getElementById('ctxTitle').value.trim();
    const project = document.getElementById('ctxProject').value.trim() || 'global';
    const tagsInput = document.getElementById('ctxTags').value.trim();
    const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(Boolean) : [];
    const content = document.getElementById('ctxContent').value;

    const btn = document.getElementById('saveBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerText = t('saving');
    }

    try {
        const resp = await apiFetch('/api/v1/contexts', {
            method: 'POST',
            body: JSON.stringify({
                title,
                project,
                tags,
                content,
            }),
        });

        if (!resp.ok) throw new Error(t('save_error') + resp.status);
        showToast(t('save_success'));
        loadRecentContexts();
        loadContextsList();
        switchTab('list');
    } catch (err) {
        showToast(err.message, true);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>${t('btn_save')}</span>`;
        }
        safeCreateIcons();
    }
}

// Delete Context
async function deleteContextItem(id, title) {
    if (!confirm(t('confirm_delete', { title }))) return;

    try {
        const resp = await apiFetch(`/api/v1/contexts/${id}`, { method: 'DELETE' });
        if (!resp.ok) throw new Error('Delete failed');
        showToast(t('delete_success'));
        loadRecentContexts();
        loadContextsList();
    } catch (err) {
        showToast(t('delete_error'), true);
    }
}

// Editor Preview Toggle
function setEditorPreview(previewMode) {
    const writeBox = document.getElementById('editorWriteContainer');
    const prevBox = document.getElementById('editorPreviewContainer');
    const btnWrite = document.getElementById('btnEditorWrite');
    const btnPrev = document.getElementById('btnEditorPreview');
    const contentVal = document.getElementById('ctxContent').value;

    if (previewMode) {
        writeBox.classList.add('hidden');
        prevBox.classList.remove('hidden');
        prevBox.innerHTML = safeRenderMarkdown(contentVal || '*Текст отсутствует*');
        btnWrite.className = 'px-2 py-0.5 rounded bg-[#21262d] text-slate-300 font-medium';
        btnPrev.className = 'px-2 py-0.5 rounded bg-indigo-600 text-white font-medium';
    } else {
        prevBox.classList.add('hidden');
        writeBox.classList.remove('hidden');
        btnWrite.className = 'px-2 py-0.5 rounded bg-indigo-600 text-white font-medium';
        btnPrev.className = 'px-2 py-0.5 rounded bg-[#21262d] text-slate-300 font-medium';
    }
}

// MCP Config Generator
function renderMcpConfigs() {
    const origin = window.location.origin;
    const sseUrl = `${origin}/sse`;
    const token = currentAuthToken || 'ctx_secret_token_7f9a8b1c4e2d3f5a';

    const sseEl = document.getElementById('displaySseUrl');
    if (sseEl) sseEl.innerText = sseUrl;

    const standardConfig = {
        mcpServers: {
            "remote-context": {
                url: sseUrl,
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        }
    };

    const remoteConfig = {
        mcpServers: {
            "remote-context": {
                command: "npx",
                args: [
                    "-y",
                    "mcp-remote",
                    `${sseUrl}?token=${token}`
                ]
            }
        }
    };

    const jsonEl = document.getElementById('mcpConfigJson');
    if (jsonEl) jsonEl.innerText = JSON.stringify(standardConfig, null, 2);

    const remoteJsonEl = document.getElementById('mcpRemoteConfigJson');
    if (remoteJsonEl) remoteJsonEl.innerText = JSON.stringify(remoteConfig, null, 2);

    const winCmdEl = document.getElementById('remoteScannerCmdWin');
    const bashCmdEl = document.getElementById('remoteScannerCmdBash');
    const scannerCmdEl = document.getElementById('remoteScannerCmd');
    const dlLinkEl = document.getElementById('remoteScannerDownloadLink');

    const winCommand = `irm ${origin}/install.ps1 | iex`;
    const bashCommand = `curl -sSL ${origin}/install.sh | bash`;

    if (winCmdEl) winCmdEl.innerText = winCommand;
    if (bashCmdEl) bashCmdEl.innerText = bashCommand;
    if (scannerCmdEl) scannerCmdEl.innerText = winCommand;
    if (dlLinkEl) dlLinkEl.href = `${origin}/scanner.py`;
}

function copyMcpJson(type) {
    const elId = type === 'standard' ? 'mcpConfigJson' : 'mcpRemoteConfigJson';
    const el = document.getElementById(elId);
    if (el) copyToClipboard(el.innerText);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Скопировано в буфер обмена!');
    }).catch(() => {
        showToast('Не удалось скопировать', true);
    });
}

// ============================================================================
// Fleet & Scanner Functions
// ============================================================================

async function loadFleet() {
    const container = document.getElementById('fleetList');
    const badge = document.getElementById('fleetCountBadge');
    if (!container) return;

    try {
        const resp = await apiFetch('/api/v1/fleet');
        if (!resp.ok) throw new Error('Fleet fetch failed');
        const data = await resp.json();
        const agents = data.agents || [];
        if (badge) badge.innerText = agents.length;

        if (agents.length === 0) {
            container.innerHTML = `
                <div class="bg-[#0d1117] border border-[#30363d] rounded-xl p-6 text-center text-slate-400 text-xs space-y-2">
                    <p>${t('fleet_empty_title')}</p>
                    <p class="text-slate-500 text-[11px]">${t('fleet_empty_desc')}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = agents.map(a => {
            const timeAgo = Math.round((new Date() - new Date(a.last_activity)) / 1000);
            return `
                <div class="bg-[#0d1117] border border-[#30363d] hover:border-slate-600 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition">
                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                            <h4 class="text-sm font-semibold text-white">${a.device_name}</h4>
                            <span class="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">${a.client_ip}</span>
                        </div>
                        <p class="text-xs text-slate-400 truncate max-w-md">${a.user_agent}</p>
                    </div>

                    <div class="flex items-center space-x-4 text-xs text-slate-400">
                        <div>
                            <span class="block text-[10px] uppercase text-slate-500 font-semibold">${t('requests')}</span>
                            <span class="font-mono text-white font-medium">${a.requests_count}</span>
                        </div>
                        <div>
                            <span class="block text-[10px] uppercase text-slate-500 font-semibold">${t('last_tool')}</span>
                            <span class="font-mono text-indigo-400 font-medium">${a.last_tool_called || '—'}</span>
                        </div>
                        <div>
                            <span class="block text-[10px] uppercase text-slate-500 font-semibold">${t('activity')}</span>
                            <span class="text-slate-300 font-medium">${timeAgo}${t('seconds_ago')}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();
    } catch (err) {
        container.innerHTML = `<div class="text-center text-red-400 py-4 text-xs">${t('fleet_auth_error')}</div>`;
    }
}

async function runLocalScanner(silent = true) {
    const list = document.getElementById('scannerTargetsList');
    const btn = document.getElementById('btnRunScanner');
    const statusBar = document.getElementById('scannerStatusBar');
    const statusText = document.getElementById('scannerStatusText');
    const lastChecked = document.getElementById('scannerLastChecked');
    if (!list) return;

    if (btn && !silent) {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>${t('scanning')}</span>`;
        safeCreateIcons();
    }

    try {
        const resp = await apiFetch('/api/v1/scanner');
        if (!resp.ok) throw new Error('Scanner failed');
        const data = await resp.json();
        const targets = data.targets || [];
        const detectedCount = data.detected_count || 0;
        const configuredCount = data.configured_count || 0;

        // Render status bar
        if (statusBar && statusText) {
            statusBar.classList.remove('hidden');
            statusText.innerText = t('scan_status_badge', {
                detected: detectedCount,
                total: targets.length,
                configured: configuredCount
            });
            if (lastChecked) {
                const now = new Date().toLocaleTimeString();
                lastChecked.innerText = `${t('last_checked_label')}${now}`;
            }
        }

        list.innerHTML = targets.map(tgt => {
            const detectedBadge = tgt.detected 
                ? `<span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">${t('detected')}</span>`
                : `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-500">${t('not_found')}</span>`;

            let actionBtn = '';
            if (tgt.configured) {
                actionBtn = `
                    <div class="flex items-center space-x-2">
                        <span class="text-xs text-emerald-400 font-medium flex items-center space-x-1">
                            <span>${t('connected')}</span>
                        </span>
                        <button onclick="injectAgent('${tgt.app_id}')" title="Обновить MCP конфигурацию" class="px-2 py-1 bg-[#21262d] hover:bg-[#30363d] text-slate-300 rounded text-xs font-medium border border-[#30363d] transition flex items-center space-x-1">
                            <i data-lucide="refresh-cw" class="w-3 h-3"></i>
                            <span>${t('btn_reconnect')}</span>
                        </button>
                    </div>
                `;
            } else if (tgt.detected) {
                actionBtn = `
                    <button onclick="injectAgent('${tgt.app_id}')" class="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition shadow flex items-center space-x-1">
                        <i data-lucide="zap" class="w-3 h-3"></i>
                        <span>${t('btn_connect')}</span>
                    </button>
                `;
            } else {
                actionBtn = `<span class="text-xs text-slate-600 font-medium">${t('not_found')}</span>`;
            }

            return `
                <div class="bg-[#0d1117] border border-[#30363d] rounded-xl p-3.5 flex flex-col justify-between space-y-2">
                    <div class="flex items-start justify-between">
                        <div>
                            <div class="flex items-center space-x-2">
                                <h4 class="text-xs font-semibold text-white">${tgt.name}</h4>
                                ${detectedBadge}
                            </div>
                            <p class="text-[10px] font-mono text-slate-500 truncate max-w-xs mt-1" title="${tgt.config_path}">${tgt.config_path}</p>
                        </div>
                    </div>
                    <div class="flex justify-end pt-1">
                        ${actionBtn}
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();

        if (!silent) {
            showToast(t('scan_all_already_connected', { count: configuredCount }));
        }
        return data;
    } catch (err) {
        list.innerHTML = `<div class="col-span-2 text-center text-red-400 py-4 text-xs">${t('scanner_win_hint')}</div>`;
    } finally {
        if (btn && !silent) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="zap" class="w-3.5 h-3.5"></i><span>${t('btn_run_scanner')}</span>`;
            safeCreateIcons();
        }
    }
}

async function runLocalScannerAndConnect(force = false) {
    const btn = force ? document.getElementById('btnReconnectAll') : document.getElementById('btnRunScanner');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader-2" class="w-3.5 h-3.5 animate-spin"></i><span>${t('scanning_and_connecting')}</span>`;
        safeCreateIcons();
    }

    try {
        // 1. Trigger injection on all detected agents (or force update all)
        const resp = await apiFetch('/api/v1/scanner/inject-all', {
            method: 'POST',
            body: JSON.stringify({ force: force }),
        });

        if (!resp.ok) throw new Error('Inject-all failed');
        const res = await resp.json();

        // 2. Refresh target UI
        const refreshed = await runLocalScanner(true);
        const configuredCount = (refreshed && refreshed.configured_count) || res.successful || 0;

        // 3. Show prominent toast
        if (res.processed > 0) {
            if (force) {
                showToast(t('scan_reconnected_all_toast', { count: res.successful }));
            } else {
                showToast(t('scan_connected_toast', { count: res.successful }));
            }
        } else {
            showToast(t('scan_all_already_connected', { count: configuredCount }));
        }
    } catch (err) {
        showToast(t('inject_error') + err.message, true);
        await runLocalScanner(true);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
            safeCreateIcons();
        }
    }
}

async function injectAgent(appId) {
    try {
        const resp = await apiFetch('/api/v1/scanner/inject', {
            method: 'POST',
            body: JSON.stringify({ app_id: appId }),
        });
        if (!resp.ok) throw new Error('Injection failed');
        const res = await resp.json();
        showToast(t('inject_success', { agent: res.agent }));
        await runLocalScanner(true);
    } catch (err) {
        showToast(t('inject_error') + err.message, true);
    }
}

// ============================================================================
// Auto-Sync Dashboard Functions
// ============================================================================

async function loadAutoSyncView() {
    const grid = document.getElementById('syncProjectsGrid');
    const badge = document.getElementById('syncProjectsBadge');
    const totalProjEl = document.getElementById('syncTotalProjects');
    const totalSessEl = document.getElementById('syncTotalSessions');
    const lastTimeEl = document.getElementById('syncLastTime');
    const countIndicator = document.getElementById('projectsCountIndicator');

    try {
        // 1. Fetch daemon status
        const statusResp = await apiFetch('/api/v1/sync/status');
        if (statusResp.ok) {
            const sData = await statusResp.json();
            if (totalProjEl) totalProjEl.innerText = sData.total_projects || '0';
            if (totalSessEl) totalSessEl.innerText = sData.synced_sessions_total || '0';
            if (badge) badge.innerText = sData.total_projects || '0';

            const lastCycle = sData.last_cycle || {};
            if (lastTimeEl) {
                if (lastCycle.timestamp) {
                    const timeAgoSec = Math.round((new Date() - new Date(lastCycle.timestamp)) / 1000);
                    lastTimeEl.innerText = `${timeAgoSec}${t('seconds_ago')} (${lastCycle.projects_updated || 0} ${t('updated_suffix')})`;
                } else {
                    lastTimeEl.innerText = t('not_run_yet');
                }
            }
        }

        // 2. Fetch detected projects
        const projResp = await apiFetch('/api/v1/sync/projects');
        if (!projResp.ok) return;
        const pData = await projResp.json();
        const projects = pData.projects || [];

        if (countIndicator) countIndicator.innerText = `${t('found_projects_indicator')}${projects.length}`;

        if (!grid) return;

        if (projects.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full bg-[#0d1117] border border-[#30363d] rounded-xl p-6 text-center text-slate-400 text-xs">
                    ${t('no_projects_found')}
                </div>
            `;
            return;
        }

        grid.innerHTML = projects.map(p => {
            const sources = p.sources || [];
            const badgesHtml = sources.map(s => {
                let colorClass = 'bg-slate-800 text-slate-300';
                if (s === 'codex') colorClass = 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/40';
                if (s === 'cursor') colorClass = 'bg-cyan-950/80 text-cyan-400 border border-cyan-800/40';
                if (s === 'workspace') colorClass = 'bg-indigo-950/80 text-indigo-400 border border-indigo-800/40';
                return `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-medium ${colorClass}">${s.toUpperCase()}</span>`;
            }).join(' ');

            return `
                <div class="bg-[#0d1117] border border-[#30363d] hover:border-slate-600 rounded-xl p-4 flex flex-col justify-between space-y-3 transition">
                    <div>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <i data-lucide="folder" class="w-4 h-4 text-indigo-400"></i>
                                <h4 class="text-sm font-semibold text-white truncate max-w-[180px]">${p.name}</h4>
                            </div>
                            <div class="flex space-x-1">${badgesHtml}</div>
                        </div>
                        <p class="text-[11px] font-mono text-slate-500 truncate mt-1.5" title="${p.path}">${p.path}</p>
                    </div>

                    <div class="pt-2 border-t border-[#21262d] flex items-center justify-between text-[11px] text-slate-400">
                        <span class="flex items-center space-x-1">
                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                            <span>${t('context_files_label')}</span>
                        </span>
                        <span class="text-emerald-400 font-mono">${t('sync_status_synced')}</span>
                    </div>
                </div>
            `;
        }).join('');

        safeCreateIcons();
    } catch (err) {
        console.warn('AutoSync view load failed:', err);
    }
}

async function triggerAutoSync() {
    const btn = document.getElementById('btnTriggerSync');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i><span>${t('syncing')}</span>`;
        safeCreateIcons();
    }

    try {
        const resp = await apiFetch('/api/v1/sync/trigger', { method: 'POST' });
        if (!resp.ok) throw new Error('Sync failed with status ' + resp.status);
        const data = await resp.json();
        const res = data.result || {};
        showToast(t('sync_completed_toast', { projects: res.projects_updated || 0, sessions: res.new_sessions_synced || 0 }));
        await loadAutoSyncView();
    } catch (err) {
        showToast('Sync error: ' + err.message, true);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4"></i><span>${t('btn_sync_now')}</span>`;
            safeCreateIcons();
        }
    }
}

const API_BASE = window.API_BASE_URL || window.location.origin;

const state = {
  mods: [],
  installed: [],
  blacklist: [],
  notifications: [],
  selectedTab: "browse",
  selectedMod: null,
  search: "",
  settings: {
    gameDirectory: "",
  },
};

const elements = {
  sidebar: document.getElementById("sidebar"),
  overlay: document.getElementById("page-overlay"),
  hamburger: document.getElementById("hamburger"),
  tabs: document.querySelectorAll(".sidebar-link"),
  pages: document.querySelectorAll(".page"),
  browseGrid: document.getElementById("browse-grid"),
  browseLoading: document.getElementById("browse-loading"),
  installedGrid: document.getElementById("installed-grid"),
  installedEmpty: document.getElementById("installed-empty"),
  blacklistList: document.getElementById("blacklist-list"),
  blacklistEmpty: document.getElementById("blacklist-empty"),
  searchInput: document.getElementById("search-input"),
  searchButton: document.getElementById("search-button"),
  modDetail: document.getElementById("mod-detail"),
  detailThumbnail: document.getElementById("detail-thumbnail"),
  detailTitle: document.getElementById("detail-title"),
  detailAuthor: document.getElementById("detail-author"),
  detailDownloads: document.getElementById("detail-downloads"),
  detailDescription: document.getElementById("detail-description"),
  detailInstall: document.getElementById("detail-install"),
  detailBlacklist: document.getElementById("detail-blacklist"),
  closeDetail: document.getElementById("close-detail"),
  installProgress: document.getElementById("install-progress"),
  installProgressBar: document.getElementById("install-progress-bar"),
  notificationButton: document.getElementById("notification-button"),
  notificationCount: document.getElementById("notification-count"),
  notificationPanel: document.getElementById("notification-panel"),
  notificationList: document.getElementById("notification-list"),
  settingsInput: document.getElementById("game-directory-input"),
  settingsSave: document.getElementById("save-settings"),
  settingsStatus: document.getElementById("settings-status"),
};

function toggleSidebar(show) {
  const shouldShow = show ?? !elements.sidebar.classList.contains("open");
  elements.sidebar.classList.toggle("open", shouldShow);
  elements.overlay.classList.toggle("active", shouldShow);
  elements.overlay.classList.toggle("hidden", !shouldShow && !state.selectedMod);
}

function closeOverlays() {
  toggleSidebar(false);
  closeModDetail();
  hideNotificationPanel();
}

function setActiveTab(tab) {
  state.selectedTab = tab;
  elements.tabs.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  elements.pages.forEach((page) => {
    page.classList.toggle("active", page.dataset.page === tab);
  });
  if (tab === "browse") {
    loadMods();
  } else if (tab === "installed") {
    renderInstalled();
  } else if (tab === "blacklist") {
    renderBlacklist();
  } else if (tab === "settings") {
    renderSettings();
  }
  closeOverlays();
}

function createModCard(mod) {
  const card = document.createElement("article");
  card.className = "mod-card";
  card.innerHTML = `
    <img src="${mod.icon || "https://placehold.co/600x400/1f2937/94a3b8?text=Mod"}" alt="${mod.display_name}" />
    <div class="mod-card-content">
      <h3 class="mod-card-title">${mod.display_name}</h3>
      <p class="mod-card-author">${mod.owner}</p>
      <p class="mod-card-summary">${truncate(mod.summary, 110)}</p>
      <span class="mod-card-downloads">${formatDownloads(mod.downloads)}</span>
    </div>
  `;
  card.addEventListener("click", () => openModDetail(mod.namespace, mod.name));
  return card;
}

function truncate(text, length) {
  if (!text) return "";
  if (text.length <= length) return text;
  return `${text.slice(0, length)}…`;
}

function formatDownloads(value) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

async function loadMods() {
  elements.browseLoading.classList.remove("hidden");
  try {
    const params = new URLSearchParams();
    params.set("limit", "60");
    if (state.search) params.set("search", state.search);
    const res = await fetch(`${API_BASE}/api/mods?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch mods");
    const mods = await res.json();
    state.mods = mods;
    renderBrowse();
  } catch (error) {
    console.error(error);
    elements.browseGrid.innerHTML = `<div class="empty-state">Unable to load mods.</div>`;
  } finally {
    elements.browseLoading.classList.add("hidden");
  }
}

function renderBrowse() {
  elements.browseGrid.innerHTML = "";
  state.mods.forEach((mod) => {
    elements.browseGrid.appendChild(createModCard(mod));
  });
}

async function openModDetail(namespace, name) {
  try {
    const res = await fetch(`${API_BASE}/api/mods/${namespace}/${name}`);
    if (!res.ok) throw new Error("Failed to load mod details");
    const detail = await res.json();
    state.selectedMod = detail;
    updateModDetail(detail);
    elements.modDetail.classList.add("open");
    elements.modDetail.classList.remove("hidden");
    elements.overlay.classList.add("active");
  } catch (error) {
    console.error(error);
  }
}

function updateModDetail(detail) {
  elements.detailThumbnail.src =
    detail.icon || "https://placehold.co/600x400/1f2937/94a3b8?text=Mod";
  elements.detailTitle.textContent = detail.display_name;
  elements.detailAuthor.textContent = detail.owner;
  elements.detailDownloads.textContent = `${formatDownloads(
    detail.downloads
  )} downloads`;
  elements.detailDescription.innerHTML = formatDescription(detail.description);

  const isBlacklisted = state.blacklist.includes(`${detail.namespace}.${detail.name}`);
  const installedMod = state.installed.find(
    (mod) => mod.namespace === detail.namespace && mod.name === detail.name
  );

  elements.detailBlacklist.textContent = isBlacklisted ? "Whitelist" : "Blacklist";
  elements.detailInstall.textContent = installedMod ? "Uninstall" : "Install";

  if (isBlacklisted) {
    elements.detailInstall.classList.add("blocked");
    elements.detailInstall.disabled = true;
    elements.detailInstall.title = "Whitelist the mod to download";
  } else {
    elements.detailInstall.classList.remove("blocked");
    elements.detailInstall.disabled = false;
    elements.detailInstall.removeAttribute("title");
  }
}

function formatDescription(description) {
  if (!description) return "No description available.";
  return description
    .split(/\n+/)
    .map((paragraph) => `<p>${paragraph}</p>`)
    .join("\n");
}

function closeModDetail() {
  state.selectedMod = null;
  elements.modDetail.classList.remove("open");
  elements.overlay.classList.toggle("active", elements.sidebar.classList.contains("open"));
  setTimeout(() => {
    if (!state.selectedMod) {
      elements.modDetail.classList.add("hidden");
    }
  }, 200);
}

async function loadInstalled() {
  const res = await fetch(`${API_BASE}/api/mods/installed`);
  if (res.ok) {
    state.installed = await res.json();
  }
}

function renderInstalled() {
  elements.installedGrid.innerHTML = "";
  if (!state.installed.length) {
    elements.installedEmpty.classList.remove("hidden");
    return;
  }
  elements.installedEmpty.classList.add("hidden");
  state.installed.forEach((mod) => {
    const card = createModCard({
      namespace: mod.namespace,
      name: mod.name,
      display_name: mod.display_name,
      owner: mod.author,
      summary: mod.summary,
      icon: mod.icon,
      downloads: 0,
    });
    elements.installedGrid.appendChild(card);
  });
}

async function loadBlacklist() {
  const res = await fetch(`${API_BASE}/api/mods/blacklisted`);
  if (res.ok) {
    state.blacklist = await res.json();
  }
}

function renderBlacklist() {
  elements.blacklistList.innerHTML = "";
  if (!state.blacklist.length) {
    elements.blacklistEmpty.classList.remove("hidden");
    return;
  }
  elements.blacklistEmpty.classList.add("hidden");
  state.blacklist.forEach((entry) => {
    const [namespace, name] = entry.split(".");
    const item = document.createElement("div");
    item.className = "blacklist-item";
    item.innerHTML = `
      <div class="meta">
        <strong>${name}</strong>
        <span>${namespace}</span>
      </div>
      <button data-entry="${entry}">Whitelist</button>
    `;
    item.querySelector("button").addEventListener("click", () => whitelistMod(namespace, name));
    elements.blacklistList.appendChild(item);
  });
}

async function whitelistMod(namespace, name) {
  await fetch(`${API_BASE}/api/mods/whitelist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace, name }),
  });
  await refreshState();
  if (state.selectedMod) {
    updateModDetail(state.selectedMod);
  }
}

async function blacklistMod(namespace, name) {
  await fetch(`${API_BASE}/api/mods/blacklist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace, name }),
  });
  await refreshState();
  if (state.selectedMod) {
    updateModDetail(state.selectedMod);
  }
}

async function installMod(namespace, name) {
  const progress = elements.installProgress;
  const bar = elements.installProgressBar;
  progress.classList.remove("hidden");
  bar.style.width = "8%";
  const interval = setInterval(() => {
    const current = parseFloat(bar.style.width);
    if (current < 90) {
      bar.style.width = `${current + 7}%`;
    }
  }, 180);

  const res = await fetch(`${API_BASE}/api/mods/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace, name }),
  });

  clearInterval(interval);
  bar.style.width = "100%";
  setTimeout(() => {
    progress.classList.add("hidden");
    bar.style.width = "0%";
  }, 600);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Install failed" }));
    alert(error.detail || "Install failed");
    return;
  }
  await refreshState();
  if (state.selectedMod) {
    updateModDetail(state.selectedMod);
  }
}

async function uninstallMod(namespace, name) {
  await fetch(`${API_BASE}/api/mods/uninstall`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ namespace, name }),
  });
  await refreshState();
  if (state.selectedMod) {
    updateModDetail(state.selectedMod);
  }
}

async function refreshState() {
  await Promise.all([loadInstalled(), loadBlacklist(), loadNotifications(), loadSettings()]);
  if (state.selectedTab === "installed") {
    renderInstalled();
  }
  if (state.selectedTab === "blacklist") {
    renderBlacklist();
  }
  renderNotifications();
}

async function saveSettings() {
  const path = elements.settingsInput.value.trim();
  if (!path) {
    elements.settingsStatus.textContent = "Please provide a valid path.";
    return;
  }
  const res = await fetch(`${API_BASE}/api/settings/game-directory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  if (res.ok) {
    elements.settingsStatus.textContent = "Saved.";
    await loadSettings();
  } else {
    const error = await res.json().catch(() => ({ detail: "Unable to save" }));
    elements.settingsStatus.textContent = error.detail || "Unable to save";
  }
}

async function loadSettings() {
  const res = await fetch(`${API_BASE}/api/settings`);
  if (res.ok) {
    const data = await res.json();
    state.settings.gameDirectory = data.game_directory || "";
    if (elements.settingsInput) {
      elements.settingsInput.value = state.settings.gameDirectory;
    }
  }
}

function renderSettings() {
  elements.settingsInput.value = state.settings.gameDirectory;
}

async function loadNotifications() {
  const res = await fetch(`${API_BASE}/api/notifications`);
  if (res.ok) {
    state.notifications = await res.json();
  }
}

function renderNotifications() {
  const count = state.notifications.length;
  if (count) {
    elements.notificationCount.textContent = count.toString();
    elements.notificationCount.classList.remove("hidden");
  } else {
    elements.notificationCount.classList.add("hidden");
  }

  elements.notificationList.innerHTML = "";
  state.notifications.forEach((notification) => {
    const item = document.createElement("div");
    item.className = "notification-item";
    item.innerHTML = `
      <img src="${notification.icon || "https://placehold.co/120x120/1f2937/94a3b8?text=Mod"}" alt="${notification.display_name}" />
      <div>
        <strong>${notification.display_name}</strong>
        <div>Update available</div>
        <div>${notification.current_version} → ${notification.latest_version}</div>
        <button data-entry="${notification.namespace}.${notification.name}">Update</button>
      </div>
    `;
    item.querySelector("button").addEventListener("click", async () => {
      await installMod(notification.namespace, notification.name);
      state.notifications = state.notifications.filter(
        (n) => n.namespace !== notification.namespace || n.name !== notification.name
      );
      renderNotifications();
      hideNotificationPanel();
    });
    elements.notificationList.appendChild(item);
  });
}

function toggleNotificationPanel() {
  const isHidden = elements.notificationPanel.classList.contains("hidden");
  if (isHidden) {
    renderNotifications();
    elements.notificationPanel.classList.remove("hidden");
  } else {
    elements.notificationPanel.classList.add("hidden");
  }
}

function hideNotificationPanel() {
  elements.notificationPanel.classList.add("hidden");
}

function attachEventListeners() {
  elements.hamburger.addEventListener("click", () => toggleSidebar());
  elements.overlay.addEventListener("click", closeOverlays);
  elements.closeDetail.addEventListener("click", closeModDetail);
  elements.detailInstall.addEventListener("click", async () => {
    if (!state.selectedMod) return;
    const { namespace, name } = state.selectedMod;
    const isInstalled = state.installed.some(
      (mod) => mod.namespace === namespace && mod.name === name
    );
    if (isInstalled) {
      await uninstallMod(namespace, name);
    } else {
      await installMod(namespace, name);
    }
  });
  elements.detailBlacklist.addEventListener("click", async () => {
    if (!state.selectedMod) return;
    const { namespace, name } = state.selectedMod;
    const key = `${namespace}.${name}`;
    if (state.blacklist.includes(key)) {
      await whitelistMod(namespace, name);
    } else {
      await blacklistMod(namespace, name);
    }
  });
  elements.searchButton.addEventListener("click", () => {
    state.search = elements.searchInput.value.trim();
    loadMods();
  });
  elements.searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      state.search = elements.searchInput.value.trim();
      loadMods();
    }
  });
  elements.notificationButton.addEventListener("click", toggleNotificationPanel);
  elements.settingsSave.addEventListener("click", saveSettings);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeOverlays();
    }
  });
  elements.tabs.forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.tab));
  });
}

async function init() {
  attachEventListeners();
  await refreshState();
  await loadMods();
}

init();

// TOTM — prototipo de UI. Datos de ejemplo; se reemplazan por la API del dispositivo.

const ICONS = {
  inicio: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="11" r="7"/><path d="M5 10h14M9 21h6"/></svg>',
  actividad: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg>',
  agentes: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="7" width="16" height="12" rx="4"/><path d="M12 3v4M9 13h.01M15 13h.01" stroke-linecap="round"/></svg>',
  dispositivo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="16" height="16" rx="3"/><path d="M9 9h6v6H9zM9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/></svg>',
  allow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5 9-10"/></svg>',
  warn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 6v7M12 18h.01"/></svg>',
  block: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>',
};

const VIEWS = [
  { id: "inicio", label: "Inicio" },
  { id: "actividad", label: "Actividad" },
  { id: "agentes", label: "Agentes" },
  { id: "dispositivo", label: "Dispositivo" },
];

const AGENTS = [
  { id: "claude", name: "Claude Code", host: "dev-server", initials: "CC", status: "ok", perms: ["shell", "git", "fs:/srv/app"], load: 64, actions: 812 },
  { id: "ops", name: "Ops Bot", host: "k8s-prod", initials: "OB", status: "ok", perms: ["kubectl get", "logs"], load: 31, actions: 377 },
  { id: "mail", name: "Inbox Assistant", host: "workspace", initials: "IA", status: "paused", perms: ["mail:read"], load: 0, actions: 95 },
];

const LABELS = { allow: "Permitido", warn: "Alerta", block: "Bloqueado" };

let events = [
  { kind: "block", agent: "Claude Code", title: "rm -rf fuera del proyecto", cmd: "rm -rf /var/lib/postgresql", rule: "fs: solo /srv/app", t: "12:41" },
  { kind: "allow", agent: "Ops Bot", title: "Lectura de logs del pod api", cmd: "kubectl logs api-7f9c --tail=200", rule: "kubectl de solo lectura", t: "12:38" },
  { kind: "block", agent: "Claude Code", title: "Petición a dominio no visto antes", cmd: "curl https://paste.example.net/upload", rule: "egress: dominios conocidos", t: "12:30" },
  { kind: "allow", agent: "Claude Code", title: "git push a rama de trabajo", cmd: "git push origin feature/login", rule: "git: ramas no protegidas", t: "12:22" },
  { kind: "block", agent: "Ops Bot", title: "Intento de borrar un deployment", cmd: "kubectl delete deploy payments", rule: "kubectl de solo lectura", t: "11:57" },
  { kind: "allow", agent: "Inbox Assistant", title: "Resumen de bandeja", cmd: "mail.list(unread=true, limit=20)", rule: "mail:read", t: "11:40" },
];

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

let filter = "all";

function openAlerts() {
  return events.filter((e) => e.kind === "warn").length;
}

function renderNav() {
  const badge = openAlerts();
  const link = (v) =>
    `<a href="#${v.id}">${ICONS[v.id]}<span>${v.label}</span>${v.id === "actividad" && badge ? `<span class="badge">${badge}</span>` : ""}</a>`;
  $(".nav").innerHTML = VIEWS.map(link).join("");
  $(".tabbar").innerHTML = VIEWS.map(link).join("");
  markCurrent();
}

function eventItem(e, i, isNew) {
  return `<li data-i="${i}" class="${isNew ? "is-new" : ""}">
    <span class="kind ${e.kind}">${ICONS[e.kind]}</span>
    <span class="what"><strong>${esc(e.title)}</strong><small>${esc(e.agent)} · ${LABELS[e.kind]}</small></span>
    <time>${e.t}</time>
  </li>`;
}

function renderFeeds(newest = false) {
  $("#feed-home").innerHTML = events.slice(0, 5).map((e, i) => eventItem(e, i, newest && i === 0)).join("");
  $("#feed-all").innerHTML = events
    .map((e, i) => [e, i])
    .filter(([e]) => filter === "all" || e.kind === filter)
    .map(([e, i]) => eventItem(e, i, newest && i === 0))
    .join("");
  $("#stat-blocked").textContent = 5 + events.filter((e) => e.kind === "block").length;
}

function renderAgents() {
  const statusText = { ok: "Vigilado", warn: "Con alerta", paused: "En pausa" };
  $("#agents-home").innerHTML = AGENTS.map(
    (a) => `<li><span class="avatar">${a.initials}</span>
      <span class="agent-name"><strong>${a.name}</strong><small>${a.host}</small></span>
      <span class="agent-status ${a.status}"><span class="dot"></span>${statusText[a.status]}</span></li>`
  ).join("");
  $("#agents-all").innerHTML = AGENTS.map(
    (a) => `<li>
      <div class="agent-row"><span class="avatar">${a.initials}</span>
        <span class="agent-name"><strong>${a.name}</strong><small>${a.host}</small></span>
        <span class="agent-status ${a.status}"><span class="dot"></span>${statusText[a.status]}</span></div>
      <div class="perm">${a.perms.map((p) => `<span>${p}</span>`).join("")}</div>
      <div class="meter"><i style="width:${a.load}%"></i></div>
      <small class="meta">${a.actions} acciones revisadas hoy</small>
    </li>`
  ).join("");
}

function renderState() {
  const alerts = openAlerts();
  const alert = alerts > 0;
  document.documentElement.dataset.state = alert ? "alert" : "ok";
  $("#state-title").textContent = alert ? "Alerta" : "Protegido";
  $("#state-sub").textContent = alert
    ? `${alerts} ${alerts === 1 ? "acción necesita" : "acciones necesitan"} tu revisión`
    : `${AGENTS.filter((a) => a.status !== "paused").length} agentes vigilados · 0 alertas abiertas`;
  $("#demo-toggle").textContent = alert ? "Resolver alertas" : "Simular alerta";
}

function markCurrent() {
  const id = currentView();
  $$(".nav a, .tabbar a").forEach((a) =>
    a.hash === `#${id}` ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")
  );
}

function currentView() {
  const id = location.hash.slice(1);
  return VIEWS.some((v) => v.id === id) ? id : "inicio";
}

function route() {
  const id = currentView();
  $$(".view").forEach((s) => (s.hidden = s.dataset.view !== id));
  $("#view-title").textContent = VIEWS.find((v) => v.id === id).label;
  markCurrent();
  window.scrollTo(0, 0);
}

function openSheet(e) {
  $("#sheet-kind").textContent = `${LABELS[e.kind]} · ${e.t}`;
  $("#sheet-title").textContent = e.title;
  $("#sheet-cmd").textContent = e.cmd;
  $("#sheet-meta").innerHTML = `<div><dt>Agente</dt><dd>${esc(e.agent)}</dd></div><div><dt>Regla</dt><dd>${esc(e.rule)}</dd></div>`;
  $("#sheet-primary").textContent = e.kind === "allow" ? "Entendido" : e.kind === "warn" ? "Bloquear" : "Mantener bloqueado";
  $("#sheet-primary").onclick = () => {
    if (e.kind === "warn") e.kind = "block";
    update();
  };
  $(".sheet").hidden = $(".sheet-backdrop").hidden = false;
}

function closeSheet() {
  $(".sheet").hidden = $(".sheet-backdrop").hidden = true;
}

function update(newest = false) {
  renderNav();
  renderFeeds(newest);
  renderState();
}

function simulate() {
  if (openAlerts()) {
    events.forEach((e) => e.kind === "warn" && (e.kind = "block"));
    update();
    return;
  }
  const now = new Date();
  events.unshift({
    kind: "warn",
    agent: "Claude Code",
    title: "Lectura de ~/.ssh/id_ed25519",
    cmd: "cat ~/.ssh/id_ed25519",
    rule: "secretos: nunca leer claves privadas",
    t: now.toTimeString().slice(0, 5),
  });
  update(true);
}

document.addEventListener("click", (ev) => {
  const li = ev.target.closest(".feed li");
  if (li) openSheet(events[+li.dataset.i]);
  if (ev.target.closest("[data-close]") || ev.target.classList.contains("sheet-backdrop")) closeSheet();
  const sw = ev.target.closest(".switch");
  if (sw) sw.setAttribute("aria-checked", sw.getAttribute("aria-checked") !== "true");
  const chip = ev.target.closest(".chip");
  if (chip) {
    filter = chip.dataset.filter;
    $$(".chip").forEach((c) => c.classList.toggle("is-active", c === chip));
    renderFeeds();
  }
});
document.addEventListener("keydown", (ev) => ev.key === "Escape" && closeSheet());
$("#demo-toggle").addEventListener("click", simulate);
window.addEventListener("hashchange", route);

renderAgents();
update();
route();

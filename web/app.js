const STORAGE_KEYS = {
  baseUrl: 'datar:baseUrl',
  sessionId: 'datar:sessionId',
};

const DEFAULT_BASE_URL = 'http://localhost:8000';

const $ = (selector) => document.querySelector(selector);

const elements = {
  baseUrlInput: $('#base-url'),
  pingBtn: $('#ping-btn'),
  statusIndicator: $('#status-indicator'),
  agentInfo: $('#agent-info'),
  refreshAgent: $('#refresh-agent'),
  sessionSelect: $('#session-select'),
  refreshSessions: $('#refresh-sessions'),
  newSession: $('#new-session'),
  chatHistory: $('#chat-history'),
  chatForm: $('#chat-form'),
  messageInput: $('#message-input'),
  sessionBadge: $('#session-badge'),
  logs: $('#logs'),
  clearLogs: $('#clear-logs'),
};

const messageTemplate = document.getElementById('message-template');

const state = {
  baseUrl: '',
  sessionId: null,
  sessions: [],
  messages: [],
  isSending: false,
};

const normalizeAgentResponse = (rawText, originalMessage) => {
  const result = {
    text: '',
    isEcho: false,
  };

  if (rawText == null) {
    return result;
  }

  const trimmed = String(rawText).trim();
  if (!trimmed) {
    return result;
  }

  const lower = trimmed.toLowerCase();
  if (lower.startsWith('echo:')) {
    const withoutPrefix = trimmed.slice(5).trim();
    const fallback = withoutPrefix || originalMessage || '';
    result.text = fallback;
    result.isEcho = true;
    return result;
  }

  result.text = trimmed;
  return result;
};

const withNormalizedAssistant = (message, originalMessage) => {
  if (!message || typeof message !== 'object') return message;
  if (message.role !== 'assistant') return message;
  const normalized = normalizeAgentResponse(message.content, originalMessage);
  return {
    ...message,
    content: normalized.text,
    type: normalized.isEcho ? 'echo' : message.type,
  };
};

const formatDate = (value) => {
  if (!value) return '';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.valueOf())) return '';
  return date.toLocaleString();
};

const normalizeUrl = (url) => {
  if (!url) return '';
  try {
    const trimmed = url.trim();
    const clean = trimmed.endsWith('/') ? trimmed.slice(0, -1) : trimmed;
    const parsed = new URL(clean);
    return parsed.origin;
  } catch (error) {
    return url;
  }
};

const setBaseUrl = (url) => {
  state.baseUrl = normalizeUrl(url) || DEFAULT_BASE_URL;
  localStorage.setItem(STORAGE_KEYS.baseUrl, state.baseUrl);
  elements.baseUrlInput.value = state.baseUrl;
  setStatus('URL configurada', 'idle');
};

const setStatus = (text, variant = 'idle') => {
  const indicator = elements.statusIndicator;
  if (!indicator) return;
  indicator.textContent = text;
  indicator.className = `status status-${variant}`;
};

const logEvent = (type, message) => {
  if (!elements.logs) return;
  const log = document.createElement('div');
  log.className = `log-entry ${type}`;

  const timeEl = document.createElement('time');
  timeEl.dateTime = new Date().toISOString();
  timeEl.textContent = new Date().toLocaleTimeString();

  const label = document.createElement('span');
  label.className = 'label';
  label.textContent = type === 'error' ? 'Error' : type === 'warn' ? 'Aviso' : 'OK';

  const content = document.createElement('span');
  content.textContent = message;

  log.append(timeEl, label, content);
  elements.logs.prepend(log);
  elements.logs.scrollTop = 0;
};

const apiFetch = async (path, options = {}) => {
  if (!state.baseUrl) {
    throw new Error('Configura la URL del API antes de continuar');
  }

  const url = `${state.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get('content-type') || '';
  let payload = null;

  if (contentType.includes('application/json')) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  if (!response.ok) {
    const detail = payload?.detail || payload || response.statusText;
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }

  return payload;
};

const renderAgentInfo = (info) => {
  const container = elements.agentInfo;
  if (!container) return;

  if (!info) {
    container.innerHTML = '<p class="placeholder">No se pudo obtener información del agente.</p>';
    return;
  }

  const subAgents = Array.isArray(info.sub_agents) && info.sub_agents.length > 0
    ? `<ul>${info.sub_agents
        .map((agent) => `<li><strong>${agent.name || agent}</strong><br>${agent.description || ''}</li>`)
        .join('')}</ul>`
    : '<p class="placeholder">Sin subagentes registrados.</p>';

  container.innerHTML = `
    <div>
      <strong>Nombre</strong>
      <p>${info.name || 'Desconocido'}</p>
    </div>
    <div>
      <strong>Descripción</strong>
      <p>${info.description || 'Sin descripción disponible.'}</p>
    </div>
    <div>
      <strong>Instrucción</strong>
      <p>${info.instruction || 'N/D'}</p>
    </div>
    <div>
      <strong>Modelo</strong>
      <p>${info.model || 'N/D'}</p>
    </div>
    <div>
      <strong>Subagentes</strong>
      ${subAgents}
    </div>
  `;
};

const renderSessions = () => {
  const select = elements.sessionSelect;
  if (!select) return;
  const current = state.sessionId;

  if (state.sessions.length === 0) {
    select.innerHTML = '<option value="">Sin sesiones activas</option>';
    select.disabled = true;
    return;
  }

  select.disabled = false;
  const options = state.sessions
    .map((session) => {
      const labelDate = session.last_activity || session.created_at;
      const formattedDate = labelDate ? formatDate(labelDate) : 'Sin fecha';
      return `<option value="${session.session_id}">${session.session_id} · ${session.message_count} mensajes · ${formattedDate}</option>`;
    })
    .join('');

  select.innerHTML = `<option value="">Selecciona una sesión</option>${options}`;
  if (current) {
    select.value = current;
  }
};

const setSessionId = (sessionId) => {
  state.sessionId = sessionId || null;
  if (state.sessionId) {
    localStorage.setItem(STORAGE_KEYS.sessionId, state.sessionId);
    elements.sessionBadge.textContent = `Sesión activa: ${state.sessionId}`;
  } else {
    localStorage.removeItem(STORAGE_KEYS.sessionId);
    elements.sessionBadge.textContent = 'Sin sesión';
  }
  renderSessions();
};

const createMessageNode = ({ role, content, timestamp, type }) => {
  const clone = messageTemplate.content.cloneNode(true);
  const article = clone.querySelector('.message');

  article.classList.add(role === 'assistant' ? 'assistant' : role === 'user' ? 'user' : 'error');
  if (type === 'echo') {
    article.classList.add('echo');
  }

  const roleEl = clone.querySelector('.role');
  roleEl.textContent = role === 'assistant'
    ? type === 'echo'
      ? 'Agente (eco)'
      : 'Agente'
    : role === 'user'
      ? 'Usuario'
      : 'Sistema';

  const timeEl = clone.querySelector('.timestamp');
  if (timeEl) {
    const date = timestamp ? new Date(timestamp) : new Date();
    timeEl.dateTime = date.toISOString();
    timeEl.textContent = formatDate(date);
  }

  const contentEl = clone.querySelector('.content');
  contentEl.textContent = content;

  return clone;
};

const renderMessages = () => {
  const container = elements.chatHistory;
  if (!container) return;

  container.innerHTML = '';

  if (!state.messages || state.messages.length === 0) {
    container.innerHTML = '<p class="placeholder">Aún no hay mensajes en esta sesión.</p>';
    return;
  }

  state.messages.forEach((msg) => {
    container.append(createMessageNode(msg));
  });

  container.scrollTop = container.scrollHeight;
};

const loadAgentInfo = async () => {
  try {
    const info = await apiFetch('/agent/info');
    renderAgentInfo(info);
    logEvent('ok', 'Información del agente obtenida');
  } catch (error) {
    renderAgentInfo(null);
    logEvent('error', `No se pudo cargar la información del agente: ${error.message}`);
  }
};

const loadSessions = async () => {
  try {
    const sessions = await apiFetch('/sessions');
    state.sessions = Array.isArray(sessions) ? sessions : [];

    if (state.sessionId && !state.sessions.find((item) => item.session_id === state.sessionId)) {
      // Mantener la sesión local aunque no esté en el backend (posible expiración)
      state.sessions.unshift({
        session_id: state.sessionId,
        message_count: state.messages.length,
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
      });
    }

    renderSessions();
    logEvent('ok', 'Sesiones actualizadas');
  } catch (error) {
    logEvent('error', `No se pudo obtener la lista de sesiones: ${error.message}`);
    renderSessions();
  }
};

const loadSessionHistory = async (sessionId) => {
  if (!sessionId) {
    state.messages = [];
    renderMessages();
    return;
  }

  try {
    const history = await apiFetch(`/sessions/${sessionId}`);
    const rawMessages = Array.isArray(history?.messages) ? history.messages : [];
    state.messages = rawMessages.map((msg) => withNormalizedAssistant(msg));
    renderMessages();
    logEvent('ok', `Historial cargado para la sesión ${sessionId}`);
  } catch (error) {
    logEvent('error', `No se pudo obtener el historial: ${error.message}`);
  }
};

const sendMessage = async (message) => {
  if (!message || !message.trim()) return;
  if (state.isSending) return;

  state.isSending = true;
  elements.chatForm.classList.add('loading');
  elements.messageInput.setAttribute('disabled', 'true');

  const trimmedMessage = message.trim();
  const userTimestamp = new Date().toISOString();

  state.messages.push({
    role: 'user',
    content: trimmedMessage,
    timestamp: userTimestamp,
  });
  renderMessages();

  const payload = { message: trimmedMessage };
  if (state.sessionId) {
    payload.session_id = state.sessionId;
  }

  try {
    logEvent('warn', 'Enviando mensaje al agente…');
    const response = await apiFetch('/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    setSessionId(response.session_id);

    const agentAnswer = normalizeAgentResponse(response.response, trimmedMessage);

    state.messages.push({
      role: 'assistant',
      content: agentAnswer.text,
      timestamp: response.timestamp || new Date().toISOString(),
      type: agentAnswer.isEcho ? 'echo' : 'normal',
    });
    renderMessages();

    await loadSessions();
    await loadSessionHistory(response.session_id);

    logEvent('ok', 'Respuesta recibida del agente');
  } catch (error) {
    logEvent('error', `Error al enviar mensaje: ${error.message}`);
    state.messages.push({
      role: 'error',
      content: error.message,
      timestamp: new Date().toISOString(),
    });
    renderMessages();
  } finally {
    state.isSending = false;
    elements.chatForm.classList.remove('loading');
    elements.messageInput.removeAttribute('disabled');
    elements.messageInput.focus();
  }
};

const pingServer = async () => {
  try {
    setStatus('Comprobando…', 'warning');
    const health = await apiFetch('/health');
    setStatus(`Servidor activo · ${health.status || 'OK'}`, 'ok');
    logEvent('ok', 'Servidor disponible');
  } catch (error) {
    setStatus(`Error: ${error.message}`, 'error');
    logEvent('error', `No fue posible conectar con el servidor: ${error.message}`);
  }
};

const clearLogs = () => {
  elements.logs.innerHTML = '';
};

const registerEvents = () => {
  elements.baseUrlInput?.addEventListener('change', (event) => {
    setBaseUrl(event.target.value || DEFAULT_BASE_URL);
  });

  elements.pingBtn?.addEventListener('click', () => {
    pingServer();
  });

  elements.refreshAgent?.addEventListener('click', () => {
    loadAgentInfo();
  });

  elements.refreshSessions?.addEventListener('click', () => {
    loadSessions();
  });

  elements.newSession?.addEventListener('click', () => {
    setSessionId(null);
    state.messages = [];
    renderMessages();
    logEvent('warn', 'Se iniciará una nueva sesión en el próximo mensaje.');
  });

  elements.sessionSelect?.addEventListener('change', (event) => {
    const selected = event.target.value;
    if (!selected) {
      setSessionId(null);
      state.messages = [];
      renderMessages();
      return;
    }

    setSessionId(selected);
    loadSessionHistory(selected);
  });

  elements.chatForm?.addEventListener('submit', (event) => {
    event.preventDefault();
    const message = elements.messageInput.value;
    if (!message.trim()) return;
    elements.messageInput.value = '';
    sendMessage(message);
  });

  elements.clearLogs?.addEventListener('click', clearLogs);
};

const bootstrap = async () => {
  const storedUrl = localStorage.getItem(STORAGE_KEYS.baseUrl) || DEFAULT_BASE_URL;
  setBaseUrl(storedUrl);

  const storedSession = localStorage.getItem(STORAGE_KEYS.sessionId);
  if (storedSession) {
    setSessionId(storedSession);
  } else {
    renderSessions();
  }

  renderMessages();
  registerEvents();

  await Promise.allSettled([pingServer(), loadAgentInfo(), loadSessions()]);
  if (state.sessionId) {
    await loadSessionHistory(state.sessionId);
  }
};

document.addEventListener('DOMContentLoaded', bootstrap);


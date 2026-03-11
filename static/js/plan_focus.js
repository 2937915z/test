function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCSRFToken() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// -------- Daily Plan (M5) --------
document.addEventListener('change', async (e) => {
  const cb = e.target.closest('.js-plan-toggle');
  if (!cb) return;

  const li = cb.closest('li[data-plan-id]');
  const planId = li.getAttribute('data-plan-id');

  try {
    await postJSON(`/api/plan-items/${planId}/toggle/`, {});
    li.querySelector('span').classList.toggle('text-decoration-line-through');
    li.querySelector('span').classList.toggle('text-muted');
  } catch (err) {
    alert(`Update failed: ${err.message}`);
    cb.checked = !cb.checked;
  }
});

document.getElementById('btn-import')?.addEventListener('click', async () => {
  try {
    await postJSON(`/api/plan-items/import/`, {});
    location.reload(); 
  } catch (err) {
    alert(`Import failed: ${err.message}`);
  }
});

// -------- Focus Timer (M6) --------
let remaining = 25 * 60;
let timerId = null;
let startedAtISO = null;

function renderTimer() {
  const m = String(Math.floor(remaining / 60)).padStart(2, '0');
  const s = String(remaining % 60).padStart(2, '0');
  document.getElementById('timer').textContent = `${m}:${s}`;
}

function setDurationFromSelect() {
  const mins = parseInt(document.getElementById('duration').value, 10);
  remaining = mins * 60;
  renderTimer();
}

document.getElementById('duration')?.addEventListener('change', () => {
  if (timerId) return; 
  setDurationFromSelect();
});

document.getElementById('btn-start')?.addEventListener('click', () => {
  if (timerId) return;
  if (!startedAtISO) startedAtISO = new Date().toISOString();

  timerId = setInterval(() => {
    remaining -= 1;
    renderTimer();
    if (remaining <= 0) {
      clearInterval(timerId);
      timerId = null;
      alert('Session complete. Click Finish to save.');
    }
  }, 1000);
});

document.getElementById('btn-pause')?.addEventListener('click', () => {
  if (!timerId) return;
  clearInterval(timerId);
  timerId = null;
});

document.getElementById('btn-finish')?.addEventListener('click', async () => {
  if (timerId) { clearInterval(timerId); timerId = null; }
  const endISO = new Date().toISOString();
  const durationMins = parseInt(document.getElementById('duration').value, 10) - Math.floor(remaining / 60);

  const payload = {
    start_time: startedAtISO || new Date().toISOString(),
    end_time: endISO,
    duration_minutes: Math.max(1, durationMins),
    note: document.getElementById('note').value || '',
    plan_item_id: document.getElementById('linked-plan').value || null,
    assignment_id: null,
  };

  try {
    await postJSON('/api/focus-sessions/create/', payload);
    alert('Focus session saved.');
    startedAtISO = null;
    setDurationFromSelect();
    document.getElementById('note').value = '';
    document.getElementById('linked-plan').value = '';
  } catch (err) {
    alert(`Save failed: ${err.message}`);
  }
});

// init
setDurationFromSelect();
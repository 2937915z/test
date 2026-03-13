function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

async function postJSON(url, payload) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
    },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || resp.statusText);
  }
  return await resp.json();
}

document.addEventListener('change', async (e) => {
  const sel = e.target.closest('.js-status');
  if (!sel) return;

  const tr = sel.closest('tr');
  const assignmentId = tr.getAttribute('data-assignment-id');
  const status = sel.value;

  try {
    await postJSON(`/api/assignments/${assignmentId}/status/`, { status });
  } catch (err) {
    alert(`Update failed: ${err.message}`);
  }
});
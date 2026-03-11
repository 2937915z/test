function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken(),
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Request failed');
  }
  return res.json();
}

function setSaveState(row, text, type = 'secondary') {
  const badge = row.querySelector('.js-attendance-save-state');
  if (!badge) return;
  badge.className = `badge js-attendance-save-state text-bg-${type}`;
  badge.textContent = text;
}

document.addEventListener('change', async (e) => {
  const select = e.target.closest('.js-attendance-status');
  if (!select) return;

  const row = select.closest('[data-attendance-row]');
  const courseId = row.getAttribute('data-course-id');
  const classDate = row.getAttribute('data-class-date');
  const status = select.value;

  setSaveState(row, 'Saving...', 'warning');

  try {
    await postJSON(`/api/attendance/${courseId}/`, {
      class_date: classDate,
      status: status,
      note: ''
    });
    setSaveState(row, 'Saved', 'success');
  } catch (err) {
    setSaveState(row, 'Failed', 'danger');
    alert(`Attendance update failed: ${err.message}`);
  }
});
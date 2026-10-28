'use strict';
(() => {
  const form = document.getElementById('lookup-form');
  const submit = document.getElementById('lookup-submit');
  const status = document.getElementById('lookup-status');
  const result = document.getElementById('lookup-result');
  const id = document.getElementById('sit-id');
  const copy = document.getElementById('copy-id');
  let timer, controller, request = 0;
  function clearResult() {
    clearTimeout(timer); result.hidden = true; id.textContent = ''; copy.textContent = '复制 ID';
  }
  function invalidate() {
    request++; controller?.abort(); clearResult(); status.textContent = ''; submit.disabled = false;
  }
  document.getElementById('student-id').addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); document.getElementById('surname').focus(); } });
  form.addEventListener('input', invalidate);
  form.addEventListener('change', invalidate);
  document.getElementById('clear-result').addEventListener('click', clearResult);
  window.addEventListener('pagehide', invalidate);
  document.addEventListener('visibilitychange', () => { if (document.hidden) invalidate(); });
  copy.addEventListener('click', async () => {
    const value = id.textContent;
    if (!value) return;
    try { await navigator.clipboard.writeText(value); if (id.textContent === value) copy.textContent = '已复制'; }
    catch { status.textContent = '无法自动复制，请手动选择 ID 复制。'; }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); invalidate();
    const current = request;
    if (!form.reportValidity()) return;
    if (window.matchMedia('(max-width: 767px)').matches) document.activeElement?.blur();
    submit.disabled = true; status.textContent = '正在查询，请稍候…';
    controller = new AbortController();
    const activeController = controller;
    const timeout = setTimeout(() => activeController.abort(), 15000);
    try {
      const response = await fetch('/api/account-lookup', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        cache: 'no-store', credentials: 'omit', signal: activeController.signal,
        body: JSON.stringify({school:form.elements.school.value,student_id:form.elements.student_id.value.trim(),surname:form.elements.surname.value.trim()})
      });
      const data = await response.json();
      if (current !== request) return;
      if (!response.ok) { status.textContent = data.message || '暂时无法查询，请稍后重试。'; return; }
      id.textContent = data.sit_id; result.hidden = false;
      if (window.matchMedia('(max-width: 767px)').matches) result.scrollIntoView({block:'nearest',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
      status.textContent = '查询成功。'; timer = setTimeout(() => {clearResult(); status.textContent = '结果已自动隐藏，如需查看请重新查询。';}, 60000);
    } catch {
      if (current === request) status.textContent = '查询暂时不可用或请求超时，请稍后重试。';
    } finally {
      clearTimeout(timeout); if (current === request) submit.disabled = false;
    }
  });
})();

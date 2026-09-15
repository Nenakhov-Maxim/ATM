document.addEventListener('DOMContentLoaded', () => {
  const popup = document.querySelector('.new_report_popup');
  const form = document.querySelector('.new_report_form');
  if (!popup || !form) return;
  const title = form.querySelector('.new_report_form__title');
  const error = form.querySelector('.report-selection-error');
  const submit = form.querySelector('.new_report_accept-button');
  const periodFields = form.querySelector('.report-period-fields');
  const shiftFields = form.querySelector('.report-shift-fields');
  const shifts = [...form.querySelectorAll('[name="report_shifts"]')];
  let opener;
  let busy = false;

  function updateMode() {
    const byShift = form.elements.report_mode.value === 'shifts';
    periodFields.hidden = byShift;
    periodFields.disabled = byShift;
    shiftFields.hidden = !byShift;
    shiftFields.disabled = !byShift;
    form.elements.date_start.required = !byShift;
    form.elements.date_end.required = !byShift;
    form.elements.production_date.required = byShift;
    shifts[0].setCustomValidity(byShift && !shifts.some(input => input.checked) ? 'Выберите хотя бы одну смену.' : '');
    error.textContent = '';
  }

  function close() {
    if (busy) return;
    popup.classList.add('disable');
    opener?.focus();
  }

  [
    ['.completed-work-report-link', '/master/new_report/', 'Акт выполненных работ'],
    ['.profiling-invoice-report-link', '/master/profiling-invoice-report/', 'Накладная на линию профилирования'],
  ].forEach(([selector, action, caption]) => {
    document.querySelector(selector)?.addEventListener('click', event => {
      event.preventDefault();
      if (busy) return;
      opener = event.currentTarget;
      form.action = action;
      title.textContent = caption;
      updateMode();
      popup.classList.remove('disable');
      form.querySelector('[name="report_mode"]:checked').focus();
    });
  });
  form.addEventListener('change', updateMode);
  form.querySelector('.new_report_cansel-button').addEventListener('click', close);
  form.querySelector('.report-dialog-close').addEventListener('click', close);
  popup.addEventListener('keydown', event => {
    if (event.key === 'Escape') close();
    if (event.key !== 'Tab') return;
    const focusable = [...form.querySelectorAll('button, input')].filter(element => !element.matches(':disabled') && element.getClientRects().length);
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (busy || !form.reportValidity()) return;
    busy = true;
    error.textContent = '';
    const payload = new FormData(form);
    const controls = [...form.querySelectorAll('button, input')];
    const disabled = controls.map(control => control.disabled);
    controls.forEach(control => { control.disabled = true; });
    submit.textContent = 'Формирование...';
    form.setAttribute('aria-busy', 'true');
    let downloaded = false;
    try {
      const response = await fetch(form.action, { method: 'POST', body: payload });
      const disposition = response.headers.get('Content-Disposition') || '';
      if (!response.ok || !disposition.includes('attachment')) {
        let message = 'Не удалось сформировать документ. Проверьте подключение и повторите попытку.';
        if ((response.headers.get('Content-Type') || '').includes('application/json')) {
          const result = await response.json();
          message = Object.values(result.errors || {}).flat().join(' ') || result.message || message;
        } else if (response.redirected || response.status === 403) {
          message = 'Нет доступа к выгрузке. Проверьте, что вы вошли в систему.';
        }
        throw new Error(message);
      }
      const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      const plainName = disposition.match(/filename="([^"]+)"/i);
      const filename = encodedName ? decodeURIComponent(encodedName[1]) : plainName?.[1] || 'report.xlsx';
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      downloaded = true;
    } catch (exception) {
      error.textContent = exception.message || 'Ошибка выгрузки документа.';
    } finally {
      busy = false;
      controls.forEach((control, index) => { control.disabled = disabled[index]; });
      submit.textContent = 'Скачать Excel';
      form.removeAttribute('aria-busy');
      if (downloaded) close();
    }
  });
  updateMode();
});

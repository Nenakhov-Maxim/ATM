(() => {
  const dialog = document.querySelector('#production-dialog');
  const stockDialog = document.querySelector('#stock-dialog');
  let current;
  let action;
  let stockSource;
  let busy = false;

  async function request(path, data) {
    const response = await fetch(`/worker/${path}`, {
      method: data ? 'POST' : 'GET',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      ...(data ? { body: JSON.stringify(data) } : {}),
    });
    const body = await response.json().catch(() => {
      throw new Error('Сервер недоступен или сеанс завершён. Обновите страницу.');
    });
    if (!response.ok) {
      const error = new Error(body.message || 'Не удалось сохранить данные.');
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function message(target, text) { target.querySelector('.production-error').textContent = text; }
  function setBusy(target, value) {
    busy = value;
    target.querySelectorAll('button').forEach(button => { button.disabled = value; });
  }

  async function openCounter(taskId, mode) {
    if (busy || dialog.open || stockDialog.open) return;
    busy = true;
    try {
      if (window.pendingProductionCount && await window.pendingProductionCount === false) {
        throw new Error('Сначала сохраните текущее количество продукции.');
      }
      current = await request(`production-state/?id_task=${encodeURIComponent(taskId)}`);
      action = mode;
      document.querySelector('#production-title').textContent = mode === 'coating' ? 'Изменить базовое покрытие' : (mode === 'handover' ? 'Передача задания следующему рабочему' : 'Завершение задания');
      document.querySelector('#production-current').textContent = `Текущее покрытие: ${current.coating || 'без покрытия'}. Счётчик: ${current.total} шт.`;
      document.querySelector('#production-total').value = current.total;
      document.querySelector('#production-coating-fields').hidden = mode !== 'coating';
      document.querySelector('#production-coating').required = mode === 'coating';
      document.querySelector('#production-coating').value = '';
      document.querySelector('#production-submit').textContent = mode === 'coating' ? 'Сменить покрытие' : (mode === 'handover' ? 'Передать задание' : 'Завершить');
      message(dialog, '');
      dialog.showModal();
    } catch (error) { alert(error.message); }
    finally { busy = false; }
  }

  function openStock(state) {
    stockSource = state.id_task;
    document.querySelector('#stock-profile').textContent = `${state.profile}, ${state.coating || 'без покрытия'}`;
    document.querySelector('#stock-length').value = state.length || 3;
    message(stockDialog, '');
    stockDialog.showModal();
  }

  window.openProductionCompletion = element => openCounter(element.closest('.task-card-item').dataset.itemid, 'complete');
  window.openProductionHandover = element => openCounter(element.closest('.task-card-item').dataset.itemid, 'handover');

  document.addEventListener('click', async event => {
    const coatingButton = event.target.closest('.change-coating-button');
    if (coatingButton) return openCounter(coatingButton.dataset.taskId, 'coating');
    const stockButton = event.target.closest('[data-stock-source]');
    if (stockButton && !busy && !stockDialog.open) {
      busy = true;
      try {
        const data = await request(`production-state/?id_task=${stockButton.dataset.stockSource}`);
        if (data.pending_stock) openStock(data);
        else location.reload();
      } catch (error) { alert(error.message); }
      finally { busy = false; }
    }
  });
  dialog.querySelectorAll('[data-close-production]').forEach(button => {
    button.addEventListener('click', () => { if (!busy) dialog.close(); });
  });
  stockDialog.querySelector('[data-close-stock]').addEventListener('click', () => { if (!busy) stockDialog.close(); });
  for (const modal of [dialog, stockDialog]) {
    modal.addEventListener('cancel', event => { if (busy) event.preventDefault(); });
  }
  stockDialog.addEventListener('close', () => { if (!busy) location.reload(); });

  document.querySelector('#production-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    setBusy(dialog, true);
    try {
      const data = {
        id_task: current.id_task, total: Number(document.querySelector('#production-total').value),
        expected_total: current.total, revision: current.revision,
      };
      if (action === 'coating') data.coating = document.querySelector('#production-coating').value.trim();
      const paths = { coating: 'change-coating/', complete: 'complete_task/', handover: 'shiftChange/' };
      const result = await request(paths[action], data);
      dialog.close();
      if (action === 'complete' && result.pending_stock) openStock(result);
      else location.reload();
    } catch (error) {
      if (error.status === 409) {
        try {
          current = await request(`production-state/?id_task=${current.id_task}`);
          document.querySelector('#production-total').value = current.total;
          document.querySelector('#production-current').textContent = `Текущее покрытие: ${current.coating || 'без покрытия'}. Счётчик: ${current.total} шт.`;
        } catch (refreshError) { error.message = refreshError.message; }
      }
      message(dialog, error.message);
    } finally { setBusy(dialog, false); }
  });

  async function decide(makeStock) {
    if (busy) return;
    setBusy(stockDialog, true);
    try {
      await request('stock-decision/', {
        id_task: stockSource, decision: makeStock ? 'yes' : 'no',
        ...(makeStock ? { length: Number(document.querySelector('#stock-length').value) } : {}),
      });
      location.reload();
    } catch (error) { message(stockDialog, error.message); }
    finally { setBusy(stockDialog, false); }
  }
  document.querySelector('#stock-form').addEventListener('submit', event => { event.preventDefault(); decide(true); });
  document.querySelector('[data-stock-no]').addEventListener('click', () => decide(false));
})();

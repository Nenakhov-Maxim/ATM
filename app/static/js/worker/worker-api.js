// ===== Task Actions API =====
// ver
function build_request_error_message(source, fallbackMessage) {
  if (typeof source === 'string' && source.trim()) {
    return source;
  }
  if (source && typeof source === 'object') {
    if (typeof source.message === 'string' && source.message.trim()) {
      return source.message;
    }
    if (typeof source.error === 'string' && source.error.trim()) {
      return source.error;
    }
    if (source.responseJSON) {
      return build_request_error_message(source.responseJSON, fallbackMessage);
    }
    if (typeof source.responseText === 'string' && source.responseText.trim()) {
      return source.responseText;
    }
  }
  return fallbackMessage;
}

// Запуск задачи в работу
function start_working(e) {
  let elem = e.closest(".task-card-item")  
  let task_id = elem.dataset.itemid
  let link = '/worker/start_working/'
  let data = {'id_task':task_id, 'revision': Number(elem.dataset.coatingRevision || 0)}
  let type_request = 'POST'
  const start_time_from_data = document.querySelectorAll('.task-card-item[data-category="Выполняется"]')
  if (start_time_from_data.length > 0)  {
    alert('Нельзя запустить несколько задач одновременно. Пожалуйста завершите другие задачи.')
  } else {
    let isUserReady = true    
    if (elem.dataset.category === 'Ожидание') {
      isUserReady = confirm("Вы уверены, что хотите начать выполнения задания без переналадки? Время на переналадку будет равно 0");
    }    
    if (isUserReady) {ajax_request(link, type_request, data)} 
  }
}

//Старт пусконаладки
function start_settingUp(e){
  let task = e.closest(".task-card-item");    
  let id_task = task.dataset.itemid;
  let link = '/worker/setting-up/'
  let data = {'id_task': id_task}
  let type_request = 'POST'  
  ajax_request(link, type_request, data)
}

//Отмена выполнения задания
function deny_task(e) {
  let task = e.closest(".task-card-item");    
  let id_task = task.dataset.itemid;
  let deny_popup = document.querySelector('.deny_task_popup')  
  deny_popup.querySelector('#id_task_id').value = id_task
  deny_popup.classList.toggle('disable')
  deny_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{deny_popup.classList.add('disable')})
}

//Приостановка выполнения задания
function paused_task(e) {
  let task = e.closest(".task-card-item");     
  let id_task = task.dataset.itemid;
  let paused_popup = document.querySelector('.pause_task_popup')  
  paused_popup.querySelector('#id_task_id').value = id_task
  paused_popup.classList.toggle('disable')
  paused_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{paused_popup.classList.add('disable')})
}

// Завершение выпонения задания
function complete_task(e) {
  window.openProductionCompletion(e);
}

//Пересменка
function shiftChange(e) {
  window.openProductionHandover(e);
}

// ===== Shared AJAX =====
// Функция отправки запросов серверу (fetch + JSON)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function ajax_request(url, type, data) {
  const csrftoken = getCookie('csrftoken');
  return fetch(url, {
    method: type,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken,
      'Accept': 'application/json'
    },
    body: JSON.stringify(data)
  }).then(async (resp) => {
    if (!resp.ok) {
      let text = await resp.text();
      let parsed = null;
      try { parsed = JSON.parse(text); } catch(e) { parsed = text }
      alert(build_request_error_message(parsed, 'Ошибка запроса к серверу.'))
      return false;
    }
    // success
    if (url.indexOf('pause_task') !== -1 || url.indexOf('deny_task') !== -1 || url.indexOf('edit-profile-amount-value') !== -1) {
      // no reload
    } else {
      location.reload()
    }
    return true;
  }).catch((err) => {
    alert(build_request_error_message(err, 'Ошибка запроса к серверу.'))
    return false;
  });
}

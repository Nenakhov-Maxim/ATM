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

// ===== Task Start/Pause =====
// Запуск, приостановка, удаление задачи
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

function master_ajax_request(url, data, onSuccess, method='POST') {
  let ajaxOptions = {
    url: url,
    type: method,
    dataType: 'json',
    success: function(answer) {
      if (typeof onSuccess === 'function') {
        onSuccess(answer);
      } else {
        location.reload();
      }
    },
    error: function(xhr, textStatus, errorThrown) {
      alert(build_request_error_message(
        xhr || errorThrown || textStatus,
        'Ошибка запроса к серверу.'
      ));
    }
  };

  if (method === 'POST') {
    ajaxOptions.data = JSON.stringify(data);
    ajaxOptions.contentType = 'application/json';
    ajaxOptions.headers = {
      'X-CSRFToken': getCookie('csrftoken'),
      'Accept': 'application/json'
    };
  } else {
    ajaxOptions.data = data;
  }

  $.ajax(ajaxOptions);
}

$(document).ready(function() {
  $('.more-info-popup__start-task').click(function(){
    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id === "start") {
      master_ajax_request('start_task/', {'id_task': id_task});
    } else if (task.id === "pause") {
      let paused_popup = document.querySelector('.pause_task_popup')
      let pause_task_popup_form = document.querySelector('.pause_task_popup_form')
      paused_popup.classList.toggle('disable')
      paused_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{paused_popup.classList.add('disable')})
      pause_task_popup_form.action = `/master/pause_task/${id_task}`
    }
  });

  // ===== Task Delete =====
  // Удаление задачи
  $('.more-info-popup__delete-task').click(function(){
    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id === "delete") {
      let isUserReady = confirm("Вы уверены, что хотите удалить задачу? Восстановление будет невозможно");
      if (isUserReady) {
        master_ajax_request('delete_task/', {'id_task': id_task});
      }
    }
  });

  // ===== Task Hide =====
  // Cкрыть задачу
  $('.more-info-popup__hide-task').click(function(){
    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id === "hide") {
      let isUserReady = confirm("Вы уверены, что хотите скрыть задачу? Задача перестанет отображаться, но будет учитываться в статистике");
      if (isUserReady) {
        master_ajax_request('hide_task/', {'id_task': id_task});
      }
    }
  });

  // ===== Task Edit =====
  // Открытие окна редактирования задачи
  $('.more-info-popup__edit-task').click(function(){
    edit_task_popup.classList.toggle('disable')
    edit_task_popup.querySelector('.edit-task-popup__exit-popup').addEventListener('click', ()=>{edit_task_popup.classList.add('disable')})
    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id === "edit") {
      master_ajax_request('edit_task/', {'id_task': id_task}, function(data) {
        edit_task_popup.querySelector('#id_task_name').value = data['task_name']
        edit_task_popup.querySelector('[name="id_task"]').value = data['id_task']
        edit_task_popup.querySelector('[name="task_shift_date"]').value = data['task_shift_date'] || ''
        edit_task_popup.querySelector('[name="task_shift"]').value = data['task_shift'] || ''
        edit_task_popup.querySelector('#id_task_profile_type').value = data['task_profile_type']
        edit_task_popup.querySelector('#id_task_workplace').value = data['task_workplace']
        edit_task_popup.querySelector('#id_task_profile_amount').value = data['task_profile_amount']
        edit_task_popup.querySelector('#id_task_profile_length').value = data['task_profile_length']
        edit_task_popup.querySelector('#id_task_order_number').value = data['task_order_number'] || ""
        edit_task_popup.querySelector('#id_task_profile_material').value = data['task_profile_material'] || ""
        edit_task_popup.querySelector('#id_task_coating_type').value = data['task_coating_type'] || ""
        edit_task_popup.querySelector('#id_task_coating_area').value = data['task_coating_area'] || ""
        edit_task_popup.querySelector('#id_task_coating_thickness').value = data['task_coating_thickness'] || ""
        edit_task_popup.querySelector('#id_task_comments').value = data['task_comments']
        edit_task_popup.querySelector('.edit-task-popup__title-text').innerText = `Редактировать задачу № ${id_task}`
        //location.reload();
      }, 'GET');
    }
  });
});

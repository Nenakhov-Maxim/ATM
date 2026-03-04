// ===== Materials Fetch API =====
let type_profile_input = new_task_popup.querySelector('.popup-content-block__type-profile')

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

function load_materials_by_profile(profile_id) {
  fetch('get-material/', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({
          profile_id: profile_id
      })
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          const type_material_select = new_task_popup.querySelector('#id_task_type_material')
          type_material_select.innerHTML = ""
          for (const key in data.data) {
            if (Object.prototype.hasOwnProperty.call(data.data, key)) {
              const element = data.data[key];
              const new_option = document.createElement('option')
              new_option.innerHTML = element
              new_option.value = key
              type_material_select.append(new_option)
            }
          }
          
      } else {
        alert(build_request_error_message(data, 'Не удалось загрузить материалы для выбранного профиля.'));
      }
  })
  .catch(error => {
      alert(build_request_error_message(error, 'Ошибка загрузки материалов.'));
  });
}

type_profile_input.addEventListener('change', (event)=> {
  const profile_id = event.target.value
  // Отправка id на сервер и получение списка материалов для выбранного профиля
  load_materials_by_profile(profile_id)
})


// ===== Task Start/Pause =====
// Запуск, приостановка, удаление задачи
function master_ajax_request(url, data, onSuccess) {
  $.ajax({
    url: url,
    type: 'GET',
    data: data,
    headers: {
      "Accept": "network/json",
      "Content-Type": "network/json",
    },
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
  });
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
        let date_start = new Date(Date.parse(data['task_timedate_start'])).toISOString().slice(0,16)
        let date_end = new Date(Date.parse(data['task_timedate_end'])).toISOString().slice(0,16);
        edit_task_popup.querySelector('#id_task_timedate_start').value = date_start
        edit_task_popup.querySelector('#id_task_timedate_end').value = date_end
        edit_task_popup.querySelector('#id_task_profile_type').value = data['task_profile_type']
        edit_task_popup.querySelector('#id_task_workplace').value = data['task_workplace']
        edit_task_popup.querySelector('#id_task_profile_amount').value = data['task_profile_amount']
        edit_task_popup.querySelector('#id_task_profile_length').value = data['task_profile_length']
        edit_task_popup.querySelector('#id_task_comments').value = data['task_comments']
        edit_task_popup.querySelector('.edit-task-popup__title-text').innerText = `Редактировать задачу № ${id_task}`
        //location.reload();
      });
    }
  });
});

// ===== Task Actions API =====
// Запуск задачи в работу
function start_working(e) {
  let elem = e.closest(".task-card-item")  
  let task_id = elem.dataset.itemid
  let link = 'start_working/'
  let data = {'id_task':task_id}
  let type_request = 'GET'
  const start_time_from_data = document.querySelectorAll('.task-card-item[data-category="Выполняется"]')
  if (start_time_from_data.length > 0)  {
    alert('Нельзя запустить несколько задач одновременно. Пожалуйста завершите другие задачи.')
  } else {
    let isUserReady = true    
    if (elem.dataset.category == 'Ожидание') {
      isUserReady = confirm("Вы уверены, что хотите начать выполнения задания без переналадки? Время на переналадку будет равно 0");
    }    
    if (isUserReady) {ajax_request(link, type_request, data)} 
  }
}

//Старт пусконаладки
function start_settingUp(e){
  let task = e.closest(".task-card-item");    
  let id_task = task.dataset.itemid;
  let link = 'setting-up/'
  let data = {'id_task': id_task}
  let type_request = 'GET'  
  ajax_request(link, type_request, data)
}

//Отмена выполнения задания
function deny_task(e) {
  let task = e.closest(".task-card-item");    
  let id_task = task.dataset.itemid;
  let deny_popup = document.querySelector('.deny_task_popup')  
  let link = 'deny_task/'
  let data = {'id_task': id_task}
  let type_request = 'GET' 
  deny_popup.querySelector('#id_task_id').value = id_task
  deny_popup.classList.toggle('disable')
  deny_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{deny_popup.classList.add('disable')})
  ajax_request(link, type_request, data)
}

//Приостановка выполнения задания
function paused_task(e) {
  let task = e.closest(".task-card-item");     
  let id_task = task.dataset.itemid;
  let paused_popup = document.querySelector('.pause_task_popup')  
  let link = 'pause_task/'
  let data = {'id_task': id_task}
  let type_request = 'GET'
  paused_popup.querySelector('#id_task_id').value = id_task
  paused_popup.classList.toggle('disable')
  paused_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{paused_popup.classList.add('disable')})
  ajax_request(link, type_request, data)
}

// Завершение выпонения задания
function complete_task(e) {
  let task = e.closest(".task-card-item")
  let id_task = task.dataset.itemid;
  let main_block_task = $(`.task-card-item[data-itemid=${id_task}]`)[0]    
  let plan_profile_amount = main_block_task.querySelector('.right-side__required-quantity__amount').innerText
  let fact_profile_amount = main_block_task.querySelector('.right-side__current-quantity__amount').value
  let link = 'complete_task/'
  let data = {'id_task': id_task}
  let type_request = 'GET'
  clearInterval(interval);  
  if (Number(plan_profile_amount) != Number(fact_profile_amount)) {
    let isUserReady = confirm("Вы уверены, что хотите завершить задачу? Плановое и фактическое количество профиля не совпадают");
    if (isUserReady) {ajax_request(link, type_request, data)}
  } else {ajax_request(link, type_request, data)}
}

//Пересменка
function shiftChange(e) {
  let task = e.closest(".task-card-item")
  let id_task = task.dataset.itemid;
  let main_block_task = $(`.task-card-item[data-itemid=${id_task}]`)[0]
  let fact_profile_amount = main_block_task.querySelector('.right-side__current-quantity__amount').value
  let link = 'shiftChange/'
  let data = {'id_task': id_task, 'profile_amount': Number(fact_profile_amount)}
  let type_request = 'GET'
  clearInterval(interval);
  ajax_request(link, type_request, data)
}

// ===== Shared AJAX =====
// Функция отправки запросов серверу
function ajax_request(url, type,  data) {  
  // console.log(url)
  $.ajax({
  
    url: url,
    
    type: type,
    
    data: data,

    headers: {
        "Accept": "network/json",
        "Content-Type": "network/json",        
    },
    
    success: function(answer){

      // console.log(url,data)
      if (url.indexOf('pause_task') !== -1 || url.indexOf('deny_task') !== -1 || url.indexOf('edit-profile-amount-value') !== -1) {

      } else {
        console.log(answer)
        location.reload()
      }
        
    },
  
    error: function(){  
    alert('Error!');  
    }      
  });
}

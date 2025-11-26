//Взаимодействие клиента с сервером по вебсоккету

$(document).ready(function() {
  let task_id_list = {}
  let name_line = document.querySelectorAll(".person-info__department")[1].dataset.line
  let tasks_list = document.querySelectorAll(".task-card-item")
  const socket_task = new WebSocket(`ws://192.168.211.1/ws/task-transfer/${name_line}`); //На сервере
  // const socket_task = new WebSocket(`ws://127.0.0.1:8000/ws/task-transfer/${name_line}`); //На домашней машине

  for (const key in tasks_list) {
    if (Object.prototype.hasOwnProperty.call(tasks_list, key)) {
      const element = tasks_list[key];      
      task_id_list[element.dataset.itemid] = element.dataset.categoryId      
    }
  }

  socket_task.onopen = function() {

    socket_task.send(JSON.stringify({message:"start", task_list:task_id_list}))

  socket_task.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type == "Welcome"){
      // alert(`Успешно подключились к серверу AT-Manager. Производственная линия № ${name_line}`)
    } else if (data.type == "new_task") {
      ws_add_new_task(data['content'])
    } else if  (data.type == 'change_task') {
      alert(`Статус задачи "${data['content']['task_name']}" № ${data['content']['id']} от ${data['content']['task_timedate_start']} изменен на "${data['content']['task_status']}"`)
      if (data['content']['task_status_id']==5 || data['content']['task_status_id']==6) {
        document.querySelector(`.task-card-item[data-itemId="${data['content']['id']}"]`).remove()  
      }
    } else if (data.type == 'change_profile_amount') {
      
      profile_now = data.content
      active_item = document.querySelector('.task-card-item[data-category-id="3"]');
      active_input = active_item.querySelector('.right-side__current-quantity__amount').value = profile_now;
    }

  };
    
    

};
 // 1. Первоначальный сбор всех данных по WSGI
 // 2. Пока страница открыта, открывается соединение по вебсоккету
 // 3.  Отслеживание событий в реальном времени:
 // - Новое задание (добавить на страницу новое задание)
 // - должны быть функции: добавить новую карточку задания, удалить карточку задания, одновить статус карточки
 // - Изменение статуса заданий (должно быть оповещение)
 //  
})

function ws_add_new_task(data){
  let date_start = new Date(data['task_timedate_start']) 
  let date_end = new Date(data['task_timedate_end']) 
  
  let date_options = {    
    year: 'numeric',
    month: 'long',
    day: 'numeric',        
    hour: 'numeric',
    minute: 'numeric',
    timeZone: 'UTC',
    
  };

  let date_hour = (date_end - date_start)/1000/60/60
  console.log(date_hour)
  if (date_hour < 10) {
    date_hour = `0${Math.trunc(date_hour)}`
  } else {
    date_hour = `${Math.trunc(date_hour)}`
  }
  let date_minute = (date_hour - Math.trunc(date_hour)) * 60
  console.log(date_minute)
  if (date_minute < 10) {
    date_minute = `0${Math.trunc(date_minute)}`
  } else {
    date_minute = `${Math.trunc(date_minute)}`
  }
  let date_seconds = Math.trunc((date_minute - Math.trunc(date_minute)) * 60)
  console.log(date_seconds)
  if (date_seconds < 10) {
    date_seconds = `0${Math.trunc(date_seconds)}`
  } else {
    date_seconds = `${Math.trunc(date_seconds)}`
  }
  

  let date_to_time = `${date_hour}:${date_minute}:${date_seconds}`
  // task-card-item
  let div_main = document.createElement('div');
  div_main.className = "task-card-item"
  div_main.setAttribute('data-itemId', data['id'])
  div_main.setAttribute('data-category', data['task_status'])
  div_main.setAttribute('data-category-id', data['task_status_id'])
  // task-card-item__wrapper
  let div_wrapper = document.createElement('div');
  div_wrapper.className = "task-card-item__wrapper"
  div_wrapper.innerHTML = 
  `
  <div class="card-item__toolbar">              
    <div class="toolbar-item__history" onclick="more_information_click(this)"><img class="toolbar-item__history__svg" src="/static/img/Master.svg" alt="Развернуть"></div>
  </div>
  <div class="card-item__workplace-name">
    <span class="card-item__title">${data['task_name']}</span><br>
    <span class="card-item__title">(${data['task_profile_type']})</span>
    <div class="worplace-name__equipment"></div>
  </div>
  <div class="card-item__task-name">
      <span class="card-item__title">Время начала: ${new Date(data['task_timedate_start']).toLocaleString("ru", date_options)}</span><br>
      <span class="card-item__title">Время окончания: ${new Date(data['task_timedate_end']).toLocaleString("ru", date_options)}</span><br>
      <span class="card-item__title">Время на работу: ${date_to_time}</span><br>                
  </div>
  <div class="card-item__position-quantity">
    <span class="card-item__title">${data['task_profile_amount']}</span>
  </div>

  `
  // card-item__task-status
  let div_task_status = document.createElement('div');
  div_task_status.className = "card-item__task-status"
  if (data['task_status_id'] == 1) {
    div_task_status.innerHTML = 
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text task_added">${data['task_status']}</span>
    </div>             
    <span class="task-status__text">Дата начала: ${data['task_timedate_start']}</span>
    
    `  
  } else if (data['task_status_id'] == 4) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text falling-off">${data['task_status']}</span>
     </div>             
    <span class="task-status__text">Принято исполнетелем. Ожидает начала</span>
    
    `
  } else if(data['task_status_id'] == 3) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text working">${data['task_status']}</span>
    </div>             
    <span class="task-status__text">Старт выполнения <br> Факт. время начала: <br> ${data['task_timedate_start_fact']}</span>
    
    `
  } else if(data['task_status_id'] == 6) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text paused">${data['task_status']}</span>
    </div>                         
    <span class="task-status__text">Задача приостановлена. <br> Расскройте историю, чтобы узнать подробнее</span>
    
    `
  } else if(data['task_status_id'] == 5) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      span class="task-status-widget__text paused">${data['task_status']}</span>
    </div>             
    <span class="task-status__text">Задача отменена. <br> Расскройте историю, чтобы узнать подробнее</span>
    
    `
  } else if (data['task_status_id'] == 2) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text well_done">${data['task_status']}</span>
    </div>             
    <span class="task-status__text">Выполнено. Фактическая дата выполнения: {{el.task_timedate_end_fact}}</span>
    
    `
  } else if (data['task_status_id'] == 7) {
    div_task_status.innerHTML =
    `
    <div class="task-status-widget">              
      <span class="task-status-widget__text settingUp">${data['task_status']}</span>
    </div>             
    <span class="task-status__text">Наладка оборудования. Старт: ${data['task_time_settingUp']}</span>
    
    `
  }

  div_wrapper.append(div_task_status)

  //card-item__actions
  let div_item_action = document.createElement('div')
  div_item_action.className = 'card-item__actions'
  //actions__more-info
  let div_more_info = document.createElement('div')
  div_more_info.className = 'actions__more-info'

  if (data['task_status_id'] == 4 || data['task_status_id'] == 6) {
    div_more_info.innerHTML = 
    `
    <span class="more-info__text__accept" data-itemId=${data['id']} onclick="start_working(this)"></span>
    <span class="more-info__text__deny" data-itemId=${data['id']} onclick="deny_task(this)"></span>
    <span class="more-info__text__setting-up" data-itemId=${data['id']} onclick="start_settingUp(this)"></span>
    
    `  
  } else if (data['task_status_id'] == 3) {
    div_more_info.innerHTML =
    `
    <span class="more-info__text__complete" data-itemId=${data['id']} onclick="complete_task(this)"></span>
    <span class="more-info__text__paused" data-itemId=${data['id']} onclick="paused_task(this)"></span>
    
    `
  } else if (data['task_status_id'] == 7)  {
    div_more_info.innerHTML =
    `
    <span class="more-info__text__accept" data-itemId=${data['id']} onclick="start_working(this)"></span>
    <span class="more-info__text__deny" data-itemId=${data['id']} onclick="deny_task(this)"></span>
    
    `
  } 

  div_item_action.append(div_more_info)
  div_wrapper.append(div_item_action)
  div_main.append(div_wrapper)

  //task-card__more-information__wrapper
  let div_more_imformation_wrapper = document.createElement('div')
  div_more_imformation_wrapper.className = 'task-card__more-information__wrapper'
  if (data['task_status_id'] != 3) {
    div_more_imformation_wrapper.classList.add('disable')
  }

  div_more_imformation_wrapper.innerHTML =
   `
  <div class="more-information__header">
    <span class="more-information__header__title">Задача № ${data['id']}</span>
    <span class="more-information__header__task-text">${data['task_name']}</span>
  </div>
  
  `
  //more-information__worker-event 
  let div_worker_event = document.createElement('div')
  div_worker_event.className = 'more-information__worker-event '

  //worker-event-leftside
  let div_event_leftside = document.createElement('div')
  div_event_leftside.className = 'worker-event-leftside'

  //event-leftside__task-information
  let div_task_information = document.createElement('div')
  div_task_information.className = 'event-leftside__task-information'

  //task-information__left-side
  let datetime_to_date_start_fact = data['task_timedate_end'] - data['task_timedate_start_fact']
  let div_ti_ls = document.createElement('div')
  div_ti_ls.className = 'task-information__left-side'
  if (data['task_timedate_start_fact']) {
    div_ti_ls.innerHTML =
    `
    <span class="task-information__left-side__text" data-dateStartFact="${data['task_timedate_start_fact']}">Фактическое время начала: ${data['task_timedate_start_fact']}</span>
    <span class="task-information__left-side__text" data-dateEnd="${data['task_timedate_end']}">Закончить до: ${data['task_timedate_end']}</span>
    <span class="task-information__left-side__text">План времени: <span>${date_to_time}</span></span>
    <span class="task-information__left-side__text">Осталось времени: <span>${datetime_to_date_start_fact}</span></span>

    `
  } else {
    div_ti_ls.innerHTML =
    `

    <span class="task-information__left-side__text" data-dateEnd="${data['task_timedate_end']}">Закончить до: ${data['task_timedate_end']}</span>
    <span class="task-information__left-side__text">План времени: <span>${date_to_time}</span></span>
    <span class="task-information__left-side__text">Осталось времени: <span>00:00:00</span></span>
        
    `
  }

  div_task_information.append(div_ti_ls)

  // task-information__right-side
  let div_ti_rs = document.createElement('div')
  div_ti_rs.className = 'task-information__right-side'
  if  (data['task_status_id'] != 7 || data['task_status_id'] != 3) {
    div_ti_rs.innerHTML =
    `

    <div class="task-information__right-side__required-quantity">
      <span class="right-side__required-quantity__text">Необходимое количество</span>
      <span class="right-side__required-quantity__amount">${data['task_profile_amount']}</span>
    </div>
    <div class="task-information__right-side__current-quantity">
      <span class="right-side__current-quantity__text">Текущее количество</span>      
      <input class="right-side__current-quantity__amount" type="number" value="${data['profile_amount_now']}"></input>      
    </div>
    
    `
  } else {
    div_ti_rs.innerHTML =
    `
    <div class="task-information__right-side__required-quantity">
      <span class="right-side__required-quantity__text">Необходимое количество</span>
      <span class="right-side__required-quantity__amount">${data['task_profile_amount']}</span>
    </div>
    <div class="task-information__right-side__current-quantity">
      <span class="right-side__current-quantity__text">Текущее количество</span>
      <input class="right-side__current-quantity__amount" type="number" value="0"></input>
    </div>
    
    `
  }
  div_task_information.append(div_ti_rs)
  div_event_leftside.append(div_task_information)

  //event-leftside__buttons
  let div_leftside_buttons = document.createElement('div')
  div_leftside_buttons.className = 'event-leftside__buttons'
  if (data['task_status_id'] != 4 || data['task_status_id'] != 6 || data['task_status_id'] != 7) {
    div_leftside_buttons.innerHTML =
    `
    <div class="event-leftside__button-accept__inner" >
      <input class="event-leftside__button-accept" name="event-leftside__button-accept" type="button" value="Начать выполнение" data-itemId=${data['id']} onclick="start_working(this)">                    
    </div>
    <div class="event-leftside__button-stop__inner">
      <input class="event-leftside__button-deny" name="event-leftside__button-deny" type="button" value="Отменить" data-itemId=${data['id']} onclick="deny_task(this)">
    </div>

    ` 
  } else {
    div_leftside_buttons.innerHTML =
    `
    <div class="event-leftside__button-accept__inner">                    
      <input class="event-leftside__button-complete-task" name="event-leftside__button-complete-task" type="button" value="Завершить задание" data-itemId=${data['id']} onclick="complete_task(this)">
    </div>
    <div class="event-leftside__button-stop__inner" >
      <input class="event-leftside__button-pause" name="event-leftside__button-pause" type="button" value="Приостановить" data-itemId=${data['id']}  onclick="paused_task(this)"> 
    </div>
    
    ` 
  }
  div_event_leftside.append(div_leftside_buttons)
  div_worker_event.append(div_event_leftside)

  //worker-event-rightside
  let div_event_rightside = document.createElement('div')
  div_event_rightside.className = 'worker-event-rightside'
  div_event_rightside.setAttribute("data-workplace", `workpalce-${data['task_workplace_id']}`)
  if (data['task_status_id'] == 3) {
    div_event_rightside.innerHTML =
    `
    <h1>Видеопоток с веб-камеры</h1>
    <video hidden id="videoElement" autoplay></video>
    <canvas hidden id="canvas" width="640" height="480"></canvas>
    
    `
  } else {
    div_event_rightside.innerHTML =
    `
    <img id="video_stream" src="/static/img/video-disabled.svg" alt="Изображение с камеры" />
    
    ` 
  }
  div_worker_event.append(div_event_rightside)
  div_more_imformation_wrapper.append(div_worker_event)
  
  div_main.append(div_more_imformation_wrapper)
  


  // Общая вставка блока задания на страницу
  let cards_wrapper = document.querySelector('.task-cards-list')
  cards_wrapper.prepend(div_main)
}

//Действие при измнении количества записей на листе
let start_value = 0
let all_cards = document.querySelectorAll('.task-card-item')

$(document).ready(function() {
  document.querySelector('.quality-position__title').value = 10
  change_block_in_page()
  $('.quality-position__title').change(() => change_block_in_page(true));
  $('.navigation__right').click(() => right_in_page());
  $('.navigation__left').click(() => left_in_page());

});

function change_block_in_page(pos)  {
  if (pos == true) {start_value = 0}
  let value_re = document.querySelector('.quality-position__title').value
  let second_value_for_visible = Number(start_value) + Number(value_re)
  if  (second_value_for_visible > all_cards.length)  {second_value_for_visible = all_cards.length}
  document.querySelector('.all-task-info__range').innerText = `${start_value + 1}-${second_value_for_visible} из ${all_cards.length}` 
  for (let i = 0; i < all_cards.length; i++) {
    const element = all_cards[i]; 
    if (i >= Number(value_re) + Number(start_value) || i < start_value) {element.classList.add('disable')} else 
    {
        if (element.classList.contains('disable')){element.classList.remove('disable')}
    }
  }  
} 

function right_in_page() {
  let value_res = document.querySelector('.quality-position__title').value
  if (Number(start_value) + Number(value_res) < all_cards.length) {    
    start_value = start_value + Number(value_res)
    change_block_in_page(false)
    
  } else {change_block_in_page(true)} 
}

function left_in_page() {
  let value_res = document.querySelector('.quality-position__title').value
  if (Number(start_value) - Number(value_res) < 0) {      
    start_value = (all_cards.length - 1) - ((all_cards.length - 1) % value_res)
    change_block_in_page(false)
  } else {    
    start_value = Number(start_value) - Number(value_res)
    change_block_in_page(false)
  } 
}

// работа таймера
let seconds = 0;
let minutes = 0;
let hours = 0;
let seconds_end = 0;
let minutes_end = 0;
let hours_end = 0;
let interval;
let timer_start
let timer_end
let timer_end_split


$(document).ready(function() {  
  start_time_from_data = document.querySelectorAll('span[data-datestartfact]:not([data-datestartfact=""])')
  for (let i = 0; i < start_time_from_data.length; i++) {
    let now = new Date();
    const element = start_time_from_data[i];
    let element_data = element.dataset.datestartfact    
    let norm_date = moment(element_data, 'YYYY-MM-DD h:mm:ss').toDate()
    let sum_time = (now - norm_date)/1000/60/60
    hours = Math.trunc(sum_time)
    let minute_sum =(sum_time - Math.trunc(sum_time)) * 60
    minutes = Math.trunc((sum_time - Math.trunc(sum_time)) * 60)
    seconds = Math.trunc((minute_sum - minutes) * 60)
    timer_start = element.parentElement.querySelectorAll('.task-information__left-side__text')[3]
    timer_end = element.parentElement.querySelectorAll('.task-information__left-side__text')[4]    
    timer_end_split = timer_end.childNodes[1].innerText.split(':')
    seconds_end = Number(timer_end_split[2]);
    minutes_end = Number(timer_end_split[1]);
    hours_end = Number(timer_end_split[0]); 
    interval = setInterval(updateTime, 1000);    
  }  
});

function updateTime() {  
  seconds++;
  if (seconds === 60) {
    minutes++;
    seconds = 0;
  }
  if (minutes === 60) {
    hours++;
    minutes = 0;
  }
  timer_start.textContent = `Затрачено времени: ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  updateTime_end()
}

function updateTime_end() {  
  seconds_end--;
  if (seconds_end === 0) {
    minutes_end--;
    seconds_end = 60;
  }
  if (minutes_end === 0) {
    hours_end--;
    minutes_end = 59;
  }
  timer_end.textContent = `Осталось времени: ${hours_end.toString().padStart(2, '0')}:${minutes_end.toString().padStart(2, '0')}:${seconds_end.toString().padStart(2, '0')}`;
}

//Открытие и закрытие дополнительной информации по задаче
function more_information_click(e) {  
  let card_item = e.closest(".task-card-item")
  card_item.querySelector('.task-card__more-information__wrapper').classList.toggle('disable')  
}

//Запуск задачи в работу
function start_working(e) {
  let elem = e.closest(".task-card-item")  
  let task_id = elem.dataset.itemid
  let link = 'start_working/'
  let data = {'id_task':task_id}
  let type_request = 'GET'
  start_time_from_data = document.querySelectorAll('.task-card-item[data-category="Выполняется"]')    
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
  let task = e.closest(".task-card-item");  ;    
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
  let task = e.closest(".task-card-item");  ;    
  let id_task = task.dataset.itemid;
  let main_block_task = $(`.task-card-item[data-itemid=${id_task}]`)[0]
  let fact_profile_amount = main_block_task.querySelector('.right-side__current-quantity__amount').value
  let link = 'shiftChange/'
  let data = {'id_task': id_task, 'profile_amount': Number(fact_profile_amount)}
  let type_request = 'GET'
  clearInterval(interval);
  ajax_request(link, type_request, data)
}

// Передача видео через websocket (Необходимо раскомментить, как только подключу камеру!)

$(document).ready(function() {
  let list_task = document.querySelectorAll('.task-card-item[data-category="Выполняется"]')
  for (const elem in list_task) {
    if (Object.prototype.hasOwnProperty.call(list_task, elem)) {
      const task = list_task[elem];
      let task_id = task.dataset.itemid
      if (task.dataset.video == 'True') {
          videoStream(task_id)  
      } else {
        alert('Автоматическое определение количества профиля для текущего типа недоступно. Пожалуйста, добавляйте вручную')
      }   
      
    }
  }
})

//Видео поток
const enabled_task = document.querySelector('div.task-card-item[data-category-id="3"]')
let videoElement 
let remoteVideoElement 
let callButton
let hangupButton
let localStream;
let peerConnection;

// const serverUrl = 'ws://192.168.211.1/ws/video/'; // URL WebSocket сервера
const serverUrl = 'ws://127.0.0.1:8000/ws/video/'; // URL WebSocket сервера
let ws;

if (enabled_task) {
  videoElement = enabled_task.querySelector('#localVideo');
  remoteVideoElement = enabled_task.querySelector('#remoteVideo');
  callButton = enabled_task.querySelector('#callButton');
  hangupButton = enabled_task.querySelector('#hangupButton');
  checkboxAutoVision = enabled_task.querySelector('#automatic-vision-checkbox'); 
}



async function videoStream() {
  if (checkboxAutoVision.checked) {
      alert('В данный момент осуществляется автоматическое определение количества профиля');
  } else {
      return;
  }
  console.log('Start Camera button clicked');
  try {
    console.log('Requesting camera access...');
    
    try {
      localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      console.log('Camera access granted, setting video source');
      videoElement.srcObject = localStream;
      callButton.disabled = false;
      callButton.click();
      // startButton.disabled = true;
      console.log('Camera started successfully');
    } catch (cameraError) {
      console.log('Camera not available, creating synthetic video stream');
      
      // Create synthetic video stream for testing
      const canvas = document.createElement('canvas');
      canvas.width = 320;
      canvas.height = 240;
      const ctx = canvas.getContext('2d');
      
      // Create a synthetic video stream
      const stream = canvas.captureStream(30); // 30 FPS
      
      // Animate the canvas
      let frame = 0;
      const animate = () => {
        // Clear canvas
        ctx.fillStyle = '#000080';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw moving rectangle
        const x = (Math.sin(frame * 0.02) * 200) + 220;
        const y = (Math.cos(frame * 0.03) * 150) + 165;
        
        ctx.fillStyle = '#FF0000';
        ctx.fillRect(x, y, 100, 50);
        
        // Draw text
        ctx.fillStyle = '#FFFFFF';
        ctx.font = '20px Arial';
        ctx.fillText(`Test Video Frame: ${frame}`, 50, 50);
        ctx.fillText('Synthetic Camera Feed', 50, 80);
        
        frame++;
        requestAnimationFrame(animate);
      };
      
      animate();
      
      localStream = stream;
      videoElement.srcObject = localStream;
      callButton.disabled = false;
      // startButton.disabled = true;
      console.log('Synthetic camera started successfully');
    }
  } catch (e) {
    console.error('Error starting video:', e);
    alert('Error starting video: ' + e.message);
  }
};

if (callButton) {
  callButton.onclick = () => {
    callButton.disabled = true;
    hangupButton.disabled = false;

    // Инициализация WebSocket соединения
    ws = new WebSocket(serverUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Отправляем предложение SDP на сервер
      createOfferAndSend();
    };
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'answer') {
        // Получаем ответ SDP от сервера и устанавливаем его
        setRemoteDescription(message.sdp);
      } else if (message.type === 'candidate') {
        // Получаем ICE candidate от сервера и добавляем его
        addIceCandidate(message.candidate);
      } else if (message.type === 'detection_result') {
        // Обрабатываем результаты обнаружения объектов
        console.log('Обнаруженные объекты:', message.objects);
        // TODO: Если требуется, то отражаем результаты на странице
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };
}
if (hangupButton) {
  hangupButton.onclick = () => {
    hangup();
  };
}




async function createPeerConnection() {
  // Configure comprehensive ICE servers for maximum compatibility
  const configuration = {
    iceServers: [
      // Google STUN servers
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      { urls: 'stun:stun2.l.google.com:19302' },
      { urls: 'stun:stun3.l.google.com:19302' },
      { urls: 'stun:stun4.l.google.com:19302' },
      // Additional public STUN servers
      { urls: 'stun:stun.stunprotocol.org:3478' },
      { urls: 'stun:stun.voiparound.com' },
      { urls: 'stun:stun.voipbuster.com' },
      // Free TURN servers for relay (when STUN fails)
      {
        urls: 'turn:openrelay.metered.ca:80',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      },
      {
        urls: 'turn:openrelay.metered.ca:443',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      },
      {
        urls: 'turn:openrelay.metered.ca:443?transport=tcp',
        username: 'openrelayproject',
        credential: 'openrelayproject'
      }
    ]
  };
  
  peerConnection = new RTCPeerConnection(configuration);
  console.log('PeerConnection created with STUN/TURN servers');

  peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
      console.log('Generated ICE candidate:', event.candidate.type, event.candidate.candidate);
        sendIceCandidate(event.candidate);
      // Отправляем ICE candidate на сервер
      
    } else {
      console.log('ICE candidate gathering completed');
    }
  };

  peerConnection.oniceconnectionstatechange = () => {
    console.log('ICE connection state changed to:', peerConnection.iceConnectionState);
    if (peerConnection.iceConnectionState === 'failed') {
      console.error('ICE connection failed - NAT traversal unsuccessful');
    } else if (peerConnection.iceConnectionState === 'connected') {
      console.log('ICE connection established successfully!');
    } else if (peerConnection.iceConnectionState === 'disconnected') {
      console.warn('ICE connection disconnected');
    }
  };

  peerConnection.onicegatheringstatechange = () => {
    console.log('ICE gathering state changed to:', peerConnection.iceGatheringState);
    if (peerConnection.iceGatheringState === 'complete') {
      console.log('All ICE candidates have been gathered');
    }
  };

  peerConnection.onconnectionstatechange = () => {
    console.log('Connection state changed to:', peerConnection.connectionState);
    if (peerConnection.connectionState === 'failed') {
      console.error('Peer connection failed completely');
    } else if (peerConnection.connectionState === 'connected') {
      console.log('Peer connection established successfully!');
    }
  };

  peerConnection.ontrack = (event) => {
    console.log('Received remote track:', event.track.kind);
    if (event.track.kind === 'video') {
      // Display the processed video from server
      // remoteVideoElement.srcObject = event.streams[0];
      profileType = remoteVideoElement.dataset.profiletype
      input_element = enabled_task.querySelector('.right-side__current-quantity__amount')
      remoteVideoElement.innerHTML = `<p>Идет автоматическое сканирование.</p> <p>Тип профиля: ${profileType}</p><p>Текущее количество: ${input_element.value}`
      console.log('Remote video stream set');
    }
  };

  localStream.getTracks().forEach(track => {
    peerConnection.addTrack(track, localStream);
  });
}

async function createOfferAndSend() {
  await createPeerConnection();
  try {
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);
    // Отправляем предложение SDP на сервер через WebSocket
    ws.send(JSON.stringify({ type: 'offer', sdp: offer.sdp, task_id: enabled_task.dataset.itemid }));
  } catch (e) {
    console.error('createOffer error:', e);
  }
}

async function setRemoteDescription(sdp) {
  try {
    remote_answer = {type: 'answer', sdp: sdp}
    await peerConnection.setRemoteDescription(remote_answer);
    // ws.send(JSON.stringify(remote_answer))
  } catch (e) {
    console.error('setRemoteDescription error:', e);
  }
}

async function addIceCandidate(candidate) {
  try {
    await peerConnection.addIceCandidate(candidate);
  } catch (e) {
    console.error('addIceCandidate error:', e);
  }
}

function sendIceCandidate(candidate) {
  candidate_new = {
    'candidate': candidate.candidate,
    'foundation': candidate.foundation,
    'ip': candidate.address || candidate.ip,
    'port': candidate.port,
    'protocol': candidate.protocol,
    'type': candidate.type,
    'priority': candidate.priority,
    'component': candidate.component,
    'sdpMid': candidate.sdpMid,
    'sdpMLineIndex': candidate.sdpMLineIndex,
    'tcpType': candidate.tcpType
  }
  ws.send(JSON.stringify({ type: 'candidate', candidate: candidate_new}));
}

function hangup() {
  if (peerConnection) {
    peerConnection.close();
    peerConnection = null;
  }
  if (localStream) {
    localStream.getTracks().forEach(track => track.stop());
    localStream = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
  callButton.disabled = false;
  hangupButton.disabled = true;
  startButton.disabled = false;
}



// Изменение количества профиля вручную на наладке (на выполнении меняется через вебсоккет)
$(document).ready(function(){
  //С камерой - document.querySelectorAll('.task-card-item[data-category="Наладка"]')
  // Без камеры - document.querySelectorAll('.task-card-item[data-category="Выполняется"], .task-card-item[data-category="Наладка"]')
  let profile_amount_input = document.querySelectorAll('.task-card-item[data-category="Выполняется"], .task-card-item[data-category="Наладка"]')
  for (const item in profile_amount_input) {
    if (Object.prototype.hasOwnProperty.call(profile_amount_input, item)) {
      const card_element = profile_amount_input[item];
      let id_task = card_element.dataset.itemid                
      input_element = card_element.querySelector('.right-side__current-quantity__amount')
               
      input_element.addEventListener('keypress', function(e){        
        var key = e.which;
        if(key == 13)  {
          e.target.blur()}})
      input_element.addEventListener('blur', (e) =>{
        let value = 0        
        let input_data = e.target.value
        if (input_data.includes('+')) {
          let arr_data = input_data.split('+')
          for (let i = 0; i < arr_data.length; i++) {
            const element = Number(arr_data[i]);
            value = value + element
          }
          // value = Number(arr_data[0]) + Number(arr_data[1])
        } else {
          value = e.target.value          
        }
       
        if (Number.isNaN(Number(value))) {
          alert('Неверное значение количества профиля. Допустимы числа и операция сложения')
        } else {
          let link = 'edit-profile-amount-value/'
          let data = {'id_task': id_task, 'value':Number(value)}
          let type_request = 'GET'         
          ajax_request(link, type_request, data)
          e.target.value = value    
        }
            
      })
    }
  }
})

//Функция отправки запросов серверу
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

// Работа чекбокса "включить автоматическое распознование"

$(document).ready(function() {

  const auto_vision_checkbox = document.querySelectorAll('#automatic-vision-checkbox[data-statusId="3"]');
  // console.log(auto_vision_checkbox)
  
  for (checkbox of auto_vision_checkbox) {
    input_profile_amount = document.querySelector('.task-card-item[data-category-id="3"]').querySelector('.right-side__current-quantity__amount')
    if (checkbox) {
      if (checkbox.checked) {
        input_profile_amount.disabled = true
        callButton.click();
      } else {
        input_profile_amount.disabled = false
        hangupButton.click();
        }
      checkbox.addEventListener('change', (event)=> {
        if (!checkbox.checked) {
          hangupButton.click(); }

        task_id = document.querySelector('.task-card-item[data-category-id="3"]').dataset.itemid
        fetch(`/change-task-automatic-vision/${task_id}/${checkbox.checked}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
          })
          .then(response=>{
            response.json()
          })
          .then(data=> {
            console.log(data)
          })
        if (checkbox.checked) {
          input_profile_amount.disabled = true
          location.reload();
          
        } else {
          input_profile_amount.disabled = false
        }
      });

    } else {
      console.warn('Element with id "automatic-vision-checkbox" not found');
    }
  }
});


// При нажатии Shift + фокус на окне добавления и поставить плюс

document.addEventListener('DOMContentLoaded', (event)=> {
  document.addEventListener('keypress', (event)=> {
    if (event.shiftKey) {
      if (event.key == '+') {
        event.preventDefault();
        value_input = document.querySelector('.task-card-item[data-category-id="3"').querySelector('.right-side__current-quantity__amount');
        value_input.focus();
        old_value = value_input.value;
        new_value = String(old_value) + '+';
        value_input.value = new_value
      }
    }
  })
})
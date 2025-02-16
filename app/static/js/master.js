
//Панель мастера
//История задачи приклике на стрелку вниз

let cards_task = document.querySelectorAll('.task-card-item')
for (const key in cards_task) {
  if (Object.prototype.hasOwnProperty.call(cards_task, key)) {
    const card_item = cards_task[key];
    let id_task = card_item.dataset.itemid    
    card_item.querySelector('.toolbar-item__history__svg').addEventListener('click', () => open_task_history(id_task, card_item))
}
}

function open_task_history(id_task, card_item) {
  let popup_history = card_item.querySelector('.task-card__more-information__wrapper')  
  if (popup_history.classList.contains('disable')) {
    popup_history.classList.remove('disable')
    card_item.querySelector('.toolbar-item__history__svg').src = '/static/img/master_top.svg'
  } else {
    popup_history.classList.add('disable')
    card_item.querySelector('.toolbar-item__history__svg').src = '/static/img/Master.svg'
  }
};

//Опции по задаче

for (const key in cards_task) {
  if (Object.prototype.hasOwnProperty.call(cards_task, key)) {
    const card_item = cards_task[key];
    let id_task = card_item.dataset.itemid    
    card_item.querySelector('.more-info__text, .actions__more-info').addEventListener('click', () => open_actions(card_item))
  }
}
//Скрытие опций при клике в любом другом месте
document.addEventListener('mouseup', function (e) {   
  let popup_action = document.querySelectorAll('.more-info-popup');
  for (const key in popup_action) {
    if (Object.prototype.hasOwnProperty.call(popup_action, key)) {
      const element = popup_action[key];           
      if (e.target.closest(".more-info-popup") && (e.target.classList != 'close-popup')) return;
      element.classList.add("disable");
    }
  }  
  
});

function open_actions(card_item) {
  let popup_action = card_item.querySelector('.more-info-popup')
  let close_button = card_item.querySelector('.close-popup')
   

  if (popup_action.classList.contains('disable')) {
    popup_action.classList.remove('disable')
  } else {
    popup_action.classList.add('disable')
  } 
};

function close_action(e) {  
  e.closest('.more-info-popup').classList.toggle('disable')   
}


// Переключение меню
let menu_items = document.querySelectorAll('.header-menu-item')

for (const key in menu_items) {

  if (Object.prototype.hasOwnProperty.call(menu_items, key)) {
    const menu_item = menu_items[key];        
    menu_item.addEventListener('click', () => toggle_menu(menu_item))
  }
};

function toggle_menu(menu_item) {
  for (const key in menu_items) {

    if (Object.prototype.hasOwnProperty.call(menu_items, key)) {
      const item = menu_items[key];   

      if (item.classList.contains('active')) {
        item.classList.remove('active')
      }
    }
  };

  menu_item.classList.add('active')
  filter_task(menu_item.outerText)
};

//Выбор стартового меню при открытии страницы
window.onload = () => load_window()

function load_window() {  
  for (const key in menu_items) {

    if (Object.prototype.hasOwnProperty.call(menu_items, key)) {
      const menu_item = menu_items[key];  

      if (menu_item.outerText === 'Все задачи') {
        menu_item.classList.add('active')
      }
    }
  };
};

//Отображение задач при выборе фильтра (надо переделать будет ;))

function filter_task(filter)  {    
  let task_item = document.querySelectorAll('.task-card-item')  
  switch (filter) {
    case 'Все задачи':      
      for (const key in task_item) {        
        if (Object.prototype.hasOwnProperty.call(task_item, key)) {
          const item = task_item[key];
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }          
        }
      }
      break;
      case 'Выполняются':        
        for (const key in task_item) {
          if (Object.prototype.hasOwnProperty.call(task_item, key)) {
            const item = task_item[key];
            if (item.classList.contains('disable')) {
              item.classList.remove('disable')
            }            
            if (item.dataset.category != 'Выполняется') {              
              item.classList.add('disable')
            }            
          }
        }
        break;
      case 'Ожидают старта':        
      for (const key in task_item) {
        if (Object.prototype.hasOwnProperty.call(task_item, key)) {
          const item = task_item[key];
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }
          if (item.dataset.category != 'Ожидание') {
            item.classList.add('disable')
          }            
        }
      }
      break;
      case 'Приостановлены':        
      for (const key in task_item) {
        if (Object.prototype.hasOwnProperty.call(task_item, key)) {
          const item = task_item[key];
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }
          if (item.dataset.category != 'Приостановлена') {
            item.classList.add('disable')
          }            
        }
      }
      break;
      case 'Завершенные':        
      for (const key in task_item) {
        if (Object.prototype.hasOwnProperty.call(task_item, key)) {
          const item = task_item[key];
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }
          if (item.dataset.category != 'Выполнено') {
            item.classList.add('disable')
          }            
        }
      }
      break;
      case 'Созданные':        
      for (const key in task_item) {
        if (Object.prototype.hasOwnProperty.call(task_item, key)) {
          const item = task_item[key];
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }
          if (item.dataset.category != 'Создана') {
            item.classList.add('disable')
          }            
        }
      }
      break;   
  
    default:
      break;
  }
}

// Новое задание открытие/скрытие poup
let new_task_button = document.querySelector('.toolbars__new-task')
let new_task_popup = document.querySelector('.new-task-popup')
let edit_task_popup = document.querySelector('.edit-task-popup')
      
new_task_button.addEventListener('click', ()=>open_new_task_popup())
new_task_popup.querySelector('.new-task-popup__exit-popup').addEventListener('click', ()=>open_new_task_popup())
new_task_popup.querySelectorAll('.popup-button')[2].addEventListener('click', ()=>open_new_task_popup())
edit_task_popup.querySelectorAll('.popup-button')[2].addEventListener('click', ()=>open_new_task_popup())

function open_new_task_popup() {  
  new_task_popup.classList.toggle('disable')
}; 

//Запуск, приостановка, удаление задачи
$(document).ready(function() {

  $('.more-info-popup__start-task').click(function(){

    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id == "start") {      
      $.ajax({
  
        url: 'start_task/',
        
        type: 'GET',
        
        data: {'id_task': id_task},
    
        headers: {
            "Accept": "network/json",
            "Content-Type": "network/json",        
        },
        
        success: function(data){ 
          console.log(data)
          location.reload();  
        },
      
        error: function(){  
        alert('Error!');  
        }      
      });  
    } else if (task.id == "pause") {
      let paused_popup = document.querySelector('.pause_task_popup')
      let pause_task_popup_form = document.querySelector('.pause_task_popup_form')     
      paused_popup.classList.toggle('disable')
      paused_popup.querySelector('.pause_task_popup_cansel-button').addEventListener('click', ()=>{paused_popup.classList.add('disable')})     
      pause_task_popup_form.action = `/master/pause_task/${id_task}`     
      
    } 
  });
});

//Удаление задачи
$(document).ready(function() {

  $('.more-info-popup__delete-task').click(function(){

    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id == "delete") {
      let isUserReady = confirm("Вы уверены, что хотите удалить задачу? Восстановление будет невозможно");
      if (isUserReady) {
        $.ajax({
    
          url: 'delete_task/',
          
          type: 'GET',
          
          data: {'id_task': id_task},
      
          headers: {
              "Accept": "network/json",
              "Content-Type": "network/json",        
          },
          
          success: function(data){ 
            console.log(data)
            location.reload(); 
          },
        
          error: function(){  
          alert('Error!');  
          }      
        });  
      }
    } 
  });
});

//Cкрыть задачу
$(document).ready(function() {

  $('.more-info-popup__hide-task').click(function(){

    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id == "hide") {
      let isUserReady = confirm("Вы уверены, что хотите скрыть задачу? Задача перестанет отображаться, но будет учитываться в статистике");
      if (isUserReady) {
        $.ajax({
    
          url: 'hide_task/',
          
          type: 'GET',
          
          data: {'id_task': id_task},
      
          headers: {
              "Accept": "network/json",
              "Content-Type": "network/json",        
          },
          
          success: function(data){ 
            console.log(data)
            location.reload();               
          },
        
          error: function(){  
          alert('Error!');  
          }      
        });  
      }  
    } 
  });
});

//Открытие окна редактирования задачи
$(document).ready(function() {
  $('.more-info-popup__edit-task').click(function(){
    edit_task_popup.classList.toggle('disable')
    edit_task_popup.querySelector('.edit-task-popup__exit-popup').addEventListener('click', ()=>{edit_task_popup.classList.add('disable')})
    let task = this;
    let id_task = task.dataset.itemid;
    if (task.id == "edit") {
         
      $.ajax({
  
        url: 'edit_task/',
        
        type: 'GET',
        
        data: {'id_task': id_task},
    
        headers: {
            "Accept": "network/json",
            "Content-Type": "network/json",        
        },
        
        success: function(data){ 
          edit_task_popup.querySelector('#id_task_name').value = data['task_name']
          let date_start = new Date(Date.parse(data['task_timedate_start'])).toISOString().slice(0,16)
          let date_end = new Date(Date.parse(data['task_timedate_end'])).toISOString().slice(0,16);
          edit_task_popup.querySelector('#id_task_timedate_start').value = date_start
          edit_task_popup.querySelector('#id_task_timedate_end').value = date_end
          edit_task_popup.querySelector('#id_task_profile_type').value = data['task_profile_type']
          edit_task_popup.querySelector('#id_task_workplace').value = data['task_workplace']
          edit_task_popup.querySelector('#id_task_profile_amount').value = data['task_profile_amount']
          edit_task_popup.querySelector('#id_task_comments').value = data['task_comments']
          edit_task_popup.querySelector('.edit-task-popup__title-text').innerText = `Редактировать задачу № ${id_task}`          
          //location.reload();            
        },
        error: function(){  
        alert('Error!');  
        }      
      });    
    } 
  });
});

//Изменение записей на странице
let start_value = 0
let all_cards = document.querySelectorAll('.task-card-item')

$(document).ready(function() {
  
  document.querySelector('.quality-position__title').value = 10
  change_block_in_page()


  $('.quality-position__title').change(() => change_block_in_page(true));
  $('.navigation__right').click(() => right_in_page());
  $('.navigation__left').click(() => left_in_page());
});

// Изменение количества отображаемых задач на странице
function change_block_in_page(pos)  {

  if (pos == true) {
    start_value = 0
  }

  let value_re = document.querySelector('.quality-position__title').value
  let second_value_for_visible = Number(start_value) + Number(value_re)
  if  (second_value_for_visible > all_cards.length)  {
    second_value_for_visible = all_cards.length
  }
  document.querySelector('.all-task-info__range').innerText = `${start_value + 1}-${second_value_for_visible} из ${all_cards.length}` 
  
  for (let i = 0; i < all_cards.length; i++) {
    const element = all_cards[i]; 

    if (i >= Number(value_re) + Number(start_value) || i < start_value) {
      element.classList.add('disable')
    } else {
        if (element.classList.contains('disable')){
          element.classList.remove('disable')
        }
    }
  }  
} 

// Действие при клике на следующую страницу
function right_in_page() {
  let value_res = document.querySelector('.quality-position__title').value

  if (Number(start_value) + Number(value_res) < all_cards.length) {        
    start_value = start_value + Number(value_res)
    change_block_in_page(false)
  } else {    
    change_block_in_page(true)
  } 
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

function menu_click () {
  const screenWidth = window.screen.width
  if (screenWidth <= 800) {
    if (document.querySelector('.header-menu-list').style.display == 'flex') {
      document.querySelector('.header-menu-list').style.display = 'none'
      // document.querySelector('.header-menu-wrapper::after').style.display = 'block' 
    } else {
      document.querySelector('.header-menu-list').style.display = 'flex'
      // document.querySelector('.header-menu-wrapper::after').style.display = 'none'
    }
    
  }
}

document.addEventListener("resize", (event) => {
  const screenWidth = window.screen.width
  if (screenWidth > 800)  {
    document.querySelector('.header-menu-list').style.display = 'flex'
  }
});

// Открытие и закрытие модального окна нового отчета
function action_report_popup(e) {
  document.querySelector('.new_report_popup').classList.toggle('disable')
  document.querySelector('.new_report_cansel-button').addEventListener('click', ()=>{
    document.querySelector('.new_report_popup').classList.add('disable')
  })
  document.querySelector('.new_report_accept-button').addEventListener('click', ()=>{
    document.querySelector('.new_report_popup').classList.add('disable')
  })
}



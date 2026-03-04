// ===== Task Cards UI =====
// Панель мастера
// История задачи при клике на стрелку вниз

// const { createElement } = require("react");

let cards_task = document.querySelectorAll('.task-card-item')
for (const card_item of cards_task) {
  const historyToggle = card_item.querySelector('.toolbar-item__history__svg')
  if (historyToggle) {
    historyToggle.addEventListener('click', () => open_task_history(card_item))
  }
}

function open_task_history(card_item) {
  let popup_history = card_item.querySelector('.task-card__more-information__wrapper')  
  if (popup_history.classList.contains('disable')) {
    popup_history.classList.remove('disable')
    card_item.querySelector('.toolbar-item__history__svg').src = '/static/img/master_top.svg'
  } else {
    popup_history.classList.add('disable')
    card_item.querySelector('.toolbar-item__history__svg').src = '/static/img/Master.svg'
  }
};

// ===== Task Actions Popup =====
// Опции по задаче

for (const card_item of cards_task) {
  const actionsToggle = card_item.querySelector('.more-info__text, .actions__more-info')
  if (actionsToggle) {
    actionsToggle.addEventListener('click', () => open_actions(card_item))
  }
}
//Скрытие опций при клике в любом другом месте
document.addEventListener('mouseup', function (e) {   
  let popup_action = document.querySelectorAll('.more-info-popup');
  for (const element of popup_action) {
    if (e.target.closest(".more-info-popup") && !e.target.classList.contains('close-popup')) return;
    element.classList.add("disable");
  }  
  
});

function open_actions(card_item) {
  let popup_action = card_item.querySelector('.more-info-popup')
   

  if (popup_action.classList.contains('disable')) {
    popup_action.classList.remove('disable')
  } else {
    popup_action.classList.add('disable')
  } 
};

function close_action(e) {  
  e.closest('.more-info-popup').classList.toggle('disable')   
}


// ===== Header Menu =====
// Переключение меню
let menu_items = document.querySelectorAll('.header-menu-item')

for (const menu_item of menu_items) {
  menu_item.addEventListener('click', () => toggle_menu(menu_item))
};

function toggle_menu(menu_item) {
  for (const item of menu_items) {
    if (item.classList.contains('active')) {
      item.classList.remove('active')
    }
  }

  menu_item.classList.add('active')
  filter_task(menu_item.outerText)
};

//Выбор стартового меню при открытии страницы
window.onload = () => load_window()

function load_window() {  
  for (const menu_item of menu_items) {
    if (menu_item.outerText === 'Все задачи') {
      menu_item.classList.add('active')
    }
  }
};

//Отображение задач при выборе фильтра (надо переделать будет ;))

function filter_task(filter)  {    
  let task_item = document.querySelectorAll('.task-card-item')  
  switch (filter) {
    case 'Все задачи':      
      for (const item of task_item) {
        if (item.classList.contains('disable')) {
          item.classList.remove('disable')
        }
      }
      break;
      case 'Выполняются':        
        for (const item of task_item) {
          if (item.classList.contains('disable')) {
            item.classList.remove('disable')
          }            
          if (item.dataset.category !== 'Выполняется') {              
            item.classList.add('disable')
          }
        }
        break;
      case 'Ожидают старта':        
      for (const item of task_item) {
        if (item.classList.contains('disable')) {
          item.classList.remove('disable')
        }
        if (item.dataset.category !== 'Ожидание') {
          item.classList.add('disable')
        }
      }
      break;
      case 'Приостановлены':        
      for (const item of task_item) {
        if (item.classList.contains('disable')) {
          item.classList.remove('disable')
        }
        if (item.dataset.category !== 'Приостановлена') {
          item.classList.add('disable')
        }
      }
      break;
      case 'Завершенные':        
      for (const item of task_item) {
        if (item.classList.contains('disable')) {
          item.classList.remove('disable')
        }
        if (item.dataset.category !== 'Выполнено') {
          item.classList.add('disable')
        }
      }
      break;
      case 'Созданные':        
      for (const item of task_item) {
        if (item.classList.contains('disable')) {
          item.classList.remove('disable')
        }
        if (item.dataset.category !== 'Создана') {
          item.classList.add('disable')
        }
      }
      break;   
  
    default:
      break;
  }
}

// ===== New Task Popup =====
// Новое задание открытие/скрытие poup
let input_index = 2

let new_task_button = document.querySelector('.toolbars__new-task')
let new_task_popup = document.querySelector('.new-task-popup')
let edit_task_popup = document.querySelector('.edit-task-popup')

if (new_task_button && new_task_popup && edit_task_popup) {
  const newPopupExit = new_task_popup.querySelector('.new-task-popup__exit-popup')
  const newPopupButtons = new_task_popup.querySelectorAll('.popup-button')
  const editPopupButtons = edit_task_popup.querySelectorAll('.popup-button')

  new_task_button.addEventListener('click', ()=>open_new_task_popup(new_task_popup))
  if (newPopupExit) {
    newPopupExit.addEventListener('click', ()=>open_new_task_popup(new_task_popup))
  }
  if (newPopupButtons[2]) {
    newPopupButtons[2].addEventListener('click', ()=>open_new_task_popup(new_task_popup))
  }
  if (editPopupButtons[2]) {
    editPopupButtons[2].addEventListener('click', ()=>open_new_task_popup(edit_task_popup))
  }
}

function open_new_task_popup(elem) {  
  elem.classList.toggle('disable')
  input_index = 2
}; 

// ===== Dynamic Form Rows =====
// Добавление длины профиля в форму

function add_profile_length(event) {
  event.preventDefault()
  const new_br = document.createElement('br')
  const new_div_length = document.createElement('div')
  const new_div_amount = document.createElement('div')
  const new_div_close = document.createElement('div')
  new_div_length.classList.add('popup-content-block__amount')
  new_div_amount.classList.add('popup-content-block__amount')
  new_div_close.classList.add('popup-content-close-line')
  
  const inner_html_length = `    
            <span class="popup-content-block__amoun__text">Длина профиля ${input_index}</span>
            <input type="number" name="task_profile_length" step="any" required="" id="id_task_profile_length">     
  `
  const inner_html_amount = `    
            <span class="popup-content-block__amoun__text">Количество профиля ${input_index}</span>
            <input type="number" name="task_profile_amount" required="" id="id_task_profile_amount">     
  `

  const inner_html_close = `<a href="">удалить строку</a>`

  new_div_length.innerHTML = inner_html_length
  new_div_amount.innerHTML = inner_html_amount
  new_div_close.innerHTML = inner_html_close
  if (input_index === 2){
    $('div.new-task-popup__content-block')[0].append(new_br)
  }  
  $('div.new-task-popup__content-block')[0].append(new_div_amount)
  $('div.new-task-popup__content-block')[0].append(new_div_length)
  $('div.new-task-popup__content-block')[0].append(new_div_close) 
  input_index += 1
  new_div_close.addEventListener('click', (event)=> {
    event.preventDefault()
    const this_elem = event.target.closest('div')
    const length_profile = this_elem.previousSibling
    const amount_profile = length_profile.previousSibling
    this_elem.remove()
    length_profile.remove()
    amount_profile.remove()
  })  
}

// ===== API-Driven Form Data =====
// Добавление материалов при выборе профиля при создании новой заявки


// ===== Pagination =====
// Изменение записей на странице
let start_value = 0
let all_cards = document.querySelectorAll('.task-card-item')

$(document).ready(function() {
  const qualityInput = document.querySelector('.quality-position__title')
  if (!qualityInput) {
    return;
  }

  qualityInput.value = 10
  change_block_in_page()


  $('.quality-position__title').change(() => change_block_in_page(true));
  $('.navigation__right').click(() => right_in_page());
  $('.navigation__left').click(() => left_in_page());
});

// Изменение количества отображаемых задач на странице
function change_block_in_page(pos)  {

  if (pos === true) {
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
  const screenWidth = window.innerWidth
  const headerMenuList = document.querySelector('.header-menu-list')
  if (!headerMenuList) {
    return;
  }
  if (screenWidth <= 800) {
    if (headerMenuList.style.display === 'flex') {
      headerMenuList.style.display = 'none'
      // document.querySelector('.header-menu-wrapper::after').style.display = 'block' 
    } else {
      headerMenuList.style.display = 'flex'
      // document.querySelector('.header-menu-wrapper::after').style.display = 'none'
    }
    
  }
}

window.addEventListener("resize", (event) => {
  const screenWidth = window.innerWidth
  const headerMenuList = document.querySelector('.header-menu-list')
  if (!headerMenuList) {
    return;
  }
  if (screenWidth > 800)  {
    headerMenuList.style.display = 'flex'
  }
});

// ===== Report Modal =====
// Открытие и закрытие модального окна нового отчета
function action_report_popup(e) {
  const reportPopup = document.querySelector('.new_report_popup')
  const cancelButton = document.querySelector('.new_report_cansel-button')
  const acceptButton = document.querySelector('.new_report_accept-button')
  if (!reportPopup) {
    return;
  }

  reportPopup.classList.toggle('disable')
  if (cancelButton) {
    cancelButton.addEventListener('click', ()=> {
      reportPopup.classList.add('disable')
    })
  }
  if (acceptButton) {
    acceptButton.addEventListener('click', ()=> {
      reportPopup.classList.add('disable')
    })
  }
}

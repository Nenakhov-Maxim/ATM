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

// Status and text search share the same pagination state.
let selectedTaskFilter = 'Все задачи'

function filter_task(filter) {
  selectedTaskFilter = filter
  change_block_in_page(true)
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
}; 

// ===== Dynamic Form Rows =====
// Добавление длины профиля в форму

function add_profile_length(event) {
  event.preventDefault()
  const contentBlock = new_task_popup.querySelector('.new-task-popup__content-block')
  const sourceRow = contentBlock.querySelector('.profile-variant-row')
  if (!sourceRow) {
    return
  }

  const rowIndex = input_index
  const newRow = sourceRow.cloneNode(true)
  newRow.dataset.variantIndex = rowIndex

  newRow.querySelectorAll('input, select').forEach((field) => {
    field.value = ''
    const label = newRow.querySelector(`label[for="${field.id}"]`)
    field.id = `${field.id}_${rowIndex}`
    if (label) label.htmlFor = field.id
  })
  newRow.querySelector('.profile-variant-title').textContent = `Продукция ${rowIndex}`

  const closeRow = document.createElement('div')
  closeRow.className = 'popup-content-close-line'
  closeRow.innerHTML = '<a href="#">Удалить строку</a>'
  closeRow.addEventListener('click', (closeEvent) => {
    closeEvent.preventDefault()
    newRow.remove()
  })
  newRow.querySelector('.profile-variant-heading').append(closeRow)
  const variantRows = contentBlock.querySelectorAll('.profile-variant-row')
  variantRows[variantRows.length - 1].after(newRow)
  input_index += 1
}

// ===== API-Driven Form Data =====
// Добавление материалов при выборе профиля при создании новой заявки


// ===== Pagination =====
// Изменение записей на странице
let start_value = 0
let all_cards = document.querySelectorAll('.task-card-item')

const taskSearch = document.querySelector('.search-item')
const taskCategories = {
  'Выполняются': 'Выполняется',
  'Ожидают старта': 'Ожидание',
  'Приостановлены': 'Приостановлена',
  'Завершенные': 'Выполнено',
  'Созданные': 'Создана',
}

function normalizeTaskText(text) {
  return text.toLocaleLowerCase('ru').replace(/ё/g, 'е').replace(/\s+/g, ' ').trim()
}

function matchingTaskCards() {
  const query = normalizeTaskText(taskSearch ? taskSearch.value : '')
  const category = taskCategories[selectedTaskFilter]
  return Array.from(all_cards).filter(card =>
    (!category || card.dataset.category === category) &&
    normalizeTaskText(card.textContent).includes(query)
  )
}

function taskPageSize() {
  const input = document.querySelector('.quality-position__title')
  const value = Number(input.value)
  const size = Number.isInteger(value) && value > 0 ? value : 10
  input.value = size
  return size
}

$(document).ready(function() {
  const qualityInput = document.querySelector('.quality-position__title')
  if (!qualityInput) return

  change_block_in_page(true)
  if (taskSearch) {
    taskSearch.addEventListener('input', () => change_block_in_page(true))
  }
  $('.quality-position__title').change(() => change_block_in_page(true))
  $('.navigation__right').click(() => right_in_page())
  $('.navigation__left').click(() => left_in_page())
})

function change_block_in_page(reset) {
  const cards = matchingTaskCards()
  const size = taskPageSize()
  if (reset || start_value >= cards.length) start_value = 0
  const end = Math.min(start_value + size, cards.length)
  const visible = new Set(cards.slice(start_value, end))
  for (const card of all_cards) {
    card.classList.toggle('disable', !visible.has(card))
  }
  document.querySelector('.all-task-info__range').innerText =
    `${cards.length ? start_value + 1 : 0}-${end} из ${cards.length}`
}

function right_in_page() {
  const size = taskPageSize()
  start_value = start_value + size < matchingTaskCards().length ? start_value + size : 0
  change_block_in_page(false)
}

function left_in_page() {
  const size = taskPageSize()
  const count = matchingTaskCards().length
  start_value = start_value >= size ? start_value - size : Math.max(0, Math.ceil(count / size) - 1) * size
  change_block_in_page(false)
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

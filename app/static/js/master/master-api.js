let type_profile_input = new_task_popup.querySelector('.popup-content-block__type-profile')
console.log(type_profile_input)
type_profile_input.addEventListener('change', (event)=> {
  profile_id = event.target.value
  // Отправка id на сервер и получение списка материалов для выбранного профиля
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
          type_material_select = new_task_popup.querySelector('#id_task_type_material')
          type_material_select.innerHTML = ""
          for (const key in data.data) {
            console.log(data.data)
            if (Object.prototype.hasOwnProperty.call(data.data, key)) {
              const element = data.data[key];
              new_option = document.createElement('option')
              new_option.innerHTML = element
              new_option.value = key
              type_material_select.append(new_option)
            }
          }
          
      } else {
          console.log(data);
      }
  })
  .catch(error => {
      console.error('Ошибка:', error);
  });
})


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
          edit_task_popup.querySelector('#id_task_profile_length').value = data['task_profile_length']
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

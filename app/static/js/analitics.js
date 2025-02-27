// Количество изготовленного профиля
const ctx_current_profile = document.getElementById('chart-current-work__profile');
const ctx_performance = document.getElementById('chart-planned-work__performance');
const ctx_load = document.getElementById('chart-planned-work__load');
const ctx_setup_speed = document.getElementById('chart__setup-speed');
const ctx_hours_worked = document.getElementById('chart__hours-worked');
const ctx_profile_amount = document.getElementById('chart__profile-amount');
const ctx_effectiveness = document.getElementById('chart__effectiveness');
const change_current_work_element = document.getElementById('choice-current-work');
const filter_date_element = document.getElementById('plan-analysis-filter__date')


// заполнение статус баров текущего выполнения задания по линиям
let status_bar_collection = document.querySelectorAll(".loading-equipment__status-bar")
for (const key in status_bar_collection) {
  if (Object.prototype.hasOwnProperty.call(status_bar_collection, key)) {
    const element = status_bar_collection[key];
    let data_koef = parseInt(element.getAttribute("data-koef"))
    let status_bar_elem = element.querySelector('.status-bar__value')    
    let new_value_status = `${data_koef}%`
    status_bar_elem.style.height = new_value_status
  }
}

//Переключение между типами графиков в количестве изготовленного профиля
function change_current_work(element) {  
  chartInstance.destroy();  
  current_profile_update(element.value); 
}

//Функция построения графика для current_profile
function current_profile_update(filter){ 
  ajax_request('update-chart/current_profile/' + filter + '/', 'GET', {}).then(answer => {    
    config = update_chart('current_profile', answer)
    chartInstance = new Chart(ctx_current_profile, config);
  })
}

//Функция построения графика производительности линии
function current_performance_update(filter=99){ 
  ajax_request('update-chart/current_performance/' + filter + '/', 'GET', {}).then(answer => {    
    config = update_chart('current_performance', answer)
    chartPerformance = new Chart(ctx_performance, config);
  })
}

//Переключение между типами графиков "рабочая загрузка"
function change_array_chart(element) {  
  chartSpeedSetup.destroy();  
  setup_speed(element.value); 
}

//Функция построения графика среднего времени переналадки по рабочим
function setup_speed(filter) {
  ajax_request('update-chart/setup_speed/' + filter + '/', 'GET', {}).then(answer => {       
    config = update_chart('setup_speed', answer)
    chartSpeedSetup = new Chart(ctx_setup_speed, config);
  })  
}

function update_chart(block, data_values) {
  let data
  let labels
  let date_value
  let label
  let type_chart
  let indexAxis_value
  let title_value
  
  if (block == 'current_profile') {    
    labels = []
    date_value = []

    for (const key in data_values.answer) {
      if (Object.prototype.hasOwnProperty.call(data_values.answer, key)) {
        if (key != '') {          
          labels.push(key)
          date_value.push(data_values.answer[key])
        }
      }
    }      
    
    label = 'Количество изготовленного профиля, шт.'
    type_chart = 'bar'
    indexAxis_value = 'y'
    title_value = 'Количество изготовленного профиля, шт.'

  } else if (block == 'current_performance') {
    labels = []
    date_value = []
    for (const key in data_values.answer) {
      if (Object.prototype.hasOwnProperty.call(data_values.answer, key)) {
        const line_perf = data_values.answer[key];
        labels.push(key)
        let sum_perfomance = 0        
        line_perf.forEach(element => {
          sum_perfomance += element
        });
        date_value.push(sum_perfomance / line_perf.length)
      }
    }    
    label = 'Производительность линии, профиль/час'
    type_chart = 'bar'
    indexAxis_value = 'x'
    title_value = 'Производительность линии, профиль/час'
  } else if (block == 'current_load') {
    labels = ['Линия 1', 'Линия 2', 'Линия 3', 'Линия 4', 'Линия 5']
    date_value = [65, 59, 80, 81, 100]
    label = 'Загрузка линии'
    type_chart = 'bar'
    indexAxis_value = 'x'
    title_value = 'Загрузка линии, %'
  } else  if (block == 'setup_speed') {
    labels = []
    date_value = []
    for (const key in data_values.answer) {
      if (Object.prototype.hasOwnProperty.call(data_values.answer, key)) {
        const time_rework= data_values.answer[key];
        labels.push(key)
        let sum_perfomance = 0        
        time_rework.forEach(element => {
          sum_perfomance += element
        });
        date_value.push(sum_perfomance / time_rework.length)
      }
    }
    label = 'Среднее время переналадки/наладки'
    type_chart = 'bar'
    indexAxis_value = 'y'
    title_value = 'Среднее время переналадки/наладки, мин.' 
  } else if (block == 'hours_worked')  {
    labels = ['Рабочий 1', 'Рабочий 2', 'Рабочий 3', 'Рабочий 4', 'Рабочий 5', 'Рабочий 6', 'Рабочий 7', 'Рабочий 8']
    date_value = [0.9, 0.45, 0.80, 0.81, 0.7, 0.65, 0.2, 0.95, 0.85,]
    label = 'Коэффициент работы'
    type_chart = 'bar'
    indexAxis_value = 'x'
    title_value = 'Среднее значение коэф.  полезной работы'   
  } else if (block == 'profile_amount') {
    labels = ['Рабочий 1', 'Рабочий 2', 'Рабочий 3', 'Рабочий 4', 'Рабочий 5', 'Рабочий 6', 'Рабочий 7', 'Рабочий 8']
    date_value = [800, 450, 300, 1200, 120, 741, 550, 640, 970,]
    label = 'Изготовлено профиля'
    type_chart = 'bar'
    indexAxis_value = 'y'
    title_value = 'Изготовлено профиля, шт.'   
  } else if (block == 'effectiveness') {
    labels = ['Рабочий 1', 'Рабочий 2', 'Рабочий 3', 'Рабочий 4', 'Рабочий 5', 'Рабочий 6', 'Рабочий 7', 'Рабочий 8']
    date_value = [150, 100, 210, 160, 50, 200, 230, 190, 170]
    label = 'Эффективность'
    type_chart = 'bar'
    indexAxis_value = 'x'
    title_value = 'Эффективность, шт/час'  
  }

  data = {
    labels: labels,
    datasets: [{
      label: label,
      data: date_value,
      backgroundColor: [
        'rgba(255, 99, 132, 0.2)',
        'rgba(255, 159, 64, 0.2)',
        'rgba(255, 205, 86, 0.2)',
        'rgba(75, 192, 192, 0.2)',  
        'rgba(54, 162, 235, 0.2)',
        'rgba(153, 102, 255, 0.2)',
        'rgba(201, 203, 207, 0.2)'
      ],
      borderColor: [
        'rgb(255, 99, 132)',
        'rgb(255, 159, 64)',
        'rgb(255, 205, 86)',
        'rgb(75, 192, 192)',
        'rgb(54, 162, 235)',
        'rgb(153, 102, 255)',
        'rgb(201, 203, 207)'
      ],
      borderWidth: 1
    }]
  };  

  const config = {
    type: type_chart,
    data: data,
    options: {
      scales: {
        y: {
          beginAtZero: true
        }
      },
      indexAxis: indexAxis_value,
      plugins: {
            legend: {
                display: false,
                labels: {
                    color: 'rgb(255, 99, 132)'
                }
            },
            title: {
              display: true,
              text: title_value
            },
      },
      
    },
  }; 
  return config
}


//Функция отправки запросов серверу
async function ajax_request(url, type,  data) {    
  let data_value = await $.ajax({
  
    url: url,
    
    type: type,
    
    data: data,    

    headers: {
        "Accept": "network/json",
        "Content-Type": "network/json",        
    },
    
    success: function(answer){  
      return answer
           
    },
  
    error: function(){  
      alert('Error!');  
      }      
  });
  return data_value
}

// setInterval(() => {
//   context.drawImage(video, 0, 0, canvas.width, canvas.height);
//   const imageData = canvas.toDataURL('image/jpeg', 0.4); //0.4 - качество изображения, изменить при плохом обнаружении
//   socket.send(JSON.stringify({ image: imageData.split(',')[1], isFs: 0, chgVal: 0}));
// }, 250);

current_profile_update(change_current_work_element.value)
current_performance_update()
setup_speed(filter_date_element.value)

// new Chart(ctx_performance, update_chart('current_performance'));
new Chart(ctx_load, update_chart('current_load'));
// new Chart(ctx_setup_speed, update_chart('setup_speed'));
new Chart(ctx_hours_worked, update_chart('hours_worked'));
new Chart(ctx_profile_amount, update_chart('profile_amount'));
new Chart(ctx_effectiveness, update_chart('effectiveness'));
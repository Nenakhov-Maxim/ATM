// Количество изготовленного профиля
const ctx_current_profile = document.getElementById('chart-current-work__profile');
const ctx_performance = document.getElementById('chart-planned-work__performance');
const ctx_load = document.getElementById('chart-planned-work__load');
const ctx_setup_speed = document.getElementById('chart__setup-speed');
const ctx_hours_worked = document.getElementById('chart__hours-worked');
const ctx_profile_amount = document.getElementById('chart__profile-amount');
const ctx_effectiveness = document.getElementById('chart__effectiveness');

function update_chart(block, filter=undefined) {
  let data
  let labels
  let date_value
  let label
  let type_chart
  let indexAxis_value
  let title_value

  if (block == 'current_profile') {
    labels = ['Рабочий 1', 'Рабочий 2', 'Рабочий 3', 'Рабочий 4', 'Рабочий 5', 'Рабочий 6', 'Рабочий 7', 'Рабочий 8']
    date_value = [65, 59, 80, 81, 56, 55, 40, 59]
    label = 'Количество изготовленного профиля, шт.'
    type_chart = 'bar'
    indexAxis_value = 'y'
    title_value = 'Количество изготовленного профиля, шт.'
  } else if (block == 'current_performance') {
    labels = ['Линия 1', 'Линия 2', 'Линия 3', 'Линия 4', 'Линия 5']
    date_value = [65, 59, 80, 81, 56]
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
    labels = ['Рабочий 1', 'Рабочий 2', 'Рабочий 3', 'Рабочий 4', 'Рабочий 5', 'Рабочий 6', 'Рабочий 7', 'Рабочий 8']
    date_value = [1.15, 0.45, 0.80, 0.81, 0.7, 1.65, 1.2, 2.0, 0.85,]
    label = 'Среднее время переналадки/наладки'
    type_chart = 'bar'
    indexAxis_value = 'y'
    title_value = 'Среднее время переналадки/наладки, час.' 
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


new Chart(ctx_current_profile, update_chart('current_profile'));
new Chart(ctx_performance, update_chart('current_performance'));
new Chart(ctx_load, update_chart('current_load'));
new Chart(ctx_setup_speed, update_chart('setup_speed'));
new Chart(ctx_hours_worked, update_chart('hours_worked'));
new Chart(ctx_profile_amount, update_chart('profile_amount'));
new Chart(ctx_effectiveness, update_chart('effectiveness'));
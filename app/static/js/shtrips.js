// Списание штрипса
document.addEventListener('DOMContentLoaded', function() {
    const work_task = document.querySelector('div.task-card-item[data-category-id="3"]')
    let shtripsButton
    const stripsModal = document.getElementById('shtrips-modal');
    const stripsModalClose = document.querySelector('.shtrips-modal-close');
    const manualStripsInput = document.getElementById('manual-shtrips-input-value');
    const manualStripsSelect = document.getElementById('manual-shtrips-input-type');
    const manualShtripsSubmit = document.getElementById('manual-shtrips-submit');
    const errorInput = document.querySelector('.error_input');
    // console.log(work_task)
    if (work_task) {
        shtripsButton = work_task.querySelector('#shtrips-offs-btn');
        
        
        // document.addEventListener('DOMContentLoaded', function() {


        // Открытие модального окна
        shtripsButton.addEventListener('click', function(e) {
            console.log(e)
            e.preventDefault();
            console.log('click open modal btn')
            openShtripsModal();
        });

        // Закрытие модального окна
        stripsModalClose.addEventListener('click', function() {
            closeShtripsModal();
        });

        // Закрытие по клику вне модального окна
        stripsModal.addEventListener('click', function(e) {
            if (e.target === stripsModal) {
                closeShtripsModal();
            }
        });

        // Закрытие по ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && stripsModal.style.display !== 'none') {
                closeShtripsModal();
            }
        });

        // Обработка ввода
        manualShtripsSubmit.addEventListener('click', function() {
            const val = manualStripsInput.value.trim();
            const type = manualStripsSelect.value
            if (isNaN(Number(val)) || val == '') {
                errorInput.innerHTML = "Допускаются только числовые значения"
            } else {
                console.log(work_task)
                data = {val_num: Number(val), type: type, task_id: work_task.dataset.itemid}
                processOffShtrips(data)
            }
        });

        // Функция открытия модального окна
        function openShtripsModal() {
        console.log('open modal window')
        stripsModal.style.display = 'flex';
        manualStripsInput.value = '';
        errorInput.innerHTML = ""
        }

        // Функция закрытия модального окна
        function closeShtripsModal() {
            stripsModal.style.display = 'none';
            
        }

        // Обработка списания
        function processOffShtrips(data) {
            if (!data) {
                console.log(data)
                return;
            }

            
            // Отправка QR-кода на сервер
            fetch('shtrips-offs/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({data})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    errorInput.innerHTML = "Запись успешно добавлена"
                    setTimeout(() => {
                        // добавляем новое значение на страницу
                        new_div = document.createElement('div')
                        new_div.classList.add('history-shtrips-offs-item')
                        new_div.innerHTML = `
                            <span>${data.id}</span>
                            <span>${data.value}</span>
                            <span>${data.type_value}</span>
                            <span>${data.date_value}</span>
                        `
                        work_task.querySelector('.history-shtrips-offs-wrapper').after(new_div);
                        // закрываем модельное окно
                        closeShtripsModal();
                    }, 1000);
                } else {
                    errorInput.innerHTML = "Произошла ошибка в обработке данных"
                }
            })
            .catch(error => {
                console.log('Ошибка:', error);
            });
        }
    }
})
// QR-код сканирование и аутентификация
document.addEventListener('DOMContentLoaded', function() {
    const qrButton = document.querySelector('.button__qr-code');
    const qrModal = document.getElementById('qr-modal');
    const qrModalClose = document.querySelector('.qr-modal-close');
    const qrInput = document.getElementById('qr-input');
    const manualQrInput = document.getElementById('manual-qr-input');
    const manualQrSubmit = document.getElementById('manual-qr-submit');
    const scannerStatus = document.getElementById('scanner-status');

    let isScanning = false;
    let scanTimeout = null;

    // Карта соответствия русских символов английским (QWERTY раскладка)
    const ruToEnMap = {
        'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p',
        'х': '[', 'ъ': ']', 'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k',
        'д': 'l', 'ж': ';', 'э': "'", 'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm',
        'б': ',', 'ю': '.', '.': '/', 'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U',
        'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '{', 'Ъ': '}', 'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G',
        'Р': 'H', 'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ':', 'Э': '"', 'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V',
        'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': '<', 'Ю': '>', ',': '?'
    };

    // Функция конвертации русского текста в английский
    function convertRuToEn(text) {
        return text.split('').map(char => ruToEnMap[char] || char).join('');
    }

    // Функция определения, содержит ли текст русские символы
    function hasRussianChars(text) {
        return /[а-яё]/i.test(text);
    }

    // Открытие модального окна
    qrButton.addEventListener('click', function(e) {
        console.log('button__qr-code')
        e.preventDefault();
        openQrModal();
    });

    // Закрытие модального окна
    qrModalClose.addEventListener('click', function() {
        closeQrModal();
    });

    // Закрытие по клику вне модального окна
    qrModal.addEventListener('click', function(e) {
        if (e.target === qrModal) {
            closeQrModal();
        }
    });

    // Закрытие по ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && qrModal.style.display !== 'none') {
            closeQrModal();
        }
    });

    // Обработка ручного ввода QR-кода
    manualQrSubmit.addEventListener('click', function() {
        const qrCode = manualQrInput.value.trim();
        if (qrCode) {
            processQrCode(qrCode);
        } else {
            updateStatus('Введите QR-код', 'qr-error');
        }
    });

    // Обработка Enter в поле ручного ввода
    manualQrInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            manualQrSubmit.click();
        }
    });

    // Автоматическая конвертация в поле ручного ввода при вводе
    manualQrInput.addEventListener('input', function(e) {
        const value = e.target.value;
        if (hasRussianChars(value)) {
            const convertedValue = convertRuToEn(value);
            e.target.value = convertedValue;
            console.log('Ручной ввод конвертирован с русской раскладки:', value, '->', convertedValue);
        }
    });

    // Функция открытия модального окна
    function openQrModal() {
        qrModal.style.display = 'flex';
        manualQrInput.value = '';
        updateStatus('Ожидание сканирования...', '');
        startScanning();
        
        // Фокус на скрытое поле для получения данных от сканера
        setTimeout(() => {
            qrInput.focus();
        }, 100);
    }

    // Функция закрытия модального окна
    function closeQrModal() {
        qrModal.style.display = 'none';
        stopScanning();
    }

    // Начало сканирования
    function startScanning() {
        isScanning = true;
        qrInput.value = '';
        
        // Обработчик ввода от USB-сканера
        qrInput.addEventListener('input', handleScannerInput);
        qrInput.addEventListener('keypress', handleScannerKeypress);
        
        updateStatus('Готов к сканированию. Отсканируйте QR-код...', 'qr-loading');
    }

    // Остановка сканирования
    function stopScanning() {
        isScanning = false;
        qrInput.removeEventListener('input', handleScannerInput);
        qrInput.removeEventListener('keypress', handleScannerKeypress);
        
        if (scanTimeout) {
            clearTimeout(scanTimeout);
            scanTimeout = null;
        }
    }

    // Обработка ввода от сканера
    function handleScannerInput(e) {
        if (!isScanning) return;
        
        const value = e.target.value.trim();
        if (value.length > 0) {
            updateStatus('Получение данных...', 'qr-loading');
            
            // Очистка предыдущего таймаута
            if (scanTimeout) {
                clearTimeout(scanTimeout);
            }
            
            // Задержка для завершения ввода от сканера
            scanTimeout = setTimeout(() => {
                const finalValue = qrInput.value.trim();
                if (finalValue) {
                    processQrCode(finalValue);
                }
            }, 100);
        }
    }

    // Обработка нажатия клавиш от сканера
    function handleScannerKeypress(e) {
        if (!isScanning) return;
        
        // Enter обычно отправляется сканером в конце
        if (e.key === 'Enter') {
            e.preventDefault();
            const value = qrInput.value.trim();
            if (value) {
                if (scanTimeout) {
                    clearTimeout(scanTimeout);
                }
                processQrCode(value);
            }
        }
    }

    // Обработка QR-кода
    function processQrCode(qrCode) {
        if (!qrCode) {
            updateStatus('QR-код пуст', 'qr-error');
            return;
        }

        // Автоматическая конвертация русской раскладки в английскую
        let processedQrCode = qrCode;
        if (hasRussianChars(qrCode)) {
            processedQrCode = convertRuToEn(qrCode);
            updateStatus('Конвертация раскладки...', 'qr-loading');
            console.log('QR-код конвертирован с русской раскладки:', qrCode, '->', processedQrCode);
        }

        updateStatus('Проверка QR-кода...', 'qr-loading');
        
        // Отправка QR-кода на сервер
        fetch('/qr-login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                qr_code: processedQrCode
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStatus('Вход выполнен успешно!', 'qr-success');
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                updateStatus(data.error || 'Ошибка входа', 'qr-error');
                // Очистка полей после ошибки
                setTimeout(() => {
                    qrInput.value = '';
                    manualQrInput.value = '';
                    if (isScanning) {
                        updateStatus('Готов к сканированию. Отсканируйте QR-код...', 'qr-loading');
                        qrInput.focus();
                    }
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            updateStatus('Ошибка соединения с сервером', 'qr-error');
            setTimeout(() => {
                qrInput.value = '';
                manualQrInput.value = '';
                if (isScanning) {
                    updateStatus('Готов к сканированию. Отсканируйте QR-код...', 'qr-loading');
                    qrInput.focus();
                }
            }, 2000);
        });
    }

    // Обновление статуса
    function updateStatus(message, className) {
        scannerStatus.textContent = message;
        scannerStatus.className = className;
    }

    // Автофокус на скрытое поле при открытии модального окна
    qrModal.addEventListener('transitionend', function() {
        if (qrModal.style.display !== 'none' && isScanning) {
            qrInput.focus();
        }
    });
});

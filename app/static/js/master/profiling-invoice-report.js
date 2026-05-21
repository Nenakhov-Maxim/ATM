document.addEventListener('DOMContentLoaded', () => {
  const reportLink = document.querySelector('.profiling-invoice-report-link');
  const completedWorkReportLink = document.querySelector('.completed-work-report-link');
  const reportPopup = document.querySelector('.new_report_popup');
  const reportForm = document.querySelector('.new_report_form');
  const reportTitle = document.querySelector('.new_report_form__title');
  const cancelButton = document.querySelector('.new_report_cansel-button');
  const acceptButton = document.querySelector('.new_report_accept-button');

  if (!reportLink || !reportPopup || !reportForm) {
    return;
  }

  reportLink.addEventListener('click', (event) => {
    event.preventDefault();
    reportForm.action = '/master/profiling-invoice-report/';
    if (reportTitle) {
      reportTitle.innerText = 'Накладная на линию профилирования';
    }
    reportPopup.classList.remove('disable');
  });

  if (completedWorkReportLink) {
    completedWorkReportLink.addEventListener('click', () => {
      reportForm.action = '/master/new_report/';
      if (reportTitle) {
        reportTitle.innerText = 'AT-Manager';
      }
    });
  }

  if (cancelButton) {
    cancelButton.addEventListener('click', () => {
      reportPopup.classList.add('disable');
      reportForm.action = '/master/new_report/';
      if (reportTitle) {
        reportTitle.innerText = 'AT-Manager';
      }
    });
  }

  if (acceptButton) {
    acceptButton.addEventListener('click', () => {
      reportPopup.classList.add('disable');
    });
  }
});

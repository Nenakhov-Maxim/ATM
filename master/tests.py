from datetime import datetime, timedelta, timezone as datetime_timezone
from types import SimpleNamespace

from django.test import SimpleTestCase

from .forms import ReportForm
from .profiling_invoice_report import SHIFT_1, SHIFT_2, SHIFT_3, _build_report_rows, _shift_key


class ReportPeriodTests(SimpleTestCase):
    def test_report_form_interprets_entered_dates_as_yekaterinburg_time(self):
        form = ReportForm({
            'date_start': '2026-08-31T08:00',
            'date_end': '2026-09-01T08:00',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data['date_start'].astimezone(datetime_timezone.utc),
            datetime(2026, 8, 31, 3, 0, tzinfo=datetime_timezone.utc),
        )
        self.assertEqual(
            form.cleaned_data['date_end'].astimezone(datetime_timezone.utc),
            datetime(2026, 9, 1, 3, 0, tzinfo=datetime_timezone.utc),
        )

    def test_report_form_rejects_reversed_period(self):
        form = ReportForm({
            'date_start': '2026-09-01T08:00',
            'date_end': '2026-08-31T08:00',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('date_end', form.errors)

    def test_shift_boundaries_use_yekaterinburg_time(self):
        local_offset = timedelta(hours=5)

        self.assertEqual(
            _shift_key(datetime(2026, 8, 31, 8, 0, tzinfo=datetime_timezone(local_offset))),
            SHIFT_1,
        )
        self.assertEqual(
            _shift_key(datetime(2026, 8, 31, 17, 0, tzinfo=datetime_timezone(local_offset))),
            SHIFT_2,
        )
        self.assertEqual(
            _shift_key(datetime(2026, 9, 1, 1, 0, tzinfo=datetime_timezone(local_offset))),
            SHIFT_3,
        )

    def test_task_without_profile_records_in_period_is_not_reported(self):
        task = SimpleNamespace(invoice_profile_records=[])

        self.assertEqual(_build_report_rows([task]), [])

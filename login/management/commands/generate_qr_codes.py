import uuid
from django.core.management.base import BaseCommand
from login.models import User


class Command(BaseCommand):
    help = 'Генерирует уникальные QR-коды для пользователей, у которых их нет'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Перегенерировать QR-коды для всех пользователей',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Генерировать QR-код для конкретного пользователя',
        )

    def handle(self, *args, **options):
        if options['username']:
            # Генерация для конкретного пользователя
            try:
                user = User.objects.get(username=options['username'])
                old_qr = user.qr_code
                user.qr_code = self.generate_unique_qr_code()
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'QR-код для пользователя {user.username} обновлен: {old_qr} -> {user.qr_code}'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Пользователь {options["username"]} не найден')
                )
                return

        elif options['all']:
            # Перегенерация для всех пользователей
            users = User.objects.all()
            updated_count = 0
            for user in users:
                old_qr = user.qr_code
                user.qr_code = self.generate_unique_qr_code()
                user.save()
                updated_count += 1
                self.stdout.write(f'Пользователь {user.username}: {old_qr} -> {user.qr_code}')
            
            self.stdout.write(
                self.style.SUCCESS(f'QR-коды обновлены для {updated_count} пользователей')
            )

        else:
            # Генерация только для пользователей без QR-кодов
            users_without_qr = User.objects.filter(qr_code__isnull=True) | User.objects.filter(qr_code='')
            generated_count = 0
            
            for user in users_without_qr:
                user.qr_code = self.generate_unique_qr_code()
                user.save()
                generated_count += 1
                self.stdout.write(f'Пользователь {user.username}: новый QR-код {user.qr_code}')
            
            if generated_count == 0:
                self.stdout.write(
                    self.style.WARNING('Все пользователи уже имеют QR-коды')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'QR-коды созданы для {generated_count} пользователей')
                )

    def generate_unique_qr_code(self):
        """Генерирует уникальный QR-код"""
        while True:
            # Генерируем короткий уникальный код
            qr_code = str(uuid.uuid4()).replace('-', '')[:12].upper()
            
            # Проверяем уникальность
            if not User.objects.filter(qr_code=qr_code).exists():
                return qr_code

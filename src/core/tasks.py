from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import MailingTemplate


@shared_task
def send_mailing_task(template_ids, user_emails):
    """
    Задача Celery для массовой отправки email.
    """
    try:
        templates = MailingTemplate.objects.filter(id__in=template_ids)
        if not templates:
            return "Ошибка: Шаблоны не найдены."

        # Читаем содержимое всех шаблонов один раз, чтобы не делать это в цикле
        html_contents = []
        for template in templates:
            with template.file.open('r') as f:
                html_contents.append(f.read())

        # Объединяем все шаблоны в одно письмо
        combined_html = "<br><hr><br>".join(html_contents)

        sent_count = 0
        for email in user_emails:
            try:
                send_mail(
                    subject="Новости нашего кинотеатра",  # Тему можно сделать динамической
                    message="",  # Текстовая версия не нужна, так как мы шлем HTML
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=combined_html,  # Отправляем HTML
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                # Логируем ошибку отправки конкретному пользователю, но не останавливаем всю рассылку
                print(f"Не удалось отправить письмо на {email}: {e}")

        return f"Рассылка завершена. Отправлено {sent_count} из {len(user_emails)} писем."

    except Exception as e:
        print(f"Критическая ошибка в задаче рассылки: {e}")
        return "Рассылка провалена из-за критической ошибки."
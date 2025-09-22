# src/core/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from src.users.models import CustomUser
from .models import MailingCampaign

@shared_task(bind=True)
def send_mailing_task(self, campaign_id):
    """
    Задача Celery, которая получает ID кампании и выполняет рассылку,
    обновляя ее статус в базе данных.
    """

    # !!! ШАГ ДЛЯ ДИАГНОСТИКИ !!!
    print("\n--- DEBUG: ЗАДАЧА send_mailing_task ПОЛУЧЕНА ---")

    # Импортируем модели здесь, чтобы избежать циклических зависимостей при запуске
    try:
        campaign = MailingCampaign.objects.get(id=campaign_id)
        campaign.status = MailingCampaign.Status.IN_PROGRESS
        campaign.save(update_fields=['status'])

        # --- ИСПРАВЛЕНА ЛОГИКА ВЫБОРА ПОЛУЧАТЕЛЕЙ ---
        if campaign.send_to_all:
            print("--- DEBUG: Выбран режим 'Отправить всем' ---")
            # Если отправляем всем
            user_emails_qs = CustomUser.objects.exclude(email__exact='').values_list('email', flat=True)
        else:
            print("--- DEBUG: Выбран режим 'Выборочно' ---")
            # Если отправляем выборочно
            recipient_ids = campaign.recipients
            if not recipient_ids:
                campaign.status = MailingCampaign.Status.FAILED
                campaign.save()
                return "Ошибка: Выборочная рассылка запущена, но список получателей пуст."

            user_emails_qs = CustomUser.objects.filter(id__in=recipient_ids).exclude(email__exact='').values_list(
                'email', flat=True)

        user_emails = list(user_emails_qs)
        total_emails = len(user_emails)

        # Обновляем общее количество получателей, если оно отличается
        if campaign.total_recipients != total_emails:
            campaign.total_recipients = total_emails
            campaign.save(update_fields=['total_recipients'])

        # Читаем и объединяем HTML-шаблоны
        html_contents = [tpl.file.read().decode('utf-8') for tpl in campaign.templates.all()]
        combined_html = "<br><hr><br>".join(html_contents)

        sent_count = 0
        for email in user_emails:
            try:
                send_mail(
                    subject="Новости нашего кинотеатра",
                    message="",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=combined_html,
                    fail_silently=False,
                )
                sent_count += 1
                if sent_count % 5 == 0 or sent_count == total_emails:
                    campaign.sent_count = sent_count
                    campaign.save(update_fields=['sent_count'])
            except Exception as e:
                print(f"Не удалось отправить письмо на {email}: {e}")

        # Помечаем кампанию как "завершенную"
        campaign.status = MailingCampaign.Status.COMPLETED
        campaign.completed_at = timezone.now()
        campaign.sent_count = sent_count
        campaign.save()

        return f"Рассылка завершена. Отправлено {sent_count} из {total_emails} писем."

    except MailingCampaign.DoesNotExist:
        return f"Ошибка: Кампания с ID {campaign_id} не найдена."
    except Exception as e:
        if 'campaign' in locals():
            campaign.status = MailingCampaign.Status.FAILED
            campaign.save()
        print(f"Критическая ошибка в задаче рассылки: {e}")
        raise e
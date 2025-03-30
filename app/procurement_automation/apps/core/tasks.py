from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def send_email_task(subject, template_name, context, recipient_list):
    html_message = render_to_string(template_name, context)
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message
    )

@shared_task
def import_products_task(file_path, supplier_id):
    from apps.products.management.commands.import_products import Command
    Command().handle(file_path=file_path, supplier_id=supplier_id)
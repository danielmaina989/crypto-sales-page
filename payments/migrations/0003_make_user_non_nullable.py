from django.db import migrations, models
from django.conf import settings


def set_default_user(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    # Resolve AUTH_USER_MODEL (e.g. 'auth.User')
    auth_app_label, auth_model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(auth_app_label, auth_model_name)

    # Prefer an existing superuser, then any user, otherwise create a system user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter().first()
    created_dummy = False
    if not user:
        # Create a minimal user; use raw SQL to avoid importing managers in migrations
        user = User.objects.create(username='payments_system')
        try:
            user.set_unusable_password()
            user.save()
        except Exception:
            pass
        created_dummy = True

    # Update payments that have no user
    Payment.objects.filter(user__isnull=True).update(user=user)

    # Attach attribute to the migration app registry so reverse knows if we created the user
    migrations._payments_created_dummy_user = (created_dummy, user.pk if user else None)


def unset_default_user(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    auth_app_label, auth_model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(auth_app_label, auth_model_name)

    # Set user back to null for payments that reference the migration-created user
    created_info = getattr(migrations, '_payments_created_dummy_user', None)
    if created_info:
        created_dummy, user_pk = created_info
    else:
        created_dummy = False
        user_pk = None

    if user_pk is not None:
        Payment.objects.filter(user__pk=user_pk).update(user=None)
        if created_dummy:
            try:
                User.objects.filter(pk=user_pk).delete()
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_rename_payments_checkout_request_id_idx_payments_pa_checkou_e4cf10_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(set_default_user, unset_default_user),
        migrations.AlterField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]


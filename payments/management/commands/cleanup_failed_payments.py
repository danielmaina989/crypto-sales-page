from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from payments.models import Payment


class Command(BaseCommand):
    help = 'Cleans up failed payments in testing/development environments.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', dest='dry_run', default=True,
                            help='Show what would be changed/deleted without persisting changes (default).')
        parser.add_argument('--apply', action='store_true', dest='apply', default=False,
                            help='Actually apply changes (non-dry-run).')
        parser.add_argument('--delete-tests', action='store_true', dest='delete_tests', default=False,
                            help='Delete failed payments that look like test data (no receipt).')
        parser.add_argument('--age-days', type=int, dest='age_days', default=0,
                            help='Only operate on payments older than this many days (default: 0, no age filter).')
        parser.add_argument('--mark-success', action='store_true', dest='mark_success', default=True,
                            help='Mark failed payments that have a mpesa_receipt_number as success (default behavior).')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run') and not options.get('apply')
        apply_changes = options.get('apply')
        delete_tests = options.get('delete_tests')
        age_days = options.get('age_days') or 0
        mark_success = options.get('mark_success')

        cutoff = None
        if age_days > 0:
            cutoff = timezone.now() - timedelta(days=age_days)

        qs = Payment.objects.filter(status='failed')
        if cutoff is not None:
            qs = qs.filter(created_at__lt=cutoff)

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f'Found {total} failed payments (age_days={age_days})'))

        if total == 0:
            return

        summary = {
            'to_mark_success': 0,
            'to_delete': 0,
            'skipped': 0,
        }

        for p in qs.order_by('created_at'):
            has_receipt = bool(p.mpesa_receipt_number)
            # Heuristic: test payments probably have small amounts and no receipt
            if has_receipt and mark_success:
                summary['to_mark_success'] += 1
                self.stdout.write(f'[MARK] Payment id={p.id} checkout={p.checkout_request_id} receipt={p.mpesa_receipt_number} amount={p.amount}')
                if apply_changes:
                    try:
                        with transaction.atomic():
                            p.status = 'success'
                            p.error_code = None
                            p.error_message = None
                            p.updated_at = timezone.now()
                            p.save()
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f'Failed to mark payment {p.id}: {e}'))
            else:
                # No receipt -> candidate for deletion if --delete-tests used
                if delete_tests:
                    summary['to_delete'] += 1
                    self.stdout.write(f'[DELETE] Payment id={p.id} checkout={p.checkout_request_id} amount={p.amount}')
                    if apply_changes:
                        try:
                            with transaction.atomic():
                                p.delete()
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f'Failed to delete payment {p.id}: {e}'))
                else:
                    summary['skipped'] += 1
                    self.stdout.write(f'[SKIP] Payment id={p.id} (no receipt)')

        # Summary
        self.stdout.write('\nSummary:')
        self.stdout.write(f"  Would mark as success: {summary['to_mark_success']}")
        self.stdout.write(f"  Would delete (if --delete-tests): {summary['to_delete']}")
        self.stdout.write(f"  Skipped: {summary['skipped']}")

        if dry_run and not apply_changes:
            self.stdout.write(self.style.WARNING('\nDry-run mode active. To apply changes run with --apply.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nCleanup complete.'))


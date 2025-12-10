from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from payments.models import Payment, PaymentAccessLog
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
import csv
from datetime import datetime
from django.utils.timezone import make_aware
from decimal import Decimal, InvalidOperation

# Try to import reportlab for PDF export; if unavailable we'll fallback to CSV
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    _HAS_REPORTLAB = True
except Exception:
    _HAS_REPORTLAB = False


@login_required
def payment_history(request):
    """Payment history with search, filters, sorting, pagination and CSV/PDF export."""
    payments = Payment.objects.filter(user=request.user).order_by("-created_at")

    # SEARCH
    q = (request.GET.get("q") or '').strip()
    if q:
        # Text fields to search (icontains)
        text_filters = (
            Q(phone_number__icontains=q)
            | Q(mpesa_receipt_number__icontains=q)
            | Q(account_ref__icontains=q)
            | Q(description__icontains=q)
            | Q(merchant_request_id__icontains=q)
            | Q(checkout_request_id__icontains=q)
        )
        qs_filters = text_filters
        # If q is an integer id
        if q.isdigit():
            try:
                qs_filters |= Q(id=int(q))
            except Exception:
                pass
        # If q can be parsed as decimal, search by amount equality
        try:
            dec = Decimal(q)
            qs_filters |= Q(amount=dec)
        except (InvalidOperation, ValueError):
            # not a decimal, ignore
            pass

        payments = payments.filter(qs_filters)

        # Fallback: if no results and q contains digits (phone-like), try digits-only match
        if payments.count() == 0:
            q_digits = ''.join(ch for ch in q if ch.isdigit())
            if q_digits:
                # generate candidate phone variants to match stored MSISDN formats
                candidates = set()
                candidates.add(q_digits)
                candidates.add(q_digits.lstrip('+'))
                candidates.add(q_digits.lstrip('0'))
                # if user typed leading 0 (07...), add 2547... form
                if q_digits.startswith('0'):
                    candidates.add('254' + q_digits.lstrip('0'))
                # if user typed 7XXXXXXXX add 254 prefix
                if q_digits.startswith('7'):
                    candidates.add('254' + q_digits)
                # if user typed +2547..., add without +
                if q_digits.startswith('254'):
                    candidates.add(q_digits)

                phone_q = Q()
                for c in candidates:
                    if c:
                        phone_q |= Q(phone_number__icontains=c)

                loose_filters = (
                    phone_q
                    | Q(mpesa_receipt_number__icontains=q_digits)
                    | Q(account_ref__icontains=q)
                )
                # Use base queryset for loose search to keep behavior predictable
                base_qs = Payment.objects.filter(user=request.user)
                payments = base_qs.filter(loose_filters).order_by('-created_at')

    # STATUS FILTER
    status = request.GET.get("status")
    if status in ("success", "pending", "failed"):
        payments = payments.filter(status=status)

    # DATE RANGE
    date_from = request.GET.get("from")
    date_to = request.GET.get("to")
    if date_from:
        try:
            dt = datetime.strptime(date_from, "%Y-%m-%d")
            payments = payments.filter(created_at__gte=make_aware(dt))
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            # include the whole day for 'to'
            payments = payments.filter(created_at__lte=make_aware(dt.replace(hour=23, minute=59, second=59)))
        except Exception:
            pass

    # SORTING
    sort = request.GET.get("sort")
    if sort == "amount":
        payments = payments.order_by("amount")
    elif sort == "-amount":
        payments = payments.order_by("-amount")
    elif sort == "date":
        payments = payments.order_by("created_at")
    elif sort == "-date":
        payments = payments.order_by("-created_at")

    # EXPORT CSV
    if request.GET.get("export") == "csv":
        return export_payments_csv(payments)

    # EXPORT PDF (fallback to CSV if reportlab not installed)
    if request.GET.get("export") == "pdf":
        if _HAS_REPORTLAB:
            return export_payments_pdf(payments)
        else:
            # fallback: return CSV with a message header
            resp = export_payments_csv(payments)
            resp["X-Export-Fallback"] = "reportlab-missing"
            return resp

    # PAGINATION
    paginator = Paginator(payments, 12)
    page = request.GET.get("page")
    payments_page = paginator.get_page(page)

    ctx = {
        "payments": payments_page,
        "request": request,
    }
    return render(request, "frontend/payments_history.html", ctx)


def export_payments_csv(queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=payment_history.csv"

    writer = csv.writer(response)
    writer.writerow(["ID", "Phone", "Amount", "Status", "Receipt", "Date"])

    for p in queryset:
        writer.writerow([
            p.id,
            p.phone_number,
            p.amount,
            p.status,
            p.mpesa_receipt_number or "-",
            p.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


def export_payments_pdf(queryset):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=payment_history.pdf"

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    y = height - 20 * mm
    p.setFont("Helvetica-Bold", 14)
    p.drawString(20 * mm, y, "Payment History")
    y -= 10 * mm

    p.setFont("Helvetica", 10)

    for item in queryset:
        if y < 20 * mm:
            p.showPage()
            y = height - 20 * mm
            p.setFont("Helvetica", 10)

        text = (
            f"ID: {item.id} | Phone: {item.phone_number} | "
            f"Amount: KES {item.amount} | Status: {item.status} | "
            f"Receipt: {item.mpesa_receipt_number or '-'} | "
            f"Date: {item.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        p.drawString(20 * mm, y, text)
        y -= 7 * mm

    p.showPage()
    p.save()
    return response


@login_required
def payment_detail(request, pk: int):
    payment = get_object_or_404(Payment, pk=pk)

    # Authorization: owners can view their own payments; others require staff/superuser or permission
    is_owner = (payment.user_id == request.user.id)
    is_staff = getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
    has_perm = request.user.has_perm('payments.view_sensitive_payment') if request.user.is_authenticated else False

    if not (is_owner or is_staff or has_perm):
        # Log the denied access attempt for audit
        try:
            PaymentAccessLog.objects.create(
                payment=payment,
                user=request.user if request.user.is_authenticated else None,
                username=request.user.get_username() if request.user.is_authenticated else None,
                action='view',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                note='unauthorized_view_attempt',
            )
        except Exception:
            # never raise on logging
            pass
        return HttpResponse(status=403)

    # Log the access
    try:
        PaymentAccessLog.objects.create(
            payment=payment,
            user=request.user if request.user.is_authenticated else None,
            username=request.user.get_username() if request.user.is_authenticated else None,
            action='view',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
        )
    except Exception:
        # ensure logging failures don't block the response
        pass

    return render(request, 'frontend/payment_detail.html', {'payment': payment})

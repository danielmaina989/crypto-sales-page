from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from payments.models import Payment, PaymentAccessLog
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, FileResponse
from django.conf import settings
import csv
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, now
from decimal import Decimal, InvalidOperation
from payments.decorators import audit_and_require_payment_view
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncDate
from django.db.models import Sum, Count
import os

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
@audit_and_require_payment_view('pk')
def payment_detail(request, pk: int):
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'frontend/payment_detail.html', {'payment': payment})


@staff_member_required
def access_logs_api(request):
    # Staff-only JSON endpoint with filtering and pagination for access logs
    qs = PaymentAccessLog.objects.select_related('user', 'payment').all().order_by('-created_at')

    # Filters
    user_q = request.GET.get('user')
    action_q = request.GET.get('action')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    if user_q:
        qs = qs.filter(username__icontains=user_q) | qs.filter(user__username__icontains=user_q)
    if action_q:
        qs = qs.filter(action__iexact=action_q)

    from datetime import datetime
    from django.utils.timezone import make_aware
    if date_from:
        try:
            dt = datetime.strptime(date_from, '%Y-%m-%d')
            qs = qs.filter(created_at__gte=make_aware(dt))
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d')
            qs = qs.filter(created_at__lte=make_aware(dt.replace(hour=23, minute=59, second=59)))
        except Exception:
            pass

    # Pagination
    try:
        page = int(request.GET.get('page', '1'))
        page_size = int(request.GET.get('page_size', '50'))
        if page_size > 200:
            page_size = 200
    except Exception:
        page = 1
        page_size = 50

    from django.core.paginator import Paginator, EmptyPage
    paginator = Paginator(qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    data = []
    for l in page_obj.object_list:
        data.append({
            'id': l.id,
            'payment_id': l.payment_id,
            'user': l.user.get_username() if l.user else l.username,
            'action': l.action,
            'ip_address': l.ip_address,
            'user_agent': (l.user_agent or '')[:200],
            'note': l.note,
            'created_at': l.created_at.isoformat(),
        })

    return JsonResponse({
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page,
        'page_size': page_size,
        'logs': data,
    })


@login_required
def history_timeseries(request):
    """Return last 30 days of payment totals for the logged-in user.

    Response format:
    { labels: ['2025-11-16', ...], totals: [123.45, ...], counts: [1, ...] }
    """
    end = now().date()
    start = end - timedelta(days=29)  # inclusive 30 days

    qs = Payment.objects.filter(user=request.user, created_at__date__gte=start, created_at__date__lte=end)
    qs = qs.annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum('amount'), count=Count('id')).order_by('day')

    # build map day -> totals
    data_map = {entry['day'].isoformat(): {'total': float(entry['total'] or 0), 'count': entry['count']} for entry in qs}

    labels = []
    totals = []
    counts = []
    for i in range(0, 30):
        d = start + timedelta(days=i)
        key = d.isoformat()
        labels.append(key)
        if key in data_map:
            totals.append(data_map[key]['total'])
            counts.append(data_map[key]['count'])
        else:
            totals.append(0)
            counts.append(0)

    return JsonResponse({'labels': labels, 'totals': totals, 'counts': counts})


@login_required
@audit_and_require_payment_view('pk')
def download_receipt(request, pk: int):
    """Development: serve a sample PDF receipt for the payment.

    In production, replace with real receipt generation (WeasyPrint/reportlab).
    """
    # For safety, only allow owner or staff (decorator enforces this)
    sample_path = os.path.join(settings.BASE_DIR, 'frontend', 'templates', 'frontend', 'receipts', 'sample_receipt.pdf')
    if not os.path.exists(sample_path):
        return HttpResponse('Receipt not available', status=404)
    return FileResponse(open(sample_path, 'rb'), as_attachment=True, filename=f'receipt_{pk}.pdf')


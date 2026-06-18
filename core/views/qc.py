from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator

# === IMPORT MODEL KAMU ===
# Ganti 'nama_aplikasi_kamu' sesuai dengan nama folder aplikasi Django-mu
from core.models import Quality, HasilProduksi, QualityControl

def dashboard_qc(request):
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)

    # Total QC
    total_qc = QualityControl.objects.count()
    
    # QC Valid in last 6 months
    valid_qc_6_bulan = QualityControl.objects.filter(
        tanggal_validasi__gte=six_months_ago
    ).count()

    # QC pending (Hasil produksi without QC)
    pending_qc = HasilProduksi.objects.filter(qc__isnull=True).count()

    # Terbaru
    terbaru = QualityControl.objects.select_related(
        'hasil_produksi', 'quality'
    ).order_by('-id')[:5]

    # Grafik Hasil Grading (Distribusi 7 hari terakhir)
    grading_180_hari = QualityControl.objects.filter(
        tanggal_validasi__gte=six_months_ago
    ).values('quality__quality').annotate(
        total=Count('id')
    ).order_by('-total')

    context = {
        'total_qc': total_qc,
        'valid_qc_6_bulan': valid_qc_6_bulan,
        'pending_qc': pending_qc,
        'terbaru': terbaru,
        'grading_180_hari': grading_180_hari, 
    }

    return render(request, 'qc/dashboard.html', context)

def quality_list(request):
    data = Quality.objects.all()
    return render(request, 'qc/list_quality.html', {'data': data})

def quality_create(request):
    if request.method == 'POST':
        Quality.objects.create(
            quality=request.POST['quality']
        )
        return redirect('quality_list')
    return render(request, 'quality/form.html')

def quality_edit(request, id):
    obj = get_object_or_404(Quality, id=id)
    if request.method == 'POST':
        obj.quality = request.POST['quality']
        obj.save()
        return redirect('quality_list')
    return render(request, 'quality/form.html', {'obj': obj})

def quality_delete(request, id):
    obj = get_object_or_404(Quality, id=id)
    obj.delete()
    return redirect('quality_list')


def qc_list(request):
    data = HasilProduksi.objects.select_related(
        'proses_produksi',
        'nama_hasil_produksi'
    ).order_by('-proses_produksi__tanggal_produksi','-id')

    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    data = paginator.get_page(page_number)

    quality_list = Quality.objects.all()

    context = {
        'data': data,
        'quality_list': quality_list
    }

    return render(request, 'qc/list_qc.html', context)

def qc_validasi(request, id):

    hasil = get_object_or_404(HasilProduksi, id=id)

    if request.method == 'POST':

        qc, created = QualityControl.objects.get_or_create(
            hasil_produksi=hasil
        )

        qc.quality_id = request.POST['quality']
        qc.catatan = request.POST['catatan']
        qc.tanggal_validasi = timezone.now()

        qc.save()

    return redirect('qc_list')

def qc_edit_validasi(request, id):

    qc = get_object_or_404(QualityControl, id=id)

    if request.method == 'POST':

        qc.quality_id = request.POST['quality']
        qc.catatan = request.POST['catatan']
        qc.save()

    return redirect('qc_list')


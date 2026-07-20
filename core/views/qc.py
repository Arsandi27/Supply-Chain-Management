from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from core.decorators import role_required

# === IMPORT MODEL KAMU ===
# Ganti 'nama_aplikasi_kamu' sesuai dengan nama folder aplikasi Django-mu
from core.models import Quality, HasilProduksi, QualityControl


@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
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

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def quality_list(request):
    data = Quality.objects.all()
    return render(request, 'qc/list_quality.html', {'data': data})

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def quality_create(request):
    if request.method == 'POST':
        Quality.objects.create(
            quality=request.POST['quality']
        )
        messages.success(request, "Data Quality / Grade berhasil ditambahkan!", extra_tags='quality')
        return redirect('quality_list')
    return render(request, 'quality/form.html')

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def quality_edit(request, id):
    obj = get_object_or_404(Quality, id=id)
    if request.method == 'POST':
        obj.quality = request.POST['quality']
        obj.save()
        messages.success(request, "Data Quality / Grade berhasil diperbarui!", extra_tags='quality')
        return redirect('quality_list')
    return render(request, 'quality/form.html', {'obj': obj})

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def quality_delete(request, id):
    obj = get_object_or_404(Quality, id=id)
    obj.delete()
    messages.success(request, "Data Quality / Grade berhasil dihapus!", extra_tags='quality')
    return redirect('quality_list')

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
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

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def qc_validasi(request, id):

    hasil = get_object_or_404(HasilProduksi, id=id)

    if request.method == 'POST':

        quality = request.POST.get('quality')
        catatan = request.POST.get('catatan', '').strip()

        if not catatan:
            messages.error(request, 'Keterangan wajib diisi.')
            return redirect('qc_list')

        qc, created = QualityControl.objects.get_or_create(
            hasil_produksi=hasil
        )

        qc.quality_id = quality
        qc.catatan = catatan
        qc.tanggal_validasi = timezone.now()

        qc.save()

        messages.success(
            request,
            "Klasifikasi berhasil dicatat!",
            extra_tags='qc_validasi'
        )

    return redirect('qc_list')

from django.contrib import messages

@login_required(login_url='login')
@role_required('qualitycontrol')
@never_cache
def qc_edit_validasi(request, id):

    qc = get_object_or_404(QualityControl, id=id)

    if request.method == 'POST':
        quality = request.POST.get('quality')
        catatan = request.POST.get('catatan', '').strip()

        if not catatan:
            messages.error(request, 'Keterangan wajib diisi.')
            return redirect('qc_list')

        qc.quality_id = quality
        qc.catatan = catatan
        qc.save()

        messages.success(request, "Klasifikasi berhasil diperbarui!", extra_tags='qc_validasi')

    return redirect('qc_list')
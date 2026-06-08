from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q

# === IMPORT MODEL KAMU ===
# Sesuaikan 'nama_aplikasi_kamu' dengan folder utama aplikasi tempat models.py berada
from core.models import Supplier, BahanBaku, BahanBakuMasuk


@login_required(login_url='login')
@never_cache
def dashboard_purchasing(request):
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)
    
    # Mengambil tanggal 1 di bulan yang berjalan saat ini
    first_day_of_month = today.replace(day=1)

    grafik_data = (
        BahanBakuMasuk.objects
        .filter(tanggal_masuk__gte=six_months_ago)
        .values('bahan_baku__nama_bahan')
        .annotate(total_stok=Sum('jumlah_pcs')) 
        .order_by('-total_stok')[:6] 
    )

    THRESHOLD_PCS = 50
    stok_menipis = BahanBaku.objects.annotate(
        total_sisa_pcs=Sum('bahanbakumasuk__sisa_pcs')
    ).filter(
        total_sisa_pcs__lte=THRESHOLD_PCS
    ).order_by('total_sisa_pcs')

    total_bahan_baku = BahanBakuMasuk.objects.aggregate(total=Sum('sisa_pcs'))['total'] or 0
    pemasok_aktif = Supplier.objects.count() 
    
        
    pembelian_bulan_ini = BahanBakuMasuk.objects.filter(
        tanggal_masuk__gte=first_day_of_month
    ).aggregate(
        total_nilai=Sum('harga_satuan')
    )
    nilai_pembelian = pembelian_bulan_ini['total_nilai'] or 0

    pemasok_terbaru = Supplier.objects.order_by('-id')[:4] 

    terbaru = BahanBakuMasuk.objects.select_related(
        'bahan_baku', 'supplier'
    ).order_by('-tanggal_masuk')[:5]

    context = {
        'grafik_data': grafik_data,
        'stok_menipis': stok_menipis,
        'threshold': THRESHOLD_PCS,  
        'total_bahan_baku': total_bahan_baku,
        'pemasok_aktif': pemasok_aktif,
        'nilai_pembelian': nilai_pembelian,
        'pemasok_terbaru': pemasok_terbaru,
        'terbaru': terbaru,
    }
    
    return render(request, 'purchasing/dashboard.html', context)



def supplier_list(request):
    data = Supplier.objects.all()
    return render(request, 'purchasing/list_supplier.html', {'data': data})

def supplier_create(request):
    if request.method == 'POST':
        Supplier.objects.create(
            nama_supplier=request.POST['nama_supplier'],
            alamat=request.POST['alamat'],
            kontak=request.POST['kontak']
        )
        messages.success(request, "Nama Supplier berhasil ditambahkan!",extra_tags='supplier')
        return redirect('supplier_list')
    return render(request, 'purchasing/form.html')

def supplier_edit(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.nama_supplier = request.POST['nama_supplier']
        supplier.alamat = request.POST['alamat']
        supplier.kontak = request.POST['kontak']
        supplier.save()
        messages.success(request, "Nama Supplier berhasil diedit!",extra_tags='supplier')
        return redirect('supplier_list')
    return render(request, 'purchasing/form.html', {'supplier': supplier})

def supplier_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    messages.success(request, "Nama Supplier berhasil dihapus!",extra_tags='supplier')
    return redirect('supplier_list')



def bahanbaku_list(request):
    data = BahanBaku.objects.all()
    return render(request, 'purchasing/list_bahanbaku.html', {'data': data})

def bahanbaku_create(request):
    if request.method == 'POST':
        BahanBaku.objects.create(
            nama_bahan=request.POST['nama_bahan']
        )
        messages.success(request, "Nama Bahan Baku berhasil ditambahkan!",extra_tags='bahan_baku')
        return redirect('bahanbaku_list')
    return render(request, 'bahanbaku/form.html')

def bahanbaku_edit(request, id):
    obj = get_object_or_404(BahanBaku, id=id)
    if request.method == 'POST':
        obj.nama_bahan = request.POST['nama_bahan']
        obj.save()
        messages.success(request, "Nama Bahan Baku berhasil diedit!",extra_tags='bahan_baku')
        return redirect('bahanbaku_list')
    return render(request, 'bahanbaku/form.html', {'obj': obj})

def bahanbaku_delete(request, id):
    obj = get_object_or_404(BahanBaku, id=id)
    obj.delete()
    messages.success(request, "Nama Bahan Baku berhasil dihapus!",extra_tags='bahan_baku')
    return redirect('bahanbaku_list')


#purchasing views for Bahan Baku Masuk

from django.db.models import Q
from decimal import Decimal

def clean_m3(value):
    if not value:
        return Decimal("0")
    return Decimal(value.strip().replace(",", "."))


def clean_rupiah(value):
    if not value:
        return Decimal("0")

    value = value.strip()
    value = value.replace("Rp", "")
    value = value.replace(" ", "")
    value = value.replace(".", "")
    value = value.replace(",", ".")

    return Decimal(value)

def bahan_baku_masuk_list(request):
    data = BahanBakuMasuk.objects.select_related('bahan_baku', 'supplier')

    # ambil parameter dari GET
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # SEARCH nama bahan baku
    if search:
        data = data.filter(
            Q(bahan_baku__nama_bahan__icontains=search) |
            Q(supplier__nama_supplier__icontains=search)
        )

    # FILTER tanggal
    if date_from and date_to:
        data = data.filter(tanggal_masuk__range=[date_from, date_to])
    elif date_from:
        data = data.filter(tanggal_masuk__gte=date_from)
    elif date_to:
        data = data.filter(tanggal_masuk__lte=date_to)

    bahan = BahanBaku.objects.all()
    supplier = Supplier.objects.all()

    context = {
        'data': data,
        'bahan': bahan,
        'supplier': supplier,
        'search': search,
        'date_from': date_from,
        'date_to': date_to
    }
    return render(request, 'purchasing/list_bahanbaku_masuk.html', context)


@transaction.atomic
def bahan_baku_masuk_add(request):
    if request.method == 'POST':
        bahan = BahanBakuMasuk.objects.create(
            bahan_baku_id=request.POST['bahan_baku'],
            supplier_id=request.POST['supplier'],
            tanggal_masuk=request.POST['tanggal_masuk'],
            jumlah_pcs=request.POST['jumlah_pcs'],
            jumlah_m3=request.POST['jumlah_m3'],
            harga_satuan=request.POST['harga_satuan'],
        )
    messages.success(request, "Bahan Baku Masuk berhasil ditambahkan!",extra_tags='bahan_baku_masuk')
    return redirect('bahan_baku_masuk_list')


def bahan_baku_masuk_edit(request, id):
    data = get_object_or_404(BahanBakuMasuk, id=id)

    if request.method == 'POST':
        # SIMPAN DATA LAMA
        old_jumlah_pcs = data.jumlah_pcs
        old_jumlah_m3 = data.jumlah_m3
        old_sisa_pcs = data.sisa_pcs
        old_sisa_m3 = data.sisa_m3

        # INPUT BARU
        new_jumlah_pcs = int(request.POST['jumlah_pcs'])
        new_jumlah_m3 = clean_m3(request.POST.get('jumlah_m3'))

        # HITUNG YANG SUDAH DIPAKAI
        used_pcs = old_jumlah_pcs - old_sisa_pcs
        used_m3 = old_jumlah_m3 - old_sisa_m3

        # ==============================
        # VALIDASI JIKA SUDAH DIPAKAI
        # ==============================
        if data.sudah_dipakai():
            if new_jumlah_pcs < used_pcs or new_jumlah_m3 < used_m3:
                messages.error(
                    request,
                    "Jumlah baru tidak boleh lebih kecil dari stok yang sudah dipakai."
                )
                return redirect('bahan_baku_masuk_list')

        # UPDATE DATA UMUM
        data.bahan_baku_id = request.POST['bahan_baku']
        data.supplier_id = request.POST['supplier']
        data.tanggal_masuk = request.POST['tanggal_masuk']
        data.harga_satuan = clean_rupiah(request.POST.get('harga_satuan'))

        # UPDATE JUMLAH
        data.jumlah_pcs = new_jumlah_pcs
        data.jumlah_m3 = new_jumlah_m3

        # ==============================
        # UPDATE SISA
        # ==============================
        if data.sudah_dipakai():
            data.sisa_pcs = new_jumlah_pcs - used_pcs
            data.sisa_m3 = new_jumlah_m3 - used_m3
        else:
            data.sisa_pcs = new_jumlah_pcs
            data.sisa_m3 = new_jumlah_m3
        print(data.jumlah_pcs, data.jumlah_m3, data.harga_satuan)
        data.save()
        data.refresh_from_db()
        print(data.jumlah_pcs, data.jumlah_m3, data.harga_satuan)
    messages.success(request, "Bahan Baku Masuk berhasil diedit!",extra_tags='bahan_baku_masuk')
    return redirect('bahan_baku_masuk_list')


def bahan_baku_masuk_delete(request, id):
    data = get_object_or_404(BahanBakuMasuk, id=id)
    data.delete()
    messages.success(request, "Bahan Baku Masuk berhasil dihapus!",extra_tags='bahan_baku_masuk')
    return redirect('bahan_baku_masuk_list')



def rekap_bahan_baku(request):
    data = BahanBakuMasuk.objects.filter()

    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        data = data.filter(tanggal_masuk__range=[start, end])

    # Menggunakan F() untuk mengalikan harga_satuan dengan jumlah_m3 per baris sebelum di-Sum
    total = data.aggregate(
        total_pcs=Sum('jumlah_pcs'),
        total_m3=Sum('jumlah_m3'),
        total_transaksi=Count('id'),
        total_harga=Sum('harga_satuan'),
    )

    context = {
        'data': data,
        'start': start,
        'end': end,
        'total_pcs': total['total_pcs'] or 0,
        'total_m3': total['total_m3'] or 0,
        'total_transaksi': total['total_transaksi'] or 0,
        'total_harga': total['total_harga'] or 0 # Kirim total_harga ke template
    }
    return render(request, 'purchasing/rekap_bahan_baku.html', context)

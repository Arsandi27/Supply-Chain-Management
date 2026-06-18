from datetime import datetime, date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator

from core.models import Pembeli, Penjualan, HasilProduksi


def dashboard_penjualan(request):
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)

    # =====================
    # KPI 6 BULAN
    # =====================
    penjualan_6_bulan = Penjualan.objects.filter(
        tanggal_penjualan__gte=six_months_ago
    )

    total_transaksi = penjualan_6_bulan.count()

    total_omset = penjualan_6_bulan.aggregate(
        total=Sum('total_harga')
    )['total'] or 0

    total_produk = penjualan_6_bulan.aggregate(
        total_pcs=Sum('pcs'),
        total_m3=Sum('m3')
    )

    # =====================
    # GRAFIK OMSET 6 BULAN
    # =====================
    grafik_penjualan = (
        penjualan_6_bulan
        .annotate(bulan=TruncMonth('tanggal_penjualan'))
        .values('bulan')
        .annotate(
            transaksi=Count('id'),
            omset=Sum('total_harga'),
            pcs=Sum('pcs'),
            m3=Sum('m3')
        )
        .order_by('bulan')
    )


    # =====================
    # TABEL PENJUALAN TERAKHIR
    # =====================
    penjualan_terakhir = (
        Penjualan.objects
        .select_related('hasil_produksi', 'pembeli')
        .order_by('-tanggal_penjualan')[:5]
    )

    context = {
        'total_transaksi': total_transaksi,
        'total_omset': total_omset,
        'total_pcs': total_produk['total_pcs'] or 0,
        'total_m3': total_produk['total_m3'] or 0,
        'grafik_penjualan': grafik_penjualan,
        'penjualan_terakhir': penjualan_terakhir,
    }

    return render(request, 'penjualan/dashboard.html', context)

def pembeli_list(request):
    data = Pembeli.objects.all()
    return render(request, 'penjualan/list_pembeli.html', {'data': data})

def pembeli_create(request):
    if request.method == 'POST':
        Pembeli.objects.create(
            nama_pembeli=request.POST['nama_pembeli']
        )
        messages.success(request, "Nama Pembeli berhasil ditambahkan!",extra_tags='pembeli')
        return redirect('pembeli_list')
    return render(request, 'pembeli/form.html')

def pembeli_edit(request, id):
    obj = get_object_or_404(Pembeli, id=id)
    if request.method == 'POST':
        obj.nama_pembeli = request.POST['nama_pembeli']
        obj.save()
        messages.success(request, "Nama Pembeli berhasil diedit!",extra_tags='pembeli')
        return redirect('pembeli_list')
    return render(request, 'pembeli/form.html', {'obj': obj})

def pembeli_delete(request, id):
    obj = get_object_or_404(Pembeli, id=id)
    obj.delete()
    messages.success(request, "Nama Pembeli berhasil dihapus!",extra_tags='pembeli')
    return redirect('pembeli_list')
def penjualan_list(request):
    search = request.GET.get('search') or ''
    date_from = request.GET.get('date_from') or ''
    date_to = request.GET.get('date_to') or ''

    if search == 'None':
        search = ''
    if date_from == 'None':
        date_from = ''
    if date_to == 'None':
        date_to = ''

    data = Penjualan.objects.select_related(
        'hasil_produksi',
        'pembeli'
    ).order_by('-tanggal_penjualan', '-id')

    if search:
        data = data.filter(
            Q(hasil_produksi__nama_hasil_produksi__nama_hasil_produksi__icontains=search) |
            Q(pembeli__nama_pembeli__icontains=search)
        )

    if date_from:
        data = data.filter(tanggal_penjualan__gte=date_from)

    if date_to:
        data = data.filter(tanggal_penjualan__lte=date_to)

    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    data = paginator.get_page(page_number)

    hasil = HasilProduksi.objects.filter(
        qc__quality__isnull=False,
        sisa_pcs__gt=0
    ).select_related(
        'nama_hasil_produksi',
        'qc__quality'
    )

    pembeli = Pembeli.objects.all()

    return render(request, 'penjualan/list_penjualan.html', {
        'data': data,
        'hasil': hasil,
        'pembeli': pembeli,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    })
    
from datetime import datetime

@transaction.atomic
def penjualan_add(request):
    if request.method == "POST":
        hasil = get_object_or_404(HasilProduksi,id=request.POST["hasil_produksi"],qc__quality__isnull=False)
        pcs = int(request.POST["pcs"])
        m3 = Decimal(request.POST["m3"])
        tanggal_str = request.POST.get('tanggal_penjualan')
        if not tanggal_str:
            return render(request, 'penjualan/add.html', {
                'error': 'Tanggal penjualan wajib diisi'
        })
        tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()

        # VALIDASI STOK
        if pcs > hasil.sisa_pcs or m3 > hasil.sisa_m3:
            raise ValueError("Stok tidak mencukupi")

        # KURANGI STOK
        hasil.sisa_pcs -= pcs
        hasil.sisa_m3 -= m3
        hasil.save()

        total_harga = request.POST.get("total_harga")
        if not total_harga:
            total_harga = 0
        print(type(total_harga), total_harga)
        print(type(Decimal(total_harga)))
        penjualan = Penjualan.objects.create(
            tanggal_penjualan=tanggal,
            hasil_produksi=hasil,
            pembeli_id=request.POST["pembeli"],
            pcs=pcs,
            m3=m3,
            total_harga=Decimal(total_harga),
        )
        print("TOTAL:", request.POST.get("total_harga"))
        # 🔥 INI YANG WAJIB ADA

        messages.success(request, "Transaksi Penjualan berhasil ditambahkan!",extra_tags='penjualan')
        return redirect("penjualan_list")
    
@transaction.atomic
def penjualan_edit(request, id):
    penjualan = get_object_or_404(Penjualan, id=id)
    hasil_lama = penjualan.hasil_produksi # Simpan data produk yang lama

    if request.method == "POST":
        # Ambil data inputan baru
        pcs_baru = int(request.POST["pcs"])
        m3_baru = Decimal(request.POST["m3"])
        tanggal_baru = request.POST["tanggal_penjualan"]
        pembeli_id = request.POST["pembeli"]
        hasil_baru_id = request.POST["hasil_produksi"]

        pembeli_baru = get_object_or_404(Pembeli, id=pembeli_id)

        # 1. BALIKKAN STOK LAMA (ke produk yang lama)
        hasil_lama.sisa_pcs += penjualan.pcs
        hasil_lama.sisa_m3 += penjualan.m3
        hasil_lama.save()

        # 2. TENTUKAN PRODUK BARUNYA
        # Jika nama produk di form tidak diganti (masih sama), pakai object hasil_lama yang stoknya baru saja direfund.
        if hasil_lama.id == int(hasil_baru_id):
            hasil_baru = hasil_lama
        else:
            # Jika user mengganti produknya ke barang lain, ambil object produk yang baru
            hasil_baru = get_object_or_404(HasilProduksi, id=hasil_baru_id)

        # 3. CEK STOK PRODUK BARU
        if pcs_baru > hasil_baru.sisa_pcs or m3_baru > hasil_baru.sisa_m3:
            # Catatan: Jika ingin lebih rapi, bisa pakai messages.error() lalu return render kembali ke form
            raise ValueError("Stok tidak mencukupi untuk produk yang dipilih")

        # 4. KURANGI STOK PRODUK BARU
        hasil_baru.sisa_pcs -= pcs_baru
        hasil_baru.sisa_m3 -= m3_baru
        hasil_baru.save()

        # 5. UPDATE DATA TRANSAKSI PENJUALAN
        penjualan.tanggal_penjualan = tanggal_baru
        penjualan.hasil_produksi = hasil_baru
        penjualan.pembeli = pembeli_baru
        penjualan.pcs = pcs_baru
        penjualan.m3 = m3_baru
        penjualan.total_harga = request.POST["total_harga"]
        penjualan.save()

        messages.success(request, "Transaksi Penjualan berhasil diubah!",extra_tags='penjualan')
        return redirect("penjualan_list")
    
@transaction.atomic
def penjualan_delete(request, id):
    penjualan = get_object_or_404(Penjualan, id=id)
    hasil = penjualan.hasil_produksi

    # KEMBALIKAN STOK
    hasil.sisa_pcs += penjualan.pcs
    hasil.sisa_m3 += penjualan.m3
    hasil.save()

    penjualan.delete()
    messages.success(request, "Transaksi Penjualan berhasil dihapus!",extra_tags='penjualan')
    return redirect("penjualan_list")

from django.db.models import Sum
from datetime import date, timedelta
def stok_penjualan(request):

    # ======================
    # STOK HASIL PRODUKSI
    # ======================
    stok = HasilProduksi.objects.select_related(
        'nama_hasil_produksi',
        'qc__quality',
        'proses_produksi'
    ).filter(
        qc__isnull=False,
        qc__quality__isnull=False,
    )

    # ======================
    # TOTAL STOK
    # ======================
    total_stok = stok.aggregate(
        total_pcs=Sum('sisa_pcs'),
        total_m3=Sum('sisa_m3')
    )

    # ======================
    # STOK TERBARU (5 data)
    # ======================
    stok_terbaru = stok.order_by('-tanggal_produksi')[:5]

    context = {
        'stok': stok,
        'stok_terbaru': stok_terbaru,
        'total_pcs': total_stok.get('total_pcs') or 0,
        'total_m3': total_stok.get('total_m3') or 0,
    }

    return render(request, 'penjualan/stok_penjualan.html', context)


def rekap_penjualan(request):
    data = Penjualan.objects.select_related(
        'hasil_produksi',
        'hasil_produksi__nama_hasil_produksi',
        'pembeli'
    )

    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        data = data.filter(
            tanggal_penjualan__range=[start, end]
        )

    total_pcs = data.aggregate(total=Sum('pcs'))['total'] or 0
    total_m3 = data.aggregate(total=Sum('m3'))['total'] or 0
    total_penjualan = data.aggregate(total=Sum('total_harga'))['total'] or 0
    total_transaksi = data.count()

    context = {
        'data': data,
        'total_pcs': total_pcs,
        'total_m3': total_m3,
        'total_penjualan': total_penjualan,
        'total_transaksi': total_transaksi,
        'start': start,
        'end': end,
    }
    return render(request, 'penjualan/rekap_penjualan.html', context)
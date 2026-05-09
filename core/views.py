from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .models import HasilProduksi, Penjualan, QualityControl, Supplier, BahanBaku, Pembeli, Quality, NamaHasilProduksi,BahanBakuMasuk,ProsesProduksi, PemakaianBahanBaku
from django.utils import timezone
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.db.models import Q

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            role = user.profile.role

            if role == 'purchasing':
                return redirect('dashboard_purchasing')
            elif role == 'produksi':
                return redirect('dashboard_produksi')
            elif role == 'penjualan':
                return redirect('dashboard_penjualan')
            elif role == 'accounting':
                return redirect('dashboard_accounting')
        else:
            messages.error(request, 'Username atau password salah')

    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


## DASHBOARD VIEWS

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

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

def dashboard_produksi(request):
    today = timezone.now().date()
    six_months_ago = today - timedelta(days=180)


    total_pemakaian = PemakaianBahanBaku.objects.filter(
        proses_produksi__tanggal_produksi__gte=six_months_ago
    ).aggregate(
        pcs=Sum('jumlah_pcs'),
        m3=Sum('jumlah_m3')
    )

    total_hasil = HasilProduksi.objects.filter(
        tanggal_produksi__gte=six_months_ago
    ).aggregate(
        pcs=Sum('jumlah_pcs'),
        m3=Sum('jumlah_m3')
    )

    # =========================
    # GRAFIK PEMAKAIAN BAHAN (6 BULAN)
    # =========================
    pemakaian_6_bulan = (
        PemakaianBahanBaku.objects
        .filter(proses_produksi__tanggal_produksi__gte=six_months_ago)
        .annotate(bulan=TruncMonth('proses_produksi__tanggal_produksi'))
        .values('bulan')
        .annotate(
            total_pcs=Sum('jumlah_pcs'),
            total_m3=Sum('jumlah_m3')
        )
        .order_by('bulan')
    )

    # =========================
    # GRAFIK HASIL PRODUKSI (6 BULAN)
    # =========================
    hasil_6_bulan = (
        HasilProduksi.objects
        .filter(tanggal_produksi__gte=six_months_ago)
        .annotate(bulan=TruncMonth('tanggal_produksi'))
        .values('bulan')
        .annotate(
            total_pcs=Sum('jumlah_pcs'),
            total_m3=Sum('jumlah_m3')
        )
        .order_by('bulan')
    )

    # =========================
    # TABEL RINGKAS
    # =========================
    pemakaian_terbaru = (
        PemakaianBahanBaku.objects
        .select_related('bahan_baku_masuk')
        .order_by('-id')[:5]
    )

    hasil_terbaru = (
        HasilProduksi.objects
        .select_related('nama_hasil_produksi')
        .order_by('-tanggal_produksi')[:5]
    )

    context = {
        'total_pemakaian': total_pemakaian, # <-- Variabel baru untuk Card
        'total_hasil': total_hasil,         # <-- Variabel baru untuk Card
        'pemakaian_6_bulan': pemakaian_6_bulan,
        'hasil_6_bulan': hasil_6_bulan,
        'pemakaian_terbaru': pemakaian_terbaru,
        'hasil_terbaru': hasil_terbaru,
    }

    return render(request, 'produksi/dashboard.html', context)


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
        return redirect('supplier_list')
    return render(request, 'purchasing/form.html')

def supplier_edit(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        supplier.nama_supplier = request.POST['nama_supplier']
        supplier.alamat = request.POST['alamat']
        supplier.kontak = request.POST['kontak']
        supplier.save()
        return redirect('supplier_list')
    return render(request, 'purchasing/form.html', {'supplier': supplier})

def supplier_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    return redirect('supplier_list')


def bahanbaku_list(request):
    data = BahanBaku.objects.all()
    return render(request, 'purchasing/list_bahanbaku.html', {'data': data})

def bahanbaku_create(request):
    if request.method == 'POST':
        BahanBaku.objects.create(
            nama_bahan=request.POST['nama_bahan']
        )
        return redirect('bahanbaku_list')
    return render(request, 'bahanbaku/form.html')

def bahanbaku_edit(request, id):
    obj = get_object_or_404(BahanBaku, id=id)
    if request.method == 'POST':
        obj.nama_bahan = request.POST['nama_bahan']
        obj.save()
        return redirect('bahanbaku_list')
    return render(request, 'bahanbaku/form.html', {'obj': obj})

def bahanbaku_delete(request, id):
    obj = get_object_or_404(BahanBaku, id=id)
    obj.delete()
    return redirect('bahanbaku_list')



def pembeli_list(request):
    data = Pembeli.objects.all()
    return render(request, 'penjualan/list_pembeli.html', {'data': data})

def pembeli_create(request):
    if request.method == 'POST':
        Pembeli.objects.create(
            nama_pembeli=request.POST['nama_pembeli']
        )
        return redirect('pembeli_list')
    return render(request, 'pembeli/form.html')

def pembeli_edit(request, id):
    obj = get_object_or_404(Pembeli, id=id)
    if request.method == 'POST':
        obj.nama_pembeli = request.POST['nama_pembeli']
        obj.save()
        return redirect('pembeli_list')
    return render(request, 'pembeli/form.html', {'obj': obj})

def pembeli_delete(request, id):
    obj = get_object_or_404(Pembeli, id=id)
    obj.delete()
    return redirect('pembeli_list')



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



def hasil_list(request):
    data = NamaHasilProduksi.objects.all()
    return render(request, 'produksi/list_nama_hasil_produksi.html', {'data': data})

def hasil_create(request):
    if request.method == 'POST':
        NamaHasilProduksi.objects.create(
            nama_hasil_produksi=request.POST['nama_hasil_produksi']
        )
        return redirect('hasil_list')
    return render(request, 'hasil/form.html')

def hasil_edit(request, id):
    obj = get_object_or_404(NamaHasilProduksi, id=id)
    if request.method == 'POST':
        obj.nama_hasil_produksi = request.POST['nama_hasil_produksi']
        obj.save()
        return redirect('hasil_list')
    return render(request, 'hasil/form.html', {'obj': obj})

def hasil_delete(request, id):
    obj = get_object_or_404(NamaHasilProduksi, id=id)
    obj.delete()
    return redirect('hasil_list')



#purchasing views for Bahan Baku Masuk

from django.db.models import Q

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
        new_jumlah_m3 = Decimal(request.POST['jumlah_m3'])

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
        data.harga_satuan = Decimal(request.POST['harga_satuan'])

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

        data.save()

    return redirect('bahan_baku_masuk_list')




def bahan_baku_masuk_delete(request, id):
    data = get_object_or_404(BahanBakuMasuk, id=id)
    data.delete()
    return redirect('bahan_baku_masuk_list')



def rekap_bahan_baku(request):
    data = BahanBakuMasuk.objects.filter()

    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        data = data.filter(tanggal_masuk__range=[start, end])

    total = data.aggregate(
        total_pcs=Sum('jumlah_pcs'),
        total_m3=Sum('jumlah_m3'),
        total_transaksi=Count('id')
    )

    context = {
        'data': data,
        'start': start,
        'end': end,
        'total_pcs': total['total_pcs'] or 0,
        'total_m3': total['total_m3'] or 0,
        'total_transaksi': total['total_transaksi'] or 0
    }

    return render(request, 'purchasing/rekap_bahan_baku.html', context)


 

def proses_produksi_list(request):
    data = ProsesProduksi.objects.all()
    return render(request, 'produksi/list_proses.html', {'data': data})


def proses_produksi_add(request):
    if request.method == 'POST':
        ProsesProduksi.objects.create(
            tanggal_produksi=request.POST['tanggal_produksi'],
            keterangan=request.POST['keterangan']
        )
    return redirect('proses_produksi_list')


def proses_produksi_edit(request, id):
    data = get_object_or_404(ProsesProduksi, id=id)
    if request.method == 'POST':
        data.tanggal_produksi = request.POST['tanggal_produksi']
        data.keterangan = request.POST['keterangan']
        data.save()
    return redirect('proses_produksi_list')


def proses_produksi_delete(request, id):
    get_object_or_404(ProsesProduksi, id=id).delete()
    return redirect('proses_produksi_list')



def pemakaian_bahan_list(request):
    data = PemakaianBahanBaku.objects.select_related(
        'proses_produksi',
        'bahan_baku_masuk',
        'bahan_baku_masuk__bahan_baku'
    )

    # ===== FILTER =====
    nama_bahan = request.GET.get('bahan')
    tanggal_mulai = request.GET.get('tanggal_mulai')
    tanggal_selesai = request.GET.get('tanggal_selesai')

    if nama_bahan:
        data = data.filter(
            bahan_baku_masuk__bahan_baku__nama_bahan__icontains=nama_bahan
        )

   # ===== LOGIKA FILTER RANGE TANGGAL =====
    if tanggal_mulai and tanggal_selesai:
        # Jika user mengisi form dari tanggal A sampai tanggal B
        data = data.filter(proses_produksi__tanggal_produksi__range=[tanggal_mulai, tanggal_selesai])
    elif tanggal_mulai:
        # Jika user cuma ngisi tanggal awal aja (mulai dari tanggal A sampai sekarang)
        data = data.filter(proses_produksi__tanggal_produksi__gte=tanggal_mulai)
    elif tanggal_selesai:
        # Jika user cuma ngisi batas akhir aja (semua data sampai tanggal B)
        data = data.filter(proses_produksi__tanggal_produksi__lte=tanggal_selesai)

    data = data.order_by('-proses_produksi__tanggal_produksi')  
    # ===== LOGIKA PENGGABUNGAN (GROUPING) =====
    # Grouping berdasarkan nama bahan baku untuk menampilkan total
    data_rekap = data.values(
        'bahan_baku_masuk__bahan_baku__nama_bahan' # Patokan groupingnya
    ).annotate(
        total_pcs=Sum('jumlah_pcs'),
        total_m3=Sum('jumlah_m3')
    ).order_by('bahan_baku_masuk__bahan_baku__nama_bahan')

    stok_gabungan = BahanBakuMasuk.objects.filter(
    sisa_pcs__gt=0,
    sisa_m3__gt=0
    ).values(
    'bahan_baku_id', # Ambil ID master bahannya
    'bahan_baku__nama_bahan' # Ambil nama bahannya
    ).annotate(
    total_pcs=Sum('sisa_pcs'),
    total_m3=Sum('sisa_m3')
    ).order_by('bahan_baku__nama_bahan')

    produksi = ProsesProduksi.objects.all()
    stok = BahanBakuMasuk.objects.filter(
        sisa_pcs__gt=0,
        sisa_m3__gt=0,
    )

    return render(request, 'produksi/list_proses_produksi.html', {
        'data_detail': data, 
        'data_rekap': data_rekap, 
        'produksi': produksi,
        'stok': stok_gabungan,
        'nama_bahan': nama_bahan,
        'tanggal_mulai': tanggal_mulai,   
        'tanggal_selesai': tanggal_selesai,
    })

from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
# Pastikan model PemakaianBahanBaku, BahanBakuMasuk sudah di-import

def pemakaian_bahan_add(request):
    if request.method == 'POST':
        proses_id = int(request.POST['proses'])
        # 1. Samain nama dengan yang ada di HTML
        bahan_master_id = request.POST.get('bahan_master_id') 
        pcs_dibutuhkan = int(request.POST['pcs'])
        m3_dibutuhkan = Decimal(request.POST['m3'])

        # Cek kalau bahan gak dipilih
        if not bahan_master_id:
            messages.error(request, "Pilih bahan baku terlebih dahulu!")
            return redirect('pemakaian_bahan_list')

        # 2. Tarik semua stok riwayat barang masuk untuk Master Bahan ini yang masih ada sisanya
        # Diurutkan dari tanggal masuk paling lama (FIFO)
        stok_tersedia = BahanBakuMasuk.objects.filter(
            bahan_baku_id=bahan_master_id,
            sisa_pcs__gt=0
        ).order_by('tanggal_masuk')

        # 3. Hitung total keseluruhan dari semua stok
        total_sisa_pcs = sum(s.sisa_pcs for s in stok_tersedia)
        total_sisa_m3 = sum(s.sisa_m3 for s in stok_tersedia)

        # Cek apakah stok gabungannya cukup
        if total_sisa_pcs < pcs_dibutuhkan or total_sisa_m3 < m3_dibutuhkan:
            messages.error(request, "Gagal! Total stok tidak mencukupi untuk pemakaian ini.")
            return redirect('pemakaian_bahan_list')

 # 4. Transaksi aman dengan metode potong antrean (FIFO)
        with transaction.atomic():
            sisa_pcs_kurang = pcs_dibutuhkan
            sisa_m3_kurang = m3_dibutuhkan

            for stok in stok_tersedia:
                if sisa_pcs_kurang <= 0:
                    break

                # Tentukan berapa PCS yang ditarik dari batch ini
                potong_pcs = min(stok.sisa_pcs, sisa_pcs_kurang)
                
                # HITUNG M3 PROPORSIONAL: (pcs ditarik / total pcs) * total m3
                proporsi = Decimal(potong_pcs) / Decimal(pcs_dibutuhkan)
                potong_m3 = round(m3_dibutuhkan * proporsi, 4)

                # Pastikan sisa M3 masuk semua di tarikan terakhir biar nggak ada sisa koma
                if sisa_pcs_kurang - potong_pcs <= 0:
                    potong_m3 = sisa_m3_kurang

                # Kurangi stok riwayatnya
                stok.sisa_pcs -= potong_pcs
                stok.sisa_m3 -= potong_m3
                stok.save()

                # Kurangi target pemakaian
                sisa_pcs_kurang -= potong_pcs
                sisa_m3_kurang -= potong_m3

                # Simpan riwayat pemakaian
                if potong_pcs > 0 or potong_m3 > 0:
                    PemakaianBahanBaku.objects.create(
                        proses_produksi_id=proses_id,
                        bahan_baku_masuk=stok, 
                        jumlah_pcs=potong_pcs,
                        jumlah_m3=potong_m3
                    )

        messages.success(request, "Pemakaian bahan baku berhasil dicatat!")
        return redirect('pemakaian_bahan_list')
def pemakaian_bahan_edit(request, id):
    # 1. Ambil salah satu data pemakaian sebagai patokan
    pemakaian_awal = get_object_or_404(PemakaianBahanBaku, id=id)
    proses_id = pemakaian_awal.proses_produksi_id
    bahan_master_id = pemakaian_awal.bahan_baku_masuk.bahan_baku_id

    if request.method == 'POST':
        pcs_baru = int(request.POST['pcs'])
        m3_baru = Decimal(request.POST['m3'])

        # Gunakan transaction agar kalau stok gak cukup, semua refund dibatalkan (rollback)
        with transaction.atomic():
            
            # 2. Cari SEMUA pecahan pemakaian lama untuk proses & bahan ini
            semua_pemakaian_lama = PemakaianBahanBaku.objects.filter(
                proses_produksi_id=proses_id,
                bahan_baku_masuk__bahan_baku_id=bahan_master_id
            )

            # 3. REFUND: Kembalikan semua stok lama ke masing-masing batch-nya
            for p in semua_pemakaian_lama:
                p.bahan_baku_masuk.sisa_pcs += p.jumlah_pcs
                p.bahan_baku_masuk.sisa_m3 += p.jumlah_m3
                p.bahan_baku_masuk.save()

            # Hapus log pemakaian lama (karena bakal diganti sama yang baru)
            semua_pemakaian_lama.delete()

            # 4. CEK STOK KESELURUHAN (Master)
            stok_tersedia = BahanBakuMasuk.objects.filter(
                bahan_baku_id=bahan_master_id,
                sisa_pcs__gt=0
            ).order_by('tanggal_masuk')

            total_sisa_pcs = sum(s.sisa_pcs for s in stok_tersedia)
            total_sisa_m3 = sum(s.sisa_m3 for s in stok_tersedia)

            # 5. VALIDASI STOK BARU
            if total_sisa_pcs < pcs_baru or total_sisa_m3 < m3_baru:
                # Sengaja pakai raise ValueError biar error kuningnya muncul (atau lu bisa ganti jadi messages.error)
                raise ValueError("Stok keseluruhan tidak mencukupi untuk nominal edit yang baru!")

            # 6. POTONG ULANG STOK (Logika proporsional FIFO yang sama kayak di fungsi Add)
            sisa_pcs_kurang = pcs_baru
            sisa_m3_kurang = m3_baru

            for stok in stok_tersedia:
                if sisa_pcs_kurang <= 0:
                    break

                potong_pcs = min(stok.sisa_pcs, sisa_pcs_kurang)
                proporsi = Decimal(potong_pcs) / Decimal(pcs_baru)
                potong_m3 = round(m3_baru * proporsi, 4)

                if sisa_pcs_kurang - potong_pcs <= 0:
                    potong_m3 = sisa_m3_kurang

                stok.sisa_pcs -= potong_pcs
                stok.sisa_m3 -= potong_m3
                stok.save()

                sisa_pcs_kurang -= potong_pcs
                sisa_m3_kurang -= potong_m3

                if potong_pcs > 0 or potong_m3 > 0:
                    PemakaianBahanBaku.objects.create(
                        proses_produksi_id=proses_id,
                        bahan_baku_masuk=stok,
                        jumlah_pcs=potong_pcs,
                        jumlah_m3=potong_m3
                    )

        return redirect('pemakaian_bahan_list')

def pemakaian_bahan_delete(request, id):
    pemakaian = get_object_or_404(PemakaianBahanBaku, id=id)
    stok = pemakaian.bahan_baku_masuk

    with transaction.atomic():
        # 1️⃣ Kembalikan stok
        stok.sisa_pcs += pemakaian.jumlah_pcs
        stok.sisa_m3 += pemakaian.jumlah_m3
        stok.save()

        # 2️⃣ Hapus pemakaian
        pemakaian.delete()

    return redirect('pemakaian_bahan_list')


def rekap_pemakaian_bahan(request):
    data = PemakaianBahanBaku.objects.select_related(
        'bahan_baku_masuk',
        'bahan_baku_masuk__supplier',
        'bahan_baku_masuk__bahan_baku'
    )

    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        data = data.filter(
            proses_produksi__tanggal_produksi__range=[start, end]
        )

    total_pcs = data.aggregate(total=Sum('jumlah_pcs'))['total'] or 0
    total_m3 = data.aggregate(total=Sum('jumlah_m3'))['total'] or 0
    total_transaksi = data.count()

    context = {
        'data': data,
        'total_pcs': total_pcs,
        'total_m3': total_m3,
        'total_transaksi': total_transaksi
    }
    return render(request, 'produksi/rekap_proses_produksi.html', context)


def hasil_produksi_list(request):
    data = HasilProduksi.objects.select_related(
        'proses_produksi',
        'nama_hasil_produksi',
        'quality', 
        'pemakaian_bahan',
    )
    
    # Ambil parameter pencarian universal dan tanggal
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # 1. FILTER PENCARIAN UNIVERSAL (Nama Produk ATAU Quality)
    if search_query:
        data = data.filter(
            Q(nama_hasil_produksi__nama_hasil_produksi__icontains=search_query) | 
            Q(qc__quality__quality__icontains=search_query) # Pastikan relasinya bener, misal: quality__nama_quality tergantung models lu
        )

    # 2. FILTER TANGGAL
    if date_from and date_to:
        data = data.filter(tanggal_produksi__range=[date_from, date_to])
    elif date_from:
        data = data.filter(tanggal_produksi__gte=date_from)
    elif date_to:
        data = data.filter(tanggal_produksi__lte=date_to)

    context = {
        'data': data,
        'proses': ProsesProduksi.objects.all(),
        'bahan': PemakaianBahanBaku.objects.all(),
        'nama': NamaHasilProduksi.objects.all(),
        'quality': Quality.objects.all(),
        
        # Kirim balik value biar di HTML tetep nangkring di formnya
        'search_query': search_query, 
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'produksi/list_hasil_produksi.html', context)


def ajax_bahan_by_proses(request):
    proses_id = request.GET.get('proses_id')

    bahan = PemakaianBahanBaku.objects.filter(
        proses_produksi_id=proses_id
    ).values('id', 'bahan_baku_masuk__bahan_baku__nama_bahan')

    return JsonResponse(list(bahan), safe=False)


def hasil_produksi_add(request):
    if request.method == 'POST':
        HasilProduksi.objects.create(
            tanggal_produksi=datetime.strptime(
                request.POST['tanggal_produksi'], '%Y-%m-%d'
            ).date(),
            proses_produksi_id=request.POST['proses'],
            pemakaian_bahan_id=request.POST['pemakaian_bahan'],
            nama_hasil_produksi_id=request.POST['nama'],
            tebal=Decimal(request.POST['tebal']),
            lebar=Decimal(request.POST['lebar']),
            panjang=Decimal(request.POST['panjang']),
            jumlah_pcs=int(request.POST['pcs']),
            jumlah_m3=Decimal(request.POST['m3']),   # ⬅️ LANGSUNG DARI JS
            sisa_pcs=int(request.POST['pcs']),
            sisa_m3=Decimal(request.POST['m3'])
        )

    return redirect('hasil_produksi_list')

def hasil_produksi_edit(request, id):
    hasil = get_object_or_404(HasilProduksi, id=id)

    if request.method == 'POST':
        hasil.nama_hasil_produksi_id = request.POST['nama']
        hasil.tebal = request.POST['tebal']
        hasil.lebar = request.POST['lebar']
        hasil.panjang = request.POST['panjang']
        hasil.jumlah_pcs = int(request.POST['pcs'])
        hasil.jumlah_m3 = Decimal(request.POST['m3'])
        hasil.sisa_pcs = hasil.jumlah_pcs
        hasil.sisa_m3 = hasil.jumlah_m3
        hasil.save()

    return redirect('hasil_produksi_list')


def hasil_produksi_delete(request, id):
    get_object_or_404(HasilProduksi, id=id).delete()
    return redirect('hasil_produksi_list')

def rekap_hasil_produksi(request):
    # Tambahkan filter isnull=False untuk memastikan hanya data yang sudah di-grade yang muncul
    data = HasilProduksi.objects.select_related(
        'proses_produksi',
        'pemakaian_bahan',
        'nama_hasil_produksi',
        'quality'
    ).filter(
        qc__isnull=False,        # Pastikan sudah ada proses QC
        qc__quality__isnull=False # Pastikan grade/quality-nya sudah dipilih
    )

    start = request.GET.get('start')
    end = request.GET.get('end')

    if start and end:
        data = data.filter(
            tanggal_produksi__range=[start, end]
        )

    # Karena data sudah di-filter di atas, 
    # hasil aggregate di bawah ini akan otomatis akurat
    total_pcs = data.aggregate(
        total=Sum('jumlah_pcs')
    )['total'] or 0

    total_m3 = data.aggregate(
        total=Sum('jumlah_m3')
    )['total'] or 0

    total_transaksi = data.count()

    context = {
        'data': data,
        'total_pcs': total_pcs,
        'total_m3': total_m3,
        'total_transaksi': total_transaksi,
        'start': start,
        'end': end
    }

    return render(request, 'produksi/rekap_hasil_produksi.html', context)

def penjualan_list(request):
    # Ambil parameter dari form filter
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Base query
    data = Penjualan.objects.select_related('hasil_produksi', 'pembeli')

    if search:
            data = data.filter(
                # Tembus 2 kali untuk produk:
                # hasil_produksi (di Penjualan) -> nama_hasil_produksi (di HasilProduksi) -> nama_hasil_produksi (di NamaHasilProduksi yang berupa CharField)
                Q(hasil_produksi__nama_hasil_produksi__nama_hasil_produksi__icontains=search) |
                
                # Tembus 1 kali untuk pembeli:
                # pembeli (di Penjualan) -> nama_pembeli (di model Pembeli yang berupa CharField)
                Q(pembeli__nama_pembeli__icontains=search) 
            )
    if date_from:
        data = data.filter(tanggal_penjualan__gte=date_from)
    if date_to:
        data = data.filter(tanggal_penjualan__lte=date_to)

    hasil = HasilProduksi.objects.all()
    pembeli = Pembeli.objects.all()

    return render(request, 'penjualan/list_penjualan.html', {
        'data': data,
        'hasil': hasil,
        'pembeli': pembeli,
        # Kirim tanggal agar tetap muncul di input field setelah difilter
        'date_from': date_from,
        'date_to': date_to,
    })
from datetime import datetime

@transaction.atomic
def penjualan_add(request):
    if request.method == "POST":
        hasil = get_object_or_404(HasilProduksi, id=request.POST["hasil_produksi"])
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

def qc_list(request):

    data = HasilProduksi.objects.select_related(
        'proses_produksi',
        'nama_hasil_produksi'
    )

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


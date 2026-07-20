from datetime import datetime, timedelta
from decimal import Decimal
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from core.decorators import role_required

from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
from django.core.paginator import Paginator
from core.models import (
    ProsesProduksi, 
    PemakaianBahanBaku, 
    BahanBakuMasuk, 
    HasilProduksi, 
    NamaHasilProduksi, 
    Quality
)


# Setup Logger untuk AJAX Error Catcher
logger = logging.getLogger(__name__)

@login_required(login_url='login')
@role_required('produksi')
@never_cache
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

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_list(request):
    data = NamaHasilProduksi.objects.all()
    return render(request, 'produksi/list_nama_hasil_produksi.html', {'data': data})

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_create(request):
    if request.method == 'POST':
        NamaHasilProduksi.objects.create(
            nama_hasil_produksi=request.POST['nama_hasil_produksi']
        )
        messages.success(request, "Nama Hasil Produksi berhasil dicatat!",extra_tags='nama_hasil_produksi')
        return redirect('hasil_list')
    return render(request, 'hasil/form.html')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_edit(request, id):
    obj = get_object_or_404(NamaHasilProduksi, id=id)
    if request.method == 'POST':
        obj.nama_hasil_produksi = request.POST['nama_hasil_produksi']
        obj.save()
        messages.success(request, "Nama Hasil Produksi berhasil diedit!",extra_tags='nama_hasil_produksi')
        return redirect('hasil_list')
    return render(request, 'hasil/form.html', {'obj': obj})

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_delete(request, id):
    obj = get_object_or_404(NamaHasilProduksi, id=id)
    obj.delete()
    messages.success(request, "Nama Hasil Produksi berhasil dihapus!",extra_tags='nama_hasil_produksi')
    return redirect('hasil_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def proses_produksi_list(request):
    data = ProsesProduksi.objects.all().order_by('-tanggal_produksi','-id')

    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    data = paginator.get_page(page_number)

    return render(request, 'produksi/list_proses.html', {
        'data': data,
    })

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def proses_produksi_add(request):
    if request.method == 'POST':
        ProsesProduksi.objects.create(
            tanggal_produksi=request.POST['tanggal_produksi'],
            keterangan=request.POST['keterangan']
        )
    messages.success(request, "Proses Produksi berhasil dicatat!",extra_tags='proses_produksi')
    return redirect('proses_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def proses_produksi_edit(request, id):
    data = get_object_or_404(ProsesProduksi, id=id)
    if request.method == 'POST':
        data.tanggal_produksi = request.POST['tanggal_produksi']
        data.keterangan = request.POST['keterangan']
        data.save()
    messages.success(request, "Proses Produksi berhasil diedit!",extra_tags='proses_produksi')
    return redirect('proses_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def proses_produksi_delete(request, id):
    get_object_or_404(ProsesProduksi, id=id).delete()
    messages.success(request, "Proses Produksi berhasil dihapus!",extra_tags='proses_produksi')
    return redirect('proses_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def pemakaian_bahan_list(request):
    data = PemakaianBahanBaku.objects.select_related(
        'proses_produksi',
        'bahan_baku_masuk',
        'bahan_baku_masuk__bahan_baku'
    )

    search = request.GET.get('search') or ''
    date_from = request.GET.get('date_from') or ''
    date_to = request.GET.get('date_to') or ''

    if search == 'None':
        search = ''
    if date_from == 'None':
        date_from = ''
    if date_to == 'None':
        date_to = ''

    if search:
        data = data.filter(
            bahan_baku_masuk__bahan_baku__nama_bahan__icontains=search
        )

    if date_from and date_to:
        data = data.filter(
            proses_produksi__tanggal_produksi__range=[date_from, date_to]
        )
    elif date_from:
        data = data.filter(
            proses_produksi__tanggal_produksi__gte=date_from
        )
    elif date_to:
        data = data.filter(
            proses_produksi__tanggal_produksi__lte=date_to
        )

    data = data.order_by('-proses_produksi__tanggal_produksi', '-id')

    data_rekap = data.values(
        'bahan_baku_masuk__bahan_baku__nama_bahan'
    ).annotate(
        total_pcs=Sum('jumlah_pcs'),
        total_m3=Sum('jumlah_m3')
    ).order_by('bahan_baku_masuk__bahan_baku__nama_bahan')

    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    data_detail = paginator.get_page(page_number)

    stok_gabungan = BahanBakuMasuk.objects.filter(
        sisa_pcs__gt=0,
        sisa_m3__gt=0
    ).values(
        'bahan_baku_id',
        'bahan_baku__nama_bahan'
    ).annotate(
        total_pcs=Sum('sisa_pcs'),
        total_m3=Sum('sisa_m3')
    ).order_by('bahan_baku__nama_bahan')

    produksi = ProsesProduksi.objects.all()

    return render(request, 'produksi/list_pemakaian_bahan.html', {
        'data': data_detail,
        'data_rekap': data_rekap,
        'produksi': produksi,
        'stok': stok_gabungan,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    })
    
    
    
from decimal import Decimal
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
# Pastikan model PemakaianBahanBaku, BahanBakuMasuk sudah di-import

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def pemakaian_bahan_add(request):
    if request.method == 'POST':
        proses_id = int(request.POST['proses'])
        # 1. Samain nama dengan yang ada di HTML
        bahan_master_id = request.POST.get('bahan_master_id') 
        pcs_dibutuhkan = int(request.POST['pcs'])
        m3_dibutuhkan = Decimal(request.POST['m3'])

        if not bahan_master_id:
            messages.error(request, "Pilih bahan baku terlebih dahulu!")
            return redirect('pemakaian_bahan_list')

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

        messages.success(request, "Pemakaian bahan baku berhasil dicatat!",extra_tags='pemakaian_bahan')
        return redirect('pemakaian_bahan_list')
    
@login_required(login_url='login')
@role_required('produksi')
@never_cache
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
    messages.success(request, "Pemakaian bahan baku berhasil diedit!",extra_tags='pemakaian_bahan')
    return redirect('pemakaian_bahan_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
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

    messages.success(request, "Pemakaian bahan baku berhasil dihapus!",extra_tags='pemakaian_bahan')
    return redirect('pemakaian_bahan_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def rekap_pemakaian_bahan(request):
    data = PemakaianBahanBaku.objects.select_related(
        'bahan_baku_masuk',
        'bahan_baku_masuk__supplier',
        'bahan_baku_masuk__bahan_baku'
    ).order_by('-proses_produksi__tanggal_produksi', '-id')

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
    return render(request, 'produksi/rekap_pemakaian_bahan.html', context)

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_produksi_list(request):
    data = HasilProduksi.objects.select_related(
        'proses_produksi',
        'nama_hasil_produksi',
        'quality',
        'pemakaian_bahan',
    ).order_by('-tanggal_produksi', '-id')

    search = request.GET.get('search') or ''
    date_from = request.GET.get('date_from') or ''
    date_to = request.GET.get('date_to') or ''

    if search == 'None':
        search = ''
    if date_from == 'None':
        date_from = ''
    if date_to == 'None':
        date_to = ''

    if search:
        data = data.filter(
            Q(nama_hasil_produksi__nama_hasil_produksi__icontains=search) |
            Q(qc__quality__quality__icontains=search)
        )

    if date_from and date_to:
        data = data.filter(tanggal_produksi__range=[date_from, date_to])
    elif date_from:
        data = data.filter(tanggal_produksi__gte=date_from)
    elif date_to:
        data = data.filter(tanggal_produksi__lte=date_to)

    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    data = paginator.get_page(page_number)

    context = {
        'data': data,
        'proses': ProsesProduksi.objects.all(),
        'bahan': PemakaianBahanBaku.objects.all(),
        'nama': NamaHasilProduksi.objects.all(),
        'quality': Quality.objects.all(),
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'produksi/list_hasil_produksi.html', context)


from django.http import JsonResponse
from django.db.models.functions import Coalesce
import logging
logger = logging.getLogger(__name__)

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def ajax_bahan_by_proses(request):
    proses_id = request.GET.get('proses_id')
    if not proses_id:
        return JsonResponse([], safe=False)
        
    try:
        # KUNCI PERBAIKAN: Pakai 'hasilproduksi__jumlah_pcs' sesuai dengan pilihan field dari log error lo!
        bahan_tersedia = PemakaianBahanBaku.objects.filter(proses_produksi_id=proses_id) \
            .annotate(
                # Menghitung total PCS hasil produksi yang sudah tercatat
                pcs_terpakai=Coalesce(Sum('hasilproduksi__jumlah_pcs'), 0)
            ) \
            .annotate(
                # Sisa Jatah PCS = Total PCS Pemakaian - PCS yang sudah jadi Hasil Produksi
                sisa_jatah_pcs=F('jumlah_pcs') - F('pcs_terpakai')
            ) \
            .filter(
                # Hanya tampilkan bahan yang sisa kuantitas PCS-nya masih di atas 0
                sisa_jatah_pcs__gt=0 
            ).select_related('bahan_baku_masuk__bahan_baku')

        data = []
        for b in bahan_tersedia:
            data.append({
                'id': b.id,
                'nama_bahan': f"{b.bahan_baku_masuk.bahan_baku.nama_bahan} (Sisa: {b.sisa_jatah_pcs} PCS)"
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        print("--- ERROR LOG BACKEND AJAX ---")
        print(str(e))
        print("------------------------------")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_produksi_add(request):
    if request.method == 'POST':
        pemakaian_id = request.POST['pemakaian_bahan']
        input_pcs = int(request.POST['pcs'])
        input_m3 = Decimal(request.POST['m3'])

        # 1. Ambil data pemakaian bahan baku sebagai patokan maksimal
        pemakaian = get_object_or_404(PemakaianBahanBaku, id=pemakaian_id)

        # 2. Hitung total hasil produksi yang SUDAH TERCATAT untuk bahan baku ini
        hasil_sebelumnya = HasilProduksi.objects.filter(
            pemakaian_bahan_id=pemakaian_id
        ).aggregate(
            total_m3=Sum('jumlah_m3')
        )
        
        # Kalau belum ada hasil produksi sama sekali, set jadi 0
        total_m3_sebelumnya = hasil_sebelumnya['total_m3'] or Decimal('0.000')

        # 3. LOGIKA VALIDASI (Mencegah Over-Production)
        total_m3_keseluruhan = total_m3_sebelumnya + input_m3

        # Jika total m3 output melebihi m3 input, tolak simpan datanya!
        if total_m3_keseluruhan > pemakaian.jumlah_m3:
            sisa_m3_boleh_diinput = pemakaian.jumlah_m3 - total_m3_sebelumnya
            pesan_error = f"Gagal! Volume melebihi bahan baku. Sisa bahan yang bisa diolah tinggal {sisa_m3_boleh_diinput} m3."
            messages.error(request, pesan_error)
            return redirect('hasil_produksi_list') # Balikin ke halaman list tanpa nyimpen data

        # 4. Jika lolos validasi, baru data disimpan
        HasilProduksi.objects.create(
            tanggal_produksi=datetime.strptime(
                request.POST['tanggal_produksi'], '%Y-%m-%d'
            ).date(),
            proses_produksi_id=request.POST['proses'],
            pemakaian_bahan_id=pemakaian_id,
            nama_hasil_produksi_id=request.POST['nama'],
            tebal=Decimal(request.POST['tebal']),
            lebar=Decimal(request.POST['lebar']),
            panjang=Decimal(request.POST['panjang']),
            jumlah_pcs=input_pcs,
            jumlah_m3=input_m3,
            sisa_pcs=input_pcs,
            sisa_m3=input_m3
        )
        
        messages.success(request, "Hasil produksi berhasil ditambahkan!", extra_tags='hasil_produksi')

    return redirect('hasil_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_produksi_edit(request, id):
    hasil = get_object_or_404(HasilProduksi, id=id)

    if request.method == 'POST':
        try:
            input_pcs = int(request.POST['pcs'])
            input_m3 = Decimal(request.POST['m3'])
        except (ValueError, KeyError):
            messages.error(request, "Gagal! Input data PCS atau M3 tidak valid.")
            return redirect('hasil_produksi_list')

        # 1️⃣ VALIDASI 1: Pengecekan jika PCS diinput 0 atau minus
        if input_pcs <= 0:
            messages.error(request, "Gagal! Jumlah PCS hasil produksi tidak boleh 0 atau minus.")
            return redirect('hasil_produksi_list')

        # 2️⃣ VALIDASI 2: Mencegah Over-Production Berdasarkan JUMLAH PCS
        # Hitung total PCS dari hasil produksi lain (kecuali data ini sendiri)
        hasil_lain = HasilProduksi.objects.filter(
            pemakaian_bahan_id=hasil.pemakaian_bahan_id
        ).exclude(
            id=id
        ).aggregate(
            total_pcs=Sum('jumlah_pcs'),
            total_m3=Sum('jumlah_m3') # Ambil juga m3-nya buat pengaman sekunder
        )
        
        total_pcs_lain = hasil_lain['total_pcs'] or 0
        total_m3_lain = hasil_lain['total_m3'] or Decimal('0.000')

        # Hitung total akumulasi baru (Data lain + Inputan edit baru)
        total_pcs_keseluruhan = total_pcs_lain + input_pcs
        total_m3_keseluruhan = total_m3_lain + input_m3

        # KUNCI VALIDASI UTAMA: Bandingkan PCS Keseluruhan vs PCS Pemakaian Bahan Baku
        if total_pcs_keseluruhan > hasil.pemakaian_bahan.jumlah_pcs:
            sisa_pcs_boleh_diinput = hasil.pemakaian_bahan.jumlah_pcs - total_pcs_lain
            messages.error(request, f"Gagal! Jumlah PCS melebihi batas pemakaian bahan. Sisa jatah maksimal yang bisa diinput tinggal {sisa_pcs_boleh_diinput} PCS.")
            return redirect('hasil_produksi_list')

        # KUNCI VALIDASI SEKUNDER: Jaga-jaga kalau volume m3-nya yang melesat melewati batas
        if total_m3_keseluruhan > hasil.pemakaian_bahan.jumlah_m3:
            sisa_m3_boleh_diinput = hasil.pemakaian_bahan.jumlah_m3 - total_m3_lain
            sisa_bersih = round(sisa_m3_boleh_diinput, 4)
            messages.error(request, f"Gagal! Volume M³ melebihi batas bahan baku. Sisa jatah volume tinggal {sisa_bersih} m3.")
            return redirect('hasil_produksi_list')

        # 3️⃣ Eksekusi Update jika lolos uji pertahanan berlapis
        hasil.nama_hasil_produksi_id = request.POST['nama']
        hasil.tebal = Decimal(request.POST['tebal'])
        hasil.lebar = Decimal(request.POST['lebar'])
        hasil.panjang = Decimal(request.POST['panjang'])
        hasil.jumlah_pcs = input_pcs
        hasil.jumlah_m3 = input_m3
        hasil.sisa_pcs = input_pcs  
        hasil.sisa_m3 = input_m3    
        hasil.save()
    
        messages.success(request, "Hasil produksi berhasil diupdate!", extra_tags='hasil_produksi')

    return redirect('hasil_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
def hasil_produksi_delete(request, id):
    get_object_or_404(HasilProduksi, id=id).delete()
    
    messages.success(request, "Hasil produksi berhasil dihapus!", extra_tags='hasil_produksi')
    return redirect('hasil_produksi_list')

@login_required(login_url='login')
@role_required('produksi')
@never_cache
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
    ).order_by('-tanggal_produksi', '-id')

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
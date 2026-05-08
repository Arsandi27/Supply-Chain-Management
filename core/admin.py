from django.contrib import admin
from .models import (
    Profile,
    Supplier,
    BahanBaku,
    BahanBakuMasuk,
    ProsesProduksi,
    PemakaianBahanBaku,
    Quality,
    HasilProduksi,
    Penjualan,
    NamaHasilProduksi,
    Pembeli,
    QualityControl,

)

# ======================
# PROFILE
# ======================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)


# ======================
# SUPPLIER
# ======================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('nama_supplier','alamat', 'kontak')
    search_fields = ('nama_supplier',)

# ======================
# BAHAN BAKU
# ======================
@admin.register(BahanBaku)
class BahanBakuAdmin(admin.ModelAdmin):
    list_display = ('nama_bahan',)
    search_fields = ('nama_bahan',)

@admin.register(Pembeli)
class PembeliAdmin(admin.ModelAdmin):
    list_display = ('nama_pembeli',)
    search_fields = ('nama_pembeli',)



@admin.register(NamaHasilProduksi)
class NamaHasilProduksiAdmin(admin.ModelAdmin):
    list_display = ('nama_hasil_produksi',)
    search_fields = ('nama_hasil_produksi',)
# ======================
# BAHAN BAKU MASUK
# ======================
@admin.register(BahanBakuMasuk)
class BahanBakuMasukAdmin(admin.ModelAdmin):
    list_display = (
        'bahan_baku',
        'supplier',
        'tanggal_masuk',
        'jumlah_pcs',
        'jumlah_m3',
        'sisa_pcs',
        'sisa_m3',
        'harga_satuan',
    )
    list_filter = ('tanggal_masuk', 'supplier', 'bahan_baku')
    search_fields = ('bahan_baku__nama_bahan', 'supplier__nama_supplier')
    ordering = ('tanggal_masuk',)


# ======================
# PROSES PRODUKSI
# ======================
@admin.register(ProsesProduksi)
class ProsesProduksiAdmin(admin.ModelAdmin):
    list_display = ('id', 'tanggal_produksi')
    list_filter = ('tanggal_produksi',)


# ======================
# PEMAKAIAN BAHAN BAKU
# ======================
@admin.register(PemakaianBahanBaku)
class PemakaianBahanBakuAdmin(admin.ModelAdmin):
    list_display = (
        'proses_produksi',
        'bahan_baku_masuk',
        'jumlah_pcs',
        'jumlah_m3',
    )
    list_filter = ('proses_produksi',)


# ======================
# QUALITY
# ======================
@admin.register(Quality)
class QualityAdmin(admin.ModelAdmin):
    list_display = ('quality',)
    search_fields = ('quality',)


# ======================
# HASIL PRODUKSI
# ======================
@admin.register(HasilProduksi)
class HasilProduksiAdmin(admin.ModelAdmin):
    list_display = (
        'proses_produksi',
        'tebal',
        'lebar',
        'panjang',
        'jumlah_pcs',
        'jumlah_m3',
        'sisa_pcs',
        'sisa_m3',
    )
    list_filter = ( 'proses_produksi',)


# ======================
# PENJUALAN
# ======================
@admin.register(Penjualan)
class PenjualanAdmin(admin.ModelAdmin):
    list_display = ('id', 'tanggal_penjualan', 'total_harga', 'pembeli')
    list_filter = ( 'tanggal_penjualan',)






# 🔥 QUALITY CONTROL
@admin.register(QualityControl)
class QualityControlAdmin(admin.ModelAdmin):
    list_display = ('hasil_produksi', 'quality', 'tanggal_validasi')
    search_fields = ('hasil_produksi__id', 'quality__nama')
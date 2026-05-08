from decimal import Decimal, InvalidOperation
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ('purchasing', 'Purchasing'),
        ('produksi', 'Produksi'),
        ('penjualan', 'Penjualan'),
        ('accounting', 'Accounting'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Supplier(models.Model):
    nama_supplier = models.CharField(max_length=100)
    alamat = models.TextField()
    kontak = models.CharField(max_length=50)

    def __str__(self):
        return self.nama_supplier
    

class BahanBaku(models.Model):
    nama_bahan = models.CharField(max_length=100)

    def __str__(self):
        return self.nama_bahan
    

from django.utils import timezone


class BahanBakuMasuk(models.Model):

    bahan_baku = models.ForeignKey(
        'BahanBaku',
        on_delete=models.CASCADE
    )

    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.CASCADE
    )

    tanggal_masuk = models.DateField(default=timezone.now)

    jumlah_pcs = models.PositiveIntegerField(default=0)
    jumlah_m3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    sisa_pcs = models.PositiveIntegerField(default=0)
    sisa_m3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    harga_satuan = models.DecimalField(max_digits=15, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.sisa_pcs = self.jumlah_pcs
            self.sisa_m3 = self.jumlah_m3
        super().save(*args, **kwargs)

    def sudah_dipakai(self):
        return (
            self.sisa_pcs < self.jumlah_pcs or
            self.sisa_m3 < self.jumlah_m3
        )
    @property
    def total(self):
        return self.harga_satuan

    class Meta:
        ordering = ['tanggal_masuk']

    def __str__(self):
        return f"{self.bahan_baku}"
    
class ProsesProduksi(models.Model):
    tanggal_produksi = models.DateField(default=timezone.now)
    keterangan = models.TextField(blank=True)

    def __str__(self):
        return f"Produksi - {self.tanggal_produksi}"

class PemakaianBahanBaku(models.Model):
    proses_produksi = models.ForeignKey(ProsesProduksi, on_delete=models.CASCADE)
    bahan_baku_masuk = models.ForeignKey(BahanBakuMasuk, on_delete=models.CASCADE)
    jumlah_pcs = models.PositiveIntegerField(default=0)
    jumlah_m3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)



class Pembeli(models.Model):
    nama_pembeli = models.CharField(max_length=100, blank=True,
    null=True)
    def __str__(self):
        return self.nama_pembeli

class Quality(models.Model):
    quality = models.CharField(max_length=100, blank=True,
    null=True)

    def __str__(self):
        return self.quality
    
class NamaHasilProduksi(models.Model):
    nama_hasil_produksi = models.CharField(max_length=100,blank=True,
    null=True)

    def __str__(self):
        return self.nama_hasil_produksi

class HasilProduksi(models.Model):
    proses_produksi = models.ForeignKey(ProsesProduksi, on_delete=models.CASCADE)
    pemakaian_bahan = models.ForeignKey(PemakaianBahanBaku,on_delete=models.CASCADE)
    nama_hasil_produksi = models.ForeignKey(NamaHasilProduksi, on_delete=models.CASCADE)
    quality = models.ForeignKey(Quality,on_delete=models.SET_NULL,null=True,blank=True)
    tanggal_produksi = models.DateField()
    tebal = models.DecimalField(max_digits=10, decimal_places=3)
    lebar = models.DecimalField(max_digits=10, decimal_places=3)
    panjang = models.DecimalField(max_digits=10, decimal_places=3)

    jumlah_pcs = models.PositiveIntegerField()
    jumlah_m3 = models.DecimalField(max_digits=12, decimal_places=3)

    sisa_pcs = models.PositiveIntegerField()
    sisa_m3 = models.DecimalField(max_digits=12, decimal_places=3)
    
    def __str__(self):
        return f"Hasil Produksi {self.id} - {self.nama_hasil_produksi }"


from django.db import models
from django.utils import timezone

class Penjualan(models.Model):
    
    hasil_produksi = models.ForeignKey(
        HasilProduksi,
        on_delete=models.CASCADE,
        related_name='penjualan'
    )

    pembeli = models.ForeignKey(
        Pembeli,
        on_delete=models.CASCADE
    )

    tanggal_penjualan = models.DateField()
    pcs = models.PositiveIntegerField(default=0)
    m3 = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    total_harga = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )


    def __str__(self):
        return f"Penjualan #{self.id} - {self.pembeli}"
    

class QualityControl(models.Model):

    hasil_produksi = models.OneToOneField(
        HasilProduksi,
        on_delete=models.CASCADE,
        related_name='qc'
    )

    quality = models.ForeignKey(Quality,on_delete=models.SET_NULL,null=True,blank=True)
    tanggal_validasi = models.DateField(null=True, blank=True)

    catatan = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"QC - {self.hasil_produksi} - {self.quality}"



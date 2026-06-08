
from django.urls import path
from core.views import penjualan
from core import views  

urlpatterns = [
    path('dashboard/penjualan/', penjualan.dashboard_penjualan, name='dashboard_penjualan'),
    path('pembeli/', penjualan.pembeli_list, name='pembeli_list'),
    path('pembeli/add/', penjualan.pembeli_create),
    path('pembeli/edit/<int:id>/', penjualan.pembeli_edit),
    path('pembeli/delete/<int:id>/', penjualan.pembeli_delete),

    path("transaksi/", penjualan.penjualan_list, name="penjualan_list"),
    path("transaksi/add/", penjualan.penjualan_add, name="penjualan_add"),
    path("transaksi/edit/<int:id>/", penjualan.penjualan_edit, name="penjualan_edit"),
    path("transaksi/delete/<int:id>/", penjualan.penjualan_delete, name="penjualan_delete"),
    path('transaksi/stok/', penjualan.stok_penjualan, name='stok_penjualan'),

    path('rekap-penjualan/', penjualan.rekap_penjualan, name='rekap_penjualan'),

]
 
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    #DASHBOARD
    path('dashboard/purchasing/', views.dashboard_purchasing, name='dashboard_purchasing'),
    path('dashboard/produksi/', views.dashboard_produksi, name='dashboard_produksi'),
    path('dashboard/penjualan/', views.dashboard_penjualan, name='dashboard_penjualan'),
    path('dashboard/qc/', views.dashboard_qc, name='dashboard_qc'),
    #PURCHASING
    path('supplier/', views.supplier_list, name='supplier_list'),
    path('supplier/add/', views.supplier_create),
    path('supplier/edit/<int:id>/', views.supplier_edit),
    path('supplier/delete/<int:id>/', views.supplier_delete),

    path('bahanbaku/', views.bahanbaku_list, name='bahanbaku_list'),
    path('bahanbaku/add/', views.bahanbaku_create),
    path('bahanbaku/edit/<int:id>/', views.bahanbaku_edit),
    path('bahanbaku/delete/<int:id>/', views.bahanbaku_delete),

    path('bahan-baku-masuk/', views.bahan_baku_masuk_list, name='bahan_baku_masuk_list'),
    path('bahan-baku-masuk/add/', views.bahan_baku_masuk_add, name='bahan_baku_masuk_add'),
    path('bahan-baku-masuk/edit/<int:id>/', views.bahan_baku_masuk_edit, name='bahan_baku_masuk_edit'),
    path('bahan-baku-masuk/delete/<int:id>/', views.bahan_baku_masuk_delete, name='bahan_baku_masuk_delete'),

    path('rekap-bahan-baku/', views.rekap_bahan_baku, name='rekap_bahan_baku'),

    #PENJUALAN
    path('pembeli/', views.pembeli_list, name='pembeli_list'),
    path('pembeli/add/', views.pembeli_create),
    path('pembeli/edit/<int:id>/', views.pembeli_edit),
    path('pembeli/delete/<int:id>/', views.pembeli_delete),

    path("penjualan/", views.penjualan_list, name="penjualan_list"),
    path("penjualan/add/", views.penjualan_add, name="penjualan_add"),
    path("penjualan/edit/<int:id>/", views.penjualan_edit, name="penjualan_edit"),
    path("penjualan/delete/<int:id>/", views.penjualan_delete, name="penjualan_delete"),
    path('penjualan/stok/', views.stok_penjualan, name='stok_penjualan'),

    path('rekap-penjualan/', views.rekap_penjualan, name='rekap_penjualan'),


    #PRODUKSI
    path('quality/', views.quality_list, name='quality_list'),
    path('quality/add/', views.quality_create),
    path('quality/edit/<int:id>/', views.quality_edit),
    path('quality/delete/<int:id>/', views.quality_delete),

    path('hasil/', views.hasil_list, name='hasil_list'),
    path('hasil/add/', views.hasil_create),
    path('hasil/edit/<int:id>/', views.hasil_edit),
    path('hasil/delete/<int:id>/', views.hasil_delete),

    path('produksi/', views.proses_produksi_list, name='proses_produksi_list'),
    path('produksi/add/', views.proses_produksi_add, name='proses_produksi_add'),
    path('produksi/edit/<int:id>/', views.proses_produksi_edit, name='proses_produksi_edit'),
    path('produksi/delete/<int:id>/', views.proses_produksi_delete, name='proses_produksi_delete'),

    path('pemakaian/', views.pemakaian_bahan_list, name='pemakaian_bahan_list'),
    path('pemakaian/add/', views.pemakaian_bahan_add, name='pemakaian_bahan_add'),
    path('pemakaian/edit/<int:id>/', views.pemakaian_bahan_edit, name='pemakaian_bahan_edit'),
    path('pemakaian/delete/<int:id>/', views.pemakaian_bahan_delete, name='pemakaian_bahan_delete'),

    path('hasil-produksi/', views.hasil_produksi_list, name='hasil_produksi_list'),
    path('ajax/bahan-by-proses/', views.ajax_bahan_by_proses, name='ajax_bahan_by_proses'),

    path('hasil-produksi/add/', views.hasil_produksi_add, name='hasil_produksi_add'),
    path('hasil-produksi/edit/<int:id>/', views.hasil_produksi_edit, name='hasil_produksi_edit'),
    path('hasil-produksi/delete/<int:id>/', views.hasil_produksi_delete, name='hasil_produksi_delete'),

    path('rekap-pemakaian-bahan/',views.rekap_pemakaian_bahan,name='rekap_pemakaian_bahan'),

    path('rekap-hasil-produksi/',views.rekap_hasil_produksi,name='rekap_hasil_produksi'),


    #QUALITY CONTROL
    path('qc/', views.qc_list, name='qc_list'),
    path('qc/validasi/<int:id>/', views.qc_validasi, name='qc_validasi'),
    path('qc/edit-validasi/<int:id>/', views.qc_edit_validasi, name='qc_edit_validasi'),

]

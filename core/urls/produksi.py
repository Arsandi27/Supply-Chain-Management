from django.urls import path
from core.views import produksi as views_produksi
urlpatterns = [
    path('dashboard/produksi/', views_produksi.dashboard_produksi, name='dashboard_produksi'),
    
    path('hasil/', views_produksi.hasil_list, name='hasil_list'),
    path('hasil/add/', views_produksi.hasil_create),
    path('hasil/edit/<int:id>/', views_produksi.hasil_edit),
    path('hasil/delete/<int:id>/', views_produksi.hasil_delete),

    path('proses/', views_produksi.proses_produksi_list, name='proses_produksi_list'),
    path('proses/add/', views_produksi.proses_produksi_add, name='proses_produksi_add'),
    path('proses/edit/<int:id>/', views_produksi.proses_produksi_edit, name='proses_produksi_edit'),
    path('proses/delete/<int:id>/', views_produksi.proses_produksi_delete, name='proses_produksi_delete'),

    path('pemakaian/', views_produksi.pemakaian_bahan_list, name='pemakaian_bahan_list'),
    path('pemakaian/add/', views_produksi.pemakaian_bahan_add, name='pemakaian_bahan_add'),
    path('pemakaian/edit/<int:id>/', views_produksi.pemakaian_bahan_edit, name='pemakaian_bahan_edit'),
    path('pemakaian/delete/<int:id>/', views_produksi.pemakaian_bahan_delete, name='pemakaian_bahan_delete'),

    path('hasil-produksi/', views_produksi.hasil_produksi_list, name='hasil_produksi_list'),
    path('ajax/bahan-by-proses/', views_produksi.ajax_bahan_by_proses, name='ajax_bahan_by_proses'),

    path('hasil-produksi/add/', views_produksi.hasil_produksi_add, name='hasil_produksi_add'),
    path('hasil-produksi/edit/<int:id>/', views_produksi.hasil_produksi_edit, name='hasil_produksi_edit'),
    path('hasil-produksi/delete/<int:id>/', views_produksi.hasil_produksi_delete, name='hasil_produksi_delete'),

    path('rekap-pemakaian-bahan/',views_produksi.rekap_pemakaian_bahan,name='rekap_pemakaian_bahan'),

    path('rekap-hasil-produksi/',views_produksi.rekap_hasil_produksi,name='rekap_hasil_produksi'),
]
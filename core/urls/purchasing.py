from django.urls import path
from core.views import purchasing

urlpatterns = [
    path('dashboard/purchasing/', purchasing.dashboard_purchasing, name='dashboard_purchasing'),
    path('supplier/', purchasing.supplier_list, name='supplier_list'),
    path('supplier/add/', purchasing.supplier_create),
    path('supplier/edit/<int:id>/', purchasing.supplier_edit),
    path('supplier/delete/<int:id>/', purchasing.supplier_delete),

    path('bahanbaku/', purchasing.bahanbaku_list, name='bahanbaku_list'),
    path('bahanbaku/add/', purchasing.bahanbaku_create),
    path('bahanbaku/edit/<int:id>/', purchasing.bahanbaku_edit),
    path('bahanbaku/delete/<int:id>/', purchasing.bahanbaku_delete),

    path('bahan-baku-masuk/', purchasing.bahan_baku_masuk_list, name='bahan_baku_masuk_list'),
    path('bahan-baku-masuk/add/', purchasing.bahan_baku_masuk_add, name='bahan_baku_masuk_add'),
    path('bahan-baku-masuk/edit/<int:id>/', purchasing.bahan_baku_masuk_edit, name='bahan_baku_masuk_edit'),
    path('bahan-baku-masuk/delete/<int:id>/', purchasing.bahan_baku_masuk_delete, name='bahan_baku_masuk_delete'),

    path('rekap-bahan-baku/', purchasing.rekap_bahan_baku, name='rekap_bahan_baku'),

]
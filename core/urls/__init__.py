from django.urls import path, include

urlpatterns = [
    path('purchasing/', include('core.urls.purchasing')),
    path('produksi/', include('core.urls.produksi')),
    path('qc/', include('core.urls.qc')),
    path('penjualan/', include('core.urls.penjualan')),
]
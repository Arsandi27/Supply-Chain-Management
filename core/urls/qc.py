from django.urls import path
from core.views import qc

urlpatterns = [
    path('dashboard/qc/', qc.dashboard_qc, name='dashboard_qc'),
    path('qc/', qc.qc_list, name='qc_list'),
    path('qc/validasi/<int:id>/', qc.qc_validasi, name='qc_validasi'),
    path('qc/edit-validasi/<int:id>/', qc.qc_edit_validasi, name='qc_edit_validasi'),

]
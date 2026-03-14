{
    'name': 'Quản lý Lương và KPI Custom',
    'version': '1.0',
    'summary': 'Module tính lương dựa trên chấm công và KPI',
    'category': 'Human Resources',
    'author': 'Your Name',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'nhan_su',
        'cham_cong',
    ],
    'data': [
        'security/security.xml',
    'security/ir.model.access.csv',
    'data/email_template.xml',
    'data/cron.xml',
    'views/hr_employee_extend_views.xml',
    'views/kpi_danh_gia_views.xml', # File mới
    'views/bang_luong_views.xml',
    'views/menu.xml',
],
    'installable': True,
    'application': True,
    'auto_install': False,
}
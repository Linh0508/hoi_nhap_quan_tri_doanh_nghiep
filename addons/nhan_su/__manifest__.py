# -*- coding: utf-8 -*-
{
    'name': "nhan_su",
    'version': '1.0',
    'category': 'Human Resources',
    'license': 'LGPL-3',

    'depends': ['base', 'hr'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view_inherit.xml',   # thay cho nhan_vien.xml
        'views/phong_ban.xml',
        'views/chuc_vu.xml',
        'views/don_vi.xml',
        'views/lich_su_cong_tac.xml',
        'views/chung_chi_bang_cap.xml',
        'views/danh_sach_chung_chi_bang_cap.xml',
        'views/menu.xml',
    ],

    'installable': True,
    'application': True,
}

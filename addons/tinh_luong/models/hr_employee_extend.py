from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    luong_co_ban = fields.Float(string="Lương cơ bản", default=0.0)
    phu_cap_an_trua = fields.Float(string="Phụ cấp ăn trưa/ngày", default=30000)
    phu_cap_xang_xe_theo_ngay = fields.Float(string="Phụ cấp xăng xe/ngày", default=15000)
    phu_cap_khac = fields.Float(string="Phụ cấp khác", default=0.0)
    luong_bhxh = fields.Float(string="Mức đóng BHXH", default=0.0)
    don_gia_phat_muon = fields.Float(string="Phạt mỗi phút (VNĐ)", default=1000)
    thuong_kpi_dinh_muc = fields.Float(string="Thưởng KPI tối đa", default=0.0)
    thue_tncn_percent = fields.Float(string="% Thuế TNCN", default=5.0)
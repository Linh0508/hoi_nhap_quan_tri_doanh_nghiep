from odoo import models, fields
from odoo import api, SUPERUSER_ID
            
class CauHinhLuong(models.Model):
    _name = 'cau.hinh.luong'
    _description = 'Cấu hình lương nhân viên'
    _sql_constraints = [
        ('unique_employee_config', 'unique(employee_id)', 
        'Mỗi nhân viên chỉ có 1 cấu hình lương!')
    ]

    employee_id = fields.Many2one(
        'hr.employee',
        string="Nhân viên",
        required=True,
        ondelete='cascade'
    )

    luong_co_ban = fields.Float(string="Lương cơ bản")
    luong_bhxh = fields.Float(string="Mức đóng BHXH")

    don_gia_tang_ca = fields.Float(string="Đơn giá tăng ca")
    muc_phat_muon = fields.Float(string="Mức phạt đi muộn")
    muc_thuong_kpi = fields.Float(string="Mức thưởng KPI")

    tro_cap_an_trua = fields.Float(string="Trợ cấp ăn trưa")
    tro_cap_xang_xe = fields.Float(string="Trợ cấp xăng xe")
    phu_cap_chuc_vu = fields.Float(string="Phụ cấp chức vụ")
    phu_cap_co_dinh = fields.Float(string="Phụ cấp cố định")

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        employees = env["hr.employee"].search([])

        for emp in employees:

            exist = env["cau.hinh.luong"].search([
                ("employee_id", "=", emp.id)
            ])
            
            if exist:
                exist.write({
                    "luong_co_ban": 10000000,
                    "luong_bhxh": 8000000,
                    "don_gia_tang_ca": 50000,
                    "muc_phat_muon": 20000,
                    "muc_thuong_kpi": 1000000,
                    "tro_cap_an_trua": 50000,
                    "tro_cap_xang_xe": 30000,
                    "phu_cap_chuc_vu": 1000000,
                    "phu_cap_co_dinh": 500000,
                })
            else:
                env["cau.hinh.luong"].create({
                                "employee_id": emp.id,
                                "luong_co_ban": 10000000,
                                "luong_bhxh": 8000000,
                                "don_gia_tang_ca": 50000,
                                "muc_phat_muon": 20000,
                                "muc_thuong_kpi": 1000000,
                                "tro_cap_an_trua": 50000,
                                "tro_cap_xang_xe": 30000,
                                "phu_cap_chuc_vu": 1000000,
                                "phu_cap_co_dinh": 500000,
                            })

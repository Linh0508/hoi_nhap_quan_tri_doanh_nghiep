from odoo import models, fields, api
from datetime import datetime


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'
    # ===== Thông tin bổ sung =====
    ma_dinh_danh = fields.Char("Mã định danh")
    que_quan = fields.Char("Quê quán")
    cccd = fields.Char("CCCD")

    # ===== Liên kết tổ chức =====
    don_vi_id = fields.Many2one("don_vi", string="Đơn vị")
    chuc_vu_id = fields.Many2one("chuc_vu", string="Chức vụ")

    tuoi = fields.Integer(compute="_compute_tuoi", store=True)
    lich_su_cong_tac_ids = fields.One2many(
        "lich_su_cong_tac",
        "nhan_vien_id",
        string="Lịch sử công tác"
    )

    danh_sach_chung_chi_bang_cap_ids = fields.One2many(
        "danh_sach_chung_chi_bang_cap",
        "nhan_vien_id",
        string="Chứng chỉ"
    )
    
    cau_hinh_luong_id = fields.One2many(
        'cau.hinh.luong',
        'employee_id',
        string="Cấu hình lương"
    )

    @api.depends('birthday')
    def _compute_tuoi(self):
        for rec in self:
            if rec.birthday:
                rec.tuoi = datetime.now().year - rec.birthday.year
            else:
                rec.tuoi = 0

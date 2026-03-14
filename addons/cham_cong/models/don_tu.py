from odoo import models, fields, api
from datetime import datetime
from odoo import api, SUPERUSER_ID
    
class DonTu(models.Model):
    _name = 'don_tu'
    _description = 'Đơn từ'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('hr.employee', string="Nhân viên", required=True)
    ngay_lam_don = fields.Date("Ngày làm đơn", required=True, default=fields.Date.today)
    ngay_ap_dung = fields.Date("Ngày áp dụng", required=True)
    
    trang_thai_duyet = fields.Selection([
        ('cho_duyet', 'Chờ duyệt'),
        ('da_duyet', 'Đã duyệt'),
        ('tu_choi', 'Từ chối')
    ], string="Trạng thái phê duyệt", default='cho_duyet', required=True)

    loai_don = fields.Selection([
        ('nghi', 'Đơn xin nghỉ'),
        ('di_muon', 'Đơn xin đi muộn'),
        ('ve_som', 'Đơn xin về sớm')
    ], string="Loại đơn", required=True)

    # Thời gian xin đi muộn/về sớm (phút)
    thoi_gian_xin = fields.Float("Thời gian xin (phút)")
    
    def init(self):
        env = api.Environment(self._cr, SUPERUSER_ID, {})

        # if env['don_tu'].search([], limit=1):
        #     return

        employees = env['hr.employee'].search([], limit=4)

        if not employees:
            return

        env['don_tu'].create({
            "nhan_vien_id": employees[0].id,
            "ngay_lam_don": "2026-02-25",
            "ngay_ap_dung": "2026-02-26",
            "loai_don": "di_muon",
            "thoi_gian_xin": 20,
            "trang_thai_duyet": "da_duyet"
        })

        env['don_tu'].create({
            "nhan_vien_id": employees[1].id,
            "ngay_lam_don": "2026-02-24",
            "ngay_ap_dung": "2026-02-25",
            "loai_don": "ve_som",
            "thoi_gian_xin": 30,
            "trang_thai_duyet": "da_duyet"
        })

        env['don_tu'].create({
            "nhan_vien_id": employees[2].id,
            "ngay_lam_don": "2026-02-25",
            "ngay_ap_dung": "2026-02-26",
            "loai_don": "nghi",
            "thoi_gian_xin": 0,
            "trang_thai_duyet": "da_duyet"
        })
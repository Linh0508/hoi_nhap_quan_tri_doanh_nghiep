from odoo import models, fields, api
from datetime import date
from odoo import api, SUPERUSER_ID
from datetime import date

class LichSuCongTac(models.Model):
    _name = "lich_su_cong_tac"
    _description = "Lịch sử công tác"
    _rec_name = "nhan_vien_id"

    nhan_vien_id = fields.Many2one(
        "hr.employee",
        string="Nhân viên",
        required=True,
        ondelete="cascade"
    )

    chuc_vu_id = fields.Many2one(
        "chuc_vu",
        string="Chức vụ",
        required=True
    )

    phong_ban_id = fields.Many2one(
        "phong_ban",
        string="Phòng ban",
        required=True
    )

    loai_chuc_vu = fields.Selection(
        [
            ("Chính", "Chính"),
            ("Kiêm nhiệm", "Kiêm nhiệm"),
        ],
        string="Loại chức vụ",
        default="Chính",
        required=True
    )

    ngay_bat_dau = fields.Date("Ngày bắt đầu", required=True)
    ngay_ket_thuc = fields.Date("Ngày kết thúc")

    trang_thai = fields.Selection(
        [
            ("Đang giữ", "Đang giữ"),
            ("Đã kết thúc", "Đã kết thúc"),
        ],
        string="Trạng thái",
        compute="_compute_trang_thai",
        store=True
    )

    @api.depends("ngay_ket_thuc")
    def _compute_trang_thai(self):
        today = date.today()
        for record in self:
            if not record.ngay_ket_thuc or record.ngay_ket_thuc >= today:
                record.trang_thai = "Đang giữ"
            else:
                record.trang_thai = "Đã kết thúc"

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        employee = env["hr.employee"].search([], limit=1)
        chuc_vu = env["chuc_vu"].search([], limit=1)
        phong_ban = env["phong_ban"].search([], limit=1)

        if employee and chuc_vu and phong_ban:

            if not env["lich_su_cong_tac"].search([("nhan_vien_id","=",employee.id)]):

                env["lich_su_cong_tac"].create({
                    "nhan_vien_id": employee.id,
                    "chuc_vu_id": chuc_vu.id,
                    "phong_ban_id": phong_ban.id,
                    "loai_chuc_vu": "Chính",
                    "ngay_bat_dau": date(2023,1,1)
                })
from odoo import models, fields
from odoo import api, SUPERUSER_ID
from datetime import date

class DanhSachChungChiBangCap(models.Model):
    _name = 'danh_sach_chung_chi_bang_cap'
    _description = 'Danh sách chứng chỉ của nhân viên'
    _rec_name = "nhan_vien_id"

    nhan_vien_id = fields.Many2one(
        "hr.employee",
        string="Nhân viên",
        required=True,
        ondelete="cascade"
    )

    chung_chi_id = fields.Many2one(
        "chung_chi_bang_cap",
        string="Tên chứng chỉ",
        required=True
    )

    loai_chung_chi = fields.Selection(
        [
            ("Bằng đại học", "Bằng đại học"),
            ("Chứng chỉ Tiếng Anh", "Chứng chỉ Tiếng Anh"),
            ("Chứng chỉ tin học văn phòng", "Chứng chỉ tin học văn phòng"),
        ],
        string="Loại chứng chỉ",
        required=True
    )

    ngay_cap = fields.Date("Ngày cấp", required=True)
    noi_cap = fields.Char("Nơi cấp")

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        employee = env["hr.employee"].search([], limit=1)
        chung_chi = env["chung_chi_bang_cap"].search([], limit=1)

        if employee and chung_chi:

            if not env["danh_sach_chung_chi_bang_cap"].search([
                ("nhan_vien_id","=",employee.id),
                ("chung_chi_id","=",chung_chi.id)
            ]):

                env["danh_sach_chung_chi_bang_cap"].create({
                    "nhan_vien_id": employee.id,
                    "chung_chi_id": chung_chi.id,
                    "loai_chung_chi": "Bằng đại học",
                    "ngay_cap": date(2022,6,1),
                    "noi_cap": "ĐH Cần Thơ"
                })
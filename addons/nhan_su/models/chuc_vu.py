from odoo import models, fields
from odoo import api, SUPERUSER_ID


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Bảng chứa thông tin chức vụ'
    _rec_name = 'ten_chuc_vu'

    ma_chuc_vu = fields.Char("Mã chức vụ", required=True)
    ten_chuc_vu = fields.Char("Tên chức vụ", required=True)

    employee_ids = fields.One2many(
        'hr.employee',
        'chuc_vu_id',
        string="Nhân viên"
    )

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        demo_data = [
            {"ma_chuc_vu": "CV01", "ten_chuc_vu": "Developer"},
            {"ma_chuc_vu": "CV02", "ten_chuc_vu": "Tester"},
            {"ma_chuc_vu": "CV03", "ten_chuc_vu": "Team Leader"},
            {"ma_chuc_vu": "CV04", "ten_chuc_vu": "Manager"},
        ]

        for d in demo_data:
            if not env["chuc_vu"].search([("ma_chuc_vu", "=", d["ma_chuc_vu"])]):
                env["chuc_vu"].create(d)
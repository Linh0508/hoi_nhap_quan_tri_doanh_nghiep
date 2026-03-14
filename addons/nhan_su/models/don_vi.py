from odoo import models, fields
from odoo import api, SUPERUSER_ID

class DonVi(models.Model):
    _name = 'don_vi'
    _description = 'Bảng chứa thông tin đơn vị'
    _rec_name = 'ten_don_vi'

    ma_don_vi = fields.Char("Mã đơn vị", required=True)
    ten_don_vi = fields.Char("Tên đơn vị", required=True)

    employee_ids = fields.One2many(
        'hr.employee',
        'don_vi_id',
        string="Nhân viên"
    )

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        demo_data = [
            {"ma_don_vi": "DV01", "ten_don_vi": "Khối Công nghệ"},
            {"ma_don_vi": "DV02", "ten_don_vi": "Khối Kinh doanh"},
            {"ma_don_vi": "DV03", "ten_don_vi": "Khối Hành chính"},
        ]

        for d in demo_data:
            if not env["don_vi"].search([("ma_don_vi", "=", d["ma_don_vi"])]):
                env["don_vi"].create(d)
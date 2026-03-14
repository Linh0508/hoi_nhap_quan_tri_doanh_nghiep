from odoo import models, fields
from odoo import api, SUPERUSER_ID

class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Bảng chứa thông tin chứng chỉ bằng cấp'
    _rec_name = 'ten_chung_chi'

    ma_chung_chi = fields.Char("Mã chứng chỉ", required=True)
    ten_chung_chi = fields.Char("Tên chứng chỉ", required=True)

    def init(self):
        
        env = api.Environment(self._cr, SUPERUSER_ID, {})

        demo_data = [
            {"ma_chung_chi": "CC01", "ten_chung_chi": "Cử nhân CNTT"},
            {"ma_chung_chi": "CC02", "ten_chung_chi": "IELTS 6.5"},
            {"ma_chung_chi": "CC03", "ten_chung_chi": "MOS Excel"},
            {"ma_chung_chi": "CC04", "ten_chung_chi": "AWS Certified"},
        ]

        for d in demo_data:
            if not env["chung_chi_bang_cap"].search([("ma_chung_chi", "=", d["ma_chung_chi"])]):
                env["chung_chi_bang_cap"].create(d)
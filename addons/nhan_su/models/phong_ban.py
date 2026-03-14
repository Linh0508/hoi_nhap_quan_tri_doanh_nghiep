from odoo import models, fields
from odoo import api, SUPERUSER_ID

class PhongBan(models.Model):
    _name = 'phong_ban'
    _description = 'Bảng chứa thông tin phòng ban'
    _rec_name = 'ten_phong_ban'

    ma_phong_ban = fields.Char("Mã phòng ban", required=True)
    ten_phong_ban = fields.Char("Tên phòng ban", required=True)

    def init(self):

        env = api.Environment(self._cr, SUPERUSER_ID, {})

        demo_data = [
            {"ma_phong_ban": "PB01", "ten_phong_ban": "Phòng Backend"},
            {"ma_phong_ban": "PB02", "ten_phong_ban": "Phòng Frontend"},
            {"ma_phong_ban": "PB03", "ten_phong_ban": "Phòng QA"},
            {"ma_phong_ban": "PB04", "ten_phong_ban": "Phòng Nhân sự"},
        ]

        for d in demo_data:
            if not env["phong_ban"].search([("ma_phong_ban", "=", d["ma_phong_ban"])]):
                env["phong_ban"].create(d)
from odoo import models, fields, api

class PayrollSetting(models.Model):
    _name = 'payroll.setting'
    _description = 'Cấu hình thuế và BHXH'
    _sql_constraints = [
        ('unique_setting', 'CHECK (id = 1)', 'Chỉ được có 1 cấu hình!')
    ]

    ty_le_bhxh_nv = fields.Float(string="Tỷ lệ BHXH NV", default=0.105)
    muc_giam_tru_ban_than = fields.Float(default=11000000)
    ty_le_thue = fields.Float(default=0.05)

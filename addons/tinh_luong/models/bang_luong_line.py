from odoo import models, fields


class BangLuongLine(models.Model):
    _name = 'tinh.luong.line'
    _description = 'Dòng lương chi tiết'

    bang_luong_id = fields.Many2one(
        'tinh.luong.bang.luong',
        string="Bảng lương",
        ondelete='cascade'
    )

    name = fields.Char("Diễn giải", required=True)

    line_type = fields.Selection([
        ('income', 'Thu nhập'),
        ('deduction', 'Khấu trừ')
    ], required=True)

    amount = fields.Float("Số tiền", required=True)

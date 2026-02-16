from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
import calendar

class BangLuong(models.Model):
    _name = 'tinh.luong.bang.luong'
    _description = 'Bảng tính lương'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ma_dinh_danh'

    ma_dinh_danh = fields.Many2one(
        'hr.employee',
        string="Nhân viên",
        required=True,
        states={'draft': [('readonly', False)]},
        readonly=True
    )

    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string="Tháng",
        default=lambda self: str(date.today().month),
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    nam = fields.Integer(
        "Năm",
        default=lambda self: date.today().year,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Hủy bỏ'),
    ], string="Trạng thái", default='draft', tracking=True)

    line_ids = fields.One2many(
        'tinh.luong.line',
        'bang_luong_id',
        string="Chi tiết lương"
    )

    # tong_nhan = fields.Float(
    #     string="Thực lĩnh",
    #     compute="_compute_total",
    #     store=True
    # )

    so_lan_muon = fields.Integer(
        compute="_compute_attendance",
        store=True
    )

    ngay_cong_chuan = fields.Integer(string="Công chuẩn", compute="_compute_attendance", store=True)
    so_cong_thuc_te = fields.Integer(string="Công thực tế", compute="_compute_attendance", store=True)
    so_ngay_huong_phu_cap = fields.Integer(string="Ngày đi làm", compute="_compute_attendance", store=True)
    so_gio_tang_ca = fields.Float(string="Giờ tăng ca", compute="_compute_attendance", store=True)

    tong_thu_nhap = fields.Float(
        string="Tổng thu nhập",
        compute="_compute_totals",
        store=True
    )

    tong_khau_tru = fields.Float(
        string="Tổng khấu trừ",
        compute="_compute_totals",
        store=True
    )

    luong_net = fields.Float(
        string="Lương thực lĩnh",
        compute="_compute_totals",
        store=True
    )

    tien_tang_ca = fields.Float(string="Tiền tăng ca", compute="_compute_breakdown", store=True)
    tien_an_trua = fields.Float(string="Tiền ăn trưa", compute="_compute_breakdown", store=True)
    tien_xang_xe = fields.Float(string="Tiền xăng xe", compute="_compute_breakdown", store=True)
    tien_thuong_kpi = fields.Float(string="Thưởng KPI", compute="_compute_breakdown", store=True)
    tien_phat_muon = fields.Float(string="Phạt đi muộn", compute="_compute_breakdown", store=True)
    bhxh_nv = fields.Float(string="BHXH nhân viên", compute="_compute_breakdown", store=True)
    thue_tncn = fields.Float(string="Thuế TNCN", compute="_compute_breakdown", store=True)

    @api.depends('line_ids.amount', 'line_ids.line_type')
    def _compute_totals(self):
        for rec in self:
            thu = sum(l.amount for l in rec.line_ids if l.line_type == 'income')
            tru = sum(l.amount for l in rec.line_ids if l.line_type == 'deduction')

            rec.tong_thu_nhap = thu
            rec.tong_khau_tru = tru
            rec.luong_net = thu - tru

    @api.depends('line_ids.amount', 'line_ids.name')
    def _compute_breakdown(self):
        for rec in self:
            rec.tien_tang_ca = 0
            rec.tien_an_trua = 0
            rec.tien_xang_xe = 0
            rec.tien_thuong_kpi = 0
            rec.tien_phat_muon = 0
            rec.bhxh_nv = 0
            rec.thue_tncn = 0

            for line in rec.line_ids:
                if line.name == "Tiền tăng ca":
                    rec.tien_tang_ca += line.amount
                elif line.name == "Tiền ăn trưa":
                    rec.tien_an_trua += line.amount
                elif line.name == "Tiền xăng xe":
                    rec.tien_xang_xe += line.amount
                elif line.name == "Thưởng KPI":
                    rec.tien_thuong_kpi += line.amount
                elif line.name == "Phạt đi muộn":
                    rec.tien_phat_muon += line.amount
                elif line.name == "BHXH nhân viên":
                    rec.bhxh_nv += line.amount
                elif line.name == "Thuế TNCN":
                    rec.thue_tncn += line.amount

    @api.depends('ma_dinh_danh', 'thang', 'nam')
    def _compute_attendance(self):
        for rec in self:
            rec.ngay_cong_chuan = 0
            rec.so_cong_thuc_te = 0
            rec.so_ngay_huong_phu_cap = 0
            rec.so_gio_tang_ca = 0  

            if not rec.ma_dinh_danh:
                continue

            _, days_in_month = calendar.monthrange(rec.nam, int(rec.thang))

            cong_chuan = 0
            for d in range(1, days_in_month + 1):
                if date(rec.nam, int(rec.thang), d).weekday() < 5:
                    cong_chuan += 1

            rec.ngay_cong_chuan = cong_chuan

            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days_in_month)

            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                ('ngay_cham_cong', '>=', first_day),
                ('ngay_cham_cong', '<=', last_day)
            ])

            rec.so_lan_muon = len(
                records_cc.filtered(lambda r: r.phut_di_muon > 0)
            )
            ngay_di_lam = len(records_cc.filtered(lambda r: r.loai_ngay_cong == 'di_lam'))
            ngay_nghi_phep = len(records_cc.filtered(lambda r: r.loai_ngay_cong == 'nghi_phep'))

            rec.so_cong_thuc_te = ngay_di_lam + ngay_nghi_phep
            rec.so_ngay_huong_phu_cap = ngay_di_lam
            rec.so_gio_tang_ca = sum(records_cc.mapped('so_gio_tang_ca'))

    def action_compute_salary(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Chỉ tính lương khi ở trạng thái Nháp!")

            if not rec.ma_dinh_danh:
                raise UserError("Chưa chọn nhân viên!")

            rec.line_ids.unlink()

            config = rec.ma_dinh_danh.cau_hinh_luong_id[:1]
            if not config:
                raise UserError("Nhân viên chưa có cấu hình lương!")
            config = config[0]

            setting = self.env['payroll.setting'].search([], limit=1)
            if not setting:
                raise UserError("Chưa cấu hình Payroll Setting!")

            if rec.ngay_cong_chuan > 0:
                luong_thoi_gian = (
                    config.luong_co_ban / rec.ngay_cong_chuan
                ) * rec.so_cong_thuc_te
            else:
                luong_thoi_gian = 0

            tien_an_trua = config.tro_cap_an_trua * rec.so_ngay_huong_phu_cap
            tien_xang_xe = config.tro_cap_xang_xe
            phu_cap_chuc_vu = config.phu_cap_chuc_vu
            phu_cap_co_dinh = config.phu_cap_co_dinh

            tien_tang_ca = rec.so_gio_tang_ca * config.don_gia_tang_ca

            kpi_record = self.env['kpi.danh.gia'].search([
                ('ma_dinh_danh', '=', rec.ma_dinh_danh.id),
                ('thang', '=', rec.thang),
                ('nam', '=', rec.nam)
            ], limit=1)

            tien_kpi = kpi_record.tien_thuong if kpi_record else 0
            tien_phat = rec.so_lan_muon * config.muc_phat_muon

            def add_line(name, amount, ltype):
                if amount:
                    self.env['tinh.luong.line'].create({
                        'bang_luong_id': rec.id,
                        'name': name,
                        'amount': amount,
                        'line_type': ltype
                    })

            add_line("Lương thời gian", luong_thoi_gian, 'income')
            add_line("Phụ cấp chức vụ", phu_cap_chuc_vu, 'income')
            add_line("Phụ cấp cố định", phu_cap_co_dinh, 'income')
            add_line("Tiền tăng ca", tien_tang_ca, 'income')
            add_line("Tiền ăn trưa", tien_an_trua, 'income')
            add_line("Tiền xăng xe", tien_xang_xe, 'income')
            add_line("Thưởng KPI", tien_kpi, 'income')

            tong_thu = sum(
                l.amount for l in rec.line_ids if l.type == 'income'
            )

            bhxh = config.luong_bhxh * setting.ty_le_bhxh_nv

            thu_nhap_chiu_thue = tong_thu - bhxh
            thue = max(
                0,
                (thu_nhap_chiu_thue - setting.muc_giam_tru_ban_than)
                * setting.ty_le_thue
            )

            add_line("Phạt đi muộn", tien_phat, 'deduction')
            add_line("BHXH nhân viên", bhxh, 'deduction')
            add_line("Thuế TNCN", thue, 'deduction')

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError("Bạn phải tính lương trước khi xác nhận!")

            _, days = calendar.monthrange(rec.nam, int(rec.thang))
            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days)

            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                ('ngay_cham_cong', '>=', first_day),
                ('ngay_cham_cong', '<=', last_day)
            ])

            records_cc.write({'is_locked': True})

            rec.state = 'confirmed'

    def action_pay(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Chỉ có thể xóa khi ở trạng thái Nháp!")
        return super().unlink()

    # ================== THÊM: KHÓA SỬA SAU CONFIRM ==================
    def write(self, vals):
        for rec in self:
            if rec.state in ['confirmed', 'paid'] and not self.env.user.has_group('base.group_system'):
                raise UserError("Chỉ Admin mới được chỉnh sửa khi đã xác nhận!")
        return super().write(vals)

    # ================== THÊM: GỬI EMAIL ==================
    def action_send_email(self):
        template = self.env.ref('tinh_luong.email_template_payroll')
        template.send_mail(self.id, force_send=True)

    # ================== THÊM: AUTO TẠO LƯƠNG THÁNG TRƯỚC ==================
    @api.model
    def cron_auto_create_payroll(self):
        today = date.today()
        thang = today.month - 1 or 12
        nam = today.year if today.month != 1 else today.year - 1

        employees = self.env['hr.employee'].search([])

        for emp in employees:
            exists = self.search([
                ('ma_dinh_danh', '=', emp.id),
                ('thang', '=', str(thang)),
                ('nam', '=', nam)
            ], limit=1)

            if not exists:
                self.create({
                    'ma_dinh_danh': emp.id,
                    'thang': str(thang),
                    'nam': nam
                })

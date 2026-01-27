from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, datetime
import calendar

class KPIDanhGia(models.Model):
    _name = 'kpi.danh.gia'
    _inherit = ['mail.thread']
    _description = 'KPI tự động theo chuyên cần'
    _order = 'nam desc, thang desc'
    _rec_name = 'ma_dinh_danh'

    ma_dinh_danh = fields.Many2one('nhan_vien', string="Nhân viên", required=True, tracking=True)
    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string="Tháng", default=lambda self: str(date.today().month), required=True, tracking=True)
    nam = fields.Integer("Năm", default=lambda self: date.today().year, tracking=True)
    
    # Thêm trường này vào DB
    state = fields.Selection([
        ('draft', 'Mới'), 
        ('done', 'Hoàn tất')
    ], default='draft', string="Trạng thái", tracking=True)

    # Đảm bảo store=True và đúng kiểu dữ liệu
    diem_kpi = fields.Float("Điểm KPI (%)", compute="_compute_kpi_tu_dong", store=True, group_operator="avg")
    tien_thuong = fields.Float(string="Tiền thưởng thực tế", compute="_compute_kpi_tu_dong", store=True, group_operator="sum")

    @api.depends('ma_dinh_danh', 'thang', 'nam')
    def _compute_kpi_tu_dong(self):
        for rec in self:
            # Khởi tạo giá trị mặc định để tránh lỗi rỗng
            rec.diem_kpi = 0.0
            rec.tien_thuong = 0.0
            
            if not rec.ma_dinh_danh or not rec.thang or not rec.nam:
                continue
                
            try:
                # 1. Tính ngày công chuẩn (Chỉ tính T2-T6)
                thang_int = int(rec.thang)
                _, days_in_month = calendar.monthrange(rec.nam, thang_int)
                cong_chuan = 0
                for d in range(1, days_in_month + 1):
                    if date(rec.nam, thang_int, d).weekday() < 5:
                        cong_chuan += 1
                
                if cong_chuan == 0: continue

                # 2. Lấy số công thực tế (Lọc chính xác theo nhan_vien_id và khoảng ngày)
                date_start = date(rec.nam, thang_int, 1)
                date_end = date(rec.nam, thang_int, days_in_month)
                
                # Sửa lỗi logic: Đếm số bản ghi chấm công HỢP LỆ (không vắng mặt)
                cc_records = self.env['bang_cham_cong'].search_count([
                    ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                    ('ngay_cham_cong', '>=', date_start),
                    ('ngay_cham_cong', '<=', date_end),
                    ('trang_thai', 'in', ['di_lam', 'muon', 've_som']) # Chỉ tính những ngày có mặt
                ])
                
                # 3. Tính % KPI (Giới hạn tối đa 100%)
                tinh_diem = (cc_records / cong_chuan) * 100
                rec.diem_kpi = min(tinh_diem, 100.0)
                
                # 4. Tính thưởng dựa trên thuong_kpi_dinh_muc của model nhan_vien
                rec.tien_thuong = (rec.diem_kpi / 100.0) * rec.ma_dinh_danh.thuong_kpi_dinh_muc
            except Exception as e:
                rec.diem_kpi = 0.0
                rec.tien_thuong = 0.0

    def action_init_kpi_records(self):
        """Khởi tạo danh sách KPI cho tháng hiện tại"""
        current_thang = str(date.today().month)
        current_nam = date.today().year
        nhan_viens = self.env['nhan_vien'].search([])
        for nv in nhan_viens:
            exists = self.search([
                ('ma_dinh_danh', '=', nv.id),
                ('thang', '=', current_thang),
                ('nam', '=', current_nam)
            ])
            if not exists:
                self.create({
                    'ma_dinh_danh': nv.id,
                    'thang': current_thang,
                    'nam': current_nam,
                    'state': 'draft'
                })
        return { 'type': 'ir.actions.client', 'tag': 'reload' }

    def action_recompute_kpi(self):
        """Tính toán lại cho các bản ghi đang chọn"""
        self._compute_kpi_tu_dong()
        return True
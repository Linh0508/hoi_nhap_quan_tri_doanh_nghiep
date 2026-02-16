from odoo import models, fields, api
from odoo.exceptions import ValidationError

class DangKyCaLamTheoNgay(models.Model):
    _name = 'dang_ky_ca_lam_theo_ngay'
    _description = "Đăng ký ca làm theo ngày"
    _rec_name = 'ma_dot_ngay'
    _order = 'dot_dang_ky_id desc, ngay_lam asc'

    ma_dot_ngay = fields.Char("Mã đợt ngày", required=True)
    dot_dang_ky_id = fields.Many2one('dot_dang_ky', string="Đợt đăng ký", required=True)
    nhan_vien_id = fields.Many2one('hr.employee', string="Nhân viên", required=True)
    ngay_lam = fields.Date(string="Ngày làm", required=True)
    ca_lam = fields.Selection([
        ("Sáng", "Sáng"),
        ("Chiều", "Chiều"),
        ("Cả ngày", "Cả Ngày"),
    ], string="Ca làm", required=True) # Bỏ option trống nếu muốn bắt buộc tạo chấm công

    # --- Ràng buộc (Constraints) ---
    @api.constrains('ngay_lam', 'dot_dang_ky_id')
    def _check_ngay_lam(self):
        for record in self:
            if record.ngay_lam and record.dot_dang_ky_id:
                start = record.dot_dang_ky_id.ngay_bat_dau
                end = record.dot_dang_ky_id.ngay_ket_thuc
                if record.ngay_lam < start or record.ngay_lam > end:
                    raise ValidationError(f'Ngày làm phải nằm trong khoảng từ {start} đến {end}')

    @api.constrains('nhan_vien_id', 'dot_dang_ky_id')
    def _check_nhan_vien_in_dot_dang_ky(self):
        for record in self:
            if record.nhan_vien_id not in record.dot_dang_ky_id.nhan_vien_ids:
                raise ValidationError(f'Nhân viên {record.nhan_vien_id.ho_va_ten} không thuộc đợt đăng ký này!')

    # --- Tự động hóa tạo Bảng chấm công ---
    @api.model_create_multi
    def create(self, vals_list):
        records = super(DangKyCaLamTheoNgay, self).create(vals_list)
        for record in records:
            record._upsert_bang_cham_cong()
        return records

    def write(self, vals):
        res = super(DangKyCaLamTheoNgay, self).write(vals)
        if any(field in vals for field in ['ngay_lam', 'ca_lam', 'nhan_vien_id']):
            for record in self:
                record._upsert_bang_cham_cong()
        return res

    def _upsert_bang_cham_cong(self):
        """Hàm hỗ trợ tạo hoặc cập nhật bảng chấm công"""
        self.ensure_one()
        # Định nghĩa giờ theo ca làm (Có thể điều chỉnh logic lấy từ cấu hình hệ thống)
        times = {
            'Sáng': {'gio_vao': 8.0, 'gio_ra': 12.0},
            'Chiều': {'gio_vao': 13.0, 'gio_ra': 17.0},
            'Cả ngày': {'gio_vao': 8.0, 'gio_ra': 17.0},
        }
        
        ca_info = times.get(self.ca_lam, {'gio_vao': 0.0, 'gio_ra': 0.0})
        
        # Tìm xem đã có bảng chấm công cho ngày này/nhân viên này chưa
        attendance_model = self.env['bang_cham_cong']
        existing = attendance_model.search([
            ('nhan_vien_id', '=', self.nhan_vien_id.id),
            ('ngay_cham_cong', '=', self.ngay_lam)
        ], limit=1)

        vals = {
            'nhan_vien_id': self.nhan_vien_id.id,
            'ngay_cham_cong': self.ngay_lam,
            'dang_ky_ca_lam_id': self.id # Để liên kết ngược lại nếu cần
        }

        if existing:
            existing.write(vals)
        else:
            attendance_model.create(vals) 
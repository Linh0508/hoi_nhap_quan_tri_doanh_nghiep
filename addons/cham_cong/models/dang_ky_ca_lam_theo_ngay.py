from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo import api, SUPERUSER_ID
from datetime import date, timedelta
            
class DangKyCaLamTheoNgay(models.Model):
    _name = 'dang_ky_ca_lam_theo_ngay'
    _description = "Đăng ký ca làm theo ngày"
    _rec_name = 'ma_dot_ngay'
    _order = 'dot_dang_ky_id desc, ngay_lam asc'
    _sql_constraints = [
        (
            'unique_work_day',
            'unique(dot_dang_ky_id, nhan_vien_id, ngay_lam)',
            'Nhân viên đã có đăng ký ca ngày này!'
        )
    ]
    
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
                raise ValidationError(f'Nhân viên {record.nhan_vien_id.name} không thuộc đợt đăng ký này!')

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
            'Sáng': {'gio_vao': 7.5, 'gio_ra': 11.5},
            'Chiều': {'gio_vao': 13.5, 'gio_ra': 17.5},
            'Cả ngày': {'gio_vao': 7.5, 'gio_ra': 17.5},
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
                
    @api.model
    def _seed_data(self, dot):

        employees = dot.nhan_vien_ids

        if not employees:
            return

        start = dot.ngay_bat_dau
        end = dot.ngay_ket_thuc - timedelta(days=3)  # gần cuối tháng

        days = []
        d = start
        while d <= end:
            days.append(d)
            d += timedelta(days=1)

        ca_patterns = ["Cả ngày", "Sáng", "Chiều"]

        for i, emp in enumerate(employees):

            for j, day in enumerate(days):

                existing = self.search([
                    ('dot_dang_ky_id','=',dot.id),
                    ('nhan_vien_id','=',emp.id),
                    ('ngay_lam','=',day)
                ], limit=1)

                if not existing:
                    self.create({
                        "ma_dot_ngay": f"{dot.ma_dot}_{emp.id}_{day}",
                        "dot_dang_ky_id": dot.id,
                        "nhan_vien_id": emp.id,
                        "ngay_lam": day,
                        "ca_lam": ca_patterns[(i+j) % 3]
                    })
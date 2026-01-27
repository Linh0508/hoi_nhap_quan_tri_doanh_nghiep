from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
import calendar

class BangLuong(models.Model):
    _name = 'tinh.luong.bang.luong'
    _description = 'Bảng tính lương'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Thêm log trao đổi
    _rec_name = 'ma_dinh_danh'

    ma_dinh_danh = fields.Many2one('nhan_vien', string="Nhân viên", required=True, states={'draft': [('readonly', False)]}, readonly=True)
    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string="Tháng", default=lambda self: str(date.today().month), required=True, readonly=True, states={'draft': [('readonly', False)]})
    nam = fields.Integer("Năm", default=lambda self: date.today().year, readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('paid', 'Đã thanh toán'),
        ('cancel', 'Hủy bỏ'),
    ], string="Trạng thái", default='draft', tracking=True)

    # --- DỮ LIỆU TÍNH TOÁN ---
    ngay_cong_chuan = fields.Integer(string="Công chuẩn", compute="_compute_all_data", store=True)
    so_cong_thuc_te = fields.Float(string="Công thực tế", compute="_compute_all_data", store=True)
    luong_thoi_gian = fields.Float(string="Lương thời gian", compute="_compute_all_data", store=True)
    tien_phat_muon = fields.Float(string="Tiền phạt", compute="_compute_all_data", store=True)
    tien_thuong_kpi = fields.Float(string="Thưởng KPI", compute="_compute_all_data", store=True)
    bhxh_nv = fields.Float(string="BHXH (10.5%)", compute="_compute_all_data", store=True)
    thue_tncn = fields.Float(string="Thuế TNCN", compute="_compute_all_data", store=True)
    tong_nhan = fields.Float(string="Thực lĩnh", compute="_compute_all_data", store=True)
    phieu_luong_html = fields.Html(string="Phiếu lương chi tiết", compute="_compute_html_preview")

    # --- HÀM XỬ LÝ TRẠNG THÁI ---
    def action_confirm(self):
        for rec in self:
            if rec.tong_nhan <= 0:
                raise UserError("Lương thực lĩnh phải lớn hơn 0 để xác nhận!")
            rec.state = 'confirmed'

    def action_pay(self):
        self.write({'state': 'paid'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    # Khóa không cho xóa nếu không phải bản nháp
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError("Chỉ có thể xóa bảng lương ở trạng thái Nháp!")
        return super(BangLuong, self).unlink()

    # Thêm các field mới phục vụ hiển thị
    so_ngay_huong_phu_cap = fields.Integer("Số ngày hưởng phụ cấp", compute="_compute_all_data", store=True)
    tien_tang_ca = fields.Float("Tiền tăng ca", compute="_compute_all_data", store=True)
    so_gio_tang_ca = fields.Float("Tổng giờ tăng ca", compute="_compute_all_data", store=True)
    tien_an_trua = fields.Float(string="Phụ cấp ăn trưa", compute="_compute_all_data", store=True)
    tien_xang_xe = fields.Float(string="Phụ cấp xăng xe", compute="_compute_all_data", store=True)

    @api.depends('ma_dinh_danh', 'thang', 'nam')
    def _compute_all_data(self):
        for rec in self:
            if not rec.ma_dinh_danh or not rec.thang: continue
            
            # 1. Tính công chuẩn (như cũ)
            _, days_in_month = calendar.monthrange(rec.nam, int(rec.thang))
            first_day = date(rec.nam, int(rec.thang), 1)
            last_day = date(rec.nam, int(rec.thang), days_in_month)
            
            work_days_standard = 0
            for day in range(1, days_in_month + 1):
                if date(rec.nam, int(rec.thang), day).weekday() < 5: work_days_standard += 1
            rec.ngay_cong_chuan = work_days_standard

            # 2. Lấy dữ liệu chấm công
            records_cc = self.env['bang_cham_cong'].search([
                ('nhan_vien_id', '=', rec.ma_dinh_danh.id),
                ('ngay_cham_cong', '>=', first_day),
                ('ngay_cham_cong', '<=', last_day)
            ])

            # Phân loại công để tính lương
            ngay_di_lam = len(records_cc.filtered(lambda r: r.loai_ngay_cong == 'di_lam'))
            ngay_nghi_phep = len(records_cc.filtered(lambda r: r.loai_ngay_cong == 'nghi_phep'))
            
            # Công thực tế = Đi làm + Nghỉ phép hưởng lương
            rec.so_cong_thuc_te = ngay_di_lam + ngay_nghi_phep
            rec.so_ngay_huong_phu_cap = ngay_di_lam # Chỉ ăn trưa/xăng xe khi thực tế có mặt

            # 3. Tính Lương Thời Gian
            if rec.ngay_cong_chuan > 0:
                rec.luong_thoi_gian = (rec.ma_dinh_danh.luong_co_ban / rec.ngay_cong_chuan) * rec.so_cong_thuc_te

            # 4. Tính Tăng Ca (Giả sử hệ số x1.5)
            rec.so_gio_tang_ca = sum(records_cc.mapped('so_gio_tang_ca'))
            luong_gio = (rec.ma_dinh_danh.luong_co_ban / rec.ngay_cong_chuan / 8) if rec.ngay_cong_chuan > 0 else 0
            rec.tien_tang_ca = rec.so_gio_tang_ca * luong_gio * 1.5

            # 5. Phụ cấp theo ngày công thực tế (Conditional Allowances)
            # Giả sử đơn giá phụ cấp lưu ở hồ sơ nhân viên
            don_gia_an = rec.ma_dinh_danh.phu_cap_an_trua_theo_ngay or 30000
            don_gia_xang = rec.ma_dinh_danh.phu_cap_xang_xe_theo_ngay or 15000
            
            tien_an = rec.so_ngay_huong_phu_cap * don_gia_an
            tien_xang = rec.so_ngay_huong_phu_cap * don_gia_xang

            # 6. Các khoản khấu trừ & Thuế (như cũ)
            muon = sum(records_cc.mapped('phut_di_muon'))
            som = sum(records_cc.mapped('phut_ve_som'))
            rec.tien_phat_muon = (muon + som) * rec.ma_dinh_danh.don_gia_phat_muon

            rec.bhxh_nv = (rec.ma_dinh_danh.luong_bhxh or 0) * 0.105
            
            # Thưởng KPI
            kpi_record = self.env['kpi.danh.gia'].search([
                ('ma_dinh_danh', '=', rec.ma_dinh_danh.id),
                ('thang', '=', rec.thang),
                ('nam', '=', rec.nam)
            ], limit=1)
            rec.tien_thuong_kpi = kpi_record.tien_thuong if kpi_record else 0.0

            # Tổng lĩnh
            thu_nhap_chiu_thue = rec.luong_thoi_gian + rec.tien_tang_ca + rec.tien_thuong_kpi
            # (Tính thuế TNCN rút gọn)
            rec.thue_tncn = max(0, (thu_nhap_chiu_thue - rec.bhxh_nv - 11000000) * 0.05)
            
            rec.tong_nhan = (thu_nhap_chiu_thue + tien_an + tien_xang) - (rec.tien_phat_muon + rec.bhxh_nv + rec.thue_tncn)

    def _compute_html_preview(self):
        for rec in self:
            def fmt(val): return "{:,.0f}".format(val or 0)
            
            # Tính toán các chỉ số hiển thị
            tyle_cong = (rec.so_cong_thuc_te / rec.ngay_cong_chuan * 100) if rec.ngay_cong_chuan > 0 else 0
            
            # Lấy thông tin đơn giá từ nhân viên (Sử dụng đơn giá theo ngày)
            tien_an = rec.tien_an_trua
            tien_xang = rec.tien_xang_xe

            rec.phieu_luong_html = f"""
                <div style="font-family: 'Segoe UI', Arial; border: 1px solid #e0e0e0; padding: 25px; background: #ffffff; border-radius: 8px; max-width: 600px; margin: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h2 style="text-align: center; color: #714B67; margin-bottom: 5px;">PHIẾU LƯƠNG CHI TIẾT</h2>
                    <p style="text-align: center; color: #666; margin-top: 0;">Tháng {rec.thang}/{rec.nam} - <b>{dict(self._fields['state'].selection).get(rec.state)}</b></p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;"/>
                    
                    <div style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <strong>Chuyên cần: {rec.so_cong_thuc_te}/{rec.ngay_cong_chuan} ngày</strong>
                            <span>{fmt(tyle_cong)}%</span>
                        </div>
                        <div style="width: 100%; background: #f0f0f0; height: 8px; border-radius: 4px;">
                            <div style="width: {tyle_cong}%; background: #714B67; height: 8px; border-radius: 4px;"></div>
                        </div>
                    </div>

                    <table style="width: 100%; border-collapse: collapse; line-height: 2;">
                        <tr><td colspan="2" style="background: #f9f9f9; padding-left: 10px;"><strong>I. CÁC KHOẢN THU NHẬP</strong></td></tr>
                        <tr><td style="padding-left: 20px;">Lương thời gian ({rec.so_cong_thuc_te} ngày)</td><td align="right">{fmt(rec.luong_thoi_gian)}</td></tr>
                        <tr style="color: #28a745;"><td style="padding-left: 20px;">Lương tăng ca ({rec.so_gio_tang_ca}h)</td><td align="right">+{fmt(rec.tien_tang_ca)}</td></tr>
                        <tr><td style="padding-left: 20px;">Phụ cấp ăn trưa ({rec.so_ngay_huong_phu_cap} ngày)</td><td align="right">{fmt(tien_an)}</td></tr>
                        <tr><td style="padding-left: 20px;">Phụ cấp xăng xe ({rec.so_ngay_huong_phu_cap} ngày)</td><td align="right">{fmt(tien_xang)}</td></tr>
                        <tr style="color: #28a745;"><td style="padding-left: 20px;">Thưởng KPI</td><td align="right">+{fmt(rec.tien_thuong_kpi)}</td></tr>
                        
                        <tr><td colspan="2" style="background: #f9f9f9; padding-left: 10px;"><strong>II. CÁC KHOẢN KHẤU TRỪ</strong></td></tr>
                        <tr style="color: #dc3545;"><td style="padding-left: 20px;">Phạt đi muộn/về sớm</td><td align="right">-{fmt(rec.tien_phat_muon)}</td></tr>
                        <tr style="color: #dc3545;"><td style="padding-left: 20px;">Bảo hiểm xã hội (10.5%)</td><td align="right">-{fmt(rec.bhxh_nv)}</td></tr>
                        <tr style="color: #dc3545;"><td style="padding-left: 20px;">Thuế TNCN</td><td align="right">-{fmt(rec.thue_tncn)}</td></tr>
                    </table>

                    <div style="background: #714B67; color: #fff; padding: 15px; margin-top: 25px; border-radius: 5px; font-size: 1.3em; display: flex; justify-content: space-between;">
                        <span>THỰC LĨNH:</span>
                        <strong>{fmt(rec.tong_nhan)} VNĐ</strong>
                    </div>
                    <p style="font-size: 0.8em; color: #999; text-align: italic; margin-top: 10px;">* Lưu ý: Mọi thắc mắc vui lòng liên hệ phòng nhân sự trước ngày 05 hàng tháng.</p>
                </div>
            """

    def action_view_payslip_dialog(self):
        self.ensure_one()
        return {
            'name': 'Xem Phiếu Lương',
            'type': 'ir.actions.act_window',
            'res_model': 'tinh.luong.bang.luong',
            'view_mode': 'form',
            'view_id': self.env.ref('tinh_luong.view_bang_luong_popup_form').id,
            'res_id': self.id,
            'target': 'new',
        }

    def action_send_telegram(self):
        # Placeholder cho Telegram API
        return True

    
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Cấu hình trang
st.set_page_config(
    page_title="Quản lý Workflow CDHA",
    page_icon="📋",
    layout="wide"
)

st.title("📋 PHẦN MỀM QUẢN LÝ WORKFLOW & THỜI GIAN TRẢ KẾT QUẢ CHẨN ĐOÁN HÌNH ẢNH")

DB_NAME = "quanly_workflow_cdha.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS studies (
        id INTEGER PRIMARY KEY,
        ma_yeu_cau TEXT UNIQUE,
        ma_benh_nhan TEXT,
        ten_benh_nhan TEXT,
        loai_hinh_anh TEXT,
        bac_si_chi_dinh TEXT,
        ky_thuat_vien TEXT,
        thoi_gian_bat_dau_chup TEXT,
        thoi_gian_ket_thuc_chup TEXT,
        thoi_gian_hen_tra TEXT,
        thoi_gian_tra_thuc_te TEXT,
        bac_si_doc TEXT,
        trang_thai TEXT DEFAULT 'Chờ chụp',
        ghi_chu TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ====================== MENU SIDEBAR ======================
menu = st.sidebar.selectbox(
    "Chọn chức năng",
    ["📋 Danh sách yêu cầu", 
     "➕ Thêm yêu cầu mới", 
     "🔄 Cập nhật trạng thái", 
     "📊 Thống kê & Trễ hạn"]
)

# ====================== THÊM YÊU CẦU MỚI ======================
if menu == "➕ Thêm yêu cầu mới":
    st.subheader("Thêm yêu cầu chẩn đoán hình ảnh mới")
    
    col1, col2 = st.columns(2)
    with col1:
        ma_yeu_cau = st.text_input("Mã yêu cầu *", placeholder="CDHA20260329001")
        ma_bn = st.text_input("Mã bệnh nhân")
        ten_bn = st.text_input("Tên bệnh nhân *")
    
    with col2:
        loai_hinh = st.selectbox("Loại hình ảnh", 
            ["X-quang", "CT Scanner", "MRI", "Siêu âm", "Mammography", "Khác"])
        bs_chi_dinh = st.text_input("Bác sĩ chỉ định")
        ky_thuat_vien = st.text_input("Kỹ thuật viên")

    if st.button("✅ Lưu yêu cầu mới", type="primary", use_container_width=True):
        if not ma_yeu_cau or not ten_bn:
            st.error("❌ Vui lòng nhập đầy đủ Mã yêu cầu và Tên bệnh nhân")
        else:
            # Tự động tính thời gian hẹn trả theo loại
            if loai_hinh == "X-quang":
                hen_tra = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
            elif loai_hinh == "CT Scanner":
                hen_tra = (datetime.now() + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
            elif loai_hinh == "MRI":
                hen_tra = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            else:
                hen_tra = (datetime.now() + timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("""INSERT INTO studies 
                    (ma_yeu_cau, ma_benh_nhan, ten_benh_nhan, loai_hinh_anh, 
                     bac_si_chi_dinh, ky_thuat_vien, thoi_gian_hen_tra)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                    (ma_yeu_cau, ma_bn, ten_bn, loai_hinh, bs_chi_dinh, ky_thuat_vien, hen_tra))
                conn.commit()
                conn.close()
                st.success(f"✅ Đã thêm yêu cầu **{ma_yeu_cau}** thành công!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi: {e}")

# ====================== DANH SÁCH YÊU CẦU ======================
elif menu == "📋 Danh sách yêu cầu":
    st.subheader("Danh sách tất cả yêu cầu")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT id, ma_yeu_cau, ten_benh_nhan, loai_hinh_anh, trang_thai, 
               thoi_gian_ket_thuc_chup, thoi_gian_hen_tra, thoi_gian_tra_thuc_te, bac_si_doc
        FROM studies 
        ORDER BY id DESC
    """, conn)
    conn.close()

    if df.empty:
        st.info("Chưa có yêu cầu nào. Hãy thêm yêu cầu mới.")
    else:
        # Tô màu đỏ cho ca trễ hạn
        def highlight_delay(row):
            if row['trang_thai'] != 'Đã trả' and pd.notna(row['thoi_gian_hen_tra']) and row['thoi_gian_hen_tra'] < now:
                return ['background-color: #ffcccc; color: black'] * len(row)
            return [''] * len(row)

        styled_df = df.style.apply(highlight_delay, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=650)

# ====================== CẬP NHẬT TRẠNG THÁI ======================
elif menu == "🔄 Cập nhật trạng thái":
    st.subheader("Cập nhật mốc thời gian và trạng thái")

    conn = sqlite3.connect(DB_NAME)
    df_list = pd.read_sql_query("SELECT id, ma_yeu_cau, ten_benh_nhan, trang_thai FROM studies ORDER BY id DESC", conn)
    conn.close()

    if df_list.empty:
        st.warning("Chưa có dữ liệu để cập nhật.")
    else:
        options = df_list['ma_yeu_cau'] + " — " + df_list['ten_benh_nhan']
        selected = st.selectbox("Chọn yêu cầu cần cập nhật", options)
        
        study_id = int(df_list[options == selected]['id'].iloc[0])

        trang_thai_moi = st.selectbox("Trạng thái mới", 
            ["Chờ chụp", "Đang chụp", "Hoàn thành chụp", "Chờ đọc", "Đang đọc", "Đã trả"])

        nguoi_thuc_hien = st.text_input("Người thực hiện (Bác sĩ / Kỹ thuật viên)", "")

        if st.button("Cập nhật trạng thái", type="primary"):
            conn = sqlite3.connect(DB_NAME)
            if trang_thai_moi == "Hoàn thành chụp":
                conn.execute("UPDATE studies SET thoi_gian_ket_thuc_chup = ?, trang_thai = ? WHERE id = ?", 
                            (now, trang_thai_moi, study_id))
            elif trang_thai_moi == "Đã trả":
                conn.execute("UPDATE studies SET thoi_gian_tra_thuc_te = ?, bac_si_doc = ?, trang_thai = ? WHERE id = ?", 
                            (now, nguoi_thuc_hien if nguoi_thuc_hien else "Không ghi", trang_thai_moi, study_id))
            else:
                conn.execute("UPDATE studies SET trang_thai = ? WHERE id = ?", (trang_thai_moi, study_id))
            conn.commit()
            conn.close()
            st.success("✅ Cập nhật thành công!")
            st.rerun()

# ====================== THỐNG KÊ & TRỄ HẠN ======================
elif menu == "📊 Thống kê & Trễ hạn":
    st.subheader("Thống kê và Cảnh báo trễ hạn")
    
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM studies", conn)
    conn.close()

    tre_han = df[(df['trang_thai'] != 'Đã trả') & (df['thoi_gian_hen_tra'] < now)]

    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng số yêu cầu", len(df))
    col2.metric("Số ca đã trả kết quả", len(df[df['trang_thai'] == 'Đã trả']))
    col3.metric("Số ca trễ hạn", len(tre_han), delta="Cần xử lý ngay" if len(tre_han) > 0 else None)

    if not tre_han.empty:
        st.error("🚨 CÁC YÊU CẦU ĐÃ TRỄ HẠN")
        st.dataframe(tre_han[['ma_yeu_cau', 'ten_benh_nhan', 'loai_hinh_anh', 'thoi_gian_hen_tra', 'trang_thai']], 
                     use_container_width=True)

    st.caption("Phần mềm quản lý workflow chẩn đoán hình ảnh - Streamlit")

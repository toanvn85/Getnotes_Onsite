import streamlit as st
import hashlib
from supabase import create_client

# QUAN TRỌNG: set_page_config() phải là lệnh Streamlit đầu tiên
st.set_page_config(page_title="Đăng nhập", layout="wide", page_icon="🔐")

# --- CSS cho giao diện ---
# Thêm vào phần CSS
st.markdown("""
<style>
div[data-testid="stForm"] {
    max-width: 500px;
    margin: 0 auto;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}
.auth-header {
    text-align: center;
    margin-bottom: 20px;
}
.stButton button {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# Hàm kết nối Supabase
def init_supabase():
    """Khởi tạo kết nối Supabase"""
    try:
        if "supabase" not in st.secrets:
            st.error("🔑 Không tìm thấy cấu hình Supabase!")
            return None
            
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        
        if not url or not key:
            st.error("🔑 URL hoặc key Supabase không hợp lệ!")
            return None
            
        # Kết nối
        client = create_client(url, key)
        return client
            
    except Exception as e:
        st.error(f"❌ Không thể kết nối đến Supabase: {e}")
        return None

# Hàm mã hóa mật khẩu
def hash_password(password):
    """Mã hóa mật khẩu với SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Hàm kiểm tra đăng nhập
def check_login(supabase, email, password):
    """Kiểm tra thông tin đăng nhập"""
    try:
        hashed_password = hash_password(password)
        response = supabase.table('users').select('*').eq('email', email).eq('password', hashed_password).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Lỗi khi kiểm tra đăng nhập: {e}")
        return None

# Hàm đăng ký người dùng
def register_user(supabase, email, password, full_name, role='member'):
    """Đăng ký người dùng mới"""
    try:
        # Kiểm tra email đã tồn tại chưa
        check = supabase.table('users').select('id').eq('email', email).execute()
        if check.data and len(check.data) > 0:
            return False, "Email đã được sử dụng"
        
        # Mã hóa mật khẩu
        hashed_password = hash_password(password)
        
        # Thêm người dùng mới
        user_data = {
            'email': email,
            'password': hashed_password,
            'full_name': full_name,
            'role': role
        }
        
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data and len(response.data) > 0:
            return True, "Đăng ký thành công"
        return False, "Đăng ký thất bại"
    except Exception as e:
        return False, f"Lỗi khi đăng ký: {e}"

# Khởi tạo session state
if 'user' not in st.session_state:
    st.session_state.user = None

# Kết nối Supabase
supabase = init_supabase()

if not supabase:
    st.error("Không thể kết nối đến cơ sở dữ liệu. Vui lòng kiểm tra cấu hình.")
    st.stop()

# Kiểm tra nếu đã đăng nhập
if st.session_state.user:
    st.success(f"Đã đăng nhập với tư cách {st.session_state.user['full_name']}")
    
    if st.button("Đăng xuất"):
        st.session_state.user = None
        st.rerun()
    
    if st.button("Đi đến trang chính"):
        # Chuyển trực tiếp đến Getnotes_Onsite.py vì nằm cùng thư mục
        st.switch_page("pages/Getnotes_Onsite.py")
    
    st.stop()

# Giao diện đăng nhập
st.title("🔐 Đăng nhập / Đăng ký")

tab1, tab2, tab3 = st.tabs(["Đăng nhập", "Đăng ký", "Đổi mật khẩu"])

with tab1:
    with st.form("login_form"):
        st.subheader("Đăng nhập")
        email = st.text_input("Email")
        password = st.text_input("Mật khẩu", type="password")
        
        submitted = st.form_submit_button("Đăng nhập")
        
        if submitted:
            if not email or not password:
                st.error("Vui lòng nhập đầy đủ thông tin")
            else:
                user = check_login(supabase, email, password)
                if user:
                    st.session_state.user = user
                    st.success(f"Đăng nhập thành công! Xin chào {user['full_name']}")
                    st.rerun()
                else:
                    st.error("Email hoặc mật khẩu không đúng")

with tab2:
    with st.form("register_form"):
        st.subheader("Đăng ký tài khoản mới")
        full_name = st.text_input("Họ và tên")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Mật khẩu", type="password", key="reg_password")
        confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
        
        # Chỉ admin đầu tiên mới được đăng ký với vai trò admin
        role = "member"
        is_first_user = False
        
        try:
            # Kiểm tra xem đã có người dùng nào chưa
            response = supabase.table('users').select('id').limit(1).execute()
            is_first_user = not response.data or len(response.data) == 0
        except:
            pass
        
        if is_first_user:
            role_option = st.selectbox("Vai trò", ["admin", "member"])
            role = role_option
        
        submitted = st.form_submit_button("Đăng ký")
        
        if submitted:
            if not full_name or not email or not password or not confirm_password:
                st.error("Vui lòng nhập đầy đủ thông tin")
            elif password != confirm_password:
                st.error("Mật khẩu xác nhận không khớp")
            else:
                success, message = register_user(supabase, email, password, full_name, role)
                if success:
                    st.success(message)
                    st.info("Vui lòng đăng nhập để tiếp tục")
                else:
                    st.error(message)

with tab3:
    with st.form("change_password_form"):
        st.subheader("Đổi mật khẩu")
        email = st.text_input("Email", key="cp_email")
        current_password = st.text_input("Mật khẩu hiện tại", type="password")
        new_password = st.text_input("Mật khẩu mới", type="password")
        confirm_new_password = st.text_input("Xác nhận mật khẩu mới", type="password")
        
        submitted = st.form_submit_button("Đổi mật khẩu")
        
        if submitted:
            if not email or not current_password or not new_password or not confirm_new_password:
                st.error("Vui lòng nhập đầy đủ thông tin")
            elif new_password != confirm_new_password:
                st.error("Mật khẩu mới xác nhận không khớp")
            else:
                # Kiểm tra mật khẩu hiện tại
                user = check_login(supabase, email, current_password)
                if not user:
                    st.error("Email hoặc mật khẩu hiện tại không đúng")
                else:
                    # Cập nhật mật khẩu mới
                    try:
                        hashed_password = hash_password(new_password)
                        supabase.table('users').update({"password": hashed_password}).eq('id', user['id']).execute()
                        st.success("Đổi mật khẩu thành công!")
                    except Exception as e:
                        st.error(f"Lỗi khi cập nhật mật khẩu: {e}")
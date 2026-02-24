import streamlit as st
from openai import OpenAI
import json
import os
import base64
from io import BytesIO

# --- 1. 基础页面设置与AI连接 ---
st.set_page_config(page_title="初中数学AI教研室(识图版)", page_icon="📸", layout="wide")
st.title("📸 专属初中数学AI教研室 - V6.0 拍照识图版")

client = OpenAI(
    api_key=st.secrets["MOONSHOT_API_KEY"],
    base_url="https://api.moonshot.cn/v1",
)

# --- 2. 核心工具函数：处理图片 ---
def encode_image(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        file_type = uploaded_file.type.split('/')[-1]
        if file_type == 'jpeg': file_type = 'jpg'
        return f"data:image/{file_type};base64,{base64_image}"
    return None

# --- 3. 建立虚拟文件柜（保存学生数据） ---
DATA_FILE = "student_archives_v6.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "archives" not in st.session_state:
    st.session_state.archives = load_data()

# ==========================================
# 核心UI升级：三标签页 + 图片上传
# ==========================================
tab1, tab2, tab3 = st.tabs(["📚 学生错题档案(拍照录入)", "📝 备课助手(拍照解题)", "🖨️ 智能组卷系统"])

# --- 标签页 1：学生错题档案（拍照版） ---
with tab1:
    with st.sidebar:
        st.header("🗂️ 学生档案管理")
        new_student = st.text_input("➕ 添加新学生姓名：")
        if st.button("建立专属档案"):
            if new_student and new_student not in st.session_state.archives:
                st.session_state.archives[new_student] = []
                save_data(st.session_state.archives)
                st.success(f"已为【{new_student}】建立档案！")
            elif new_student in st.session_state.archives:
                st.warning("该学生档案已存在！")
        st.divider()
        student_list = list(st.session_state.archives.keys())
        current_student = st.selectbox("👤 当前正在辅导：", student_list) if student_list else None

    if current_student:
        st.subheader(f"📖 【{current_student}】的错题记录")
        student_history = st.session_state.archives[current_student]
        with st.expander("查看历史记录"):
             for item in student_history:
                 st.text(f"[{item['time']}] {item['type']}")

        st.divider()
        st.write("### 📸 拍照录入新错题")
        # 这就是您要的图片上传组件！
        uploaded_mistake = st.file_uploader("请上传原题及学生错解的图片", type=["jpg", "png", "jpeg"], key="mistake_img")
        additional_note = st.text_input("补充说明（可选，例如：学生在第二步卡住了）：")

        if st.button("🚀 分析图片错题并存档"):
            if not uploaded_mistake:
                st.warning("老师，请先上传图片哦！")
            else:
                with st.spinner("AI正在努力识别图片中的数学内容并分析..."):
                    image_data = encode_image(uploaded_mistake)
                    messages = [
                        {"role": "system", "content": "你是一位拥有20年经验的初中数学名师。你能完美识别图片中的数学公式和几何图形。请分析图片内容，给出考点、错因诊断、2道变式题和教学建议。"},
                        {"role": "user", "content": [
                            {"type": "image_url", "image_url": {"url": image_data}},
                            {"type": "text", "text": f"这是学生的错题图片。补充说明：{additional_note}。请分析。"}
                        ]}
                    ]
                    response = client.chat.completions.create(
                        model="moonshot-v1-128k",
                        messages=messages,
                        temperature=0.3
                    )
                    result_text = response.choices[0].message.content
                    st.markdown("### 🎯 图片错题分析报告")
                    st.write(result_text)
                    
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.archives[current_student].append({"time": timestamp, "type": "图片错题分析", "content": result_text})
                    save_data(st.session_state.archives)
                    st.success("✅ 分析结果已保存！")

# --- 标签页 2：试卷与新题解析（文字版保持稳定） ---
with tab2:
    st.subheader("💡 备课助手：给AI投喂试卷/压轴题")
    uploaded_exam = st.text_area("请将题目文字粘贴到这里：", height=200)
    if st.button("📝 生成【备课解析报告】"):
         if not uploaded_exam:
            st.warning("请输入题目文字。")
         else:
            with st.spinner("AI教研组长正在解题..."):
                prep_prompt = "你是数学特级教师。提供备课解析报告：1.满分板书作答(步骤严谨) 2.考点分布 3.命题意图与难度 4.设计3个循序渐进的问题引导学生。"
                response = client.chat.completions.create(model="moonshot-v1-128k", messages=[{"role": "system", "content": prep_prompt}, {"role": "user", "content": uploaded_exam}])
                st.markdown(response.choices[0].message.content)

# --- 标签页 3：智能组卷系统（文字版保持稳定） ---
with tab3:
    st.subheader("🖨️ 一键生成随堂测验与平行试卷")
    build_mode = st.radio("出卷模式", ["🎯 专项突破（按知识点）", "📄 仿造原卷（出一套平行卷）"])
    st.divider()
    if build_mode == "🎯 专项突破（按知识点）":
        topics = st.text_input("📝 输入知识点（如：圆周角定理）：")
        q_diff = st.select_slider("📈 难度梯度", ["基础巩固", "中等强化", "压轴拔高"], value="中等强化")
        if st.button("✨ 生成专项测验"):
            if not topics: st.warning("请输入知识点！")
            else:
                with st.spinner("AI正在组卷..."):
                    prompt = f"初中数学教师。针对【{topics}】出5道【{q_diff}】难度的题。要求：排版清晰，适合打印，最后附解答。"
                    response = client.chat.completions.create(model="moonshot-v1-128k", messages=[{"role": "user", "content": prompt}], temperature=0.5)
                    st.markdown(response.choices[0].message.content)
    else:
        original_paper = st.text_area("📥 粘贴原卷文字内容：", height=150)
        if st.button("🔄 生成平行试卷"):
             if not original_paper: st.warning("请粘贴原卷文字。")
             else:
                with st.spinner("AI正在生成平行卷..."):
                    prompt = f"中考命题专家。仿照以下原题出平行卷：\n{original_paper}\n要求：考点难度一致，背景数字不同。最后附解答。"
                    response = client.chat.completions.create(model="moonshot-v1-128k", messages=[{"role": "user", "content": prompt}], temperature=0.7)
                    st.markdown(response.choices[0].message.content)

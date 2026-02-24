import streamlit as st
from openai import OpenAI
import json
import os

st.set_page_config(page_title="初中数学AI教研室", page_icon="🏫", layout="wide")
st.title("🏫 专属初中数学教研室 - V5.0 终极完全体")

DATA_FILE = "student_archives.json"

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

tab1, tab2, tab3 = st.tabs(["📚 第一教研室：学生错题档案", "📝 第二教研室：试卷与新题解析", "🖨️ 第三教研室：智能组卷系统"])

# --- 标签页 1：学生错题档案 ---
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
        if not student_list:
            st.warning("👈 请先在上方添加至少一个学生档案。")
        else:
            current_student = st.selectbox("👤 当前正在辅导：", student_list)

    if student_list:
        st.subheader(f"📖 【{current_student}】的错题本与学习记录")
        student_history = st.session_state.archives[current_student]

        if student_history:
            with st.expander("点击展开/折叠该生过往所有错题记录"):
                for msg in student_history:
                    if msg["role"] == "user":
                        st.info(f"📝 录入错题：\n{msg['content']}")
                    elif msg["role"] == "assistant":
                        st.success(f"🤖 AI分析：\n{msg['content']}")
        else:
            st.write("该生档案为空，请录入第一道错题！")

        st.divider()
        problem = st.text_area("输入原题及学生的错误步骤：", height=150, key="mistake_input")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 分析当前错题并存档"):
                if not problem:
                    st.warning("请输入题目内容哦！")
                else:
                    with st.spinner("AI正在分析..."):
                        client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                        messages = [{"role": "system", "content": "你是一位初中数学名师。请给出考点、错因、2道变式题和全班讲评建议。"}]
                        messages.extend(student_history)
                        messages.append({"role": "user", "content": problem})
                        response = client.chat.completions.create(model="deepseek-chat", messages=messages)
                        result_text = response.choices[0].message.content
                        st.markdown("### 🎯 错题分析报告")
                        st.write(result_text)
                        st.session_state.archives[current_student].extend([{"role": "user", "content": problem}, {"role": "assistant", "content": result_text}])
                        save_data(st.session_state.archives)
                        st.success("✅ 分析已保存！")

        with col2:
            if st.button("📊 生成阶段学情分析"):
                user_messages = [m['content'] for m in student_history if m["role"] == "user"]
                if len(user_messages) < 2:
                    st.warning("错题不足2道，请先多录入。")
                else:
                    with st.spinner("AI正在生成学情报告..."):
                        client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                        history_text = "\n".join(user_messages)
                        prompt = f"你是初中数学名师。基于学生【{current_student}】错题：\n{history_text}\n提供阶段学情分析：1.知识漏洞 2.思维习惯 3.后续计划。"
                        response = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                        st.markdown("### 📈 专属阶段学情分析")
                        st.write(response.choices[0].message.content)

# --- 标签页 2：试卷与新题解析 ---
with tab2:
    st.subheader("💡 备课助手：给AI投喂试卷或压轴题")
    exam_paper = st.text_area("在此输入题目内容：", height=200, key="exam_input")
    if st.button("📝 让AI作答并生成【备课解析报告】"):
        if not exam_paper:
            st.warning("请输入题目呢！")
        else:
            with st.spinner("AI教研组长正在做题..."):
                client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                prompt = "你是数学特级教师。提供备课解析报告：1.满分板书作答 2.考点分布 3.命题意图 4.学生易错陷阱。"
                response = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "system", "content": prompt}, {"role": "user", "content": exam_paper}])
                st.success("报告生成完毕！")
                st.markdown(response.choices[0].message.content)

# --- 标签页 3：智能组卷系统 ---
with tab3:
    st.subheader("🖨️ 一键生成随堂测验与平行试卷")
    build_mode = st.radio("出卷模式", ["🎯 1. 专项突破（按知识点组卷）", "📄 2. 仿造原卷（出一套平行卷）"], label_visibility="collapsed")
    st.divider()
    
    if build_mode == "🎯 1. 专项突破（按知识点组卷）":
        topics = st.text_input("📝 请输入考查知识点（如：反比例函数）：")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            q_count = st.slider("🔢 题目数量", 1, 10, 5)
        with col_q2:
            q_diff = st.select_slider("📈 难度梯度", ["基础巩固", "中等强化", "压轴拔高"], value="中等强化")
            
        if st.button("✨ 一键生成专项测验"):
            if not topics:
                st.warning("请输入考察的知识点！")
            else:
                with st.spinner("AI正在海量题库中组卷..."):
                    client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                    prompt = f"你是一名数学教师。针对【{topics}】出【{q_count}】道难度为【{q_diff}】的题。要求：排版清晰，试卷末尾附详细解答。"
                    response = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                    st.success("专项测验生成完毕！")
                    st.markdown(response.choices[0].message.content)
                    
    else:
        original_paper = st.text_area("📥 粘贴原试卷的题目：", height=200)
        if st.button("🔄 一键生成平行试卷"):
            if not original_paper:
                st.warning("请先输入原卷内容！")
            else:
                with st.spinner("AI正在拆解原卷考点，生成平行卷..."):
                    client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                    prompt = f"你是一名中考命题专家。分析以下原题并出平行卷：\n{original_paper}\n要求：题型考点难度一致，数字背景不同，最后附解答。"
                    response = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": prompt}])
                    st.success("平行卷生成完毕！")
                    st.markdown(response.choices[0].message.content)

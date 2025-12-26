import streamlit as st
import time
from agent import ZootopiaAgent
import os

# === 页面配置 ===
st.set_page_config(
    page_title="Zootopia Social Simulation",
    page_icon="🐰",
    layout="wide"
)

# === 样式美化 (CSS) ===
st.markdown("""
<style>
    .stChatMessage { font-size: 16px; }
    .thought-bubble {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #555;
        border-left: 3px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# === 1. 初始化 Session State (保持 Agent 存活) ===
if "agents" not in st.session_state:
    # 这里初始化你的 Agent
    judy = ZootopiaAgent(
        name="Judy_Hopps", # 注意：名字不要带空格，方便数据库命名
        persona="你是一只来自兔窝镇的兔子警官，乐观、坚韧、正义感爆棚。你正在调查一起失踪案，时间非常紧迫。你现在很着急。",
        speech_style="语速快，充满能量，礼貌但急切。喜欢用'Sweet cheese and crackers!'作为感叹词。",
        is_slow=False
    )
    
    flash = ZootopiaAgent(
        name="Flash",
        persona="你是车管所的一只树懒。你是那里动作最快的树懒。你非常友善，专业，但是你的动作和思维极其缓慢。你听完一句话需要很久才能反应过来。",
        speech_style="说话......非常......非常......慢。每两个字......之间......都要......停顿。最后......才......笑。",
        is_slow=True # 记得在 agent.py 里我们要把 sleep 去掉或者减少，不然网页会卡住
    )
    
    st.session_state.agents = {"Judy": judy, "Flash": flash}
    st.session_state.chat_history = [] # 存储聊天记录
    st.session_state.round_count = 0

# 获取 Agent 实例
judy = st.session_state.agents["Judy"]
flash = st.session_state.agents["Flash"]

# === 2. 侧边栏：上帝视角与记忆监控 ===
with st.sidebar:
    st.title("🕵️‍♂️ 上帝控制台 (God View)")
    
    # 模拟场景设置
    context_input = st.text_area(
        "当前环境/突发事件 (Context)", 
        value="Judy 冲进了车管所，站在 Flash 的柜台前。她手里拿着一张照片，想要查车牌 29THD03。",
        height=100
    )
    
    st.divider()
    
    # 记忆查看器 (Phase 2 核心 - 已修正适配 AgenticMemorySystem)
    st.subheader("🧠 记忆库透视 (Memory Matrix)")
    selected_agent = st.selectbox("选择要查看大脑的角色:", ["Judy", "Flash"])
    
    # 增加一个输入框，让用户可以自定义检索关键词
    search_query = st.text_input("输入检索关键词:", value="车牌 树懒")

    if st.button("刷新记忆库"):
        # 修改点 1: 参数名从 n_results 改为 k
        # 修改点 2: 使用用户输入的 query
        agent_memory = st.session_state.agents[selected_agent].memory
        memories = agent_memory.retrieve(query=search_query, k=5)
        st.session_state.current_view_memories = memories
    
    if "current_view_memories" in st.session_state:
        for mem in st.session_state.current_view_memories:
            # 修改点 3: 解析结构化数据 (Dict) 进行更美观的展示
            # mem 结构: {'id':..., 'content':..., 'context':..., 'tags':..., 'score':...}
            
            with st.container():
                # 标题显示核心内容的前几十个字
                content_preview = mem.get('content', '')[:20] + "..."
                st.markdown(f"**📜 记忆片段**: {content_preview}")
                
                # 使用 expander 显示详细信息，保持界面整洁
                with st.expander("查看详情 (Context & Tags)"):
                    st.markdown(f"**内容 (Content):**\n{mem.get('content', '')}")
                    st.markdown(f"**背景 (Context):**\n{mem.get('context', '无')}")
                    
                    # 渲染标签
                    tags = mem.get('tags', [])
                    if tags:
                        st.markdown(f"**标签 (Tags):**")
                        st.markdown(" ".join([f"`{tag}`" for tag in tags if tag]))
                    
                    st.caption(f"ID: {mem.get('id')} | Relevance Score: {mem.get('score'):.4f}")

# === 3. 主界面：聊天窗口 ===
st.header("🎬 Zootopia Social Lab")
st.caption("观察基于 LLM 的多智能体社会演化")

# 展示历史聊天
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        # 渲染内心独白 (折叠起来)
        with st.expander(f"💭 {msg['role']} 的内心独白 (Thinking Process)"):
            st.markdown(f"<div class='thought-bubble'>{msg['thought']}</div>", unsafe_allow_html=True)
        # 渲染公开对话
        st.write(msg["content"])

# === 4. 交互控制区 ===
col1, col2 = st.columns([1, 1])

def agent_speak(agent_obj, target_agent_name, context, avatar_emoji):
    """封装 Agent 说话的逻辑"""
    with st.spinner(f"{agent_obj.name} 正在思考..."):
        
        # 这里的 context 是拼接了历史对话的
        response_speech = agent_obj.think_and_act(context) 
        
        # 调用修改后的 agent.py
        thought_content, response_speech = agent_obj.think_and_act(context)
        
        # 存入历史
        st.session_state.chat_history.append({
            "role": agent_obj.name,
            "avatar": avatar_emoji,
            "content": response_speech,
            "thought": thought_content  # 现在这里有真正的思考内容了！
        })
        
        # 对方产生记忆
        st.session_state.agents[target_agent_name].perceive(f"{agent_obj.name} 对我说: {response_speech}")
        
    st.rerun() # 刷新页面显示新消息

with col1:
    if st.button("🐰 让 Judy 发言"):
        # 构建上下文：包含当前场景 + 最近一条对话
        last_msg = st.session_state.chat_history[-1]['content'] if st.session_state.chat_history else "无"
        full_context = f"【当前场景】{context_input}\n【上一句对话】{last_msg}"
        agent_speak(judy, "Flash", full_context, "🐰")

with col2:
    if st.button("🦥 让 Flash 回复"):
        last_msg = st.session_state.chat_history[-1]['content'] if st.session_state.chat_history else "无"
        full_context = f"【当前场景】{context_input}\n【Judy 刚才说】{last_msg}"
        agent_speak(flash, "Judy", full_context, "🦥")

# 重置按钮
if st.button("🔄 重置模拟 (清空历史)"):
    st.session_state.chat_history = []
    st.rerun()
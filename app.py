import streamlit as st
import time
import random
from agent import ZootopiaAgent

# === 页面配置 ===
st.set_page_config(
    page_title="Zootopia Social Simulation",
    page_icon="🏙️",
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
    .status-box {
        padding: 10px;
        background-color: #e8f0fe;
        border-radius: 5px;
        margin-bottom: 10px;
        text-align: center;
        font-weight: bold;
        color: #1a73e8;
    }
</style>
""", unsafe_allow_html=True)

# === 1. 角色配置 (在此处添加更多角色) ===
CHARACTERS_CONFIG = [
    {
        "name": "Judy_Hopps",
        "avatar": "🐰",
        "persona": "你是一只来自兔窝镇的兔子警官，乐观、坚韧、正义感爆棚。你正在调查一起失踪案，虽然现在是休息时间，但你依然时刻保持警惕。",
        "speech_style": "语速快，充满能量，礼貌但急切。喜欢用'Sweet cheese and crackers!'作为感叹词。",
        "is_slow": False
    },
    {
        "name": "Nick_Wilde",
        "avatar": "🦊",
        "persona": "你是一只以此为生的狐狸，狡猾但有良心。你喜欢嘲讽朱迪，但也把她当好朋友。你喜欢戴着墨镜观察周围。",
        "speech_style": "懒洋洋的，带着玩世不恭的调侃，喜欢叫朱迪'Carrots'（萝卜头）。每一句话似乎都带着一点点讽刺。",
        "is_slow": False
    },
    {
        "name": "Flash",
        "avatar": "🦥",
        "persona": "你是车管所的一只树懒。你是那里动作最快的树懒。你非常友善，专业，但是你的动作和思维极其缓慢。",
        "speech_style": "说话......非常......非常......慢。每两个字......之间......都要......停顿。最后......才......笑。",
        "is_slow": True
    },
    {
        "name": "Chief_Bogo",
        "avatar": "🐃",
        "persona": "你是动物城警察局局长，一只严厉的水牛。你对下属要求很高，不喜欢听废话。",
        "speech_style": "嗓音低沉，威严，不怒自威。说话简短有力，喜欢用命令的口吻。",
        "is_slow": False
    }
]

# === 2. 初始化 Session State ===
if "agents" not in st.session_state:
    st.session_state.agents = {}
    st.session_state.chat_history = []
    st.session_state.is_running = False  # 控制自动对话开关
    
    # 动态初始化所有角色
    with st.spinner("正在初始化动物城居民 (加载模型中)..."):
        for config in CHARACTERS_CONFIG:
            agent = ZootopiaAgent(
                name=config["name"],
                persona=config["persona"],
                speech_style=config["speech_style"],
                is_slow=config["is_slow"]
            )
            st.session_state.agents[config["name"]] = {
                "obj": agent,
                "avatar": config["avatar"],
                "config": config
            }

# === 3. 侧边栏：上帝控制台 ===
with st.sidebar:
    st.title("🕵️‍♂️ 上帝控制台 (God View)")
    
    # 场景设置 (World Event)
    st.subheader("🌍 环境设定")
    context_input = st.text_area(
        "当前场景/突发事件", 
        value="大家都在警察局的休息室里喝下午茶。气氛很轻松，但朱迪看起来有点坐立难安。",
        height=100
    )
    
    st.divider()
    
    # 演化控制
    st.subheader("⚙️ 演化控制")
    delay_time = st.slider("对话间隔 (秒)", 1, 10, 3, help="控制角色发言的速度")
    
    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("🚀 开始自动演化", type="primary"):
            st.session_state.is_running = True
            st.rerun()
    with col_stop:
        if st.button("⏸️ 暂停演化"):
            st.session_state.is_running = False
            st.rerun()

    st.divider()

    # 记忆查看器
    st.subheader("🧠 记忆透视")
    agent_names = list(st.session_state.agents.keys())
    selected_agent_name = st.selectbox("潜入谁的大脑:", agent_names)
    search_query = st.text_input("记忆检索关键词:", value="朱迪 树懒")
    
    if st.button("刷新记忆"):
        agent_obj = st.session_state.agents[selected_agent_name]["obj"]
        memories = agent_obj.memory.retrieve(query=search_query, k=3)
        st.session_state.current_view_memories = memories

    if "current_view_memories" in st.session_state:
        for mem in st.session_state.current_view_memories:
            with st.expander(f"📜 {mem.get('content', '')[:15]}..."):
                st.markdown(f"**Content:** {mem.get('content')}")
                st.markdown(f"**Tags:** {mem.get('tags')}")
                st.caption(f"Score: {mem.get('score'):.4f}")
                
    if st.button("🗑️ 清空所有历史与记忆"):
        st.session_state.clear()
        st.rerun()

# === 4. 主界面：剧场展示 ===
st.header("🎬 Zootopia Social Lab")
if st.session_state.is_running:
    st.markdown("<div class='status-box'>🔴 正在自动演化中... (God is watching)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-box'>⏸️ 演化已暂停</div>", unsafe_allow_html=True)

# 渲染历史聊天
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        # 渲染内心独白
        if msg.get("thought"):
            with st.expander(f"💭 {msg['role']} 的内心活动"):
                st.markdown(f"<div class='thought-bubble'>{msg['thought']}</div>", unsafe_allow_html=True)
        st.write(msg["content"])

# === 5. 自动演化核心逻辑 ===
if st.session_state.is_running:
    # A. 决定下一个发言者
    # 规则：随机选择一个不是刚说完话的人 (避免自言自语)
    all_names = list(st.session_state.agents.keys())
    last_speaker = st.session_state.chat_history[-1]["role"] if st.session_state.chat_history else None
    
    candidates = [n for n in all_names if n != last_speaker]
    # 如果只有一个人，那就只能自言自语了；否则随机选
    next_speaker_name = random.choice(candidates) if candidates else all_names[0]
    
    current_agent_data = st.session_state.agents[next_speaker_name]
    current_agent = current_agent_data["obj"]
    
    # B. 构建“上帝视角”的全知上下文
    # 包括：用户设定的场景 + 最近几轮的对话历史
    recent_msgs = st.session_state.chat_history[-4:] # 给 LLM 看最近 4 条，防止 context 过长
    history_text = "\n".join([f"[{m['role']}]: {m['content']}" for m in recent_msgs])
    if not history_text:
        history_text = "(对话刚刚开始)"
        
    full_context = f"""
    【当前公共场景】
    {context_input}
    
    【最近发生的对话】
    {history_text}
    
    【轮到你了】
    现在轮到你 ({next_speaker_name}) 发言了。请根据你的性格和当前局势接话。
    """

    # C. Agent 思考与行动
    # 使用 container 和 spinner 优化 UI 体验
    with st.chat_message(next_speaker_name, avatar=current_agent_data["avatar"]):
        with st.spinner(f"{next_speaker_name} 正在思考..."):
            thought, speech = current_agent.think_and_act(full_context)
            
            # 实时渲染当前回复
            with st.expander(f"💭 {next_speaker_name} 的内心独白"):
                st.write(thought)
            st.write(speech)
    
    # D. 更新历史记录
    st.session_state.chat_history.append({
        "role": next_speaker_name,
        "avatar": current_agent_data["avatar"],
        "content": speech,
        "thought": thought
    })

    # E. 群体感知 (Broadcast)
    # 让在场的所有其他 Agent 都“听到”这句话，存入他们的记忆
    # 这样下次轮到别人时，他们就知道刚才发生了什么
    for name, data in st.session_state.agents.items():
        if name != next_speaker_name:
            # 存入格式：[Speaker] 说: [Content]
            perception_text = f"{next_speaker_name} 在大家面前说: {speech}"
            data["obj"].perceive(perception_text)

    # F. 循环控制
    time.sleep(delay_time) # 等待一段时间，方便用户阅读
    st.rerun() # 刷新页面，触发下一轮循环
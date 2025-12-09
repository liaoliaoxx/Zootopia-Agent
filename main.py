from agent import ZootopiaAgent
import shutil
import os

def reset_memory():
    """每次运行时强制清空旧记忆，防止脏数据干扰"""
    if os.path.exists("./db"):
        try:
            shutil.rmtree("./db")
            print("🧹 已清空旧的记忆数据库 (Reset DB)")
        except Exception as e:
            print(f"⚠️ 无法自动删除 db 文件夹: {e}")

def main():
    # === 0. 自动清理脏数据 (可选，建议开发阶段开启) ===
    reset_memory()

    # === 1. 初始化角色 ===
    # 朱迪 (Judy Hopps)
    judy = ZootopiaAgent(
        name="Judy Hopps",
        persona="你是一只来自兔窝镇的兔子警官，乐观、坚韧、正义感爆棚。你正在调查一起失踪案，时间非常紧迫，你只有48小时。你现在很着急，想查一个车牌号。",
        speech_style="语速快，充满能量，礼貌但急切。",
        is_slow=False
    )

    # 闪电 (Flash)
    flash = ZootopiaAgent(
        name="Flash",
        persona="你是车管所的一只树懒。你是那里动作最快的树懒。你非常友善，专业，但是你的动作和思维极其缓慢。你听完一句话需要很久才能反应过来。",
        speech_style="说话......非常......非常......慢。每两个字......之间......都要......停顿。最后......才......笑。",
        is_slow=True
    )

    # === 2. 预植入记忆 (Pre-load Memory) ===
    print("--- 正在初始化记忆系统 ---")
    judy.perceive("尼克告诉我，查车牌必须找Flash，他是车管所最快的。")
    flash.perceive("今天早上刚喝了一杯很棒的咖啡。")

    # === 3. 模拟开始：DMV 场景 ===
    print("\n🎬 === SCENE START: Zootopia DMV === 🎬\n")

    # Round 1: Judy 发起对话
    context = "Judy 走到了 Flash 的柜台前，想要查一个车牌号 29THD03。"
    judy_thought, judy_speech = judy.think_and_act(context)
    print(f"🐰 Judy: {judy_speech}")
    
    # 将 Judy 的话存入 Flash 的记忆（作为观察）
    flash.perceive(f"Judy 对我说: {judy_speech}")

    # Round 2: Flash 反应
    # Flash 的上下文是 Judy 刚才说的话
    flash_context = f"Judy 刚才对我说了: {judy_speech}"
    flash_thought, flash_speech = flash.think_and_act(flash_context)
    print(f"🦥 Flash: {flash_speech}")

    # 将 Flash 的话存入 Judy 的记忆
    judy.perceive(f"Flash 回复我: {flash_speech}")

    # Round 3: Judy 崩溃
    judy_context = f"Flash 回复非常慢，他说: {flash_speech}。你现在非常着急，快疯了。"
    judy_thought_2, judy_speech_2 = judy.think_and_act(judy_context)
    print(f"🐰 Judy: {judy_speech_2}")

if __name__ == "__main__":
    main()
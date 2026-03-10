import json
import os
import logging
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.platform import AstrMessageEvent
from astrbot.api.message_components import At

logger = logging.getLogger("astrbot")

@register("astrbot_plugin_dnf_optimize", "qingcai", "DNF小团体优化助手", "1.2.0")
class DnfOptimizePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        
        # === 核心逻辑：自动路径处理 ===
        # 1. 定义存储目录：data/plugin_data/插件名
        self.data_dir = os.path.join("data", "plugin_data", "astrbot_plugin_dnf_optimize")
        self.db_path = os.path.join(self.data_dir, "config.json")
        
        # 2. 自动创建文件夹 (exist_ok=True 确保文件夹存在时不报错)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 3. 加载或初始化配置
        self.config = self._load_config()
        logger.info(f"===== [优化助手] 插件已就绪。存储路径: {self.db_path} =====")

    def _load_config(self):
        """读取配置文件，不存在则返回默认值"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取配置失败: {e}")
        
        # 默认初始数据
        return {
            "admin_qq": ["1023902556"], 
            "keywords": ["优化", "伤害低", "奶太小", "奶小", "没伤害", "输出低", "太菜", "垃圾数据"]
        }

    def _save_config(self):
        """保存配置到 JSON"""
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_optimize(self, event: AstrMessageEvent):
        msg_str = event.get_message_str()
        if msg_str.startswith("/"): return # 指令类不触发圣经

        # 1. 关键词命中检查
        matched = any(word in msg_str for word in self.config.get("keywords", []))
        if not matched: return

        # 2. 识别被 @ 的目标
        target_id = ""
        for seg in event.get_messages():
            if isinstance(seg, At):
                target_id = str(seg.qq)
            elif hasattr(seg, 'type') and seg.type == "at":
                target_id = str(seg.data.get("qq") or seg.data.get("user_id", ""))
            elif hasattr(seg, 'qq') and seg.qq:
                target_id = str(seg.qq)
        
        if not target_id: return

        # 3. 发送辞退圣经
        optimize_text = (
            "您的伤害太低了，小团体已经复盘完了，不得不非常遗憾地通知您：\n\n"
            "我们这边做了同装备同打造的打法和实战对比，也做了历史数据溯源回顾，"
            "在确保没有其他的干扰因素的情况下，您的伤害和奶量整体上可能不太适合我们小团体了。\n\n"
            "抱歉，我们这边就先把您优化了，希望您早日找到更加契合的环境，找到更符合您的12人狄瑞吉噩梦团，"
            "获得更好的游戏体验。也祝生活顺利，前程似锦！\n\n"
            "您已被优化，请勿回复。"
        )

        event.stop_event()
        # 发送：@目标人 + 换行 + 圣经内容
        await event.send_message([At(qq=target_id), "\n\n", optimize_text])

    # --- 管理指令：关键词管理 ---
    @filter.command("opt_add")
    async def add_keyword(self, event: AstrMessageEvent, word: str):
        if str(event.get_sender_id()) not in self.config["admin_qq"]: return
        if word not in self.config["keywords"]:
            self.config["keywords"].append(word)
            self._save_config()
            yield event.plain_result(f"✅ 已添加关键词: {word}")
        else:
            yield event.plain_result(f"⚠️ 关键词已存在。")

    @filter.command("opt_del")
    async def del_keyword(self, event: AstrMessageEvent, word: str):
        if str(event.get_sender_id()) not in self.config["admin_qq"]: return
        if word in self.config["keywords"]:
            self.config["keywords"].remove(word)
            self._save_config()
            yield event.plain_result(f"✅ 已移除关键词: {word}")
        else:
            yield event.plain_result(f"❌ 列表中没找到该词。")

    @filter.command("opt_list")
    async def list_keywords(self, event: AstrMessageEvent):
        words = self.config.get("keywords", [])
        yield event.plain_result(f"📋 DNF 优化词库:\n{', '.join(words)}")

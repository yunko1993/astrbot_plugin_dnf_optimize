import json
import os
import logging
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.core.platform import AstrMessageEvent
from astrbot.api.message_components import At

logger = logging.getLogger("astrbot")

@register("astrbot_plugin_dnf_optimize", "qingcai", "DNF小团体优化助手", "1.2.1")
class DnfOptimizePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_dir = os.path.join("data", "plugin_data", "astrbot_plugin_dnf_optimize")
        self.db_path = os.path.join(self.data_dir, "config.json")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 加载配置
        self.config = self._load_config()
        logger.info(f"===== [优化助手] 插件已就绪。配置文件: {self.db_path} =====")

    def _load_config(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取配置失败: {e}")
        
        # --- 改进点：如果文件不存在，定义默认值并立刻存一次盘 ---
        default_config = {
            "admin_qq": ["1023902556"], 
            "keywords": ["优化", "伤害低", "奶太小", "奶小", "没伤害", "输出低", "太菜", "垃圾数据"]
        }
        self.config = default_config # 临时赋值
        self._save_config_static(default_config) # 强行存盘
        return default_config

    def _save_config_static(self, conf):
        """静态保存方法，用于初始化时调用"""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(conf, f, ensure_ascii=False, indent=4)

    def _save_config(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    # ... 下面 handle_optimize 和其他指令的代码保持不变 ...
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_optimize(self, event: AstrMessageEvent):
        msg_str = event.get_message_str()
        if msg_str.startswith("/"): return 
        matched = any(word in msg_str for word in self.config.get("keywords", []))
        if not matched: return
        target_id = ""
        for seg in event.get_messages():
            if isinstance(seg, At): target_id = str(seg.qq)
            elif hasattr(seg, 'type') and seg.type == "at": target_id = str(seg.data.get("qq") or seg.data.get("user_id", ""))
            elif hasattr(seg, 'qq') and seg.qq: target_id = str(seg.qq)
        if not target_id: return

        optimize_text = (
            "您的伤害太低了，小团体已经复盘完了，不得不非常遗憾地通知您：\n\n"
            "我们这边做了同装备同打造的打法和实战对比，也做了历史数据溯源回顾，"
            "在确保没有其他的干扰因素的情况下，您的伤害和奶量整体上可能不太适合我们小团体了。\n\n"
            "抱歉，我们这边就先把您优化了，希望您早日找到更加契合的环境，找到更符合您的12人狄瑞吉噩梦团，"
            "获得更好的游戏体验。也祝生活顺利，前程似锦！\n\n"
            "您已被优化，请勿回复。"
        )
        event.stop_event()
        await event.send_message([At(qq=target_id), "\n\n", optimize_text])

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

"""
智能标题生成器模块 - 纯规则优化版
- 无需外部网络
- 预编译正则 + 缓存 + 截断加速
- 改进的句子评分与主题提取
"""

import re
import logging
from functools import lru_cache
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


class ReplyType(Enum):
    STEP_BY_STEP = "step_by_step"
    COMPARISON = "comparison"
    SUGGESTION = "suggestion"
    EXPLANATION = "explanation"
    CODE_EXAMPLE = "code_example"
    LIST = "list"
    QUESTION = "question"
    GENERAL = "general"


@dataclass
class TitleConfig:
    max_length: int = 18
    min_length: int = 2
    ellipsis: str = "..."
    depth_prefixes: Dict[int, str] = None

    max_scan_chars: int = 2000          # 只分析前2000字符
    max_scan_paragraphs: int = 8
    max_scan_sentences: int = 20

    def __post_init__(self):
        if self.depth_prefixes is None:
            self.depth_prefixes = {
                0: "主分支",
                1: "探索",
                2: "深入",
                3: "细节"
            }


class OptimizedTitleGenerator:
    """纯规则优化版标题生成器（无网络依赖）"""

    # 预编译正则
    CODE_PATTERN = re.compile(
        r'```|def\s+\w+|function\s+\w+|class\s+\w+|import\s+[\w\.]+|from\s+[\w\.]+\s+import',
        re.I
    )
    LIST_PATTERN = re.compile(r'^\s*(\d+\.|[一二三四五六七八九十]、|①|②|③|④|⑤)', re.M)
    SENTENCE_SPLIT = re.compile(r'[。！？!?；;]+')
    CLEAN_PREFIX = re.compile(
        r'^(其实|实际上|一般来说|通常来说|简单来说|总的来说|综上所述|总结一下|'
        r'可以看出|值得注意的是|需要注意的是|换句话说|也就是说|好的|明白了|'
        r'根据您的问题|关于您的问题|对于这个问题)[，,：:\s]*'
    )
    CLEAN_EDGE = re.compile(r'^[，。！？、；：,.!?;:\s]+|[，。！？、；：,.!?;:\s]+$')
    VS_PATTERN = re.compile(
        r'([^\s，。]{2,12})\s*(?:vs\.?|VS\.?|vs|VS)\s*([^\s，。]{2,12})|'
        r'([^\s，。]{2,12})与([^\s，。]{2,12})的?(?:区别|差异|对比|相比)'
    )
    CHINESE_WORDS = re.compile(r'[\u4e00-\u9fff]{2,8}')

    def __init__(self, config: Optional[TitleConfig] = None):
        self.config = config or TitleConfig()

        # 停用词
        self.stop_words = {
            "的", "了", "是", "在", "和", "与", "或", "有", "要", "能", "可以",
            "这个", "那个", "什么", "怎么", "如何", "为什么", "我们", "你们", "他们",
            "首先", "其次", "然后", "最后", "另外", "而且", "但是", "因此", "所以"
        }

        # 信号词
        self.high_value_signals = {
            "总结", "综上", "因此", "所以", "结论", "核心", "关键", "重点",
            "建议", "推荐", "最佳", "最适合", "方案", "方法", "步骤", "流程",
            "原理", "本质", "解释", "说明", "风险", "注意"
        }

        self.template_suffixes = ["方案", "优化", "建议", "解析", "对比", "步骤", "流程", "示例"]

        # 尝试导入 jieba（可选）
        self._has_jieba = False
        try:
            import jieba
            import jieba.analyse
            self._has_jieba = True
        except ImportError:
            logger.info("jieba未安装，将使用简单词频统计")

    # ---------- 公共接口（带缓存）----------
    @lru_cache(maxsize=128)
    def generate_title(self, ai_content: str, thread_count: int, depth: int) -> str:
        if not ai_content or not isinstance(ai_content, str):
            return self._get_fallback_title(thread_count, depth)

        content = ai_content.strip()[:self.config.max_scan_chars]
        if len(content) < 10:
            return self._get_fallback_title(thread_count, depth)

        # 1. 类型识别
        reply_type = self._analyze_reply_type(content)

        # 2. 主题词提取
        topic_phrases = self._extract_topic_phrases(content)

        # 3. 候选句子
        sentences = self._extract_candidate_sentences(content)

        # 4. 最佳句子选择（基于改进的评分）
        best_sentence = self._select_best_sentence(sentences, topic_phrases, reply_type)

        # 5. 压缩为标题
        title = self._compress_sentence(best_sentence) if best_sentence else ""

        # 6. 兜底生成
        if not self._is_good_title(title):
            title = self._fallback_title_from_topic(topic_phrases, reply_type)

        # 7. 清理与截断
        title = self._clean_title(title)
        title = self._smart_truncate(title)

        if not self._is_good_title(title):
            return self._get_fallback_title(thread_count, depth)

        return title

    # ---------- 类型分析（快速规则）----------
    def _analyze_reply_type(self, content: str) -> ReplyType:
        lower = content.lower()
        if self.CODE_PATTERN.search(content):
            return ReplyType.CODE_EXAMPLE
        if self.LIST_PATTERN.search(content):
            if "步骤" in content or "流程" in content:
                return ReplyType.STEP_BY_STEP
            return ReplyType.LIST
        if "vs" in lower or "对比" in content or "区别" in content:
            return ReplyType.COMPARISON
        if "建议" in content or "推荐" in content:
            return ReplyType.SUGGESTION
        if "解释" in content or "原理" in content or "本质" in content:
            return ReplyType.EXPLANATION
        if "?" in content or "？" in content:
            return ReplyType.QUESTION
        return ReplyType.GENERAL

    # ---------- 主题短语提取 ----------
    def _extract_topic_phrases(self, content: str) -> List[str]:
        if self._has_jieba:
            return self._extract_with_jieba(content)
        return self._extract_with_frequency(content)

    def _extract_with_jieba(self, content: str) -> List[str]:
        try:
            import jieba.analyse
            keywords = jieba.analyse.extract_tags(
                content, topK=8, allowPOS=('n', 'vn', 'nr', 'ns', 'nt')
            )
            return [kw for kw in keywords if kw not in self.stop_words and 2 <= len(kw) <= 12]
        except Exception as e:
            logger.warning(f"jieba提取失败: {e}")
            return self._extract_with_frequency(content)

    def _extract_with_frequency(self, content: str) -> List[str]:
        words = self.CHINESE_WORDS.findall(content)
        filtered = [w for w in words if w not in self.stop_words]
        counter = Counter(filtered)
        # 按频次排序，取前8
        return [word for word, _ in counter.most_common(8)]

    # ---------- 候选句子抽取（改进评分）----------
    def _extract_candidate_sentences(self, content: str) -> List[str]:
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        paragraphs = paragraphs[:self.config.max_scan_paragraphs]

        sentences = []
        for p in paragraphs:
            for part in self.SENTENCE_SPLIT.split(p):
                s = part.strip()
                if len(s) >= self.config.min_length:
                    sentences.append(s)

        # 控制数量
        sentences = sentences[:self.config.max_scan_sentences]

        # 评分并排序
        scored = []
        total = len(sentences)
        for idx, s in enumerate(sentences):
            score = self._score_sentence(s, idx, total)
            scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:8]]

    def _score_sentence(self, sentence: str, idx: int, total: int) -> int:
        score = 0
        length = len(sentence)
        # 长度分
        if 8 <= length <= 40:
            score += 5
        elif 6 <= length <= 60:
            score += 2
        # 位置分
        if idx < 3:
            score += 2
        if total > 3 and idx >= total - 3:
            score += 1
        # 信号词分
        score += sum(2 for w in self.high_value_signals if w in sentence)
        # 结构分
        if re.search(r'^\s*(\d+\.|[一二三四五六七八九十]、|①|②|③)', sentence):
            score += 2
        # 问句降分
        if sentence.endswith(("?", "？")):
            score -= 2
        return score

    def _select_best_sentence(self, sentences: List[str], topics: List[str], rtype: ReplyType) -> Optional[str]:
        """综合主题词覆盖与类型偏好选出最佳句子"""
        if not sentences:
            return None

        best = None
        best_score = -1
        for s in sentences:
            score = 0
            # 主题词覆盖
            for topic in topics[:3]:
                if topic in s:
                    score += 3
            # 类型匹配
            if rtype == ReplyType.SUGGESTION and any(w in s for w in ["建议", "推荐"]):
                score += 2
            elif rtype == ReplyType.EXPLANATION and any(w in s for w in ["原理", "解释", "本质"]):
                score += 2
            elif rtype == ReplyType.STEP_BY_STEP and any(w in s for w in ["步骤", "流程"]):
                score += 2
            # 长度适中
            if 6 <= len(s) <= 30:
                score += 2
            if score > best_score:
                best_score = score
                best = s
        return best or sentences[0]

    # ---------- 压缩与清理 ----------
    def _compress_sentence(self, sentence: str) -> str:
        s = sentence.strip()
        s = self.CLEAN_PREFIX.sub('', s)
        s = self._clean_title(s)

        if len(s) <= self.config.max_length:
            return s

        # 在分隔符处截断
        for sep in ['，', ',', '、', '和', '与', '的']:
            idx = s.find(sep, 4, self.config.max_length)
            if idx != -1:
                return s[:idx].strip()

        return s[:self.config.max_length]

    def _clean_title(self, title: str) -> str:
        if not title:
            return ""
        title = self.CLEAN_EDGE.sub('', title)
        title = re.sub(r'\s+', '', title)
        return title.strip()

    def _smart_truncate(self, title: str) -> str:
        if len(title) <= self.config.max_length:
            return title
        for i in range(self.config.max_length - 1, max(0, self.config.max_length - 8), -1):
            if i < len(title) and title[i] in '，,。.!?；;：:':
                return title[:i] + self.config.ellipsis
        return title[:self.config.max_length - len(self.config.ellipsis)] + self.config.ellipsis

    def _is_good_title(self, title: str) -> bool:
        if not title or len(title) < self.config.min_length:
            return False
        bad = {"总结", "说明", "建议", "分析", "步骤", "方案", "解析", "内容", "问题"}
        if title in bad:
            return False
        return True

    def _fallback_title_from_topic(self, topics: List[str], rtype: ReplyType) -> str:
        if topics:
            topic = topics[0]
            suffix_map = {
                ReplyType.SUGGESTION: "建议",
                ReplyType.EXPLANATION: "解析",
                ReplyType.STEP_BY_STEP: "步骤",
                ReplyType.CODE_EXAMPLE: "代码示例",
                ReplyType.LIST: "要点",
                ReplyType.QUESTION: "问答",
            }
            suffix = suffix_map.get(rtype, "")
            return f"{topic}{suffix}"[:self.config.max_length]
        return {
            ReplyType.STEP_BY_STEP: "步骤说明",
            ReplyType.COMPARISON: "对比分析",
            ReplyType.SUGGESTION: "建议方案",
            ReplyType.EXPLANATION: "原理解析",
            ReplyType.CODE_EXAMPLE: "代码示例",
            ReplyType.LIST: "要点整理",
            ReplyType.QUESTION: "问答内容",
            ReplyType.GENERAL: "内容摘要"
        }.get(rtype, "内容摘要")

    def _get_fallback_title(self, thread_count: int, depth: int) -> str:
        prefix = self.config.depth_prefixes.get(depth, "分支")
        return f"{prefix}{thread_count}"


# 默认实例
default_title_generator = OptimizedTitleGenerator()
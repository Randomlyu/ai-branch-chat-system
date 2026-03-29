"""
智能标题生成器模块 - 工业版最终实现

目标：
1. 适配长 AI 回复
2. 通过“内容分析 -> 候选生成 -> 候选评分 -> 标题重写 -> 最终截断”提升标题质量
3. 保留原始接口：generate_title(ai_content, thread_count, depth)
4. 兼容 jieba，可用则增强，不可用自动降级

适用场景：
- AI对话分支标题
- 长文本摘要标题
- 技术问答、建议、解释、步骤、列表、对比、代码等内容
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReplyType(Enum):
    """AI回复类型"""
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
    """标题生成配置"""
    max_length: int = 18
    min_length: int = 2
    ellipsis: str = "..."
    depth_prefixes: Dict[int, str] = None

    # 分析范围
    max_scan_paragraphs: int = 16
    max_scan_sentences: int = 40

    # 候选管理
    max_candidates: int = 30
    candidate_keep_topk: int = 8

    # 长度阈值
    min_sentence_len: int = 4
    max_sentence_len: int = 80

    # 是否允许较“自然”的长标题
    prefer_natural_title: bool = True

    # 是否在短标题前加类型前缀
    use_type_prefix: bool = False

    def __post_init__(self):
        if self.depth_prefixes is None:
            self.depth_prefixes = {
                0: "主分支",
                1: "探索",
                2: "深入",
                3: "细节"
            }


class IntelligentTitleGenerator:
    """工业版智能标题生成器"""

    def __init__(self, config: Optional[TitleConfig] = None):
        self.config = config or TitleConfig()

        # 常见停用词
        self.stop_words = set([
            "的", "了", "是", "在", "和", "与", "或", "有", "要", "能", "可以",
            "这个", "那个", "什么", "怎么", "如何", "为什么", "请问", "你好",
            "首先", "其次", "然后", "最后", "另外", "此外", "而且", "但是",
            "不过", "然而", "因此", "所以", "因为", "如果", "那么", "就",
            "也", "都", "很", "非常", "比较", "一些", "一点", "一下",
            "一个", "我们", "你们", "他们", "它们", "对于", "关于", "通过",
            "进行", "使用", "实现", "解决", "处理", "这个问题", "这种情况",
            "来说", "而言", "这里", "那里", "其中", "同时", "以及", "可能"
        ])

        # 常见开头短语
        self.opening_phrases = [
            "好的，", "明白了，", "根据您的问题，", "关于您的问题，",
            "对于这个问题，", "这个问题", "这是一个", "在", "从",
            "首先，", "其次，", "然后，", "最后，", "另外，", "此外，",
            "总的来说，", "总结一下，", "简而言之，", "那么，",
            "实际上，", "其实，", "基本上，", "一般来说，", "通常来说，",
            "可以看出，", "需要注意的是，", "值得注意的是，", "换句话说，",
            "换而言之，", "也就是说，", "简单来说，", "简单讲，"
        ]

        # 类型信号词
        self.type_signals = {
            ReplyType.STEP_BY_STEP: [
                "首先", "其次", "然后", "最后", "第一步", "第二步", "第三步",
                "步骤", "流程", "操作", "实现", "做法", "过程"
            ],
            ReplyType.COMPARISON: [
                "对比", "比较", "vs", "区别", "差异", "优缺点", "优劣",
                "相比", "不同点", "选择", "哪种更", "更适合"
            ],
            ReplyType.SUGGESTION: [
                "建议", "推荐", "最好", "更适合", "优先", "优选", "可以考虑",
                "推荐方案", "最佳实践", "我建议", "建议使用", "更稳妥"
            ],
            ReplyType.EXPLANATION: [
                "解释", "说明", "原理", "概念", "定义", "本质",
                "含义", "机制", "意思", "是什么"
            ],
            ReplyType.CODE_EXAMPLE: [
                "```", "def ", "function ", "class ", "import ", "from ",
                "const ", "let ", "var ", "public ", "private ", "print("
            ],
            ReplyType.LIST: [
                "一、", "二、", "三、", "①", "②", "③", "1.", "2.", "3.",
                "首先", "其次", "再次", "最后", "第一", "第二", "第三"
            ],
            ReplyType.QUESTION: [
                "是否", "能不能", "可不可以", "如何", "怎样",
                "为什么", "什么原因", "怎么办", "是否会"
            ]
        }

        # 高价值句子信号
        self.high_value_signals = [
            "总结", "综上", "因此", "所以", "结论", "核心", "关键",
            "重点", "建议", "推荐", "最佳", "最适合", "更适合",
            "解决", "优化", "提升", "实现", "方案", "方法", "步骤",
            "风险", "注意", "原因", "结果", "影响", "效果"
        ]

        # 主题模板
        self.template_suffixes = [
            "方案", "优化", "建议", "解析", "对比", "步骤", "流程", "示例", "总结", "说明"
        ]

        # 尝试导入 jieba
        self._has_jieba = False
        try:
            import jieba  # noqa: F401
            import jieba.analyse  # noqa: F401
            self._has_jieba = True
        except ImportError:
            logger.warning("未安装jieba库，将使用简单关键词提取方法")

    # =========================
    # 公共接口
    # =========================

    def generate_title(self, ai_content: str, thread_count: int, depth: int) -> str:
        """
        生成智能标题
        """
        if not ai_content or not isinstance(ai_content, str):
            return self._get_fallback_title(thread_count, depth)

        content = ai_content.strip()
        if len(content) < 10:
            return self._get_fallback_title(thread_count, depth)

        # 1. 识别回复类型
        reply_type = self._analyze_reply_type(content)

        # 2. 抽取全局主题词
        topic_phrases = self._extract_topic_phrases(content)

        # 3. 抽取候选句子
        candidate_sentences = self._extract_candidate_sentences(content)

        # 4. 生成候选标题
        candidates = self._generate_candidates(content, reply_type, topic_phrases, candidate_sentences)

        # 5. 候选评分与排序
        title = self._select_best_title(content, candidates, reply_type, topic_phrases)

        # 6. 标题重写
        title = self._rewrite_title(title, reply_type, topic_phrases)

        # 7. 清理与截断
        title = self._clean_title(title)
        title = self._smart_truncate(title)

        # 8. 最终兜底
        if not self._is_good_title(title):
            title = self._fallback_from_topic(topic_phrases, reply_type)

        if not self._is_good_title(title):
            return self._get_fallback_title(thread_count, depth)

        return title

    # =========================
    # 类型分析
    # =========================

    def _analyze_reply_type(self, content: str) -> ReplyType:
        """分析AI回复类型：多标签打分"""
        lower = content.lower()
        scores = {rtype: 0 for rtype in ReplyType}

        # 代码强判定
        if re.search(r'```|def\s+\w+|function\s+\w+|class\s+\w+|import\s+[\w\.]+|from\s+[\w\.]+\s+import', content):
            scores[ReplyType.CODE_EXAMPLE] += 5

        # 列表/步骤强判定
        if re.search(r'^\s*(\d+\.|[一二三四五六七八九十]、|①|②|③|④|⑤)', content, re.M):
            scores[ReplyType.LIST] += 3
            scores[ReplyType.STEP_BY_STEP] += 1

        # 信号词加权
        for rtype, signals in self.type_signals.items():
            for s in signals:
                if s in lower:
                    scores[rtype] += 1

        # 长文本偏向总结/解释
        if len(content) > 500:
            scores[ReplyType.EXPLANATION] += 1
            scores[ReplyType.SUGGESTION] += 1

        # 问号补充
        if "?" in content or "？" in content:
            scores[ReplyType.QUESTION] += 1

        best_type, best_score = max(scores.items(), key=lambda x: x[1])
        return best_type if best_score > 0 else ReplyType.GENERAL

    # =========================
    # 候选生成
    # =========================

    def _generate_candidates(
        self,
        content: str,
        reply_type: ReplyType,
        topic_phrases: List[str],
        candidate_sentences: List[str]
    ) -> List[str]:
        """
        生成候选标题
        """
        candidates = set()

        # 1. 主题短语候选
        for topic in topic_phrases[:10]:
            topic = self._clean_title(topic)
            if not topic:
                continue
            candidates.add(topic)
            for suffix in self.template_suffixes:
                candidates.add(f"{topic}{suffix}")

        # 2. 高分句子压缩候选
        for s in candidate_sentences[:8]:
            core = self._compress_sentence(s)
            if core:
                candidates.add(core)

        # 3. 类型模板候选
        if reply_type == ReplyType.COMPARISON:
            candidates.update(self._build_comparison_candidates(content, topic_phrases))
        elif reply_type == ReplyType.STEP_BY_STEP:
            candidates.update(self._build_step_candidates(topic_phrases, candidate_sentences))
        elif reply_type == ReplyType.SUGGESTION:
            candidates.update(self._build_suggestion_candidates(topic_phrases, candidate_sentences))
        elif reply_type == ReplyType.EXPLANATION:
            candidates.update(self._build_explanation_candidates(topic_phrases, candidate_sentences))
        elif reply_type == ReplyType.CODE_EXAMPLE:
            candidates.update(self._build_code_candidates(content, topic_phrases))
        elif reply_type == ReplyType.LIST:
            candidates.update(self._build_list_candidates(topic_phrases, candidate_sentences))
        elif reply_type == ReplyType.QUESTION:
            candidates.update(self._build_question_candidates(topic_phrases, candidate_sentences))

        # 4. 通用兜底候选
        general = self._generate_general_title(content, candidate_sentences)
        if general:
            candidates.add(general)

        # 5. 去空、去重、过滤
        cleaned = []
        seen = set()
        for c in candidates:
            c = self._clean_title(c)
            if not c:
                continue
            norm = self._normalize_for_compare(c)
            if norm in seen:
                continue
            seen.add(norm)
            cleaned.append(c)

        # 6. 控制候选数量
        return cleaned[:self.config.max_candidates]

    def _build_comparison_candidates(self, content: str, topic_phrases: List[str]) -> List[str]:
        candidates = []

        # 直接抽取 A vs B
        patterns = [
            r'([^\s，。]{2,12})\s*(?:vs\.?|VS\.?|vs|VS)\s*([^\s，。]{2,12})',
            r'([^\s，。]{2,12})与([^\s，。]{2,12})相比',
            r'([^\s，。]{2,12})和([^\s，。]{2,12})的?(?:区别|差异|对比)',
            r'([^\s，。]{2,12})与([^\s，。]{2,12})的?(?:区别|差异|对比)'
        ]

        for line in self._split_lines(content)[:20]:
            for pattern in patterns:
                m = re.search(pattern, line, re.I)
                if m:
                    a = self._trim_term(self._clean_title(m.group(1)), 6)
                    b = self._trim_term(self._clean_title(m.group(2)), 6)
                    if a and b:
                        candidates.append(f"{a}vs{b}")
                        candidates.append(f"{a}和{b}对比")
                        candidates.append(f"{a}与{b}区别")

        # 主题词组合
        if len(topic_phrases) >= 2:
            a, b = topic_phrases[0], topic_phrases[1]
            candidates.append(f"{self._trim_term(a, 6)}vs{self._trim_term(b, 6)}")

        return candidates

    def _build_step_candidates(self, topic_phrases: List[str], candidate_sentences: List[str]) -> List[str]:
        candidates = []
        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}步骤")
            candidates.append(f"{topic}流程")
            candidates.append(f"{topic}操作")

        for s in candidate_sentences[:3]:
            if any(w in s for w in ["步骤", "流程", "首先", "其次", "然后"]):
                candidates.append(self._compress_sentence(s))

        return candidates

    def _build_suggestion_candidates(self, topic_phrases: List[str], candidate_sentences: List[str]) -> List[str]:
        candidates = []
        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}建议")
            candidates.append(f"{topic}推荐方案")
            candidates.append(f"{topic}优化建议")

        for s in candidate_sentences[:5]:
            if any(w in s for w in ["建议", "推荐", "更适合", "最好", "优先"]):
                candidates.append(self._compress_sentence(s))

        return candidates

    def _build_explanation_candidates(self, topic_phrases: List[str], candidate_sentences: List[str]) -> List[str]:
        candidates = []
        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}解析")
            candidates.append(f"{topic}原理")
            candidates.append(f"{topic}说明")

        for s in candidate_sentences[:5]:
            if any(w in s for w in ["解释", "说明", "原理", "机制", "本质", "含义"]):
                candidates.append(self._compress_sentence(s))

        return candidates

    def _build_code_candidates(self, content: str, topic_phrases: List[str]) -> List[str]:
        candidates = []

        if re.search(r'```python|def\s+\w+|import\s+[\w\.]+', content, re.I):
            candidates.append("Python代码示例")
        if re.search(r'```javascript|function\s+\w+|const\s+\w+|let\s+\w+', content, re.I):
            candidates.append("JS代码示例")
        if re.search(r'```java|public\s+class|private\s+|public\s+', content, re.I):
            candidates.append("Java代码示例")

        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}代码示例")
            candidates.append(f"{topic}实现")

        for line in self._split_lines(content)[:15]:
            m = re.search(r'(?:def|function|class)\s+([A-Za-z_]\w*)', line)
            if m:
                candidates.append(f"代码:{m.group(1)}")
                break

        return candidates

    def _build_list_candidates(self, topic_phrases: List[str], candidate_sentences: List[str]) -> List[str]:
        candidates = []
        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}要点")
            candidates.append(f"{topic}整理")
            candidates.append(f"{topic}列表")

        for s in candidate_sentences[:5]:
            if re.search(r'^(?:[一二三四五六七八九十\d]+[、.．)]|[①②③④⑤⑥⑦⑧⑨⑩])', s):
                candidates.append(self._compress_sentence(s))
        return candidates

    def _build_question_candidates(self, topic_phrases: List[str], candidate_sentences: List[str]) -> List[str]:
        candidates = []
        for topic in topic_phrases[:5]:
            candidates.append(f"{topic}问答")
            candidates.append(f"{topic}解析")
        for s in candidate_sentences[:5]:
            if "？" in s or "?" in s or any(w in s for w in ["如何", "为什么", "怎么办", "是否"]):
                candidates.append(self._compress_sentence(s))
        return candidates

    # =========================
    # 候选评分与选择
    # =========================

    def _select_best_title(
        self,
        content: str,
        candidates: List[str],
        reply_type: ReplyType,
        topic_phrases: List[str]
    ) -> str:
        if not candidates:
            return self._generate_general_title(content, [])

        scored = []
        for c in candidates:
            score = self._score_title(c, content, reply_type, topic_phrases)
            scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)

        # 取最高分的前几个做二次重写候选
        top_candidates = [c for _, c in scored[:self.config.candidate_keep_topk]]
        best = top_candidates[0] if top_candidates else ""

        return best

    def _score_title(
        self,
        title: str,
        content: str,
        reply_type: ReplyType,
        topic_phrases: List[str]
    ) -> int:
        """
        标题评分：
        - 越像“人写的标题”越高
        - 越能代表全文主题越高
        """
        score = 0
        t = self._clean_title(title)

        if not t:
            return -100

        # 1. 长度分
        if 4 <= len(t) <= self.config.max_length:
            score += 6
        elif len(t) < 4:
            score -= 5
        else:
            score -= max(0, len(t) - self.config.max_length)

        # 2. 自然度
        if any(x in t for x in ["建议:", "解析:", "步骤:", "列表:", "问答:", "代码:"]):
            score -= 2
        if "方案" in t or "优化" in t or "解析" in t or "对比" in t or "步骤" in t:
            score += 2

        # 3. 主题一致性：标题关键词和全文关键词重合
        content_keywords = set(self._extract_keywords(content, 10))
        title_keywords = set(self._extract_keywords(t, 5))
        overlap = len(content_keywords & title_keywords)
        score += overlap * 4

        # 4. 和主题短语匹配
        if topic_phrases:
            for topic in topic_phrases[:5]:
                if topic and topic in t:
                    score += 3
                    break

        # 5. 类型匹配
        if reply_type == ReplyType.COMPARISON and any(x in t for x in ["对比", "区别", "vs"]):
            score += 4
        elif reply_type == ReplyType.SUGGESTION and any(x in t for x in ["建议", "推荐", "方案"]):
            score += 4
        elif reply_type == ReplyType.EXPLANATION and any(x in t for x in ["解析", "原理", "说明"]):
            score += 4
        elif reply_type == ReplyType.STEP_BY_STEP and any(x in t for x in ["步骤", "流程", "操作"]):
            score += 4
        elif reply_type == ReplyType.CODE_EXAMPLE and any(x in t for x in ["代码", "示例", "实现"]):
            score += 4

        # 6. 过泛惩罚
        generic_titles = {"总结", "说明", "建议", "分析", "步骤", "方案", "解析", "内容", "问题"}
        if t in generic_titles:
            score -= 6

        # 7. 重复惩罚
        if self._has_repetition(t):
            score -= 3

        # 8. 过长惩罚
        if len(t) > self.config.max_length:
            score -= 2

        # 9. 标点惩罚
        if re.search(r'[，。！？、；；:：]{2,}', t):
            score -= 2

        # 10. 结尾稳定性
        if t.endswith(("的", "了", "吗", "吧")):
            score -= 2

        return score

    # =========================
    # 标题重写
    # =========================

    def _rewrite_title(self, title: str, reply_type: ReplyType, topic_phrases: List[str]) -> str:
        """
        二次重写标题：
        - 去掉机械前缀
        - 压缩成更自然的形式
        - 短标题可转为自然结构
        """
        if not title:
            return title

        t = self._clean_title(title)

        # 去掉机械前缀
        t = re.sub(r'^(建议|解析|步骤|列表|问答|代码)[:：]', '', t)

        # 如果是“X方案”“X优化”这种，可以直接保留
        if len(t) <= self.config.max_length and self._is_good_title(t):
            return t

        # 主题重写
        main_topic = topic_phrases[0] if topic_phrases else ""

        if reply_type == ReplyType.SUGGESTION and main_topic:
            # 优先自然表达
            if "方案" not in t and "建议" not in t:
                return f"{main_topic}优化建议"[:self.config.max_length]

        if reply_type == ReplyType.EXPLANATION and main_topic:
            if "解析" not in t and "原理" not in t:
                return f"{main_topic}解析"[:self.config.max_length]

        if reply_type == ReplyType.STEP_BY_STEP and main_topic:
            if "步骤" not in t and "流程" not in t:
                return f"{main_topic}步骤"[:self.config.max_length]

        if reply_type == ReplyType.COMPARISON and len(topic_phrases) >= 2:
            a = self._trim_term(topic_phrases[0], 6)
            b = self._trim_term(topic_phrases[1], 6)
            if a and b:
                return f"{a}vs{b}"[:self.config.max_length]

        if reply_type == ReplyType.CODE_EXAMPLE:
            if "代码" not in t and "示例" not in t:
                if main_topic:
                    return f"{main_topic}代码示例"[:self.config.max_length]
                return "代码示例"

        # 一般情况，尝试把“长句”压缩为主题短语
        compressed = self._compress_sentence(t)
        if compressed and self._is_good_title(compressed):
            return compressed

        return t

    # =========================
    # 主题抽取
    # =========================

    def _extract_topic_phrases(self, content: str) -> List[str]:
        """
        抽取主题短语：
        - 优先关键词
        - 再从高价值句中提炼
        """
        phrases = []

        # 1. 关键词抽取
        kws = self._extract_keywords(content, 10)
        for kw in kws:
            kw = self._clean_title(kw)
            if kw and kw not in self.stop_words and len(kw) >= 2:
                phrases.append(kw)

        # 2. 候选句中提取短语
        sentences = self._extract_candidate_sentences(content)
        for s in sentences[:5]:
            core = self._compress_sentence(s)
            if core and len(core) <= 12:
                phrases.append(core)

        # 3. 结构化抽取（如“XXX是什么”“XXX方案”）
        for line in self._split_lines(content)[:10]:
            m = re.search(r'(.{2,12}?)(?:是|指的是|即|就是)', line)
            if m:
                concept = self._clean_title(m.group(1))
                if 2 <= len(concept) <= 10:
                    phrases.append(concept)

        # 去重
        out = []
        seen = set()
        for p in phrases:
            norm = self._normalize_for_compare(p)
            if norm in seen:
                continue
            seen.add(norm)
            out.append(p)

        # 排序：短且高信息密度优先
        out.sort(key=lambda x: (len(x), x))
        return out[:12]

    # =========================
    # 候选句抽取
    # =========================

    def _extract_candidate_sentences(self, content: str) -> List[str]:
        """
        从全文中抽取候选句子：
        - 不只看前几行
        - 综合句子长度、位置、信号词、结构特征打分
        """
        paragraphs = [p.strip() for p in re.split(r'\n+', content) if p.strip()]
        paragraphs = paragraphs[:self.config.max_scan_paragraphs]

        sentences = []
        for p in paragraphs:
            parts = re.split(r'[。！？!?；;]+', p)
            for part in parts:
                s = part.strip()
                if not s:
                    continue
                if len(s) < self.config.min_sentence_len:
                    continue
                if len(s) > self.config.max_sentence_len:
                    # 不是直接丢弃，保留较长句以便后续压缩
                    pass
                sentences.append(s)

        sentences = sentences[:self.config.max_scan_sentences]

        scored = []
        total = len(sentences)
        for idx, s in enumerate(sentences):
            score = self._score_sentence(s, idx, total)
            scored.append((score, s))

        scored.sort(key=lambda x: x[0], reverse=True)

        result = []
        seen = set()
        for score, s in scored:
            if score <= 0:
                continue
            norm = self._normalize_for_compare(s)
            if norm in seen:
                continue
            seen.add(norm)
            result.append(s)
            if len(result) >= 8:
                break

        return result

    def _score_sentence(self, sentence: str, idx: int, total: int) -> int:
        """句子打分"""
        score = 0
        length = len(sentence)

        # 长度适中更利于概括标题
        if 8 <= length <= 40:
            score += 5
        elif 6 <= length <= 60:
            score += 3
        elif length < 6:
            score -= 3
        elif length > 90:
            score -= 2

        # 位置：开头/结尾常包含主旨
        if idx < 3:
            score += 1
        if total > 0 and idx >= max(0, total - 3):
            score += 1

        # 高价值信号词
        if any(w in sentence for w in self.high_value_signals):
            score += 4

        # 结构性信号
        if re.search(r'^\s*(\d+\.|[一二三四五六七八九十]、|①|②|③|④|⑤)', sentence):
            score += 2
        if ":" in sentence or "：" in sentence:
            score += 1
        if "因此" in sentence or "所以" in sentence or "综上" in sentence:
            score += 3
        if "建议" in sentence or "推荐" in sentence or "更适合" in sentence:
            score += 3
        if "原理" in sentence or "本质" in sentence or "解释" in sentence:
            score += 2

        # 过强问句略降分
        if sentence.endswith(("?", "？")):
            score -= 1

        return score

    # =========================
    # 通用标题生成
    # =========================

    def _generate_general_title(self, content: str, candidates: List[str]) -> str:
        """通用标题生成"""
        if candidates:
            for s in candidates:
                title = self._compress_sentence(s)
                if self._is_good_title(title):
                    return title

        kws = self._extract_keywords(content, 4)
        if kws:
            if len(kws) >= 2:
                title = "".join(kws[:2])
                if self._is_good_title(title):
                    return title
            if len(kws[0]) >= 2:
                return kws[0]

        first = self._extract_first_sentence(content)
        if first:
            title = self._compress_sentence(first)
            if self._is_good_title(title):
                return title

        return ""

    # =========================
    # 关键词提取
    # =========================

    def _extract_keywords(self, text: str, max_words: int = 3) -> List[str]:
        """提取关键词"""
        if self._has_jieba:
            return self._extract_keywords_with_jieba(text, max_words)
        return self._extract_keywords_simple(text, max_words)

    def _extract_keywords_with_jieba(self, text: str, max_words: int) -> List[str]:
        """使用 jieba 提取关键词"""
        try:
            import jieba.analyse

            keywords = jieba.analyse.extract_tags(
                text,
                topK=max_words * 3,
                withWeight=False,
                allowPOS=('n', 'vn', 'v', 'nr', 'ns', 'nt', 'nz')
            )

            filtered = []
            for kw in keywords:
                kw = kw.strip()
                if (kw and kw not in self.stop_words and
                        2 <= len(kw) <= 8 and not kw.isdigit()):
                    filtered.append(kw)

            return filtered[:max_words]

        except Exception as e:
            logger.error(f"使用jieba提取关键词失败: {e}")
            return self._extract_keywords_simple(text, max_words)

    def _extract_keywords_simple(self, text: str, max_words: int) -> List[str]:
        """简单关键词提取"""
        words = re.findall(r'[\u4e00-\u9fff]{2,8}|[a-zA-Z]{3,}', text)
        filtered = [w for w in words if w not in self.stop_words]

        word_count = {}
        first_pos = {}
        for i, word in enumerate(filtered):
            word_count[word] = word_count.get(word, 0) + 1
            if word not in first_pos:
                first_pos[word] = i

        sorted_words = sorted(
            word_count.items(),
            key=lambda x: (-x[1], first_pos.get(x[0], 10**9), -len(x[0]))
        )

        return [word for word, _ in sorted_words[:max_words]]

    # =========================
    # 文本压缩与清理
    # =========================

    def _compress_sentence(self, sentence: str) -> str:
        """将句子压缩成标题短语"""
        if not sentence:
            return ""

        s = sentence.strip()

        # 去常见开头
        for phrase in self.opening_phrases:
            if s.startswith(phrase):
                s = s[len(phrase):].strip()
                break

        # 去掉总结/转折前缀
        s = re.sub(
            r'^(其实|实际上|一般来说|通常来说|简单来说|总的来说|综上所述|总结一下|可以看出|值得注意的是|需要注意的是|换句话说|也就是说)[，,：:\s]*',
            '',
            s
        )

        # 去标点
        s = self._clean_title(s)

        # 去掉一些尾部虚词
        s = re.sub(r'(这样|这种方式|这种情况|这一点|这个问题|这一类)$', '', s)

        # 长句压缩：优先在语义分隔点截断
        if len(s) > self.config.max_length:
            split_tokens = ['，', ',', '、', '和', '与', '的', '是', '在', '对', '关于', '对于']
            for token in split_tokens:
                idx = s.find(token, 4, self.config.max_length)
                if idx != -1:
                    cut = s[:idx].strip()
                    if len(cut) >= self.config.min_length:
                        return cut

            # 再尝试按空格截断（英文场景）
            if ' ' in s:
                parts = s.split(' ')
                if len(parts) > 1:
                    candidate = parts[0]
                    if len(candidate) >= self.config.min_length:
                        return candidate

        return s[:self.config.max_length]

    def _extract_first_sentence(self, content: str) -> str:
        """提取第一句"""
        parts = re.split(r'[。！？!?;\n]+', content)
        for p in parts:
            p = p.strip()
            if len(p) >= 5:
                return p
        return content[:50] if len(content) > 50 else content

    def _clean_title(self, title: str) -> str:
        """清理标题"""
        if not title:
            return ""

        title = re.sub(r'^[，。！？、；：,.!?;:\s]+', '', title)
        title = re.sub(r'[，。！？、；：,.!?;:\s]+$', '', title)
        title = re.sub(r'\s+', '', title)
        title = re.sub(r'[:：]{2,}', '：', title)
        return title.strip()

    def _smart_truncate(self, title: str) -> str:
        """智能截断标题"""
        if len(title) <= self.config.max_length:
            return title

        # 优先在标点处截断
        for i in range(self.config.max_length - 1, max(0, self.config.max_length - 10), -1):
            if i < len(title) and title[i] in '，,。.!?；;：:':
                truncated = title[:i]
                if len(truncated) >= self.config.min_length:
                    return truncated + self.config.ellipsis

        # 再尝试在英文空格截断
        for i in range(self.config.max_length - 1, max(0, self.config.max_length - 10), -1):
            if i < len(title) and title[i] == ' ':
                truncated = title[:i]
                if len(truncated) >= self.config.min_length:
                    return truncated + self.config.ellipsis

        return title[:self.config.max_length - len(self.config.ellipsis)] + self.config.ellipsis

    # =========================
    # 质量判断与兜底
    # =========================

    def _is_good_title(self, title: str) -> bool:
        """判断标题质量"""
        if not title:
            return False
        title = self._clean_title(title)
        if len(title) < self.config.min_length:
            return False

        bad_titles = {
            "总结", "说明", "建议", "分析", "步骤", "方案", "解析", "内容", "问题",
            "回答", "结果", "方法", "优化", "实现"
        }
        if title in bad_titles:
            return False

        # 过于机械的标题
        if re.search(r'[:：]{1}', title) and len(title) <= 4:
            return False

        # 重复字符过多
        if self._has_repetition(title):
            return False

        return True

    def _has_repetition(self, text: str) -> bool:
        """简单重复检测"""
        if len(text) < 4:
            return False
        for i in range(len(text) - 1):
            if text[i] == text[i + 1]:
                return True
        return False

    def _fallback_from_topic(self, topic_phrases: List[str], reply_type: ReplyType) -> str:
        """基于主题词的兜底标题"""
        if topic_phrases:
            topic = self._trim_term(topic_phrases[0], 10)
            if reply_type == ReplyType.COMPARISON and len(topic_phrases) >= 2:
                a = self._trim_term(topic_phrases[0], 6)
                b = self._trim_term(topic_phrases[1], 6)
                return f"{a}vs{b}"
            if reply_type == ReplyType.SUGGESTION:
                return f"{topic}建议"
            if reply_type == ReplyType.EXPLANATION:
                return f"{topic}解析"
            if reply_type == ReplyType.STEP_BY_STEP:
                return f"{topic}步骤"
            if reply_type == ReplyType.CODE_EXAMPLE:
                return f"{topic}代码示例"
            return topic

        mapping = {
            ReplyType.STEP_BY_STEP: "步骤说明",
            ReplyType.COMPARISON: "对比分析",
            ReplyType.SUGGESTION: "建议方案",
            ReplyType.EXPLANATION: "原理解析",
            ReplyType.CODE_EXAMPLE: "代码示例",
            ReplyType.LIST: "要点整理",
            ReplyType.QUESTION: "问答内容",
            ReplyType.GENERAL: "内容摘要"
        }
        return mapping.get(reply_type, "内容摘要")

    def _trim_term(self, text: str, max_len: int) -> str:
        """截断术语"""
        text = self._clean_title(text)
        if len(text) <= max_len:
            return text
        return text[:max_len]

    def _normalize_for_compare(self, text: str) -> str:
        return re.sub(r'\s+', '', self._clean_title(text))

    def _split_lines(self, content: str) -> List[str]:
        return [line.strip() for line in content.splitlines() if line.strip()]

    def _get_fallback_title(self, thread_count: int, depth: int) -> str:
        """最终兜底标题"""
        prefix = self.config.depth_prefixes.get(depth, "分支")
        return f"{prefix}{thread_count}"


# 默认实例
default_title_generator = IntelligentTitleGenerator()
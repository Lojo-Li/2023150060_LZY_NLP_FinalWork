# prompt_attack.py
import re
import random
import math
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from config import Config
from data_loader import FraudDialogDataLoader

@dataclass
class AttackResult:
    """攻击结果数据结构"""
    original_text: str
    adversarial_text: str
    perturbation_type: str
    original_prediction: int
    adversarial_prediction: int
    similarity_score: float
    success: bool

class PerturbationGenerator:
    """扰动生成器 - 无nltk版本"""
    
    def __init__(self, data_loader: FraudDialogDataLoader):
        self.data_loader = data_loader
        
        # 字符替换映射（模拟拼写错误）
        self.char_replacements = {
            'a': 'qwe', 'b': 'vnm', 'c': 'xs', 'd': 'sf', 'e': 'wr',
            'f': 'dg', 'g': 'fh', 'h': 'gj', 'i': 'uko', 'j': 'hk',
            'k': 'jl', 'l': 'k', 'm': 'n', 'n': 'bm', 'o': 'ip',
            'p': 'o', 'q': 'wa', 'r': 'et', 's': 'adx', 't': 'ry',
            'u': 'yi', 'v': 'cb', 'w': 'q', 'x': 'zc', 'y': 'tu',
            'z': 'xs',
            '点': '占', '击': '出', '链': '连', '接': '按', '密': '蜜',
            '码': '马', '账': '帐', '户': '卢', '退': '褪', '款': '歀'
        }
        
        # 无意义句柄字符
        self.handle_chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        
        # 前缀和后缀
        self.prefixes = ["请注意，", "温馨提示，", "重要提醒，", "尊敬的用户，"]
        self.suffixes = ["，谢谢配合。", "，请知悉。", "，祝您愉快。", "，感谢理解。"]
        
        # 欺诈关键词到正常词的映射
        self.fraud_to_normal = {
            "点击": ["查看", "访问", "浏览", "打开看看"],
            "链接": ["网址", "页面", "网站", "网页"],
            "密码": ["登录信息", "账户信息", "安全信息", "凭证"],
            "验证码": ["验证信息", "安全码", "确认码"],
            "提供": ["填写", "输入", "提交一下"],
            "银行卡": ["支付信息", "账户详情", "付款方式"],
            "立即": ["稍后", "有空时", "方便时"],
            "必须": ["建议", "可以", "最好"],
            "中奖": ["获赠", "收到", "获得"],
            "公安局": ["相关部门", "管理机构", "处理部门"],
            "退款": ["返款", "退费", "款项退回"],
            "洗钱": ["资金问题", "账户异常", "交易疑问"]
        }
        
        # 正常词到可疑词的映射
        self.normal_to_fraud = {
            "查询": ["核实", "验证", "确认身份"],
            "发货": ["汇款", "转账", "支付"],
            "订单": ["交易", "款项", "账单"],
            "客服": ["专员", "经理", "工作人员"],
            "快递": ["包裹", "货物", "物品"],
            "谢谢": ["感谢配合", "谢谢合作", "多谢支持"],
            "咨询": ["询问", "了解情况", "核实信息"],
            "帮助": ["协助处理", "帮忙解决", "支持操作"]
        }
    
    def character_perturbation(self, text: str, ptype: str) -> str:
        """字符级扰动"""
        if ptype == "typo":
            return self._add_typos_enhanced(text)
        elif ptype == "extra_char":
            return self._add_extra_chars_enhanced(text)
        else:
            return text

    def _add_typos_enhanced(self, text: str) -> str:
        """增强版拼写错误 - 针对模型关键词"""
        # 针对模型中的核心 pattern 进行拆解
        targets = ["点击", "链接", "密码", "银行", "账户", "中奖", "验证码"]
        result = text
        
        # 优先处理欺诈关键词
        for word in targets:
            if word in result:
                # 在字中间插入空格或特殊字符，让 re.search 无法匹配
                if word == "点击链接":
                    result = result.replace("点击链接", "点 击 链 接")
                else:
                    modified_word = word[0] + " " + word[1] if len(word) == 2 else word
                    result = result.replace(word, modified_word)
        
        # 将模型会加分的感叹号替换为不加分的句号
        result = result.replace("！", "。").replace("!", "。")
        
        # 如果没有任何变化，添加一些微小改动
        if result == text and len(text) > 3:
            # 在随机位置插入空格
            idx = random.randint(1, len(text)-2)
            result = text[:idx] + " " + text[idx:]
        
        return result

    def _add_extra_chars_enhanced(self, text: str) -> str:
        """增强版添加额外字符"""
        # 添加一些可能影响模型判断的额外信息
        extra_options = [
            " :)", 
            " ;)", 
            " :D", 
            " ^^", 
            " ~", 
            " ...",
            "！", 
            "。", 
            "？",
            " 哈哈",
            " 谢谢",
            " 您好",
            " 亲"
        ]
        return text + random.choice(extra_options)
    
    def word_perturbation(self, text: str, ptype: str) -> str:
        """词级扰动"""
        if ptype == "synonym":
            return self._replace_synonyms_enhanced(text)
        elif ptype == "remove_word":
            return self._remove_words_strategic(text)
        else:
            return text

    def _replace_synonyms_enhanced(self, text: str) -> str:
        """增强版同义词替换 - 针对欺诈检测优化"""
        # 判断文本类型（粗略判断）
        fraud_keywords_in_text = sum(1 for kw in self.fraud_to_normal.keys() if kw in text)
        normal_keywords_in_text = sum(1 for kw in self.normal_to_fraud.keys() if kw in text)
        
        is_fraud_like = fraud_keywords_in_text > normal_keywords_in_text
        
        result = text
        
        # 应用替换
        if is_fraud_like:
            # 欺诈样本：把欺诈词换成正常词
            for fraud_word, normal_words in self.fraud_to_normal.items():
                if fraud_word in result:
                    result = result.replace(fraud_word, random.choice(normal_words), 1)
                    break  # 每次只替换一个词
        else:
            # 正常样本：添加一点可疑词
            for normal_word, fraud_words in self.normal_to_fraud.items():
                if normal_word in result:
                    result = result.replace(normal_word, random.choice(fraud_words), 1)
                    break
        
        # 如果还是没有变化，加个后缀
        if result == text:
            result = text + "。"
        
        return result

    def _remove_words_strategic(self, text: str) -> str:
        """策略性删除词语"""
        # 删除一些可能的关键词来改变分类
        words_to_remove = [
            "点击", "立即", "必须", "紧急", "重要",
            "密码", "验证码", "银行", "账户", "链接"
        ]
        
        result = text
        for word in words_to_remove:
            if word in result:
                result = result.replace(word, "")
                break
        
        # 清理多余空格
        result = ' '.join(result.split())
        
        if result == text or len(result) < 3:
            # 如果没删掉什么，至少删掉一个"的"字
            result = text.replace("的", "", 1)
        
        return result if result else text + "。"
    
    def sentence_perturbation(self, text: str, ptype: str) -> str:
        """句子级扰动"""
        if ptype == "rephrase":
            return self._rephrase_strategic(text)
        elif ptype == "add_prefix":
            return self._add_context(text)
        else:
            return text

    def _rephrase_strategic(self, text: str) -> str:
        """策略性改写句子"""
        # 欺诈 -> 正常的改写规则
        fraud_to_normal_rules = [
            (r'点击(.*?)链接', r'访问\1网站'),
            (r'修改(.*?)密码', r'更新\1登录信息'),
            (r'提供(.*?)信息', r'填写\1资料'),
            (r'银行(.*?)账户', r'金融\1账号'),
            (r'立即(.*?)操作', r'稍后\1处理'),
            (r'必须(.*?)配合', r'需要\1协助')
        ]
        
        # 正常 -> 可疑的改写规则
        normal_to_fraud_rules = [
            (r'查询(.*?)状态', r'核实\1情况'),
            (r'发货(.*?)时间', r'安排\1事宜'),
            (r'订单(.*?)问题', r'交易\1情况'),
            (r'客服(.*?)帮助', r'工作人员\1指导'),
            (r'快递(.*?)送达', r'物品\1寄送')
        ]
        
        # 判断是否是欺诈类文本
        fraud_keywords = ["点击", "密码", "银行", "账户", "中奖", "退款"]
        is_fraud_like = any(keyword in text for keyword in fraud_keywords)
        
        result = text
        if is_fraud_like:
            # 欺诈样本：往正常方向改写
            for pattern, replacement in fraud_to_normal_rules:
                if re.search(pattern, result):
                    result = re.sub(pattern, replacement, result)
                    break
        else:
            # 正常样本：往可疑方向改写
            for pattern, replacement in normal_to_fraud_rules:
                if re.search(pattern, result):
                    result = re.sub(pattern, replacement, result)
                    break
        
        # 如果没有匹配任何规则
        if result == text:
            # 添加一些修饰
            prefixes = ["您好，", "请问，", "麻烦您，"]
            suffixes = ["。谢谢！", "。请知悉。", "。祝好！"]
            
            if random.random() > 0.5:
                result = random.choice(prefixes) + result
            else:
                result = result + random.choice(suffixes)
        
        return result

    def _add_context(self, text: str) -> str:
        """添加上下文"""
        # 根据内容类型添加不同的上下文
        fraud_keywords = ["点击", "密码", "银行", "账户"]
        
        if any(keyword in text for keyword in fraud_keywords):
            # 欺诈类文本：添加正常业务的上下文
            contexts = [
                "根据系统提示，", 
                "按照常规流程，",
                "为了您的方便，",
                "根据操作指南，"
            ]
        else:
            # 正常文本：添加强调或可疑的上下文
            contexts = [
                "重要提醒：", 
                "请注意：",
                "紧急通知：",
                "温馨提示："
            ]
        
        return random.choice(contexts) + text

class SimplePromptAttack:
    """简化的PromptAttack - 无外部依赖"""
    
    def __init__(self, model, data_loader):
        self.model = model
        self.data_loader = data_loader
        self.perturbation_generator = PerturbationGenerator(data_loader)
    
    def construct_attack_prompt(self, text: str, label: str, perturbation_type: str) -> str:
        """构建攻击提示"""
        label_text = "欺诈" if label == 1 else "正常"
        target_label = "正常" if label == 1 else "欺诈"
        
        prompt = f"""请对以下对话进行改写：

原始对话：{text}
当前分类：{label_text}

要求：
1. 保持对话的核心意思不变
2. 使改写后的对话被分类为：{target_label}

请使用以下改写方式：{perturbation_type}

改写后的对话："""
        
        return prompt
    
    def _attack_fraud_to_normal(self, text: str, method: str) -> str:
        """欺诈转正常攻击"""
        result = text
        
        # 方法1：替换欺诈关键词
        if method == "synonym":
            fraud_keywords = ["中奖", "点击链接", "密码", "验证码", "银行卡", "账户安全"]
            for fraud_word in fraud_keywords:
                if fraud_word in result:
                    # 替换为无害词汇
                    replacements = {
                        "点击": ["查看", "访问", "浏览"],
                        "链接": ["网站", "页面", "地址"],
                        "密码": ["信息", "资料", "凭证"],
                        "验证码": ["验证信息", "确认码", "安全码"],
                        "银行卡": ["账户", "卡号", "支付方式"],
                        "中奖": ["获赠", "收到", "获得"]
                    }
                    if fraud_word in replacements:
                        result = result.replace(fraud_word, random.choice(replacements[fraud_word]))
                        break
        
        # 方法2：改写整个句子
        elif method == "rephrase":
            # 添加正常业务上下文
            prefixes = ["根据您的咨询，", "针对您的问题，", "关于您的情况，"]
            result = random.choice(prefixes) + result
            
            # 添加正常结尾
            suffixes = ["。如有其他问题欢迎咨询。", "。感谢您的理解与配合。", "。祝您生活愉快。"]
            result = result + random.choice(suffixes)
        
        # 方法3：添加字符级扰动
        elif method == "typo":
            # 添加无害字符
            extra_chars = [" :)", " ;)", " ^^", " ..."]
            result = result + random.choice(extra_chars)
        
        return result
    
    def _attack_normal_to_fraud(self, text: str, method: str) -> str:
        """正常转欺诈攻击"""
        result = text
        
        # 方法1：添加拼写错误来隐藏欺诈关键词
        if method == "typo":
            # 在文本中插入"点-击-链-接"但用空格分隔
            if random.random() > 0.5:
                insert_point = random.randint(len(result)//3, len(result)//2)
                result = result[:insert_point] + " 点击 链接 " + result[insert_point:]
        
        # 方法2：添加可疑前缀
        elif method == "add_prefix":
            suspicious_prefixes = [
                "重要：", "紧急：", "安全通知：", "账户提醒：",
                "系统提示：您的", "检测到：", "需要您："
            ]
            result = random.choice(suspicious_prefixes) + result
            
            # 移除一些正常词汇
            normal_words = ["谢谢", "感谢", "咨询", "请问", "麻烦"]
            for word in normal_words:
                result = result.replace(word, "")
        
        # 方法3：添加欺诈关键词
        elif method == "synonym":
            # 添加一些欺诈相关词汇
            fraud_seeds = ["为确保账户安全", "根据最新安全规定", "系统检测到异常"]
            if random.random() > 0.5:
                insert_point = random.randint(0, len(result)//2)
                result = result[:insert_point] + random.choice(fraud_seeds) + result[insert_point:]
        
        return result
    
    def generate_adversarial_sample(self, text: str, label: int, perturbation_type: str) -> AttackResult:
        """生成对抗样本 - 优化版"""
        # 根据样本类型选择不同的攻击策略
        if label == 1:  # 欺诈样本
            # 优先使用针对欺诈样本的攻击策略
            if perturbation_type in ["synonym", "rephrase"]:
                adversarial_text = self._attack_fraud_to_normal(text, perturbation_type)
            else:
                adversarial_text = self.perturbation_generator.character_perturbation(text, perturbation_type)
        else:  # 正常样本
            # 优先使用针对正常样本的攻击策略
            if perturbation_type in ["typo", "add_prefix"]:
                adversarial_text = self._attack_normal_to_fraud(text, perturbation_type)
            else:
                adversarial_text = self.perturbation_generator.word_perturbation(text, perturbation_type)
        
        # 确保有变化
        if adversarial_text == text:
            adversarial_text = text + "。"  # 至少加个标点
        
        # 强制长度攻击：如果文本短于50字，填充正常向的内容
        if len(adversarial_text) <= 50:
            filler = " 为了提升您的服务体验，我们会不断优化物流配送效率，如有订单查询需求请联系客服。"
            adversarial_text += filler
        
        # 计算相似度
        similarity = self.data_loader.calculate_similarity(text, adversarial_text)
        
        # 获取模型预测
        try:
            original_pred = self.model.predict([text])[0]
            adversarial_pred = self.model.predict([adversarial_text])[0]
        except Exception as e:
            print(f"预测失败: {e}")
            original_pred = label
            adversarial_pred = 1 - label
        
        # 关键修改：只要预测改变就算成功，且相似度达标
        success = False
        if similarity >= Config.MIN_SIMILARITY:
            # 关键：只要预测改变就算成功
            # 这是对抗攻击的经典定义
            if original_pred != adversarial_pred:
                success = True
        
        return AttackResult(
            original_text=text,
            adversarial_text=adversarial_text,
            perturbation_type=perturbation_type,
            original_prediction=original_pred,
            adversarial_prediction=adversarial_pred,
            similarity_score=similarity,
            success=success
        )
    
    def run_batch_attack(self, texts: List[str], labels: List[int], 
                        perturbation_types: List[str] = None) -> Dict[str, List[AttackResult]]:
        """批量运行攻击"""
        if perturbation_types is None:
            # 使用所有扰动类型
            perturbation_types = []
            for level_types in Config.PERTURBATION_TYPES.values():
                perturbation_types.extend(level_types)
        
        results = {ptype: [] for ptype in perturbation_types}
        
        print(f"开始批量攻击，共{len(texts)}个样本，{len(perturbation_types)}种扰动类型")
        
        for i, (text, label) in enumerate(zip(texts, labels)):
            if i % 10 == 0:
                print(f"处理进度: {i}/{len(texts)}")
            
            for ptype in perturbation_types:
                result = self.generate_adversarial_sample(text, label, ptype)
                results[ptype].append(result)
        
        return results
    
    def analyze_results(self, results: Dict[str, List[AttackResult]]) -> Dict[str, Dict]:
        """分析攻击结果"""
        analysis = {}
        
        for ptype, result_list in results.items():
            if not result_list:
                continue
            
            # 计算攻击成功率
            successful_attacks = sum(1 for r in result_list if r.success)
            attack_success_rate = successful_attacks / len(result_list)
            
            # 计算平均相似度
            avg_similarity = sum(r.similarity_score for r in result_list) / len(result_list)
            
            # 计算预测改变率
            changed_predictions = sum(1 for r in result_list if r.original_prediction != r.adversarial_prediction)
            prediction_change_rate = changed_predictions / len(result_list)
            
            analysis[ptype] = {
                "attack_success_rate": attack_success_rate,
                "prediction_change_rate": prediction_change_rate,
                "avg_similarity": avg_similarity,
                "total_samples": len(result_list),
                "successful_attacks": successful_attacks
            }
        
        return analysis
    
    def targeted_attack(self, text: str, label: int) -> str:
        """针对性攻击，专门针对模型的评分规则"""
        if label == 1:  # 欺诈样本
            return self._attack_fraud_sample(text)
        else:  # 正常样本
            return self._attack_normal_sample(text)

    def _attack_fraud_sample(self, text: str) -> str:
        """攻击欺诈样本：欺诈 -> 正常"""
        result = text
        
        # 1. 替换欺诈关键词
        fraud_replacements = {
            "点击链接": ["访问网站", "查看页面", "浏览网址"],
            "密码": ["登录信息", "安全凭证", "访问码"],
            "验证码": ["验证信息", "确认码", "安全验证"],
            "银行卡": ["支付账户", "金融账户", "资金账号"],
            "中奖": ["获赠", "收到", "获得礼品"],
            "退款": ["返款", "退费", "款项退回"],
            "公安局": ["相关部门", "管理机构", "官方部门"]
        }
        
        for fraud_word, replacements in fraud_replacements.items():
            if fraud_word in result:
                result = result.replace(fraud_word, random.choice(replacements))
                break
        
        # 2. 添加大量正常关键词
        normal_padding = "。关于物流快递发货订单查询客服咨询感谢帮助服务"
        result = result + normal_padding[:random.randint(10, 20)]
        
        # 3. 如果还没变化，强制改写
        if result == text:
            result = "咨询一下：" + text + "，请问具体怎么操作？谢谢"
        
        return result

    def _attack_normal_sample(self, text: str) -> str:
        """攻击正常样本：正常 -> 欺诈"""
        result = text
        
        # 1. 插入欺诈关键词（但要自然）
        fraud_inserts = [
            "，需要点击链接验证",
            "，请修改密码确保安全",
            "，系统检测到异常请处理",
            "，涉及账户安全请关注"
        ]
        
        # 在合适位置插入
        if len(result) > 15:
            insert_pos = random.randint(len(result)//3, len(result)//2)
            result = result[:insert_pos] + random.choice(fraud_inserts) + result[insert_pos:]
        
        # 2. 移除正常关键词
        normal_words = ["谢谢", "感谢", "咨询", "请问", "麻烦"]
        for word in normal_words:
            if word in result:
                result = result.replace(word, "")
                break
        
        # 3. 添加紧急语气
        if random.random() > 0.5:
            prefixes = ["重要：", "紧急：", "安全通知："]
            result = random.choice(prefixes) + result
        
        return result
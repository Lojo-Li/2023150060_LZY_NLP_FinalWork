# data_loader.py
import re
import random
import csv
from typing import List, Dict, Tuple
from config import Config

class FraudDialogDataLoader:
    """加载和预处理欺诈对话数据集 - 无外部依赖版本"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or Config.DATA_PATH
        self.data = []
        self.extended_data = []  # 新增：扩展数据
        self.label_map = {"正常": 0, "非欺诈": 0, "欺诈": 1, "诈骗": 1}
        
        # 内置同义词词典（简化版）
        self.synonyms = {
            "点击": ["打开", "访问", "进入", "点开"],
            "链接": ["网址", "连接", "URL", "网站"],
            "密码": ["密钥", "口令", "登录码"],
            "验证码": ["验证号", "确认码", "安全码"],
            "账户": ["账号", "户头", "ID"],
            "退款": ["返款", "退还", "退回"],
            "中奖": ["获奖", "得奖", "幸运"],
            "领取": ["获取", "得到", "获得"],
            "提供": ["给出", "提交", "发送"],
            "操作": ["步骤", "流程", "过程"],
            "需要": ["要求", "需求", "要"],
            "请": ["麻烦您", "请您", "恳请"],
            "您好": ["你好", "您好啊", "你好呀"],
            "谢谢": ["感谢", "多谢", "谢啦"]
        }
    
    def parse_dialog(self, text: str) -> str:
        """解析对话格式，转换为单行文本"""
        # 移除标记和多余空格
        text = re.sub(r'#+.*?#+', '', text)  # 移除#包围的内容
        text = re.sub(r'\*\*.*?\*\*:', ' ', text)  # 移除**标记
        text = re.sub(r'\s+', ' ', text).strip()  # 合并空格
        
        return text
    
    def extract_label(self, text: str) -> int:
        """从文本中提取标签"""
        text_lower = text.lower()
        
        # 欺诈关键词
        fraud_keywords = ["诈骗", "欺诈", "中奖", "点击链接", "密码", "验证码", "账户安全", "退款", "银行卡"]
        # 正常关键词
        normal_keywords = ["客服", "咨询", "快递", "发货", "订单", "查询", "感谢", "帮助"]
        
        fraud_count = sum(1 for keyword in fraud_keywords if keyword in text_lower)
        normal_count = sum(1 for keyword in normal_keywords if keyword in text_lower)
        
        # 简单规则：如果包含欺诈关键词且无明显正常关键词，则标记为欺诈
        if fraud_count > 0 and (fraud_count > normal_count or normal_count == 0):
            return 1  # 欺诈
        return 0  # 正常
    
    def simple_tokenize(self, text: str) -> List[str]:
        """简单的分词函数（不使用nltk）"""
        # 中文简单分词：按字符分割，但保留常用词
        words = []
        i = 0
        while i < len(text):
            # 尝试匹配2-4个字符的常见词
            found = False
            for length in range(4, 1, -1):
                if i + length <= len(text):
                    word = text[i:i+length]
                    if word in self.synonyms:
                        words.append(word)
                        i += length
                        found = True
                        break
            if not found:
                words.append(text[i])
                i += 1
        
        return words
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（不使用BERTScore）"""
        # 简单的Jaccard相似度
        set1 = set(self.simple_tokenize(text1))
        set2 = set(self.simple_tokenize(text2))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def load_data(self, sample_size: int = None) -> List[Dict]:
        """加载数据并转换为标准格式"""
        data = []
        
        try:
            # 尝试加载CSV文件
            if self.data_path.endswith('.csv'):
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if 'text' in row and 'label' in row:
                            text = self.parse_dialog(row['text'])
                            label = int(row['label']) if row['label'].isdigit() else self.extract_label(row['text'])
                            data.append({'text': text, 'label': label})
                        else:
                            # 如果没有标准列，尝试从内容中提取
                            for key, value in row.items():
                                if value and len(value) > 10:  # 假设文本较长
                                    text = self.parse_dialog(value)
                                    label = self.extract_label(value)
                                    data.append({'text': text, 'label': label})
                                    break
            else:
                # 尝试加载文本文件
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 按行分割
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip() and len(line.strip()) > 10:
                            text = self.parse_dialog(line)
                            label = self.extract_label(line)
                            data.append({'text': text, 'label': label})
        except Exception as e:
            print(f"加载数据失败: {e}")
            # 创建示例数据
            data = self.create_example_data()
        
        # 随机抽样（如果数据量大）
        if sample_size and len(data) > sample_size:
            random.seed(Config.SEED)
            data = random.sample(data, sample_size)
        
        self.data = data
        print(f"加载了 {len(data)} 条数据")
        
        # 统计标签分布
        fraud_count = sum(1 for item in data if item['label'] == 1)
        normal_count = len(data) - fraud_count
        print(f"欺诈对话: {fraud_count} 条")
        print(f"正常对话: {normal_count} 条")
        
        return data
    
    def create_example_data(self) -> List[Dict]:
        """创建示例数据"""
        examples = [
            {
                "text": "客服您好我收到一条短信说我的账户有异常需要点击链接修改密码",
                "label": 1
            },
            {
                "text": "恭喜您中奖了请点击链接领取奖品需要提供您的银行卡信息",
                "label": 1
            },
            {
                "text": "我们是公安局您的账户涉嫌洗钱请配合调查点击链接下载安全软件",
                "label": 1
            },
            {
                "text": "您的快递已经发货单号是SF123456预计明天送达请注意查收",
                "label": 0
            },
            {
                "text": "客服您好我想查询一下我的订单状态订单号是2023123456",
                "label": 0
            },
            {
                "text": "感谢您的咨询如果还有其他问题请随时联系我们祝您生活愉快",
                "label": 0
            }
        ]
        
        return examples
    
    def get_data(self) -> Tuple[List[str], List[int]]:
        """获取文本和标签列表"""
        if not self.data:
            self.load_data()
        
        texts = [item['text'] for item in self.data]
        labels = [item['label'] for item in self.data]
        
        return texts, labels
    
    def load_extended_dataset(self, num_samples: int = 100) -> List[Dict]:
        """加载扩展数据集（原始数据 + 合成数据）"""
        print(f"加载扩展数据集，目标样本数: {num_samples}")
        
        # 1. 加载原始数据
        original_data = self.load_data()
        print(f"原始数据: {len(original_data)} 条")
        
        # 2. 生成合成数据（如果原始数据不足）
        if len(original_data) < num_samples:
            additional_needed = num_samples - len(original_data)
            synthetic_data = self.generate_synthetic_data(additional_needed)
            print(f"生成合成数据: {len(synthetic_data)} 条")
            
            # 合并数据
            extended_data = original_data + synthetic_data
        else:
            extended_data = original_data[:num_samples]
        
        self.extended_data = extended_data
        
        # 统计信息
        fraud_count = sum(1 for item in extended_data if item['label'] == 1)
        normal_count = len(extended_data) - fraud_count
        
        print(f"扩展数据集统计:")
        print(f"  总样本数: {len(extended_data)}")
        print(f"  欺诈对话: {fraud_count} 条 ({fraud_count/len(extended_data)*100:.1f}%)")
        print(f"  正常对话: {normal_count} 条 ({normal_count/len(extended_data)*100:.1f}%)")
        
        return extended_data
    
    def generate_synthetic_data(self, num_samples: int) -> List[Dict]:
        """生成合成数据"""
        synthetic_data = []
        
        # 欺诈对话模板
        fraud_templates = [
            "您有一笔{}元退款未领取，请点击链接{}完成退款操作",
            "恭喜您获得{}奖品，请点击{}领取并提供银行卡信息",
            "您的{}账户存在风险，请立即点击{}修改密码",
            "{}通知：您的账户涉嫌{}，请点击链接配合调查",
            "您有{}积分即将过期，请点击{}兑换现金奖励"
        ]
        
        # 正常对话模板
        normal_templates = [
            "客服您好，我想查询一下我的{}订单状态",
            "{}快递什么时候能送到，单号是多少",
            "关于{}产品，我有几个问题想咨询",
            "我的{}账户登录有问题，提示{}错误",
            "感谢客服{}的耐心解答，问题已解决"
        ]
        
        # 填充词
        fillers = {
            "金额": ["1000", "5000", "200", "50", "188"],
            "链接": ["www.refund-example.com", "领取地址", "安全链接", "官方网址"],
            "奖品": ["苹果手机", "笔记本电脑", "现金红包", "购物卡", "优惠券"],
            "银行": ["工商银行", "建设银行", "招商银行", "支付宝", "微信支付"],
            "机构": ["公安局", "检察院", "法院", "银行系统", "安全中心"],
            "违规": ["洗钱", "诈骗", "异常交易", "盗刷风险", "安全漏洞"],
            "产品": ["手机", "电脑", "衣服", "食品", "家电"],
            "快递": ["顺丰", "中通", "圆通", "韵达", "京东"],
            "问题": ["质量", "发货", "退款", "售后", "安装"],
            "错误": ["密码", "验证码", "账号不存在", "系统繁忙", "网络超时"]
        }
        
        # 生成欺诈样本
        num_fraud = int(num_samples * 0.5)  # 50%欺诈样本
        for i in range(num_fraud):
            template = random.choice(fraud_templates)
            text = template
            
            # 替换占位符
            for placeholder in ["{}", "{}", "{}"]:
                if "{}" in text:
                    filler_type = random.choice(list(fillers.keys()))
                    filler = random.choice(fillers[filler_type])
                    text = text.replace("{}", filler, 1)
            
            synthetic_data.append({
                'text': text,
                'label': 1,
                'type': 'synthetic_fraud'
            })
        
        # 生成正常样本
        num_normal = num_samples - num_fraud
        for i in range(num_normal):
            template = random.choice(normal_templates)
            text = template
            
            # 替换占位符
            for placeholder in ["{}", "{}"]:
                if "{}" in text:
                    filler_type = random.choice(list(fillers.keys()))
                    filler = random.choice(fillers[filler_type])
                    text = text.replace("{}", filler, 1)
            
            synthetic_data.append({
                'text': text,
                'label': 0,
                'type': 'synthetic_normal'
            })
        
        return synthetic_data
    
    def load_custom_data(self, data_path: str = None) -> List[Dict]:
        """加载自定义数据"""
        path = data_path or Config.CUSTOM_DATA_PATH
        
        if not os.path.exists(path):
            print(f"自定义数据文件不存在: {path}")
            print("将使用扩展数据集...")
            return self.load_extended_dataset(Config.SAMPLE_SIZE_LARGE)
        
        print(f"加载自定义数据: {path}")
        self.data_path = path
        return self.load_data()
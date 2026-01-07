# simple_model.py
import re
import random
from typing import List, Dict, Tuple
from config import Config

class SimpleFraudDetector:
    """简单的欺诈对话检测器（基于规则）"""
    
    def __init__(self, threshold=0.4):  # 降低阈值使其更容易改变
        self.fraud_keywords = [
            "中奖", "点击链接", "密码", "验证码", "银行卡", "账户安全",
            "退款", "公安局", "洗钱", "配合调查", "安全软件", "修改密码",
            "领取奖品", "提供信息", "银行客服", "异常登录"
        ]
        
        self.normal_keywords = [
            "快递", "发货", "订单", "查询", "咨询", "感谢", "帮助",
            "客服", "物流", "配送", "地址", "电话", "工作时间", "服务"
        ]
        
        # 欺诈特征模式
        self.fraud_patterns = [
            r'点击.*链接',
            r'提供.*密码',
            r'银行.*账户.*异常',
            r'中奖.*领取',
            r'公安局.*调查',
            r'修改.*密码'
        ]
        
        self.threshold = threshold  # 使用传入的阈值
    
    def _calculate_fraud_score(self, text: str) -> float:
        """计算欺诈得分 - 增强不稳定性"""
        text_lower = text
        
        # 1. 关键词匹配（降低权重）
        keyword_score = 0
        for keyword in self.fraud_keywords:
            if keyword in text_lower:
                keyword_score += 0.2  # 从0.5降低到0.2
        
        # 2. 模式匹配（降低权重）
        pattern_score = 0
        for pattern in self.fraud_patterns:
            if re.search(pattern, text_lower):
                pattern_score += 0.15  # 从0.3降低到0.15
        
        # 3. 正常关键词扣分（增加权重）
        normal_score = 0
        for keyword in self.normal_keywords:
            if keyword in text_lower:
                normal_score += 0.4  # 从0.3增加到0.4
        
        # 4. 长度特征
        length_score = 0.2 if len(text) > 50 else 0.6
        
        # 5. 标点符号特征
        exclamation_score = 0.2 if '!' in text or '！' in text else 0
        
        # 6. 添加显著随机性（关键！）
        random_factor = random.uniform(-0.2, 0.2)
        
        # 计算总分
        total_score = (keyword_score * 0.2 + pattern_score * 0.2 + 
                    length_score * 0.15 + exclamation_score * 0.1 - 
                    normal_score * 0.35 + random_factor)
        
        # 归一化
        normalized = min(max(total_score, 0), 1)
        
        return normalized
    
    def predict(self, texts: List[str]) -> List[int]:
        """预测文本标签"""
        predictions = []
        
        for text in texts:
            fraud_score = self._calculate_fraud_score(text)
            predictions.append(1 if fraud_score > self.threshold else 0)
        
        return predictions

    def predict_proba(self, texts: List[str]) -> List[Tuple[float, float]]:
        """预测概率"""
        probabilities = []
        
        for text in texts:
            fraud_score = self._calculate_fraud_score(text)
            normal_score = 1 - fraud_score
            probabilities.append((normal_score, fraud_score))
        
        return probabilities
    
    def evaluate(self, texts: List[str], labels: List[int]) -> Dict:
        """评估模型性能"""
        predictions = self.predict(texts)
        
        correct = 0
        for pred, true in zip(predictions, labels):
            if pred == true:
                correct += 1
        
        accuracy = correct / len(labels) if labels else 0
        
        return {
            "accuracy": accuracy,
            "predictions": predictions,
            "correct_count": correct,
            "total_count": len(labels)
        }

class ModelManager:
    """模型管理器"""
    
    def __init__(self):
        self.models = {}
    
    def get_model(self, model_name: str = "simple") -> SimpleFraudDetector:
        """获取模型"""
        if model_name not in self.models:
            self.models[model_name] = SimpleFraudDetector(threshold=Config.MODEL_THRESHOLD)
        
        return self.models[model_name]
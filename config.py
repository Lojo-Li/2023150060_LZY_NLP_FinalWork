# config.py
import os

class Config:
    # 实验设置
    EXPERIMENT_NAME = "PromptAttack_Fraud_Detection_NoNLTK"
    SEED = 42
    DEBUG = True
    SAMPLE_SIZE = 50  # 从大数据集中抽取的样本数
    
    # 数据设置
    DATA_PATH = "./data/fraud_dialog_dataset.csv"
    CUSTOM_DATA_PATH = "./data/custom_fraud_data.csv"  # 新增：自定义数据路径
    USE_CUSTOM_DATA = False  # 是否使用自定义数据
    
    # 实验设置
    EXPERIMENT_NAME = "PromptAttack_Fraud_Detection_Extended"
    SEED = 42
    DEBUG = True
    SAMPLE_SIZE_LARGE = 100  # 新增：大样本实验
    SAMPLE_SIZE_SMALL = 50
    
    # 图形化分析设置
    GENERATE_PLOTS = True  # 是否生成图表
    PLOT_FORMAT = "png"  # 图片格式: png, pdf, svg
    PLOT_DPI = 300  # 图片分辨率
    
    # 模型设置（简化版，不使用复杂模型）
    USE_SIMPLE_MODEL = True  # 使用简单的基于规则模型
    
    # PromptAttack参数
    PERTURBATION_LEVELS = ["character", "word", "sentence"]
    
    # 简化版扰动类型（不使用nltk）
    PERTURBATION_TYPES = {
        "character": ["typo", "extra_char"],
        "word": ["synonym", "remove_word"],
        "sentence": ["rephrase", "add_prefix"]
    }
    
    # 保真度阈值（简化）
    MAX_WORD_CHANGES = 15  # 最多允许修改的词数
    MIN_SIMILARITY = 0.3  # 降低相似度要求从0.5到0.3，允许更大改动
    
    # 模型阈值调整
    MODEL_THRESHOLD = 0.4  # 可以调整模型阈值，更容易改变预测
    
    # 实验输出
    OUTPUT_DIR = "./results"
    ADVERSARIAL_SAMPLES_DIR = "./results/adversarial_samples"
    LOGS_DIR = "./results/logs"
    FIGURES_DIR = "./results/figures"
    
    # 创建输出目录
    @staticmethod
    def create_dirs():
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        os.makedirs(Config.ADVERSARIAL_SAMPLES_DIR, exist_ok=True)
        os.makedirs(Config.LOGS_DIR, exist_ok=True)
        os.makedirs(Config.FIGURES_DIR, exist_ok=True)
# PromptAttack 欺诈对话检测实验（无外部依赖版本）

基于论文《An LLM Can Fool Itself: A Prompt-Based Adversarial Attack》的简化实现，专门针对无法安装复杂Python库的环境设计。

## 项目特点

✅ **无需安装任何外部Python库** - 仅使用Python标准库
✅ **完全离线运行** - 不需要网络连接
✅ **轻量级** - 代码简洁，运行速度快
✅ **功能完整** - 包含论文核心方法的实现

## 文件结构
fraud_detection_simple/
├── config.py # 配置文件
├── data_loader.py # 数据加载器（无外部依赖）
├── simple_model.py # 简单分类模型（基于规则）
├── prompt_attack.py # PromptAttack核心实现（无nltk）
├── experiment.py # 实验运行器
├── run_experiment.py # 主运行脚本
├── create_example_data.py # 创建示例数据
└── README.md # 说明文档


## 快速开始

### 步骤1：准备环境

1. 确保已安装Python 3.6+
2. 将上述所有文件保存到同一目录
3. 不需要安装任何额外的Python包

### 步骤2：创建示例数据

```bash
python create_example_data.py
# run_optimized.py
import sys
sys.path.append('.')

from simple_model import SimpleFraudDetector
from data_loader import FraudDialogDataLoader
from prompt_attack import SimplePromptAttack, AttackResult
import random

def run_optimized_experiment(test_data_limit=100):
    """运行优化的实验
    Args:
        test_data_limit: 每次测试的样本数量，默认100
    """
    print(f"=== 优化版PromptAttack实验 (测试样本数: {test_data_limit}) ===")
    
    # 固定随机种子以便复现
    random.seed(42)
    
    # 1. 准备数据 - 修改为你的实际数据路径
    data_loader = FraudDialogDataLoader(data_path="D:/desktop/2023150060_LZY_NLP_FinalWork本地/data/训练集结果.csv")
    
    # 加载指定数量的数据
    data = data_loader.load_data(sample_size=test_data_limit)
    
    # 检查数据格式，确保有text和label字段
    if len(data) == 0:
        print("错误: 没有加载到数据，请检查数据路径和格式")
        return
    
    # 提取文本和标签
    texts = []
    labels = []
    for item in data:
        # 确保每个数据项都有text和label
        if 'text' in item and 'label' in item:
            texts.append(item['text'])
            labels.append(item['label'])
        else:
            print(f"警告: 数据项缺少text或label字段: {item}")
    
    # 如果没有足够的数据，使用示例数据
    if len(texts) == 0:
        print("使用示例数据")
        example_data = data_loader.create_example_data()
        texts = [item['text'] for item in example_data]
        labels = [item['label'] for item in example_data]
    
    # 确保不超过指定的测试限制
    if len(texts) > test_data_limit:
        texts = texts[:test_data_limit]
        labels = labels[:test_data_limit]
    
    print(f"使用 {len(texts)} 个样本")
    print(f"欺诈样本: {sum(labels)} 个")
    print(f"正常样本: {len(labels)-sum(labels)} 个")
    
    # 2. 创建并测试模型（使用更低的阈值）
    model = SimpleFraudDetector(threshold=0.3)  # 进一步降低阈值
    
    print("\n=== 模型基线测试 ===")
    correct = 0
    detailed_results = []
    for i, (text, label) in enumerate(zip(texts, labels)):
        pred = model.predict([text])[0]
        score = model._calculate_fraud_score(text)
        if pred == label:
            correct += 1
        
        # 存储详细信息用于分析
        detailed_results.append({
            'text': text,
            'label': label,
            'pred': pred,
            'score': score
        })
        
        # 只显示前5个样本的详细信息
        if i < 5:
            print(f"样本{i+1}: {text[:40]}... 标签:{label} 得分:{score:.3f} 预测:{pred} {'✓' if pred==label else '✗'}")
    
    baseline_acc = correct / len(texts)
    print(f"\n基线准确率: {baseline_acc:.4f} ({correct}/{len(texts)})")
    
    # 分析模型易受攻击的样本
    vulnerable_samples = []
    for i, result in enumerate(detailed_results):
        # 寻找得分接近阈值的样本（这些更容易被攻击）
        score = result['score']
        if abs(score - 0.3) < 0.1:  # 得分在阈值附近
            vulnerable_samples.append(i)
    
    print(f"易受攻击样本（得分接近阈值）: {len(vulnerable_samples)} 个")
    
    # 3. 创建攻击器
    attack = SimplePromptAttack(model, data_loader)
    
    # 4. 测试所有扰动类型
    perturbation_types = ["typo", "extra_char", "synonym", "remove_word", "rephrase", "add_prefix"]
    
    print("\n" + "="*80)
    print("开始攻击实验 (目标: 改变模型预测)")
    print("="*80)
    
    results = {}
    
    for ptype in perturbation_types:
        print(f"\n>>> 测试扰动类型: {ptype}")
        
        success_count = 0
        change_count = 0
        detail_log = []
        
        # 优先测试易受攻击的样本
        sample_indices = list(range(len(texts)))
        if vulnerable_samples:
            # 将易受攻击样本放在前面
            sample_indices = vulnerable_samples + [i for i in range(len(texts)) if i not in vulnerable_samples]
        
        for i in sample_indices:
            text = texts[i]
            label = labels[i]
            result = attack.generate_adversarial_sample(text, label, ptype)
            
            if result.original_prediction != result.adversarial_prediction:
                change_count += 1
                # 只记录前3个改变预测的样本
                if change_count <= 3:
                    detail_log.append(f"    样本{i+1}: {text[:20]}... 预测 {result.original_prediction}→{result.adversarial_prediction}")
            
            if result.success:
                success_count += 1
        
        total_tested = len(texts)
        success_rate = success_count / total_tested if total_tested > 0 else 0
        change_rate = change_count / total_tested if total_tested > 0 else 0
        
        results[ptype] = {
            'success_rate': success_rate,
            'change_rate': change_rate,
            'success_count': success_count,
            'change_count': change_count,
            'total_tested': total_tested
        }
        
        print(f"  攻击成功率: {success_rate:.4f} ({success_count}/{total_tested})")
        print(f"  预测改变率: {change_rate:.4f} ({change_count}/{total_tested})")
        
        if change_count > 0:
            print("  预测改变的样本:")
            for log in detail_log:
                print(log)
    
    # 5. 汇总结果
    print("\n" + "="*80)
    print("实验结果汇总")
    print("="*80)
    print(f"{'扰动类型':<12} {'攻击成功率':<12} {'预测改变率':<12} {'成功数/总数':<15}")
    print("-"*80)
    
    best_type = None
    best_rate = 0
    
    for ptype, result in results.items():
        print(f"{ptype:<12} {result['success_rate']:<12.4f} {result['change_rate']:<12.4f} "
              f"{result['success_count']}/{result['total_tested']:<15}")
        
        if result['success_rate'] > best_rate:
            best_rate = result['success_rate']
            best_type = ptype
    
    # 6. 分析结论
    print("\n" + "="*80)
    print("结论分析")
    print("="*80)
    
    if best_rate > 0:
        print(f"✓ 实验成功！找到了有效的攻击方法。")
        print(f"  最佳扰动类型: {best_type} (成功率: {best_rate:.4f})")
        print(f"  这证明欺诈对话检测模型存在对抗脆弱性。")
        
        # 显示一些成功案例
        print(f"\n成功案例展示:")
        for ptype in perturbation_types[:3]:  # 只显示前3种扰动类型
            if results[ptype]['success_count'] > 0:
                print(f"  {ptype}:")
                # 重新运行找到成功案例
                success_examples = []
                for text, label in zip(texts, labels):
                    result = attack.generate_adversarial_sample(text, label, ptype)
                    if result.success:
                        success_examples.append(result)
                        if len(success_examples) >= 2:
                            break
                
                for example in success_examples[:2]:
                    print(f"    - 原始: {example.original_text[:30]}...")
                    print(f"      对抗: {example.adversarial_text[:30]}...")
                    print(f"      预测: {example.original_prediction} → {example.adversarial_prediction}")
                    print(f"      相似度: {example.similarity_score:.3f}")
    else:
        print(f"✗ 所有攻击都失败了。需要进一步分析:")
        print(f"  1. 检查模型是否过于简单/鲁棒")
        print(f"  2. 检查扰动是否真正改变了文本")
        print(f"  3. 检查相似度阈值是否设置过高")
        print(f"  4. 检查攻击成功判定逻辑")
    
    # 7. 保存结果
    output_file = f"optimized_results_{test_data_limit}samples.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"优化版PromptAttack实验报告 (测试样本数: {test_data_limit})\n")
        f.write("="*60 + "\n")
        f.write(f"总样本数: {len(texts)}\n")
        f.write(f"基线准确率: {baseline_acc:.4f}\n")
        f.write(f"易受攻击样本数: {len(vulnerable_samples)}\n\n")
        
        f.write("各扰动类型结果:\n")
        for ptype, result in results.items():
            f.write(f"  {ptype}: 成功率={result['success_rate']:.4f}, "
                   f"改变率={result['change_rate']:.4f}, "
                   f"成功数={result['success_count']}/{result['total_tested']}\n")
        
        f.write(f"\n最佳攻击方法: {best_type} (成功率: {best_rate:.4f})\n")
    
    print(f"\n详细结果已保存到: {output_file}")
    
    # 8. 返回关键结果
    return {
        'total_samples': len(texts),
        'baseline_accuracy': baseline_acc,
        'best_perturbation': best_type,
        'best_success_rate': best_rate,
        'vulnerable_samples': len(vulnerable_samples)
    }

if __name__ == "__main__":
    # 使用方法1：默认运行100个样本
    run_optimized_experiment(test_data_limit=100)
    
    # 使用方法2：指定样本数量
    # sample_count = int(input("请输入要测试的样本数量 (例如: 100, 500, 1000): ") or "100")
    # run_optimized_experiment(test_data_limit=sample_count)
    
    # 使用方法3：批量测试不同数量的样本
    # for count in [50, 100, 200, 500]:
    #     print(f"\n{'='*80}")
    #     print(f"测试 {count} 个样本")
    #     print('='*80)
    #     run_optimized_experiment(test_data_limit=count)
"""
代码分析师主程序
支持通过命令行参数和环境变量配置
"""
import os
import json
import argparse
from scanner import analyze_repo
from strategist import Strategist
from auditor import CodeAnalyst
from synthesizer import Synthesizer
from configs.env_config import EnvConfig
from configs.model_config import ModelConfig


def run_code_analyst_role(repo_url, github_token, model_config: ModelConfig = None):
    """
    运行代码分析师角色
    Args:
        repo_url: GitHub仓库URL
        github_token: GitHub Token
        model_config: 模型配置对象（可选）
    """
    if model_config is None:
        model_config = ModelConfig()
    
    print(f"\n{'='*20} 代码分析师角色：启动深度尽调 {'='*20}\n")

    # 1. Scanner 阶段：抓取 GitHub 宏观指标
    print("步骤 1: 抓取 GitHub 宏观数据...")
    scan_result = analyze_repo(repo_url, github_token)

    # 2. Strategist 阶段：规划审计路径
    print("步骤 2: 正在根据目录树规划核心审计路径...")
    strat = Strategist(repo_url, github_token, model_config=model_config)
    audit_plan = strat.create_audit_plan()
    print(f"审计路径: {audit_plan}")
    
    # 3. Auditor 阶段：执行深度双轨审计 (并发执行)
    print("步骤 3: 启动主辅双轨代码审计...")
    analyst = CodeAnalyst(github_token, model_config=model_config)
    audit_data = analyst.run_dual_track_audit(audit_plan)

    
    # 4. Synthesizer 阶段：跨维度逻辑对撞
    print("步骤 4: 正在融合宏观数据与微观审计，生成最终报告...")
    synthesizer_model = model_config.get_model_name("synthesizer")
    synth = Synthesizer(model_name=synthesizer_model)
    
    # 将 Scanner 的初步报告和 Auditor 的原始报告一起喂给整合者
    final_report = synth.generate_final_report(
        github_data=scan_result, 
        audit_results=audit_data
    )
    
    return final_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="代码分析师 - GitHub仓库深度尽调工具")
    parser.add_argument(
        "--repo-url",
        type=str,
        help="GitHub仓库URL（例如：https://github.com/owner/repo）"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="模型配置文件路径（JSON格式）"
    )
    parser.add_argument(
        "--primary-audit-model",
        type=str,
        help="主审计轨道使用的模型"
    )
    parser.add_argument(
        "--random-audit-model",
        type=str,
        help="随机审计轨道使用的模型"
    )
    parser.add_argument(
        "--strategist-model",
        type=str,
        help="策略规划使用的模型"
    )
    parser.add_argument(
        "--synthesizer-model",
        type=str,
        help="综合报告生成使用的模型"
    )
    
    args = parser.parse_args()
    
    # 获取GitHub Token
    try:
        github_token = EnvConfig.get_github_token()
    except ValueError as e:
        print(f"错误: {e}")
        print("请设置 GITHUB_TOKEN 环境变量或创建 .env 文件")
        exit(1)
    
    # 获取仓库URL
    repo_url = args.repo_url or os.getenv("REPO_URL")
    if not repo_url:
        print("错误: 请通过 --repo-url 参数或 REPO_URL 环境变量指定仓库URL")
        exit(1)
    
    # 创建模型配置
    model_config = ModelConfig(config_file=args.config)
    
    # 应用命令行参数（如果提供）
    if args.primary_audit_model:
        os.environ["PRIMARY_AUDIT_MODEL"] = args.primary_audit_model
    if args.random_audit_model:
        os.environ["RANDOM_AUDIT_MODEL"] = args.random_audit_model
    if args.strategist_model:
        os.environ["STRATEGIST_MODEL"] = args.strategist_model
    if args.synthesizer_model:
        os.environ["SYNTHESIZER_MODEL"] = args.synthesizer_model
    
    try:
        final_md = run_code_analyst_role(repo_url, github_token, model_config)
        
        output_file = "final_due_diligence_report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_md)
        
        print(f"\n{'='*20} 尽调任务完成 {'='*20}")
        print(f"最终报告已生成: {output_file}")
        
    except Exception as e:
        print(f"\n{'='*20} 角色运行崩溃 {'='*20}")
        print(f"详情: {str(e)}")
        import traceback
        traceback.print_exc()
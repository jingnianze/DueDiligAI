import sqlite3
import os
import json
import argparse
from configs.env_config import EnvConfig
from typing import TypedDict
from configs.model_config import ModelConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI

from scanner import analyze_repo
from strategist import Strategist
from auditor import CodeAnalyst
from synthesizer import Synthesizer

class AuditState(TypedDict):
    # 输入信息
    repo_url: str
    token: str
    model_name: str

    # 中间数据
    scanner_data: [str]  # Scanner 的输出
    audit_plan: [str]  # Strategist 的输出
    audit_results: [str]  # Auditor 的输出

    # 最终产物
    final_report: str
def scanner_node(state:AuditState):
    print("Scanner 正在抓取宏观指标")
    result=analyze_repo(state['repo_url'], state['token'])
    return {"scanner_data": result}

def strategist_node(state:AuditState):
    print("Strategist 正在生成审计计划")
    result=Strategist(state['repo_url'], state['token']).create_audit_plan()
    return {"audit_plan": result}

def auditor_node(state:AuditState):
    print("Auditor 正在执行双轨道审计")
    analyst=CodeAnalyst(state["token"])
    result=analyst.run_dual_track_audit(state["audit_plan"])
    return {"audit_results": result}

def synthesizer_node(state:AuditState):
    print("Synthesizer 正在生成审计报告")
    synthesizer=Synthesizer(state["model_name"])
    result=synthesizer.generate_final_report(state["scanner_data"],state["audit_results"])
    return {"final_report": result}


workflow = StateGraph(AuditState)


workflow.add_node("scanner_node", scanner_node)
workflow.add_node("strategist_node", strategist_node)
workflow.add_node("auditor_node", auditor_node)
workflow.add_node("synthesizer_node", synthesizer_node)


workflow.set_entry_point("scanner_node")
workflow.add_edge("scanner_node", "strategist_node")
workflow.add_edge("strategist_node", "auditor_node")
workflow.add_edge("auditor_node", "synthesizer_node")
workflow.add_edge("synthesizer_node", END)

db_path = "audit_checkpoints.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
memory = SqliteSaver(conn)

app = workflow.compile(checkpointer=memory)

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
    
    config = {"configurable": {"thread_id": "audit_task_001"}}
    inputs={
        "repo_url": repo_url,
        "token": github_token,
        "model_name": args.synthesizer_model,
    }
    try:
        print("🚀 启动/恢复审计任务...")
        final_state = app.invoke(inputs, config=config)

        with open("langgraph_report.md", "w", encoding="utf-8") as f:
            f.write(final_state['final_report'])
        print("✅ 基于 LangGraph 的自动化审计任务圆满完成！")

    except Exception as e:
        print(f"❌ 运行中途出错: {e}")
        print("💡 状态已保存。修复问题后再次运行，程序将从断点处继续。")
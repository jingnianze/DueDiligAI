"""
模型配置管理模块
支持通过命令行参数、环境变量或配置文件指定模型
"""
import os
import argparse
import json
from typing import Optional, Dict, Any
from pathlib import Path
from configs.env_config import EnvConfig


class ModelConfig:
    """模型配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化模型配置
        Args:
            config_file: 配置文件路径（可选）
        """
        self.config_file = config_file
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config = {}
        
        # 从配置文件加载（如果存在）
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        return config
    
    def get_model_name(self, role: str = "default") -> str:
        """
        获取指定角色的模型名称
        优先级：命令行参数 > 环境变量 > 配置文件 > 默认值
        """
        # 角色到环境变量的映射
        role_env_map = {
            "primary_audit": "PRIMARY_AUDIT_MODEL",
            "random_audit": "RANDOM_AUDIT_MODEL",
            "strategist": "STRATEGIST_MODEL",
            "synthesizer": "SYNTHESIZER_MODEL",
            "default": "DEFAULT_MODEL_NAME",
        }
        
        # 从环境变量获取
        env_key = role_env_map.get(role, "DEFAULT_MODEL_NAME")
        model_name = os.getenv(env_key)
        
        # 从配置文件获取
        if not model_name and self._config:
            model_name = self._config.get(role, self._config.get("default_model"))
        
        # 使用默认值
        if not model_name:
            defaults = {
                "primary_audit": EnvConfig.get_primary_audit_model(),
                "random_audit": EnvConfig.get_random_audit_model(),
                "strategist": EnvConfig.get_strategist_model(),
                "synthesizer": EnvConfig.get_synthesizer_model(),
                "default": EnvConfig.get_default_model_name(),
            }
            model_name = defaults.get(role, defaults["default"])
        
        return model_name
    
    def get_model_provider(self) -> str:
        """获取模型提供方"""
        provider = os.getenv("MODEL_PROVIDER")
        if not provider and self._config:
            provider = self._config.get("model_provider")
        if not provider:
            provider = EnvConfig.get_model_provider()
        return provider
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description="代码分析工具 - 支持通过命令行参数配置模型"
        )
        
        parser.add_argument(
            "--model",
            type=str,
            help="指定使用的模型名称（覆盖所有角色的默认模型）"
        )
        
        parser.add_argument(
            "--model-provider",
            type=str,
            help="指定模型提供方（openai, deepseek, qwen, gemini, vectorengine等）"
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
        
        parser.add_argument(
            "--config",
            type=str,
            help="配置文件路径（JSON格式）"
        )
        
        parser.add_argument(
            "--repo-url",
            type=str,
            help="GitHub仓库URL"
        )
        
        return parser.parse_args()



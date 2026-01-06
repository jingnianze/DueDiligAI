"""
统一的环境变量配置管理模块
所有敏感信息必须从此模块读取
"""
import os
from typing import Optional, Dict, Any


class EnvConfig:
    """环境变量配置管理器"""
    
    # GitHub配置
    @staticmethod
    def get_github_token() -> str:
        """获取GitHub Token"""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_TOKEN 环境变量未设置。"
                "请设置环境变量或创建 .env 文件。"
            )
        return token
    
    @staticmethod
    def get_github_proxy() -> Optional[str]:
        """获取GitHub代理地址（可选）"""
        return os.getenv("GITHUB_PROXY")
    
    # LLM API配置
    @staticmethod
    def get_llm_api_key(model_provider: str = "default") -> str:
        """
        获取LLM API密钥
        支持多提供方：OPENAI_API_KEY, DEEPSEEK_API_KEY, QWEN_API_KEY, GEMINI_API_KEY
        或使用通用的 LLM_API_KEY
        """
        # 优先使用通用密钥
        api_key = os.getenv("LLM_API_KEY")
        if api_key:
            return api_key
        
        # 按提供方获取
        provider_map = {
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "qwen": "QWEN_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "vectorengine": "VECTORENGINE_API_KEY",
        }
        
        env_key = provider_map.get(model_provider.lower(), "LLM_API_KEY")
        api_key = os.getenv(env_key)
        
        if not api_key:
            raise ValueError(
                f"LLM API密钥未设置。请设置 {env_key} 或 LLM_API_KEY 环境变量。"
            )
        return api_key
    
    @staticmethod
    def get_llm_base_url(model_provider: str = "default") -> Optional[str]:
        """获取LLM API Base URL"""
        # 优先使用通用URL
        base_url = os.getenv("LLM_BASE_URL")
        if base_url:
            return base_url
        
        # 按提供方获取
        provider_map = {
            "openai": "OPENAI_BASE_URL",
            "deepseek": "DEEPSEEK_BASE_URL",
            "qwen": "QWEN_BASE_URL",
            "gemini": "GEMINI_BASE_URL",
            "vectorengine": "VECTORENGINE_BASE_URL",
        }
        
        env_key = provider_map.get(model_provider.lower())
        if env_key:
            return os.getenv(env_key)
        
        return None
    
    # 模型配置
    @staticmethod
    def get_default_model_name() -> str:
        """获取默认模型名称"""
        return os.getenv("DEFAULT_MODEL_NAME", "gpt-4o-mini")
    
    @staticmethod
    def get_model_provider() -> str:
        """获取模型提供方"""
        return os.getenv("MODEL_PROVIDER", "vectorengine")
    
    @staticmethod
    def get_primary_audit_model() -> str:
        """获取主审计模型名称"""
        return os.getenv("PRIMARY_AUDIT_MODEL", "gpt-4o-mini")
    
    @staticmethod
    def get_random_audit_model() -> str:
        """获取随机审计模型名称"""
        return os.getenv("RANDOM_AUDIT_MODEL", "qwen-plus")
    
    @staticmethod
    def get_strategist_model() -> str:
        """获取策略规划模型名称"""
        return os.getenv("STRATEGIST_MODEL", "gpt-4o-mini")
    
    @staticmethod
    def get_synthesizer_model() -> str:
        """获取综合报告模型名称"""
        return os.getenv("SYNTHESIZER_MODEL", "deepseek-v3")



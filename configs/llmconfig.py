"""
统一的LLM调用接口
支持多模型提供方，所有API密钥从环境变量读取
"""
import json
import openai
import os
import time
import random
from typing import Optional, Dict, Any


class LLMManager:
    """统一的LLM管理器，支持多模型提供方"""

    # 模型配置模板
    MODEL_CONFIGS = {
        "gemini-3-flash": {
            "model_name": "gemini-3-flash-preview",
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "temperature": 0.5,
        },
        "qwen-plus": {
            "model_name": "qwen-plus-2025-12-01",
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "temperature": 0.5,
        },
        "gpt-5-mini": {
            "model_name": "gpt-5-mini-2025-08-07",
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "temperature": 0.5,
        },
        "gpt-4o-mini": {
            "model_name": "gpt-4o-mini",
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "temperature": 0.5,
        },
        "deepseek-v3": {
            "model_name": "deepseek-v3.2-thinking",
            "base_url": "https://openrouter.ai/api/v1/chat/completions",
            "temperature": 0.5,
        },
    }

    def __init__(self):
        """初始化LLM管理器"""
        pass

    def _get_client_config(self, model_config_name: str) -> Dict[str, Any]:
        """
        获取客户端配置
        Args:
            model_config_name: 模型配置名称
        Returns:
            包含api_key和base_url的配置字典
        """
        config = self.MODEL_CONFIGS.get(model_config_name)
        if not config:
            raise ValueError(
                f"未找到模型配置 {model_config_name}，"
                f"可用配置：{list(self.MODEL_CONFIGS.keys())}"
            )

        # 从环境变量获取 OpenRouter API Key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("未设置环境变量 OPENROUTER_API_KEY")

        # 从环境变量获取 Base URL（如果设置了）
        base_url = os.getenv("OPENROUTER_BASE_URL") or config.get("base_url")

        return {
            "api_key": api_key,
            "base_url": base_url,
            "model_name": config["model_name"],
            "temperature": config.get("temperature", 0.5),
        }

    def call(
        self,
        model_config_name: str,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 5,
        **kwargs
    ) -> str:
        """
        调用LLM模型
        Args:
            model_config_name: 模型配置名称（如 "gpt-4o-mini", "deepseek-v3"）
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            max_retries: 最大重试次数
            **kwargs: 额外的生成参数（如temperature）
        Returns:
            LLM返回的文本内容
        """
        client_config = self._get_client_config(model_config_name)

        client = openai.OpenAI(
            api_key=client_config["api_key"],
            base_url=client_config["base_url"]
        )

        # 合并生成参数
        generate_args = {
            "temperature": kwargs.get("temperature", client_config["temperature"]),
            **{k: v for k, v in kwargs.items() if k != "temperature"}
        }

        last_exception = None

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=client_config["model_name"],
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    **generate_args
                )
                return response.choices[0].message.content

            except Exception as e:
                last_exception = e
                err_msg = str(e)

                is_retryable = (
                    "429" in err_msg
                    or "负载" in err_msg
                    or "model_not_found" in err_msg
                    or "rate limit" in err_msg.lower()
                )

                if not is_retryable:
                    raise

                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                print(
                    f"[LLM RETRY] {model_config_name} | "
                    f"第 {attempt + 1}/{max_retries} 次失败，"
                    f"{sleep_time:.2f}s 后重试\n"
                    f"原因: {err_msg}"
                )
                time.sleep(sleep_time)

        raise RuntimeError(
            f"LLM 调用失败（重试 {max_retries} 次仍失败）: {model_config_name}\n"
            f"最后错误: {last_exception}"
        )


# 全局LLM管理器实例
llm_manager = LLMManager()

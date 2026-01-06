import yaml
from jinja2 import Template
from configs.llmconfig import llm_manager

class Synthesizer:
    def __init__(self, model_name="deepseek-v3"):
        self.model_name = model_name

    def _load_prompt(self, **kwargs):
        with open("prompts/synthesizer.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        sys_p = data['synthesizer']['system']
        usr_p = Template(data['synthesizer']['user']).render(**kwargs)
        return sys_p, usr_p

    def generate_final_report(self, github_data, audit_results):
        """
        核心接口：接收 Scanner JSON 和 Auditor 字典结果
        """
        print("正在启动跨维度融合分析 (Synthesizing)...")
        
        sys_p, usr_p = self._load_prompt(
            github_json=github_data,
            core_audit_results=audit_results.get('core', []),
            random_audit_results=audit_results.get('random', [])
        )

        try:
            report = llm_manager.call(self.model_name, sys_p, usr_p)
            return report
        except Exception as e:
            return f"Error during synthesis: {str(e)}"
import yaml
import sys
from jinja2 import Template
from configs.llmconfig import llm_manager
from concurrent.futures import ThreadPoolExecutor
from utils.github_reader import GitHubReader
from configs.model_config import ModelConfig
import os

class CodeAnalyst:
    def __init__(self, github_token, model_config: ModelConfig = None):
        self.reader = GitHubReader(github_token)
        self.model_config = model_config or ModelConfig()

    def _parse_repo(self, repo_url):
        """
        repo_url: https://github.com/owner/repo
        """
        parts = repo_url.rstrip("/").split("/")
        return parts[-2], parts[-1]

    def _get_file_full_content(self, repo_url, path):
        try:
            owner, repo = self._parse_repo(repo_url)
            return self.reader.get_file_raw(owner, repo, path)
        except Exception as e:
            return f"Error fetching file {path}: {str(e)}"

    def _load_prompt(self, role, **kwargs):
        with open(f"prompts/auditor.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        sys_p = data[role]['system']
        usr_p = Template(data[role]['user']).render(**kwargs)
        return sys_p, usr_p

    def _audit_single_file(self, repo_url, path, role, model_name):
        content = self._get_file_full_content(repo_url, path)
        sys_p, usr_p = self._load_prompt(role, file_path=path, file_content=content)
        
        print(f"[{'CORE' if 'primary' in role else 'RAND'}] 正在审计: {path}...")
        report = llm_manager.call(model_name, sys_p, usr_p)
        return {"path": path, "report": report}

    def run_dual_track_audit(self, audit_plan):
        """
        接收 Strategist 的输出: 
        audit_plan = {
            "repo_url": "...",
            "core_tracks": [...],
            "random_tracks": [...],
            "metadata": {...}
        }
        """
        repo_url = audit_plan["repo_url"]
        audit_reports = {"core": [], "random": []}

        # 从配置获取模型名称
        primary_model = self.model_config.get_model_name("primary_audit")
        random_model = self.model_config.get_model_name("random_audit")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            core_tasks = [
                executor.submit(self._audit_single_file, repo_url, path, "primary_auditor", primary_model)
                for path in audit_plan['core_tracks']
            ]
            
            random_tasks = [
                executor.submit(self._audit_single_file, repo_url, path, "random_auditor", random_model)
                for path in audit_plan['random_tracks']
            ]

            for task in core_tasks:
                audit_reports["core"].append(task.result())
            
            for task in random_tasks:
                audit_reports["random"].append(task.result())

        return audit_reports
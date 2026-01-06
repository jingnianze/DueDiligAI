import random
import re
import yaml
from utils.github_reader import GitHubReader
from jinja2 import Template
from configs.llmconfig import llm_manager
import os
from urllib.parse import urlparse

class Strategist:
    CORE_CODE_EXTENSIONS = {
        ".py", ".pyi",
        ".cpp", ".cc", ".c", ".h", ".hpp",
        ".rs",
        ".java",
        ".go",
        ".ts",
        ".scala",
        ".jl",
        ".m",
        ".r",
        ".cu",
    }
    EXCLUDED_EXTENSIONS = {
        ".json", ".csv", ".tsv",
        ".txt", ".md",
        ".yaml", ".yml",
        ".js",
        ".html", ".css",
        ".pdf", ".png", ".jpg",
    }
    EXCLUDED_KEYWORDS = {
        "result", "results",
        "output", "outputs",
        "log", "logs",
        "plot", "figure",
        "data", "dataset",
        "checkpoint", "ckpt",
        "weight", "weights",
        "experiment", "analysis",
        "benchmark", "report",
    }
    RANDOM_ALLOWED_EXTENSIONS = {
        ".py", ".cpp", ".cc", ".c", ".h", ".hpp",
        ".rs", ".go", ".java", ".ts", ".js",
        ".scala", ".kt", ".swift", ".jl"
    }

    RANDOM_EXCLUDE_KEYWORDS = {
        "data", "dataset", "result", "results", "output", "outputs",
        "log", "logs", "figure", "figures", "plot",
        "cache", "tmp", "temp", "checkpoint",
        "node_modules", "dist", "build",
        "__pycache__", ".git", ".github"
    }
    def __init__(self, repo_url, github_token, model_config=None):
        self.repo_url = repo_url
        self.tree_structure = ""
        self.readme_content = ""
        self.reader = GitHubReader(github_token)
        from configs.model_config import ModelConfig
        self.model_config = model_config or ModelConfig()

    def _load_prompt_template(self):
        with open("prompts/strategist.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        role="core_file_selector"
        data=data[role]
        return data['system'], data['user']

    def _parse_repo(self):
        path = urlparse(self.repo_url).path.strip("/")
        owner, repo = path.split("/")[:2]
        return owner, repo

    def fetch_repo_overview(self):
        owner, repo = self._parse_repo()
        tree = self.reader.get_repo_tree(owner, repo)
        self.tree_structure = tree
        readme_candidates = [
            "README.md", "readme.md", "README.MD"
        ]
        readme_text = ""
        for path in readme_candidates:
            try:
                readme_text = self.reader.get_file_raw(owner, repo, path)
                break
            except Exception:
                continue

        self.readme_content = readme_text
        return self.tree_structure

    def _is_valid_core_candidate(self, path: str) -> bool:
        path_lower = path.lower()

        if "." not in path:
            return False

        ext = "." + path_lower.split(".")[-1]

        if ext in self.EXCLUDED_EXTENSIONS:
            return False
        if ext not in self.CORE_CODE_EXTENSIONS:
            return False

        for kw in self.EXCLUDED_KEYWORDS:
            if kw in path_lower:
                return False
        return True

    def _is_valid_core_candidate_random(self, tree_item):
        """
        tree_item: GitHub API tree 的单个 dict
        """
        if tree_item.get("type") != "blob":
            return False

        path = tree_item.get("path", "").lower()

        # 扩展名过滤
        if not any(path.endswith(ext) for ext in self.RANDOM_ALLOWED_EXTENSIONS):
            return False

        # 关键词过滤
        for kw in self.RANDOM_EXCLUDE_KEYWORDS:
            if f"/{kw}/" in f"/{path}/":
                return False

        return True
    def _filter_tree_for_core_candidates(self, tree_text: str) -> str:
        """
        在不破坏树结构（缩进）的前提下，
        仅保留通过 _is_valid_core_candidate 的文件
        """
        lines = tree_text.splitlines()
        kept_lines = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                continue

            # 目录行：先保留（是否“空目录”可后续再优化）
            if stripped.endswith("/"):
                kept_lines.append(line)
                continue

            filename = stripped
            if self._is_valid_core_candidate(filename):
                kept_lines.append(line)

        return "\n".join(kept_lines)

    def select_core_files(self):
        sys_p, usr_t = self._load_prompt_template()
        filtered_tree = self._filter_tree_for_core_candidates(self.tree_structure)
        usr_p = Template(usr_t).render(
            tree_structure=filtered_tree,
            readme_content=self.readme_content[:30000]
        )
        model_name = self.model_config.get_model_name("strategist")
        response = llm_manager.call(model_name, sys_p, usr_p)
        core_paths = []
        pattern = r'-.*?:\s*(.+)'
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = re.match(pattern, line)
            if match:
                path = match.group(1).strip()
                if path and ('/' in path or '.' in path):
                    core_paths.append(path)
        return core_paths[:3]

    def select_random_files(self, exclude_paths):
        """
        从 GitHub API 原始 tree 中随机抽取代码文件
        """
        owner, repo = self._parse_repo()

        tree_all = self.reader.get_repo_tree_all(owner, repo)

        candidates = []
        for item in tree_all:
            if not self._is_valid_core_candidate_random(item):
                continue

            path = item["path"]
            if path in exclude_paths:
                continue

            candidates.append(path)

        sample_size = min(2, len(candidates))
        return random.sample(candidates, sample_size) if sample_size > 0 else []

    def create_audit_plan(self):
        print(f"扫描仓库结构: {self.repo_url}...")
        self.fetch_repo_overview()

        print("规划核心审计轨道 (Primary Tracks)...")
        core_files = self.select_core_files()

        print("规划辅助抽检轨道 (Random Tracks)...")
        random_files = self.select_random_files(exclude_paths=core_files)

        return {
            "repo_url": self.repo_url,
            "core_tracks": core_files,
            "random_tracks": random_files,
            "metadata": {
                "tree": self.tree_structure,
                "readme": self.readme_content[:10000]
            }
        }

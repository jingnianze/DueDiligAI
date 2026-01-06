import requests
import base64
import os
from typing import Optional
from configs.env_config import EnvConfig

class GitHubReader:
    def __init__(self, token, proxy: Optional[str] = None):
        self.headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        # 从环境变量获取代理，如果没有提供则使用None（不使用代理）
        if proxy is None:
            proxy = EnvConfig.get_github_proxy()
        if proxy:
            self.proxies = {"http": proxy, "https": proxy}
        else:
            self.proxies = None

    def get_repo_tree(self, owner, repo):
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        res = requests.get(url, headers=self.headers, proxies=self.proxies).json()
        if "tree" not in res:
            url = url.replace("main", "master")
            res = requests.get(url, headers=self.headers, proxies=self.proxies).json()
        files = [item['path'] for item in res.get('tree', []) if item['type'] == 'blob']

        # 构建树状缩进文本
        tree_dict = {}
        for f in files:
            parts = f.split("/")
            current = tree_dict
            for p in parts[:-1]:
                current = current.setdefault(p + "/", {})
            current[parts[-1]] = None

        def render_tree(d, indent=0):
            lines = []
            for k, v in d.items():
                lines.append("    " * indent + k)
                if isinstance(v, dict):
                    lines.extend(render_tree(v, indent + 1))
            return lines

        return "\n".join(render_tree(tree_dict))

    def get_repo_tree_all(self, owner, repo, branch="main"):
        """
        返回 GitHub API 原始 tree 结构（扁平）
        """
        url_ref = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
        ref_resp = requests.get(url_ref, headers=self.headers, proxies=self.proxies)
        ref_resp.raise_for_status()
        commit_sha = ref_resp.json()["object"]["sha"]

        url_commit = f"https://api.github.com/repos/{owner}/{repo}/git/commits/{commit_sha}"
        commit_resp = requests.get(url_commit, headers=self.headers, proxies=self.proxies)
        commit_resp.raise_for_status()
        tree_sha = commit_resp.json()["tree"]["sha"]

        url_tree = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{tree_sha}?recursive=1"
        tree_resp = requests.get(url_tree, headers=self.headers, proxies=self.proxies)
        tree_resp.raise_for_status()

        return tree_resp.json()["tree"]

    def get_file_raw(self, owner, repo, path):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=self.headers, proxies=self.proxies).json()
        return base64.b64decode(res['content']).decode('utf-8')
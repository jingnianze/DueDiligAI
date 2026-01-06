# DueDiligAI ---正在更新中
DueDiligAI是一个全面分析GitHub项目质量的可靠助手
# 🛠️ CodeAnalyst AI: 深度代码尽调专家
CodeAnalyst AI 是一款基于多智能体（Multi-Agent）架构的开源代码仓库分析与技术尽调工具。它不满足于简单的静态扫描，而是通过模拟 CTO 视角，对项目进行 **“宏观统计 + 微观审计”** 的双重逻辑对撞，为代码仓库提供全方位的技术评估。

## 🌟 功能特性

#### 1. 宏观 vs 微观对撞分析
不止关注 Star 数等外部指标，更结合代码实际质量（如安全漏洞、工程规范合规性）进行交叉验证，避免 “虚高” 项目误判。
#### 2. 双轨审计逻辑
核心轨道 (Primary Tracks)：精准锁定算法实现、核心模拟逻辑、系统架构设计等关键代码模块，进行深度穿透式扫描。<br>
抽检轨道 (Random Tracks)：随机捕获边缘模块、辅助工具类中的 “代码异味”（如冗余代码、不规范命名、潜在 Bug），真实反映项目工程纪律水平。
#### 3. 去本地依赖设计
完全基于 GitHub API 实现数据拉取与分析，无需执行 git clone 操作，彻底告别网络超时、庞大仓库磁盘占用等问题，轻量化运行。
#### 4. 深度推理引擎
内置 DeepSeek-V3 / GPT-4o 级别的推理逻辑，能够精准识别 “错误掩埋”“过度工程”“循环依赖” 等高级代码反模式，输出专业级问题诊断。
#### 5. 专业/友好双版本支持
提供CTO专业版与开发者友好版两个版本的代码技术尽调报告，兼顾专业性和用户友好性。

## 🏗️ 架构概览
CodeAnalyst AI 采用多智能体协同架构，各模块职责清晰、高效联动：
#### 1. Scanner（宏观扫描智能体）
核心能力：抓取 GitHub 项目核心指标（活跃度、贡献者数量、Issue 解决效率、版本迭代频率）<br>
输出：项目宏观健康评分及指标明细
#### 2. Strategist（战略规划智能体）
核心能力：解析项目 README 文档、目录树结构，智能筛选 3-5 个最具审计价值的核心文件<br>
输出：核心文件清单及筛选依据
#### 3. Auditor（审计专家智能体）
核心能力：并发执行多维度审计（代码规范、安全风险、性能瓶颈、可读性），定位问题并关联具体行号<br>
输出：带行号引用的精细化技术审计报告
#### 4. Synthesizer（终审汇总智能体）
核心能力：整合宏观指标、核心文件审计结果，进行 “逻辑对撞” 验证（如外部活跃度与内部代码质量的一致性）<br>
输出：Markdown 格式的 CTO 级别综合评估报告
## 安装

1. 克隆仓库
```bash
git clone <repository-url>
cd <repository-name>
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量<br>
本项目使用 OpenRouter 作为统一的 LLM 接入平台。当然，如果用户有自己的LLM平台可以替换，仅需配置base_url和api_key即可。<br>
复制 `.env.example` 为 `.env` 并填写你的配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下必需的环境变量：
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `LLM_API_KEY`: LLM API密钥（或使用特定提供方的密钥）

## 使用方法

### 基本使用

```bash
python code_analysit.py --repo-url https://github.com/owner/repo
```

### 命令行参数

```bash
python code_analysit.py \
  --repo-url https://github.com/owner/repo \
  --primary-audit-model gpt-4o-mini \
  --random-audit-model qwen-plus \
  --strategist-model gpt-4o-mini \
  --synthesizer-model deepseek-v3 \
  --config config.json
```

### 环境变量配置

所有配置都可以通过环境变量设置：

```bash
export GITHUB_TOKEN=your_token
export LLM_API_KEY=your_api_key
export PRIMARY_AUDIT_MODEL=gpt-4o-mini
export RANDOM_AUDIT_MODEL=qwen-plus
export STRATEGIST_MODEL=gpt-4o-mini
export SYNTHESIZER_MODEL=deepseek-v3
```

### 配置文件

创建JSON配置文件（可选）：

```json
{
  "default_model": "gpt-4o-mini",
  "model_provider": "vectorengine",
  "primary_audit": "gpt-4o-mini",
  "random_audit": "qwen-plus",
  "strategist": "gpt-4o-mini",
  "synthesizer": "deepseek-v3"
}
```

使用配置文件：
```bash
python code_analysit.py --repo-url <url> --config config.json
```

## 环境变量说明

### 必需的环境变量

- `GITHUB_TOKEN`: GitHub Personal Access Token
- `LLM_API_KEY`: LLM API密钥（或使用特定提供方的密钥）

### 可选的环境变量

#### GitHub配置
- `GITHUB_PROXY`: GitHub API代理地址（可选）


#### 模型配置
- `DEFAULT_MODEL_NAME`: 默认模型名称（默认：gpt-4o-mini）
- `PRIMARY_AUDIT_MODEL`: 主审计模型（默认：gpt-4o-mini）
- `RANDOM_AUDIT_MODEL`: 随机审计模型（默认：qwen-plus）
- `STRATEGIST_MODEL`: 策略规划模型（默认：gpt-4o-mini）
- `SYNTHESIZER_MODEL`: 综合报告模型（默认：deepseek-v3）

## 项目结构

```
.
├── code_analysit.py      # 主程序入口
├── scanner.py            # GitHub仓库扫描模块
├── strategist.py         # 审计策略规划模块
├── auditor.py            # 代码审计模块
├── synthesizer.py        # 报告综合模块
├── configs/              # 配置模块
│   ├── env_config.py     # 环境变量配置管理
│   ├── model_config.py   # 模型配置管理
│   └── llmconfig.py     # LLM调用接口
├── utils/                # 工具模块
│   └── github_reader.py  # GitHub API读取器
├── prompts/              # 提示词模板
│   ├── auditor.yaml
│   ├── strategist.yaml
│   └── synthesizer.yaml
├── .env.example          # 环境变量示例
└── README.md            # 本文件
└── LICENSE              # 许可证
```
## ⚠️ 免责声明 (Disclaimer) 
本项目生成的审计报告仅供技术参考与学习交流，不构成任何形式的投资建议或生产环境接入保障。LLM 可能产生幻觉，请在根据报告做出决策前，由人工进行二次核实。作者不对因使用本工具导致的任何代码损失、系统故障或法律纠纷承担责任。
## 安全说明

⚠️ **重要**：本项目已完全移除所有硬编码的敏感信息（API密钥、Token等）。所有敏感信息必须通过环境变量或`.env`文件配置。

- ✅ 所有API密钥从环境变量读取
- ✅ 已删除包含硬编码密钥的配置文件
- ✅ `.env`文件已添加到`.gitignore`
- ✅ 提供了`.env.example`作为配置模板

## 许可证
本项目基于 MIT 许可证开源，完整许可文本见 LICENSE 文件

## 贡献

欢迎提交Issue和Pull Request！



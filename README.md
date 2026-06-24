# Gaokao/Kaoyan Agent - 智能志愿填报助手

基于 LangChain + LangGraph + Streamlit 构建的高考/考研志愿填报智能咨询 Agent。采用 ReAct（推理+行动）模式，结合 RAG（检索增强生成）技术，提供专业选择、院校风险评估和志愿方案生成等功能。

## 功能特性

- **智能问答**：基于张雪峰方法论的知识库问答
- **专业推荐**：根据家庭类型推荐/排除专业
- **风险评估**：多维度志愿方案风险分析（梯度、滑档、调剂、学科匹配、策略一致性）
- **志愿报告**：一键生成结构化志愿填报报告
- **流式输出**：打字机效果实时展示回答

## 项目结构

```
AgentProject/
├── app.py                          # Streamlit Web UI 入口
├── md5.text                        # MD5 哈希记录（文档去重用）
├── agent/
│   ├── react_agent.py              # ReAct Agent 核心定义
│   └── tools/
│       ├── agent_tools.py          # Agent 工具集（12个工具）
│       └── midddleware.py          # LangGraph 中间件（日志、工具监控、Prompt 切换）
├── config/
│   ├── chroma.yml                  # ChromaDB 向量库配置
│   ├── prompts.yml                 # Prompt 文件路径配置
│   └── rag.yml                     # LLM 和 Embedding 模型配置
├── data/                           # 知识库文本文件
├── model/
│   └── factory.py                  # 模型工厂（LLM 和 Embedding 实例创建）
├── prompts/
│   ├── main_prompt.txt             # 主 Agent 系统 Prompt
│   ├── rag_summarize.txt           # RAG 摘要 Prompt 模板
│   └── report_prompt.txt           # 报告生成 Prompt 模板
├── rag/
│   ├── rag_service.py              # RAG 摘要服务
│   └── vector_store.py             # ChromaDB 向量存储管理
├── report/                         # 生成的志愿填报报告
└── utils/
    ├── config_handler.py           # YAML 配置加载
    ├── file_handler.py             # 文件 MD5、目录列表、文本加载
    ├── logger_handler.py           # 日志工具
    ├── path_tool.py                # 绝对路径解析
    └── prompt_loader.py            # Prompt 文件加载
```

## 环境配置

### Python 依赖

```
streamlit
langchain
langchain-core
langchain-community
langchain-openai
langchain-chroma
langchain-text-splitters
langgraph
pyyaml
dashscope
```

### 安装

```bash
pip install streamlit langchain langchain-core langchain-community langchain-openai langchain-chroma langchain-text-splitters langgraph pyyaml dashscope
```

### 模型配置

编辑 `config/rag.yml`：

```yaml
# 聊天模型（使用 OpenAI 兼容 API）
chat_model_name: "mimo-v2.5-pro"
chat_model_api_key: "your-chat-model-api-key"
chat_model_url: "https://token-plan-cn.xiaomimimo.com/v1"

# Embedding 模型（阿里 DashScope）
embedding_model_name: "text-embedding-v4"
embedding_model_api_key: "your-embedding-model-api-key"
```

### 向量库配置

编辑 `config/chroma.yml`：

```yaml
collection_name: "agent"
persist_directory: "chroma_db"
k: 3                    # 检索返回的 Top-K 文档数
data_path: "data"
md5_hex_store: "md5.text"
allow_knowledge_file_type: ["txt"]
chunk_size: 200
chunk_overlap: 20
separators: ["#", "##", "###", "---", "\n\n", "。", "！", "？", "；", ".", "!", "?", ";", " "]
```

### Prompt 配置

编辑 `config/prompts.yml` 指定各 Prompt 模板路径：

```yaml
main_prompt_path: "prompts/main_prompt.txt"
rag_summarize_prompt_path: "prompts/rag_summarize.txt"
report_prompt_path: "prompts/report_prompt.txt"
```

## 启动

```bash
cd AgentProject
streamlit run app.py
```

## 各模块详细说明

### app.py - Streamlit Web UI

| 函数 | 说明 |
|------|------|
| `caputer(generator, cache_list)` | 流式输出控制，逐字符展示 Agent 响应并缓存，实现打字机效果 |

模块级逻辑：
- 在 `st.session_state["agent"]` 中创建并缓存 `ReactAgent` 实例
- 维护 `st.session_state["message"]` 聊天历史
- 接收用户输入，调用 `agent.execute_stream(prompt)` 流式输出

---

### agent/react_agent.py - ReAct Agent 核心

#### 类：`ReactAgent`

| 方法 | 参数 | 说明 |
|------|------|------|
| `__init__()` | - | 使用 `langchain.agents.create_agent` 初始化 Agent，绑定聊天模型、系统 Prompt、12 个工具和 3 个中间件 |
| `execute_stream(query)` | `query: str` | 流式执行用户查询。使用 `stream_mode="values"`，传递 `context={"report":False}` 支持动态 Prompt 切换。逐块 yield 最新消息内容 |

---

### agent/tools/agent_tools.py - Agent 工具集

#### 工具函数

| 函数 | 参数 | 说明 |
|------|------|------|
| `rag_summarize(query)` | `query: str` | 从向量存储中检索参考资料并生成摘要（RAG） |
| `list_majors(family_type)` | `family_type: str = "普通家庭"` | 解析专业选择分析数据，输出张雪峰推荐/不推荐的专业列表 |
| `assess_risk(rank, schools, accept_adjustment, priority, weak_subjects)` | `rank: int`, `schools: str`, `accept_adjustment: bool = True`, `priority: str = "专业优先"`, `weak_subjects: str = ""` | 多维度风险评估：梯度检查、滑档风险、调剂风险、学科专业匹配、策略一致性、黑名单检测 |
| `fill_context_for_report()` | - | 触发中间件切换到报告生成 Prompt 的标记工具 |
| `set_rank(rank)` | `rank: int` | 记录考生排名 |
| `set_province(province)` | `province: str` | 记录考生省份 |
| `set_priority(priority)` | `priority: str` | 记录志愿策略偏好（"专业优先" / "学校优先"） |
| `set_target_majors(target_majors)` | `target_majors: str` | 记录目标专业（逗号分隔） |
| `set_weak_subjects(weak_subjects)` | `weak_subjects: str` | 记录弱势学科（逗号分隔） |
| `set_accept_adjustment(accept_adjustment)` | `accept_adjustment: bool` | 记录是否接受调剂 |
| `generate_report(report_content)` | `report_content: str` | 将报告保存为带时间戳的 `.txt` 文件到 `report/` 目录 |

#### 内部辅助函数

| 函数 | 说明 |
|------|------|
| `_read_data_file(relative_path)` | 带文件修改时间缓存的数据文件读取器 |
| `parse_schools(text)` | 解析 "学校\|专业\|预估位次" 格式的院校条目 |
| `check_gradient(entries, student_rank)` | 检查冲/稳/保梯度是否合理 |
| `check_slide_risk(entries)` | 检查位次跨度是否足够防止滑档 |
| `check_adjustment(entries, accept_adj, prio)` | 检查调剂风险 |
| `check_subject_major(weak, entries)` | 交叉检查弱势学科与目标专业的匹配度 |
| `check_strategy_consistency(prio, accept_adj)` | 检查策略组合是否矛盾 |
| `check_blacklist(entries)` | 检查是否选择了黑名单专业 |

---

### agent/tools/midddleware.py - LangGraph 中间件

| 函数 | 类型 | 说明 |
|------|------|------|
| `monitor_tool(request, handler)` | `@wrap_tool_call` | 工具调用监控：记录工具名和参数，执行后若为 `fill_context_for_report` 则设置 `context["report"]=True` 触发 Prompt 切换 |
| `log_before_model(state, runtime)` | `@before_model` | 模型调用前的日志记录：输出消息数量和最后一条消息内容 |
| `report_prompt_switch(request)` | `@dynamic_prompt` | 动态 Prompt 切换：根据 `context["report"]` 返回对应的系统 Prompt |

---

### model/factory.py - 模型工厂

| 类/变量 | 说明 |
|---------|------|
| `BaseModelFactory` | 抽象基类，定义 `generator()` 工厂接口 |
| `ChatModelFactory` | 创建 `ChatOpenAI` 实例，连接小米 MiMo API |
| `EmbeddingsModelFactory` | 创建 `DashScopeEmbeddings` 实例，使用阿里 DashScope |
| `chat_model` | 模块级单例，聊天模型实例 |
| `embedding_model` | 模块级单例，Embedding 模型实例 |

---

### rag/vector_store.py - 向量存储

#### 类：`VectorStoreService`

| 方法 | 说明 |
|------|------|
| `__init__()` | 初始化 Chroma 向量库和文本分割器 |
| `get_retriever()` | 返回配置了 Top-K 的检索器 |
| `load_document()` | 加载 `data/` 目录下的文本文件到向量库，通过 MD5 去重避免重复加载 |

---

### rag/rag_service.py - RAG 摘要服务

| 函数/类 | 说明 |
|---------|------|
| `print_prompt(prompt)` | 调试用 Prompt 打印函数，透传返回原始 Prompt |
| `RagSummarizeService.__init__()` | 初始化：创建向量存储、获取检索器、加载 Prompt 模板、构建 LCEL Chain |
| `RagSummarizeService._init_chain()` | 构建 `PromptTemplate -> LLM -> StrOutputParser` 链 |
| `RagSummarizeService.retriever_docs(query)` | 从向量库检索相关文档 |
| `RagSummarizeService.rag_summarize(query)` | 完整 RAG 流程：检索 -> 格式化上下文 -> 调用模型生成摘要 |

---

### utils/ 工具模块

#### utils/config_handler.py - 配置加载

| 函数 | 说明 |
|------|------|
| `load_rag_config()` | 加载 `config/rag.yml` |
| `load_chroma_config()` | 加载 `config/chroma.yml` |
| `load_prompts_config()` | 加载 `config/prompts.yml` |
| `load_agent_config()` | 加载 `config/agent.yml` |

#### utils/file_handler.py - 文件操作

| 函数 | 说明 |
|------|------|
| `get_file_md5_hex(filepath)` | 计算文件 MD5 哈希值 |
| `listdir_with_allowed_type(path, allowed_types)` | 列出指定类型的文件 |
| `txt_loader(filepath)` | 加载文本文件为 LangChain Document 对象 |

#### utils/logger_handler.py - 日志

| 函数 | 说明 |
|------|------|
| `get_logger(name, console_level, file_level, log_file)` | 创建带控制台和文件双输出的 Logger |

#### utils/path_tool.py - 路径解析

| 函数 | 说明 |
|------|------|
| `get_project_root()` | 获取项目根目录绝对路径 |
| `get_abs_path(relative_path)` | 将相对路径转为绝对路径 |

#### utils/prompt_loader.py - Prompt 加载

| 函数 | 说明 |
|------|------|
| `load_system_prompts()` | 加载主系统 Prompt |
| `load_rag_prompts()` | 加载 RAG 摘要 Prompt 模板 |
| `load_report_prompts()` | 加载报告生成 Prompt 模板 |

## 数据文件

`data/` 目录下的知识库文件：

| 文件 | 内容 |
|------|------|
| `01总体观点总结.txt` | 张雪峰总体观点总结 |
| `02高考志愿填报方法论.txt` | 高考志愿填报方法论 |
| `03考研指导手册.txt` | 考研指导手册 |
| `04专业选择分析汇总.txt` | 专业选择分析（供 `list_majors` 工具解析） |
| `05语录与价值观.txt` | 张雪峰语录与价值观 |
| `06问答知识库.txt` | 问答知识库 |

新增 `.txt` 文件放入 `data/` 目录后会自动加载（通过 MD5 去重）。

## 工作流程

```
用户输入
  │
  ▼
ReactAgent (ReAct 循环)
  │
  ├─ 普通问答 ──► rag_summarize 工具 ──► RAG 检索 + LLM 生成
  │
  ├─ 专业咨询 ──► list_majors 工具 ──► 解析专业数据
  │
  ├─ 风险评估 ──► assess_risk 工具 ──► 五维度风险检测
  │
  └─ 生成报告 ──► set_* 工具收集信息
                   └─► fill_context_for_report
                       └─► 动态切换 Report Prompt
                           └─► generate_report 保存文件
```

## 注意事项

1. **API Key 安全**：API Key 目前存储在 `config/rag.yml` 中，请勿将包含真实 Key 的配置文件提交到公开仓库
2. **工作目录**：启动命令需在 `AgentProject/AgentProject/` 目录下执行
3. **知识库更新**：新增知识文件后无需手动处理，系统会通过 MD5 去重自动加载新文件
4. **日志文件**：运行日志保存在 `logs/` 目录，按时间戳命名

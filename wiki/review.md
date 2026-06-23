# 主题综述 LLM 草稿 · Review

- 共 **125** 个主题已起草（候选总数 125）
- 用途：人工审阅 LLM 自动生成的 topic 顶部综述，确认满意后再跑 `--all`。
- 修改方式：直接编辑 `wiki/topics/<topic>.md` 中 `<!-- LLM-DRAFT:BEGIN/END -->` 之间的内容；
  审阅通过后，建议把该 markers 替换为 `<!-- HUMAN-REVIEWED:BEGIN/END -->` 以避免被重跑覆盖。

---

## `learning-notes`  · 66 篇笔记  · 447 字

> 该主题下的笔记围绕 LLM 应用从 Prompt 设计到 RAG 落地的全链路展开，核心关注点是如何让不确定性输出在工程层面变得可测、可控、可回归：覆盖 LLM 基础原理、Prompt 工程进阶（CoT/ToT/ReAct）、结构化输出约束（JSON Mode、Regex Constraint）、Prompt 稳定性评测，以及 Embedding 相似度、向量数据库切片入库与 RAG 标准架构。跨笔记可复用的工程实践包括：基于多次采样的稳定性评测（pass@k、语义一致性）、用 cosine similarity 做语义断言、用 FAISS/Chroma 等向量库构建检索基线、用 JSON Schema 校验结构化输出，并结合 Ginkgo、pytest 等框架沉淀回归用例。对 QA 的启发是：应将"语义等价 + 结构合规 + 检索命中率"三类指标纳入回归门禁，替代传统精确匹配断言；同时为 RAG 链路建立切片质量与召回 Top-K 的离线评测集，把不稳定环节前移到 CI 中拦截。

- 源文件：[`wiki/topics/learning-notes.md`](topics/learning-notes.md)

---

## `QA`  · 54 篇笔记  · 429 字

> 该主题下的笔记围绕大模型与 AI Agent 的可测性展开，核心问题是如何把不确定性输出转化为可度量、可回归的质量信号，覆盖从 Prompt 工程（CoT/ToT/ReAct）、结构化输出约束（JSON Mode、Regex Constraint）到 Embedding 相似度、向量检索（FAISS）、多 Agent 协作、性能基线与全链路可观测性的完整链路。跨笔记可复用的方法集中在：以 Schema 校验加正则约束兜底输出稳定性、用 Embedding 相似度替代字面 diff 做语义断言、基于 Locust/k6 构建 Agent 场景化压测、借助 OpenTelemetry Trace 追踪多 Agent 调用链与 Token 成本。建议 QA 在落地时优先沉淀两层资产：一是建立带语义断言的回归用例集，把 Prompt 与 Skill 变更纳入版本化评测；二是将性能基线与 Trace 指标接入 CI，形成质量、成本、时延三位一体的准入门槛。

- 源文件：[`wiki/topics/QA.md`](topics/QA.md)

---

## `AI`  · 53 篇笔记  · 477 字

> 该主题下的 53 篇笔记围绕 LLM 与 AI Agent 的全链路质量保障展开，核心问题是：在生成式系统不确定性强、调用链长、依赖外部模型与向量检索的前提下，如何构建可度量、可回归、可观测的测试体系，覆盖从 Prompt 工程、结构化输出约束、ToT/ReAct 推理、Embedding 与向量库（FAISS）相似度评估，到多 Agent 协作、Skill 编排、性能基线与混沌注入的完整链路。可复用的工程实践包括：以 JSON Mode 与 Regex Constraint 固化输出契约、以 Embedding 相似度替代精确断言、用 Locust/k6 建立 Agent 场景下的吞吐与延迟基线、借助 OpenTelemetry Trace 串联多 Agent 调用、通过 Chaos Mesh 与 Ginkgo E2E 注入故障验证韧性。对 QA 的落地建议是：先把 Prompt 稳定性与结构化校验沉淀为可回归的断言层，再以 Trace + 性能基线 + 混沌实验组合形成 Agent 版"非功能测试矩阵"，避免停留在人工抽检式的效果评估。

- 源文件：[`wiki/topics/AI.md`](topics/AI.md)

---

## `Agent`  · 48 篇笔记  · 409 字

> 本主题下的 48 篇笔记围绕 AI Agent 的工程化测试与稳定性保障展开，核心问题聚焦在如何让具备推理（ToT/ReAct）、工具调用与多 Agent 协作能力的非确定性系统，在真实负载与故障场景下保持输出质量、链路可追踪与性能可回归。跨笔记可复用的方法论包括：以结构化输出与 Prompt 稳定性测试构建语义层断言、用 Embedding 与 FAISS 做相似度回归、依托 Ginkgo 编写 E2E 与契约用例、使用 Locust 与 k6（含 WebSocket）建立性能基线、通过 OpenTelemetry Trace 打通 Agent 调用链、并借助 Chaos Mesh 注入故障验证多 Agent 协作的韧性。对 QA 的启发是：应尽早将性能基线与语义评估资产化、纳入 CI 回归门禁，避免依赖人工抽检；同时把 Trace、Token 消耗与工具调用成功率作为一等可观测指标，与功能用例同权治理。

- 源文件：[`wiki/topics/Agent.md`](topics/Agent.md)

---

## `Ginkgo`  · 41 篇笔记  · 393 字

> 该主题下的笔记围绕「AI Agent 在交付链路中如何被系统化验证」这一核心问题展开，覆盖多 Agent 协作、性能压测资产化、K8s 端到端发布验收、安全防线、评测样本集工程、失败归因分诊、质量 SLO 与发布评分卡及持续监控看板，呈现出从单点用例到全链路质量体系的演进路径。可复用的方法栈以 Ginkgo 作为 BDD 化测试组织框架，配合 k6 WebSocket 与 Locust 做性能基线与回归门禁，借助 FAISS、结构化输出校验、Prompt 稳定性回放等手段沉淀评测样本，并通过失败分诊、SLO 评分卡与 Grafana 类看板形成闭环反馈。对 QA 工作的启发是：一方面应把 Agent 测试资产（样本集、压测脚本、归因规则）纳入版本化管理并接入 CI 门禁，避免一次性脚本化；另一方面建议以 SLO 评分卡替代单一通过率，将质量、性能、安全指标统一为发布准入信号。

- 源文件：[`wiki/topics/Ginkgo.md`](topics/Ginkgo.md)

---

## `Playwright`  · 40 篇笔记  · 378 字

> 该主题下的笔记围绕 AI Agent 在交付链路上的质量保障展开，核心问题集中在如何把不确定性较高的大模型应用纳入可度量、可回归、可发布的工程体系，覆盖性能压测、端到端验收、安全防线、评测样本集、失败归因、SLO 与评分卡、质量看板及灰度与影子流量等环节。跨笔记可复用的工程实践包括：以 k6 WebSocket 与 Locust 做流式与并发压测、用 Ginkgo 编排回归门禁、用 Playwright 串联端到端用户路径、借 FAISS 等向量检索沉淀评测样本与归因聚类，并以 SLO 评分卡和监控看板驱动灰度/影子发布决策。对 QA 工作的启发是：一方面应把"压测脚本、评测集、归因规则"资产化进版本库，使其与 Prompt、模型版本同步演进；另一方面建议以发布评分卡作为唯一放行口径，将安全、性能、效果指标统一为可阻断的门禁，避免靠人工评审兜底。

- 源文件：[`wiki/topics/Playwright.md`](topics/Playwright.md)

---

## `Kubernetes`  · 28 篇笔记  · 433 字

> 这批笔记围绕一个核心命题展开：当 AI Agent 从"会回答"走向"能调用工具、读数据、执行动作"后，质量保障的边界必须从回答正确性扩展到行为可控性，覆盖混沌容错、SLO 评分卡、灰度与影子流量、Token 成本预算、Prompt Injection 与越权防护、合规审计、最小权限委托等纵深议题。跨笔记可复用的工程范式高度一致：以 Ginkgo 承担后端 E2E 与契约断言、Playwright 校验前端高风险交互与告知链路、Chaos Mesh 注入故障验证韧性，并依托 Kubernetes 做租户隔离、配额与工作负载身份治理，配合 Trace 对账、声明化策略与回归基线，把"可观测—可约束—可优化"沉淀为持续门禁。对 QA 的启发是：一方面应把成本、安全、权限、合规这类非功能维度前置为发布评分卡中的硬性指标，而非事后审计项；另一方面建议以"用户最小权限"而非"系统最大权限"为基线设计 Agent 授权用例，让红队评测和影子流量成为日常回归的一部分。

- 源文件：[`wiki/topics/Kubernetes.md`](topics/Kubernetes.md)

---

## `API-Testing`  · 20 篇笔记  · 407 字

> 这组笔记共同聚焦一个核心命题：当 AI Agent 从"会回答"演进到"会决策、会执行、会记忆、会跨人协同"后，质量风险的重心从答案准确性转向了行为可控性，包括权限代理失真、模型路由与降级失效、决策不可解释、记忆污染、自主规划越界、长任务断点失守、人工接管缺位以及多租户串数等系统性缺陷。跨笔记可复用的工程实践高度一致：以 Ginkgo 做后端链路 E2E 与状态机校验、Python/API 做契约测试与故障注入、Playwright 做用户视角的透明性与接管体验验证、K8s 做多副本漂移、熔断与恢复演练，并普遍要求结构化建模 tenant_id、session_id、审批快照、幂等键、审计轨迹等关键对象。对 QA 的启发是：应把"最小权限、可解释、可审计、可恢复、可隔离"沉淀为 Agent 类系统的统一质量基线，并将审计日志、决策轨迹、状态机视为一等测试资产，而非附属产物，提前在用例设计阶段就显式覆盖。

- 源文件：[`wiki/topics/API-Testing.md`](topics/API-Testing.md)

---

## `K8s`  · 11 篇笔记  · 442 字

> 该主题下的 11 篇笔记围绕 AI Agent 在 K8s 环境下从发布验收、安全防线、评测样本集、失败归因到线上巡检的全生命周期质量保障展开，核心问题是如何把非确定性的 LLM 系统纳入可工程化、可回归、可观测的测试体系。跨笔记反复出现的关键实践包括：基于 Ginkgo Label 与 Playwright Tag 的分层用例筛选、Test Impact Analysis 与风险评分驱动的智能回归、依赖注入与 Recording/Replay 中间件支撑的确定性回放、FAISS/Embedding 语义断言、合成探针与金丝雀断言构成的线上活性检测，以及围绕 Prompt、工具 Schema、模型版本的变更感知路由。对 QA 的启发是：一方面应在 Design Review 阶段把可观测性、可控制性、可隔离性作为架构验收项前置，杜绝"测不动"的 Agent 进入交付链路；另一方面要建设离线 Eval 基线与线上探针双轨制，让生产 Trace 反哺评测样本集，形成质量闭环。

- 源文件：[`wiki/topics/K8s.md`](topics/K8s.md)

---

## `SDET`  · 10 篇笔记  · 402 字

> 本主题围绕 AI Agent 在 K8s 化交付链路中的端到端质量保障展开，覆盖发布验收、安全防线、评测样本集工程、失败归因与自动化分诊、质量看板、灰度与影子流量、契约与 Schema 演进、测试数据与环境治理八个环节，核心问题是如何为具备非确定性输出的 Agent 系统建立可度量、可回归、可追责的工程化测试闭环；可复用方法包括以 Ginkgo 组织端到端用例、Playwright 驱动多模态交互验证、FAISS 做语义相似度断言与样本去重、基于 JSON Schema 的契约测试与版本兼容矩阵、影子流量比对与灰度放量门禁、Prompt Injection 与越权用例集、归因标签体系驱动自动分诊以及 Prometheus/Grafana 质量看板。建议 QA 将"评测集即代码"和"质量门禁即流水线"作为团队基建优先级，先沉淀分层断言库与失败归因字典，再以影子流量打通线上回放，逐步替代人工抽检。

- 源文件：[`wiki/topics/SDET.md`](topics/SDET.md)

---

## `API-testing`  · 6 篇笔记  · 393 字

> 本主题聚焦 AI Agent 从环境就绪到上线运营全链路的 API 层验收问题，覆盖 K8s 端到端发布验收、评测样本集构建、失败归因与自动分诊、质量看板与持续监控、灰度与影子流量、契约测试与 Schema 演进六个环节，核心矛盾是如何在模型输出非确定性下保障接口语义稳定与回归可控。可复用的工程实践包括：基于 Ginkgo/Pytest 的分层用例编排、Playwright 驱动的端到端回放、FAISS 做语义断言与相似样本聚类、JSON Schema/Pact 守护契约边界、影子流量与灰度分桶做线上对照、Prometheus + Grafana 沉淀质量看板与归因标签体系。对 QA 的落地建议有二：一是把"样本集 + 契约 + 监控"作为 Agent 项目的最小测试基线，先于功能用例建设；二是将失败归因结构化为可消费的标签流，反哺灰度门禁与发布卡点，形成闭环而非一次性验收。

- 源文件：[`wiki/topics/API-testing.md`](topics/API-testing.md)

---

## `observability`  · 6 篇笔记  · 416 字

> 这组笔记围绕 AI Agent 全链路可观测性展开，核心问题是如何让一个由 LLM 推理、工具调用、异步任务和前端交互拼接而成的非确定性系统变得"可被看见、可被解释、可被归因"，覆盖从 OpenTelemetry Trace 埋点、失败分诊与质量看板，到决策审计、合成巡检的完整闭环。跨笔记可复用的方法论已较为收敛：以 OpenTelemetry 统一 Trace/Span 语义并贯穿工具调用链，用 Ginkgo 守护推理轨迹与工具调用顺序的 E2E 正确性，用 Python/API 测试承担指标聚合、契约校验与告警阈值，用 Playwright 验证前端可见状态与可解释性 UI，用 K8s CronJob 承载周期化合成探针与审计日志可靠性校验。对 QA 的启发是：测试断言应从"输出文本对不对"前移到"推理链路、工具轨迹、审计记录是否完整可复盘"，并把合成巡检结果直接接入发布门禁，让线上质量信号在真实用户受损前触发拦截。

- 源文件：[`wiki/topics/observability.md`](topics/observability.md)

---

## `reliability`  · 6 篇笔记  · 454 字

> 这组笔记共同聚焦 AI Agent 走向生产环境后的可靠性命题：当系统从单轮问答演进为长任务、异步回调、多模型路由与事件驱动架构时，故障形态从"答错"转向"状态不收敛、回调重复、降级不透明、链路无法复盘"，测试关注点也随之从结果正确性扩展到状态机完整性、幂等性、可重放性与 SLO 可度量性。可复用的方法栈相对收敛：Ginkgo 承担后端 E2E 与状态机/事件链路编排，Python API Testing 负责 webhook 契约、签名、去重与审计查询校验，Playwright 验证降级提示与进度时间线的用户可感知性，Chaos Mesh 与 Kubernetes 用于 consumer 重启、队列堆积、Worker 漂移等故障注入，并以发布评分卡沉淀 SLO 基线。落地建议有二：一是把"任务状态机 + 事件溯源"作为 Agent 类系统的测试基建前置项，没有清晰状态枚举与重放能力就不进入 E2E；二是 QA 应主动牵头降级透明度与审计可追溯性的验收标准，避免可靠性问题只在事故复盘时才被发现。

- 源文件：[`wiki/topics/reliability.md`](topics/reliability.md)

---

## `performance`  · 5 篇笔记  · 375 字

> 本主题聚焦 AI Agent 在真实负载下的性能、稳定性与成本治理，关注的并非单次推理延迟，而是长上下文、多工具调用、流式 WebSocket 通信、重试放大与租户级预算在持续压测中的退化行为，以及如何把这些指标沉淀为可回归的质量门禁。跨笔记可复用的工程实践包括：以 Locust 与 k6（含 WebSocket 场景）构建 Agent 化压测脚本，以 Ginkgo 做后端断言与预算校验，以 Playwright 验证前端成本与降级提示，结合 Trace 对账、基线快照与 K8s 限流配额，形成"基线—压测—资产化—门禁"的闭环，核心指标覆盖 P95 延迟、单会话 Token、失败重试倍数与工具调用 ROI。建议 QA 侧把性能与成本基线纳入每次发版的强制门禁，并将压测脚本与阈值同业务用例一同版本化，避免性能回归在上线后才被账单和告警发现。

- 源文件：[`wiki/topics/performance.md`](topics/performance.md)

---

## `agent`  · 4 篇笔记  · 409 字

> 本主题下的四篇笔记围绕 AI Agent 上线前后的质量保障展开，核心问题集中在如何对一个非确定性、多跳调用、依赖外部工具与模型的系统进行性能、可观测性、韧性与安全四个维度的工程化验证。可复用的方法栈较为清晰：性能侧用 Locust 与 k6 构造多轮对话与工具调用混合场景，关注 TTFT、tokens/s 与并发下的尾延迟；可观测性侧以 OpenTelemetry 串联 LLM 调用、Tool 调用与向量检索（如 FAISS）的 Trace，沉淀 span 级指标；韧性侧用 ChaosMesh 注入网络延迟、依赖中断与模型超时，验证降级与重试策略；安全侧覆盖 Prompt Injection、越权访问与数据泄露的用例集。对 QA 的启发是，应尽早把 Agent 当作分布式系统而非单接口看待，建立"压测—追踪—混沌—红队"一体化流水线，并将 Trace ID 贯穿用例与缺陷单，使非确定性失败可复现、可归因。

- 源文件：[`wiki/topics/agent.md`](topics/agent.md)

---

## `load-testing`  · 4 篇笔记  · 384 字

> 本主题四篇笔记聚焦于 AI Agent 场景下的性能压测如何从一次性脚本演进为可回归、可门禁的工程资产，核心问题在于传统 HTTP 压测工具难以覆盖 LLM 流式响应、长会话 WebSocket、多轮工具调用等不确定性负载，且缺乏对 token 吞吐、首包延迟（TTFT）、尾延迟与失败语义的统一度量。跨笔记可复用的方法论包括：以 Locust 承载多步骤业务化用户行为、以 k6（含 WebSocket 扩展）承载高并发与协议级压测、用 Ginkgo 将压测断言与基线对比纳入 BDD 风格回归、并通过 SLO 阈值（P95/P99、错误率、token/s）形成 CI 门禁。对 QA 的启发是：应尽早将 Agent 压测脚本与 Mock LLM、数据集快照一同纳入版本库，按场景分层维护基线指标，并在流水线中以红绿门禁阻断性能回退，避免性能问题滞留到线上才被发现。

- 源文件：[`wiki/topics/load-testing.md`](topics/load-testing.md)

---

## `audit`  · 3 篇笔记  · 420 字

> 这三篇笔记共同聚焦于 AI Agent 进入企业关键业务后“可追溯、可解释、可复盘”的质量底座问题：当 Agent 具备读库、调用工具、异步回调与跨系统写操作能力后，单纯校验输出正确性已不足以覆盖风险，必须把数据流转边界、决策推理链路、事件溯源序列、审计日志与重放能力一并纳入测试范围，回答“谁在什么输入下做了什么动作、是否合规、能否复盘”。可复用的方法论上，三篇均收敛到同一套组合拳——Ginkgo 做后端 E2E 全链路与事件生命周期校验、Python/API 做合规与审计契约测试、Playwright 做前端权限告知与时间线一致性验证、Kubernetes 做隔离治理与消费者重启重放演练，并强调将合规规则、审计事件、留存策略声明化、结构化。落地建议有二：一是把审计完整性、脱敏正确性与事件可重放性沉淀为 CI 持续门禁而非一次性用例；二是要求每条关键链路同时产出可被测试消费的结构化事件，让 QA 能从“验断言”升级到“验轨迹”。

- 源文件：[`wiki/topics/audit.md`](topics/audit.md)

---

## `e2e`  · 3 篇笔记  · 365 字

> 本主题三篇笔记聚焦于 AI Agent 端到端质量保障的闭环建设，核心问题是如何在非确定性输出场景下，将安全防线、评测样本与失败归因串成可持续运行的 E2E 测试体系：Day 28 从输入注入、工具调用越权到输出泄露分层设计防御用例，Day 29 讨论评测样本集的分层抽样、版本化与脏数据治理，Day 30 则覆盖失败模式分类与自动分诊回流。可复用的工程实践包括用 Playwright 驱动多轮对话回放、Ginkgo 组织分层 BDD 用例、FAISS 做语义去重与相似 case 聚类，以及通过 LLM-as-Judge 配合规则断言形成双轨校验。对 QA 的启发是：应把样本集、断言器与归因标签视为与被测系统同等重要的资产纳入 CI 流水线，并建立失败用例自动回灌评测集的机制，让 E2E 体系随 Agent 迭代共同演进。

- 源文件：[`wiki/topics/e2e.md`](topics/e2e.md)

---

## `k6`  · 3 篇笔记  · 381 字

> 围绕 k6 主题的三篇笔记共同聚焦于 AI Agent 场景下的性能压测工程化与回归门禁问题，关注点从单次跑分转向资产化、可回归、可纳管的质量基线，覆盖 LLM 长会话、流式响应与 WebSocket 长连接等典型 Agent 交互形态。跨笔记可复用的方法栈包括：以 k6 承接 HTTP/WebSocket 协议层压测、以 Locust 编排多角色业务流与混合负载、以 Ginkgo 将性能断言纳入 BDD 风格的回归用例，并通过 P95/P99 延迟、Token 吞吐、错误率与会话完成率构建多维 SLO，再借助阈值门禁与基线对比实现 CI 内的性能回归拦截。对 QA 工作的启发是：应尽早把性能脚本与基线数据作为一等代码资产纳入仓库与流水线管理，并针对 Agent 的非确定性输出，将语义级成功率与传统性能指标共同纳入门禁，避免只看 RT 而漏判效果回退。

- 源文件：[`wiki/topics/k6.md`](topics/k6.md)

---

## `security`  · 3 篇笔记  · 372 字

> 本主题聚焦 AI Agent 区别于传统 Web 的新型复合安全风险，核心覆盖 Prompt Injection、工具越权、记忆污染、跨租户数据串读、敏感信息外泄与危险动作误执行等攻击面，强调测试目标需从"答得对不对"转向"是否仅在授权边界内行动"。跨笔记可复用的工程实践包括五层安全护栏（输入防护、决策约束、执行鉴权、结果审计、持续红队评测），以及 Ginkgo 驱动的后端 E2E 越权校验、Python/API 契约校验、Playwright 前端高风险交互验证、K8s 命名空间隔离策略，构成攻防闭环。落地建议有二：一是把红队用例（注入语料、越权路径、数据泄露探针）沉淀为可回归的安全测试集并接入 CI 门禁，避免一次性演练；二是优先以最小权限收敛工具与数据访问边界，再围绕该边界设计攻击用例，让 QA 从被动验证转为主动的风险建模者。

- 源文件：[`wiki/topics/security.md`](topics/security.md)

---

## `tracing`  · 3 篇笔记  · 380 字

> 本主题三篇笔记共同聚焦 AI Agent 全链路可观测性问题：在入口、编排、模型、工具、状态、前端等多层异步协作的系统里，单看接口返回往往看不出问题，必须借助统一 Trace 还原"哪里先偏了"。可复用的工程骨架是以 OpenTelemetry 贯穿 trace_id / span，将 Prompt 路由、检索召回、工具调用参数、状态机推进、前端渲染态串成同一条时间线，再用 Ginkgo 固化后端轨迹断言、用 Python 做日志拼装与根因聚合、用 Playwright 验证用户可见态与后端事实一致、用 Kubernetes 保证脏样本可隔离复现。对 QA 的落地启发是：测试用例的断言对象应从"最终输出"前移到"关键 span 属性"，把每一次线上故障的 trace 沉淀为可回放的回归样本，让链路追踪而非事后看日志成为 AI 系统质量定位的默认入口。

- 源文件：[`wiki/topics/tracing.md`](topics/tracing.md)

---

## `LLM`  · 2 篇笔记  · 398 字

> 本主题下的两篇笔记聚焦于大模型从底层机理到工程可控性的链路问题：Day 01 梳理 LLM 的演进脉络与 Transformer、预训练-微调范式等基础概念，Day 04 则切入结构化输出约束，讨论 JSON Mode、Regex Constraint 与 Function Calling 等手段对输出可解析性的保障。跨笔记可复用的关键词包括 Token 级概率分布、温度与 top-p 采样、JSON Schema 校验、约束解码（Outlines、Guidance）以及与 Ginkgo/Pytest 结合的输出断言流水线。对 QA 工作的启发在于：一是将"输出可被机器解析"作为 LLM 接口的一等验收指标，使用 Schema 校验加正则双层断言替代字符串模糊匹配；二是为非确定性响应建立基于多次采样的稳定性回归用例，量化字段缺失率与格式漂移率，使大模型测试具备可观测、可回归的工程基线。

- 源文件：[`wiki/topics/LLM.md`](topics/LLM.md)

---

## `Locust`  · 2 篇笔记  · 361 字

> 本主题聚焦于 AI Agent 场景下的性能压测工程化与回归门禁建设，核心问题是如何将一次性的压测脚本沉淀为可复用、可纳入 CI 的质量资产，覆盖 LLM 推理、流式输出与 WebSocket 长连接等非传统 HTTP 形态的负载特征。跨笔记可复用的实践包括：以 Locust 承载有状态的会话级用户行为建模、以 k6 处理 WebSocket 与高并发短连接、以 Ginkgo 编写 BDD 风格的回归断言，并围绕 P95/P99、Token 吞吐、首字节延迟等指标设定基线阈值，通过资产化的场景库与门禁脚本实现版本间的横向对比。对 QA 工作的启发是：应将压测脚本与基线指标纳入版本仓库与流水线，像功能用例一样治理；同时为 Agent 场景单独建立流式与长连接的指标口径，避免沿用传统接口压测的均值思维而漏掉尾部劣化。

- 源文件：[`wiki/topics/Locust.md`](topics/Locust.md)

---

## `OpenTelemetry`  · 2 篇笔记  · 432 字

> 这两篇笔记共同聚焦于 AI Agent 系统的运行时可观测性与韧性保障：Day 23 从 OpenTelemetry Trace 切入，关注 LLM 调用链、Embedding 检索、工具调用等跨服务环节的 span 串联与延迟归因；Day 41 则把视角延伸到灾备演练，按控制面（编排、路由、模型网关）、数据面（Memory、向量库、缓存）、用户面（流式降级提示）三层组织故障注入与恢复验证。可复用的工程关键词包括 OTel SDK + Collector、TraceID 透传、span 属性打点（model、tokens、retrieval_topk）、FAISS/向量库只读降级、流式响应断点续传，以及结合 Ginkgo 或 Playwright 做端到端故障回放。对 QA 的启发是：一方面把 trace 字段约定纳入接口契约测试，让链路数据成为断言依据而非排查辅助；另一方面将灾备场景沉淀为定期跑的混沌用例集，覆盖切换 RTO 与降级 UI 双重验收。

- 源文件：[`wiki/topics/OpenTelemetry.md`](topics/OpenTelemetry.md)

---

## `SRE`  · 2 篇笔记  · 436 字

> SRE 主题下两篇笔记共同聚焦 AI Agent 在生产环境的质量守护问题：模型漂移、Prompt 注入、工具 API 退化、RAG 数据腐化、记忆污染、多 Agent 死锁等长尾故障无法被离线测试覆盖，必须依赖线上手段持续验证并通过事故反向沉淀回归资产。可复用的方法论包括合成探针（确定性断言＋语义相似度模糊断言）、金丝雀断言式活性检测、生产 Trace 采样脱敏后在影子环境回放、持续评估流水线，以及 Incident-Driven Testing 的 Detect-Classify-Reproduce-Codify-Prevent 闭环，配合 Model/Prompt/Tool/Memory/Orchestration/Infra 六类故障 Taxonomy 标准化复现模板。对 QA 的落地启发：一是将探针与金丝雀断言接入告警体系，把"测试用例"前移为线上守护资产；二是建立 48h 内事故转回归用例的硬性 SLA，并纳入 CI Gate，确保同类故障不二犯。

- 源文件：[`wiki/topics/SRE.md`](topics/SRE.md)

---

## `authorization`  · 2 篇笔记  · 376 字

> 本主题聚焦于 AI Agent 在代替用户执行工具调用与数据访问时的授权失真风险，核心问题是 Agent 容易以系统身份的最大权限运行，而非用户被允许的最小权限，由此衍生出越权调用、原始数据泄露、绕过审批门禁等高风险缺陷，并与 Prompt Injection 形成叠加攻击面。可复用的测试方法包括用户身份透传与作用域约束校验、最小权限裁剪、审批门禁与执行审计的 E2E 验证，以及策略契约测试；技术栈层面常组合使用 Ginkgo 做后端授权链路校验、Python/API 层做策略契约断言、Playwright 验证前端审批与告知流程、K8s 做工作负载身份隔离。落地建议是将"用户身份—作用域—审批—审计"四段式校验沉淀为 Agent 类需求的准入基线，并在 CI 中针对每个新增工具调用强制补齐越权用例与注入对抗用例，避免授权回归被功能迭代淹没。

- 源文件：[`wiki/topics/authorization.md`](topics/authorization.md)

---

## `chaos-engineering`  · 2 篇笔记  · 494 字

> 这两篇笔记共同聚焦 AI Agent 系统在生产环境下的可靠性保障问题——前者从事后视角切入，强调以 Incident-Driven Testing 将 P0/P1 事故沉淀为自动化回归用例；后者从事前视角切入，借助 ChaosMesh 主动注入故障验证 Agent 在模型退化、Prompt 漂移、工具链断裂、记忆污染、多 Agent 死锁等场景下的韧性。可复用的工程骨架包括：基于 Detect→Classify→Reproduce→Codify→Prevent 的闭环、Agent 故障 6 大类 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）、ChaosMesh 网络与 Pod 级故障注入、回归用例纳入 CI Gate，以及 FAISS 召回校验、Playwright 端到端复现等手段。对 QA 落地的启发是：一方面应建立 Postmortem 到测试代码的强制转化机制，明确 48h SLA 与 Taxonomy 标签；另一方面将混沌实验常态化嵌入预发流水线，把 Agent 韧性指标作为发布准入门槛而非可选项。

- 源文件：[`wiki/topics/chaos-engineering.md`](topics/chaos-engineering.md)

---

## `event-sourcing`  · 2 篇笔记  · 379 字

> 这两篇笔记共同关注一个核心问题：当 AI Agent 具备规划、工具调用、异步回调与跨系统写操作能力后，质量保障的关键已从"接口是否报错"转向"系统经历了什么、状态如何推进、用户视图与后台事实是否一致、线上事故能否被原样重放"，事件溯源与审计链路因此成为可验证、可追溯、可重放的事实基座。可复用的工程实践包括：用 Ginkgo 验证事件追加顺序、投影一致性与任务生命周期的最终状态，用 Python API Testing 校验审计查询、脱敏过滤与重放接口，用 Playwright 比对用户侧时间线与后端事件事实，用 Kubernetes 演练 consumer 重启、消息重复投递、日志落库延迟与投影重建。落地建议是把"可重放"作为回归测试的一等公民，沉淀历史事件流为回归用例库；并在验收标准中加入幂等性、租户隔离与审计完整性三项硬性校验，避免事后补证。

- 源文件：[`wiki/topics/event-sourcing.md`](topics/event-sourcing.md)

---

## `prompt-injection`  · 2 篇笔记  · 375 字

> 这两篇笔记共同聚焦于 AI Agent 时代的安全测试范式迁移，核心议题是如何在 Prompt Injection、工具越权调用、记忆污染、敏感信息外泄与跨租户数据串读等复合风险下，验证模型与 Agent 是否始终在被授权的能力边界内行动，而非仅评估输出正确性。可复用的工程实践包括：以输入防护、决策约束、执行鉴权、结果审计、红队评测构成五层护栏，并通过 Ginkgo 编排后端越权与 API 契约用例、Playwright 覆盖前端高风险交互、K8s 命名空间与 RBAC 做租户隔离、注入语料库做回归扫描，形成攻防闭环。对 QA 的启发是：应把红队 Prompt 与越权用例沉淀为持续运行的安全门禁，纳入 CI 强制卡点；同时在测试设计阶段前置威胁建模，按"能力边界—攻击路径—审计证据"三段式补齐用例，避免安全验证滞后于 Agent 能力扩张。

- 源文件：[`wiki/topics/prompt-injection.md`](topics/prompt-injection.md)

---

## `resilience`  · 2 篇笔记  · 366 字

> 这两篇笔记共同聚焦 AI Agent 在异常态下的可恢复性与降级可观察性：Day 41 自控制面、数据面、用户面三层切入灾备演练，关注编排服务、向量库与流式响应中断后的切换、重建与续传；Day 59 则把视角推向外部依赖，验证模型网关、检索、Webhook 等在超时、429、5xx 下的降级路径、幂等性与用户侧的诚实暴露。可复用的工程方法包括用 Ginkgo 断言后端编排的降级与幂等行为、用 Python/API Testing 做契约探测与熔断状态校验、用 Playwright 校验降级页面的提示与按钮可见性、用 Kubernetes 注入故障并周期性演练恢复，配合 FAISS 等向量存储的只读与重建预案。对 QA 的启发是：把"依赖故障演练"纳入常态化回归，并为每条降级路径定义可断言的用户可见契约，而非仅验证系统报错。

- 源文件：[`wiki/topics/resilience.md`](topics/resilience.md)

---

## `synthetic-monitoring`  · 2 篇笔记  · 407 字

> 这两篇笔记共同聚焦 AI Agent 在生产环境下的质量守护问题：模型漂移、Prompt 注入、工具 API 退化、RAG 数据腐化、拒答策略偏移与异步链路丢失等长尾故障，往往无法被离线评测覆盖，必须在真实流量入口侧持续探测。可复用的方法论包括以合成探针覆盖黄金路径、对每条 Query 同时设置确定性断言（工具调用序列、结构化字段）与模糊断言（语义相似度阈值）、金丝雀断言做活性检测、生产 Trace 采样后在影子环境回放，并配套 Ginkgo 校验工具轨迹、Playwright 验证前端可见状态、Python/API Testing 做探针编排与指标聚合、Kubernetes CronJob 负责周期化与环境隔离。对 QA 的落地建议是：先把 Synthetic Monitoring 沉淀为发布门禁与故障归因的一等输入，而非孤立看板；同时为每条探针明确 owner、脱敏策略与告警阈值，避免演化成噪声源。

- 源文件：[`wiki/topics/synthetic-monitoring.md`](topics/synthetic-monitoring.md)

---

## `测试开发`  · 2 篇笔记  · 362 字

> 本主题下两篇笔记共同聚焦于 AI Agent 体系中"可编排能力"与"协作可靠性"的测试问题：Day 14 关注 Skill 的开发与编排机制，本质是单 Agent 内部工具调用链的契约与稳定性；Day 20 则将视角扩展至多 Agent 协作场景下的状态一致性、消息路由与失败回滚验证。可复用的工程实践包括：以结构化输出（JSON Schema）作为 Skill 边界契约、用 Ginkgo 等 BDD 框架编写编排路径的断言用例、借助 FAISS 等向量检索做语义级回归比对，以及通过 Playwright 串接端到端的多角色交互。对 QA 的启发在于：应尽早把 Skill 注册表与 Agent 拓扑纳入测试资产管理，并为多 Agent 链路建立可观测的 trace 基线，避免把 LLM 不确定性与编排缺陷混为一谈。

- 源文件：[`wiki/topics/测试开发.md`](topics/测试开发.md)

---

## `Automation`  · 1 篇笔记  · 391 字

> 本主题围绕 AI Agent 上线后的可度量质量治理展开，核心问题是如何把模糊的"模型表现好不好"翻译成可追踪、可回归、可阻断发布的工程指标，即 SLO 设计、发布评分卡与自动化门禁的闭环。可复用的关键实践包括：以任务成功率、工具调用准确率、首响延迟 P95、单次会话成本等组成多维 SLO，结合金标集（golden set）回放与 LLM-as-Judge 双轨评估，落到 CI 中的发布评分卡，并通过 Ginkgo 编排行为级用例、Playwright 驱动端到端 Agent 操作、FAISS 维护检索基线、Prometheus + Grafana 跟踪线上 SLI 漂移。对 QA 的启示是：应尽早把评分卡纳入发布流水线，设定红线指标自动拦截劣化版本；同时建立golden set 与线上 badcase 的双向回流机制，让评测集随真实流量演进，避免离线分数虚高而线上回归。

- 源文件：[`wiki/topics/Automation.md`](topics/Automation.md)

---

## `CI-CD`  · 1 篇笔记  · 390 字

> 本主题聚焦于 AI Agent 在 CI/CD 流水线中的端到端测试编排难题，核心矛盾在于如何用确定性的工程框架去约束非确定性的模型行为、长链路依赖与不稳定的推理延迟。可复用的工程范式包括：Setup-Execute-Verify 三阶段编排模型、基于 YAML/Go Struct 的 ScenarioSpec 场景 DSL、语义+结构+副作用的三维断言体系，以及 Smoke/Core/Full/Chaos 四层流水线分级（分别绑定 PR Gate、Merge Gate、Nightly、Weekly），配合 K8s Namespace 实现并行隔离与 Label 选择器驱动用例子集。对 QA 落地的启发是：一方面应将测试场景声明化、数据驱动化，沉淀为可参数复用的资产而非一次性脚本；另一方面要按执行时长与稳定性给用例分层挂载到不同 Gate，避免长尾用例阻塞主干合入节奏。

- 源文件：[`wiki/topics/CI-CD.md`](topics/CI-CD.md)

---

## `E2E-testing`  · 1 篇笔记  · 386 字

> 本主题聚焦于 AI Agent 场景下端到端测试的核心矛盾：如何在非确定性输出、长链路依赖（模型→编排→工具→存储）与推理延迟波动的约束下，构建稳定可回归的 E2E 流水线。可复用的工程实践包括 Setup-Execute-Verify 三阶段编排模型、基于 YAML/Go Struct 的 ScenarioSpec 声明式场景 DSL、语义+结构+副作用的三维断言体系，以及 Smoke/Core/Full/Chaos 四层分级与 Label 选择器驱动的 CI/CD 集成；技术栈上可结合 Ginkgo 组织用例、K8s Namespace 实现并行隔离、FAISS 或 Mock 工具链支撑依赖注入。对 QA 落地的建议是：优先沉淀场景 DSL 与断言库而非堆砌脚本，并按 PR/Merge/Nightly 节奏匹配测试深度与超时熔断，避免长链路用例阻塞主干交付。

- 源文件：[`wiki/topics/E2E-testing.md`](topics/E2E-testing.md)

---

## `EvalOps`  · 1 篇笔记  · 357 字

> EvalOps 主题聚焦于 AI Agent 质量保障的核心痛点：如何把线上真实失败、用户反馈、人工纠正与轨迹日志，系统性回灌为可复跑、可归因、可阻断发布的评测资产，而非停留在一次性离线评分。可复用的工程实践包括以闭环视角串联「线上问题→标准样本→自动评测→回归门禁→发布决策→再观测」，技术栈上以 Ginkgo 守住 P0 回归与工具调用正确性，Python/API Testing 承担样本治理与指标聚合，Playwright 覆盖用户视角体验，Kubernetes CronJob/Job 驱动周期化回归与线上回灌。对 QA 的落地启发是：把事故复盘的产出物强制规范化为评测样本并纳入发布门禁，建立分级阻断机制，确保同类线上问题不会以相同形态二次发生，让样本治理而非分数本身成为 EvalOps 的核心资产。

- 源文件：[`wiki/topics/EvalOps.md`](topics/EvalOps.md)

---

## `GitHub-Actions`  · 1 篇笔记  · 407 字

> 本主题聚焦 AI Agent 端到端测试在 GitHub Actions 流水线中的工程化落地，核心问题在于如何应对 LLM 输出非确定性、模型→编排→工具→存储的长链路依赖以及推理延迟波动，使 E2E 测试在 CI 中保持稳定可控。可复用的关键实践包括：Setup-Execute-Verify 三阶段编排模型并配套超时熔断与失败隔离、基于 YAML/Go Struct 的 ScenarioSpec DSL 实现声明式场景与数据驱动、语义+结构+副作用的三维断言、按 Smoke/Core/Full/Chaos 分层并通过 Label 选择器绑定 PR Gate 与 Nightly，以及借助 K8s Namespace 做并行化资源隔离。对 QA 工作的启发是：应优先将测试场景 DSL 化以沉淀为资产而非一次性脚本，并在 GitHub Actions 中按时长预算严格分层，避免 PR 卡点被长尾用例拖垮。

- 源文件：[`wiki/topics/GitHub-Actions.md`](topics/GitHub-Actions.md)

---

## `MultiAgent`  · 1 篇笔记  · 366 字

> 该主题聚焦于多 Agent 协作系统的可测性与质量评估，核心问题是如何在角色分工、消息传递与共享上下文的复杂拓扑下，验证协作链路的正确性、稳定性与性能边界，并将单 Agent 时代的测试经验迁移到群体智能场景。跨笔记可复用的实践包括：以 Ginkgo 组织行为驱动用例覆盖 Planner-Worker-Critic 等协作模式，结合 Playwright 驱动端到端交互回放，借助 FAISS 对共享记忆与检索结果做语义断言，并通过性能基线、负载压测与可观测性指标（trace、token、延迟）形成闭环。对 QA 工作的启发是：一方面应建立 Agent 间通信契约与消息 schema 校验，将“协作失败”从模糊的输出问题前移为可定位的链路问题；另一方面建议沉淀一套可回放的多 Agent 场景集，作为回归与性能基线的统一入口。

- 源文件：[`wiki/topics/MultiAgent.md`](topics/MultiAgent.md)

---

## `Skill`  · 1 篇笔记  · 370 字

> 本主题聚焦于 Skill 作为 Agent 可调用能力单元的开发范式与编排机制，核心问题在于如何将松散的 Prompt 与工具调用沉淀为可注册、可版本化、可被多 Agent 复用的标准化技能，并解决技能选择、参数填充与执行链路的可观测性问题。可复用的工程实践包括：以 JSON Schema 约束 Skill 入参与结构化输出、通过 Manifest 注册与语义检索（FAISS 等向量索引）完成技能路由、用 Ginkgo 等 BDD 框架对单技能与编排链路做契约测试，以及借助 Playwright 模拟前端触发端到端验证。对 QA 工作的启发是：应将每个 Skill 视为独立被测单元，建立"单技能契约测试 + 编排回归测试"双层用例库，并在 CI 中接入 Schema 校验与调用轨迹断言，避免 Agent 升级后出现静默的技能漂移。

- 源文件：[`wiki/topics/Skill.md`](topics/Skill.md)

---

## `StateMachine`  · 1 篇笔记  · 396 字

> 该主题聚焦于 AI Agent 在多步推理与工具调用过程中的状态一致性问题，核心关注如何用状态机建模刻画 Agent 的合法状态空间、转移条件与终止性，并验证其在长链路、异常分支与重试场景下是否仍满足关键不变量（如上下文单调性、工具调用幂等、token 预算守恒）与收敛性（步数上界、目标可达）。可复用的工程实践包括：用有限状态机或行为树对 Agent 流程显式建模，配合 Ginkgo 的 DescribeTable 做转移矩阵覆盖，引入基于属性的随机测试（property-based testing）与 fuzz 注入触发非预期转移，结合 FAISS 等向量召回构造对抗性上下文，并对终止条件做超时与发散检测。建议 QA 将状态机不变量沉淀为可执行断言库，纳入回归基线；同时为每个 Agent 配置"最大步数 + 循环检测 + 状态快照 diff"三件套，便于线上异常的快速复现与定位。

- 源文件：[`wiki/topics/StateMachine.md`](topics/StateMachine.md)

---

## `ab-testing`  · 1 篇笔记  · 364 字

> 该主题聚焦 AI Agent 线上实验的质量保障问题，核心矛盾在于一次 A/B 实验往往不仅改变文案表现，还会牵动工具调用路径、拒绝边界、任务副作用、时延与 Token 成本，传统"比均值"的实验范式无法覆盖安全红线与生产稳定性。可复用的工程实践包括：基于用户 ID 的一致性分流保障体验稳定，Ginkgo 验证实验路由与风控隔离，Python/API Testing 监控指标分布与异常，Playwright 回归端到端用户链路，Kubernetes 灰度发布配合 Kill Switch 实现分钟级止损，并同时观测效果指标与护栏指标。对 QA 的启发是：把线上实验当作一套可追踪、可回滚、可审计的质量系统来设计，护栏指标（拒绝率、工具误调用、副作用）必须与业务指标同权重纳入实验准出，任何一项越线即自动熔断，而非等人工复盘。

- 源文件：[`wiki/topics/ab-testing.md`](topics/ab-testing.md)

---

## `approval`  · 1 篇笔记  · 355 字

> 本主题聚焦于 AI Agent 从“建议者”跃迁为“执行者”后，如何通过 Human-in-the-Loop 机制确保高风险动作真正交还给人决策，而非停留在表层的“确认按钮”。可复用的工程实践是将审批链路拆解为风险识别、审批挂起、证据快照、审批人校验、人工接管、结果回传、任务续跑与审计留痕八个可验证环节，并采用 Ginkgo 覆盖后端审批 E2E、Python/API 验证审批契约与过期幂等、Playwright 还原用户接管体验、K8s 演练审批服务高可用与故障恢复的组合栈，重点校验过期审批、错人审批、重复审批与上下文漂移四类典型缺陷。对 QA 的落地启发是：审批对象必须结构化暴露审批人、证据、待执行动作、超时与幂等键，并把“决策权是否真正回到人手里”作为用例设计的第一判据，而非仅验证流程是否跑通。

- 源文件：[`wiki/topics/approval.md`](topics/approval.md)

---

## `async-callback`  · 1 篇笔记  · 366 字

> 本主题聚焦 AI Agent 从同步问答迈向异步执行后暴露的可靠性短板：事件已达但状态未收敛、回调重放引发副作用重复、前端进度与后端真实状态脱节、乱序回调导致终态被错误覆盖，本质是缺乏幂等、顺序约束与端到端可观测性。可复用的工程实践包括：用 Ginkgo 编写事件链路用例验证幂等与唯一终态，用 Python 的 API Testing 覆盖 webhook 签名校验、重试、乱序与去重策略，用 Playwright 校验用户可见进度与真实事件的一致性，用 Kubernetes 演练 consumer 重启、队列堆积与回调重投，并辅以状态机约束兜底。对 QA 的启发是：异步场景的测试设计应以 E2E 事件链路而非单接口为最小单元，把幂等键、终态唯一性和回调乱序作为强制用例纳入回归基线，避免把异步可靠性问题留到生产事故复盘阶段。

- 源文件：[`wiki/topics/async-callback.md`](topics/async-callback.md)

---

## `async-workflow`  · 1 篇笔记  · 352 字

> 本主题聚焦于 AI Agent 在分钟级乃至小时级长任务场景下的可靠性验证，核心问题不是 Agent 能否最终给出正确结果，而是其在异步执行链路中状态是否可追踪、断点是否可恢复、重试是否幂等、超时与取消是否可控。可复用的工程实践包括：将长任务显式拆解为任务创建、计划冻结、异步执行、进度回传、失败重试、人工确认、断点恢复、结果归档八个可验证环节，并组合使用 Ginkgo 做后端任务编排 E2E、Python/API 做回调契约与幂等校验、Playwright 做进度可观测性验证、K8s 做 Worker 漂移与重启恢复演练。对 QA 的启发是：测试用例设计应以任务状态机为骨架，覆盖每个状态迁移与异常分支；同时把"杀 Worker、断网、重放回调"作为长任务回归的常规演练项，而非故障注入的临时动作。

- 源文件：[`wiki/topics/async-workflow.md`](topics/async-workflow.md)

---

## `audit-log`  · 1 篇笔记  · 377 字

> 本主题聚焦于 AI Agent 在企业级生产环境下的可追溯性与可重放性问题：当一次 Agent 执行涉及规划、工具调用、权限审批与多轮状态变更时，如何通过事件溯源与审计日志，把结果还原成可验证的事实流，而非仅停留在"跑通"层面。可复用的工程实践包括以事件追加（append-only）为核心的存储模型、状态投影与重放一致性校验、审计查询的脱敏与完整性断言，以及围绕 consumer 重启、事件重复投递、投影重建等故障注入演练；测试栈上呈现出 Ginkgo 验证事件与投影、Python 做 API 层审计与脱敏校验、Playwright 校验用户侧时间线、Kubernetes 演练落库延迟的分层组合。对 QA 的启发是：把"同一批事件能否重放出同一结果"纳入回归基线，并在用例设计阶段就要求每条关键路径产出可被审计查询命中的事件字段，避免事后补埋点。

- 源文件：[`wiki/topics/audit-log.md`](topics/audit-log.md)

---

## `backward-compatibility`  · 1 篇笔记  · 338 字

> 本主题聚焦于 AI Agent 在版本迭代过程中如何保障接口与数据契约的向后兼容，核心问题是当 Prompt、Schema 或工具调用签名发生演进时，下游消费者与历史回放数据不应被破坏。可复用的工程实践包括基于 JSON Schema / Pydantic 的契约校验、使用 Ginkgo 或 Pact 编写消费者驱动的契约测试、对 structured output 字段做新增可选而非删除重命名的演进策略，以及借助快照测试与回放语料库验证旧版本输入在新版 Agent 下的稳定性。对 QA 工作的启发是：应在 CI 中固化 Schema diff 检查，对破坏性变更强制阻断合并，并维护一份带版本标签的黄金用例集，确保模型升级或 Prompt 重构时能快速定位兼容性回归。

- 源文件：[`wiki/topics/backward-compatibility.md`](topics/backward-compatibility.md)

---

## `baseline`  · 1 篇笔记  · 379 字

> 该主题聚焦于 AI Agent 在真实负载下的性能与稳定性基线建设，核心问题是如何为非确定性的 LLM 应用沉淀一套可量化、可回归比对的指标体系，包括端到端时延、Token 吞吐、工具调用成功率以及多轮会话下的资源占用与失败模式。可复用的工程实践包括：使用 Locust 或自研压测脚本驱动并发会话、以 Ginkgo 组织分层用例并通过表驱动方式覆盖冷启动与稳态、借助 Prometheus + Grafana 采集 P50/P95/P99 时延与显存曲线、对检索链路用 FAISS 做向量召回基准、并将每次基线结果归档为可 diff 的 JSON 快照。对 QA 工作的启发是：应在 CI 中固化"性能基线门禁"，对关键指标设置回归阈值并阻断劣化合入；同时建议将稳定性测试与 Prompt 版本、模型版本绑定打标，便于后续在出现质量回退时快速定位变更源头。

- 源文件：[`wiki/topics/baseline.md`](topics/baseline.md)

---

## `canary-assertion`  · 1 篇笔记  · 385 字

> 该主题聚焦于 AI Agent 在生产环境下的持续质量守护问题，核心矛盾在于离线测试无法覆盖模型漂移、Prompt 注入、工具 API 退化与 RAG 数据腐化等长尾故障，必须依赖线上态的主动探测机制来兜底。可复用的工程实践包括：以合成探针覆盖黄金路径并组合确定性断言（Tool 调用序列、结构化字段校验）与模糊断言（基于 FAISS 或 sentence-transformers 的语义相似度阈值）、在稳定版本上以 Cron 触发金丝雀断言做活性检测、通过 OpenTelemetry 采样生产 Trace 后在影子环境回放、以及搭建持续评估 Pipeline 形成递进防线。对 QA 落地的启发是：应明确区分金丝雀断言与金丝雀发布，将前者建设为独立于灰度流程的线上回归资产；同时把探针用例与离线评测集双向同步，让生产暴露的 Bad Case 反哺回归库，形成闭环。

- 源文件：[`wiki/topics/canary-assertion.md`](topics/canary-assertion.md)

---

## `canary`  · 1 篇笔记  · 357 字

> 该主题聚焦 AI Agent 在生产环境中如何低风险上线，核心问题是如何在不影响真实用户的前提下验证新模型或新 Prompt 链路的稳定性与效果回归。跨笔记可复用的实践包括：基于流量染色的灰度切分（按用户 ID 哈希或 Header 路由）、影子流量双跑与响应 Diff 比对、关键指标（延迟、Token 消耗、工具调用成功率、答案相似度）的实时埋点，常用技术栈涉及 Istio/Envoy 做流量镜像、FAISS 或 BERTScore 做语义相似度比对、Ginkgo 编写回归用例、Prometheus + Grafana 监控漂移。对 QA 工作的启发是：应将影子流量回放纳入发布门禁，在预发环境建立离线 Diff 报告基线，并为 Agent 输出定义可量化的语义等价阈值，避免仅依赖人工抽检导致的回归遗漏。

- 源文件：[`wiki/topics/canary.md`](topics/canary.md)

---

## `cancellation`  · 1 篇笔记  · 390 字

> 该主题聚焦 AI Agent 长任务在超时、取消与恢复三个环节的质量盲区：后端已超时但第三方副作用仍在执行、用户取消后任务偷跑完成、Pod 重启后任务重复或丢失续跑点，本质是缺乏统一的超时预算、取消传播链路与 checkpoint 语义。可复用的工程实践包括用 Ginkgo 验证超时预算在模型推理、工具调用、异步轮询各阶段的拆分与取消信号透传，用 Python/API Testing 覆盖任务状态机迁移、取消幂等与 checkpoint 元数据一致性，用 Playwright 校验"运行中/取消中/已取消/恢复中"对用户的真实可见性，再用 Kubernetes 演练 Pod 中断与 Job 续跑。对 QA 的启发是：长任务测试要从单接口超时断言升级为端到端的"停-断-续"三态验证，并在用例库中固化一组取消与重启的混沌场景，确保系统在异常时刻仍能给出唯一、可追踪的最终态。

- 源文件：[`wiki/topics/cancellation.md`](topics/cancellation.md)

---

## `chaos`  · 1 篇笔记  · 361 字

> 本主题聚焦 AI Agent 在真实生产环境中的韧性问题，核心矛盾是 LLM 调用链路长、依赖外部模型与向量检索服务，一旦出现网络抖动、节点宕机或下游限流，Agent 容易陷入幻觉重试或静默失败，传统功能测试难以覆盖。可复用的工程实践包括：以 Chaos Mesh 注入 Pod Kill、网络延迟与 DNS 故障，结合 Ginkgo 编写 E2E 场景化用例，对 LLM Gateway、FAISS 向量库与 Agent 调度器进行分层故障演练，并通过 SLO（成功率、P99 时延、降级路径命中率）作为稳态假设的判定指标。对 QA 工作的启发是：应把混沌实验左移至 CI 流水线，针对每个新增 Tool 调用补充对应的故障矩阵；同时建立降级回归基线，确保模型超时或检索失败时 Agent 能稳定走兜底回答而非随机生成。

- 源文件：[`wiki/topics/chaos.md`](topics/chaos.md)

---

## `chaosmesh`  · 1 篇笔记  · 381 字

> 本主题聚焦于 AI Agent 系统在生产环境下的稳定性验证问题，核心是如何通过混沌工程手段主动暴露 LLM 调用链路、向量检索与外部工具依赖中的脆弱点，而非依赖事后故障复盘。可复用的工程实践包括：使用 ChaosMesh 在 Kubernetes 层注入 Pod Kill、网络延迟、DNS 故障与带宽限制，针对 LLM Gateway、FAISS/向量库、Redis 会话存储等关键依赖编排稳态假设与爆炸半径控制，并结合 Ginkgo 或 pytest 编写故障场景下的回归用例，配合 Prometheus 指标作为自动化判稳信号。对 QA 工作的落地建议有两点：一是将故障注入纳入 Agent 上线前的准入流水线，把超时降级、重试幂等与上下文回滚作为强制验收项；二是为每条 Agent 链路预先定义 SLO 与稳态指标，避免混沌实验沦为无判据的"演练秀"。

- 源文件：[`wiki/topics/chaosmesh.md`](topics/chaosmesh.md)

---

## `checkpoint-recovery`  · 1 篇笔记  · 417 字

> 该主题聚焦 AI Agent 长任务在超时、取消与崩溃恢复三类边界场景下的一致性问题，核心矛盾在于模型推理、工具调用、异步轮询与审批回调等多阶段链路缺乏统一的超时预算与取消传播路径，导致后端超时后第三方副作用仍在继续、用户取消却被偷偷跑完、Pod 重启后任务重复执行等"状态错位"故障；可复用的工程实践包括以 Ginkgo 验证超时预算的逐层拆分与 context 取消透传，用 Python/API Testing 覆盖任务状态机迁移、取消幂等与 checkpoint 元数据正确性，借 Playwright 校验"运行中/取消中/已取消/恢复中"在前端的真实可见性，并通过 Kubernetes 演练 Pod 重启与 Job 中断下的续跑链路。建议 QA 将"超时—取消—恢复"作为长任务的标配测试三元组纳入用例模板，并在混沌演练中强制注入 Pod kill 与回调延迟，确保每条任务在该停、该断、该恢复时都有唯一且可追踪的终态。

- 源文件：[`wiki/topics/checkpoint-recovery.md`](topics/checkpoint-recovery.md)

---

## `compensation`  · 1 篇笔记  · 340 字

> 该主题聚焦于 AI Agent 从“回答型”升级为“执行型”后所暴露的跨系统事务一致性风险，核心问题不再是单步失败，而是动作做了一半导致的状态漂移、回调重放与用户误导。可复用的工程实践包括：以 Ginkgo 驱动 Saga 编排与补偿顺序的契约验证，借助 Python/API Testing 覆盖状态机流转与幂等键去重，使用 Playwright 校验前端在“处理中/补偿中/已恢复”各阶段的诚实展示，并通过 Kubernetes 主动演练异步 worker 崩溃与重启路径。对 QA 而言，落地建议有二：一是将“可恢复边界、可追踪状态、唯一收敛结果”纳入 Agent 类需求的准入检查清单；二是建设常态化的故障注入与补偿回放用例集，把最终一致性从口头约定变为可回归的质量资产。

- 源文件：[`wiki/topics/compensation.md`](topics/compensation.md)

---

## `compliance`  · 1 篇笔记  · 342 字

> 该主题聚焦 AI Agent 接入企业数据资产后引发的合规与治理问题，核心矛盾不再是回答正确性，而是数据读取的合法性、敏感字段脱敏、关键动作可审计、留存与删除策略落地，以及多租户边界的真实隔离。可复用的工程实践包括：将合规规则声明化以驱动契约测试、用 Ginkgo 编排后端 E2E 数据链路校验、以 Python/API 层验证脱敏与审计事件结构、用 Playwright 覆盖前端权限提示与用户告知、并借助 K8s 命名空间与网络策略验证基础设施级隔离，形成"边界识别—流转追踪—门禁固化"的闭环。对 QA 的启发是：把审计日志与数据保留策略纳入回归用例库，让合规校验像功能用例一样可执行、可回放；同时建议在 CI 中引入跨租户越权探测与 PII 泄漏扫描，作为发布前的强制门禁。

- 源文件：[`wiki/topics/compliance.md`](topics/compliance.md)

---

## `config-drift`  · 1 篇笔记  · 391 字

> 本主题聚焦 AI Agent 在生产环境中因 Prompt 模板热更新、工具 schema 变更、特征开关分租户不一致、ConfigMap/Secret 滚动不完整、灰度包与后端版本错位等导致的配置漂移与环境一致性缺口，揭示了大量"模型变笨"类事故的真正根因并非代码逻辑而是配置面失控。可复用的工程实践包括：以 Ginkgo 对后端关键配置快照与能力矩阵做契约式断言、用 Python 与 API Testing 做配置 diff 与基线比对、借 Playwright 在多配置下回归用户可见行为、以 Kubernetes 声明式固化环境并通过定时任务巡检漂移。对 QA 的启发是：质量门禁需从"接口成功率"扩展到配置、依赖、特征开关与模型路由的可观测可断言范围，并在 CI 中引入"线上配置快照 vs 验证基线"的强制比对，确保任何一次发布都能明确回答当前线上究竟跑着哪一套配置。

- 源文件：[`wiki/topics/config-drift.md`](topics/config-drift.md)

---

## `contract-testing`  · 1 篇笔记  · 380 字

> 该主题聚焦于 AI Agent 在多版本迭代与多服务协作场景下的接口稳定性问题，核心矛盾在于 LLM 输出的非确定性与上下游对结构化数据的强约束之间如何达成可验证的契约。可复用的工程实践包括：以 JSON Schema / Pydantic 模型固化 Agent 的输入输出契约，借助 Pact 或自研 schema diff 工具进行消费者驱动的契约校验，结合 Ginkgo、pytest 编写版本兼容性回归用例，并在 CI 中引入 schema 演进检查（新增字段向后兼容、删除字段需走 deprecation 流程）以及基于快照的语义回归。对 QA 工作的启发是：应将 Agent 视为一个具备版本号的 API 而非黑盒模型，把 schema 变更纳入发布门禁，并为 prompt、模型、工具链分别维护独立的契约测试套件，避免一次升级引发跨链路静默失败。

- 源文件：[`wiki/topics/contract-testing.md`](topics/contract-testing.md)

---

## `data-governance`  · 1 篇笔记  · 344 字

> 本主题聚焦于 AI Agent 接入企业数据资产后衍生的数据治理与合规审计问题，关注点已从"答案正确性"前移到数据读取合法性、敏感字段脱敏、关键动作可审计、留存与删除合规、以及多租户边界的真实隔离等数据流全链路质量。可复用的工程实践包括：以声明化方式描述合规规则、以结构化事件落地审计日志、以可追踪方式刻画数据流转路径，并通过 Ginkgo 做后端 E2E 数据链路校验、Python/API 层承接合规契约测试、Playwright 验证前端权限与用户告知、K8s 层兜底基础设施隔离，形成纵深防御式的治理测试组合。对 QA 工作的启发是：应把"先识别数据边界、再验证流转路径"内化为用例设计范式，并将审计事件完整性与脱敏/删除可验证性沉淀为发布流水线中的持续门禁，而非一次性安全评审。

- 源文件：[`wiki/topics/data-governance.md`](topics/data-governance.md)

---

## `data-leakage`  · 1 篇笔记  · 378 字

> 本主题聚焦大模型应用中数据泄露风险的识别与防控，核心问题是如何在 Prompt 注入、越权访问与上下文回流等场景下，验证模型与检索链路是否会外泄系统提示词、用户隐私或向量库中的敏感片段。可复用的测试方法包括：构造对抗性 Prompt 用例集（含越狱、角色扮演、间接注入）跑回归，结合 Playwright 端到端模拟用户多轮诱导，使用 Ginkgo 组织分层断言，并在 RAG 链路上对 FAISS / Milvus 召回结果做敏感字段命中校验与 PII 正则扫描，同时引入 LLM-as-Judge 对响应内容做泄露评分。对 QA 工作的启发是：一方面应将数据泄露用例沉淀为独立的安全测试套件并纳入每次模型或 Prompt 变更的准入流水线，另一方面建议在测试环境预埋 Canary 敏感数据，通过日志与响应双向监控量化泄露率，形成可追踪的安全质量指标。

- 源文件：[`wiki/topics/data-leakage.md`](topics/data-leakage.md)

---

## `dataset`  · 1 篇笔记  · 405 字

> 该主题聚焦于 AI Agent 评测样本集的工程化建设，核心问题是如何把零散的 Prompt 用例、工具调用轨迹与回归数据沉淀为可版本化、可复跑、可度量的 dataset，从而支撑 Agent 在多轮决策、结构化输出与稳定性维度上的持续评测。可复用的工程实践包括按场景分层（基础问答、ReAct/ToT 推理、结构化抽取、检索召回）切分样本，使用 JSONL/Parquet 固化输入与期望输出、配合 FAISS 做语义去重与相似召回、通过 Ginkgo 或 pytest 驱动断言式回归、并以 Playwright 覆盖端到端 UI Agent 链路，同时引入 LLM-as-Judge 与人工标注双轨打分。对 QA 的启发是：将评测样本集当作一等公民代码资产管理，建立 schema 校验与 CI 回归门禁；并在每次 Prompt 或模型升级时跑差分对比，量化 Pass@k 与稳定性漂移，避免凭感觉调优。

- 源文件：[`wiki/topics/dataset.md`](topics/dataset.md)

---

## `debugging`  · 1 篇笔记  · 361 字

> 本主题聚焦 AI Agent 全链路故障定位的核心痛点：错误往往不在接口层显性抛出，而是在 Prompt 路由、检索召回、工具调用、状态机推进、前端渲染或异步回调等中间环节悄然偏离，最终答案看似可用却已失真。可复用的工程范式是以统一 TraceID 串联入口层、编排层、模型层、工具层、状态层与前端层，配合 Ginkgo 固化后端轨迹断言、Python/API Testing 做日志拼装与根因聚合、Playwright 校验用户可见态与后台事实的一致性、Kubernetes 保障问题样本的隔离复现。对 QA 的启发是：调试能力应从"事后查日志"升级为"分层断点+可回放+可归因"的资产沉淀，建议为每个线上 Badcase 强制产出一条带 Trace 快照的回归用例，并把根因层级标签纳入缺陷字段，避免同类偏移反复发生。

- 源文件：[`wiki/topics/debugging.md`](topics/debugging.md)

---

## `decision-making`  · 1 篇笔记  · 395 字

> 本主题聚焦于 AI Agent 自主决策与规划场景下的测试范式转变：测试关注点从"答案是否正确"迁移到"决策过程是否可解释、可收敛、可止损"，强调对目标理解、约束继承、工具选择、计划生成、执行反馈、动态重规划与止损策略这七个环节的可验证性建模，尤其关注工具失败、权限不足、信息缺失、部分成功、长链路超时等动态分支下的鲁棒性。可复用的工程实践包括：以 Ginkgo 编排后端决策链路的 E2E 用例，以 Python/API 层做计划契约校验与故障注入，借助 Playwright 验证计划在用户侧的透明度与可解释性，并通过 K8s 多副本与发布门禁演练越权拦截与副作用控制。对 QA 的落地启示是：应建立"决策路径断言库"，将计划结构、工具调用序列与止损触发点沉淀为可回归资产；同时在 CI 中常态化注入工具异常与权限边界用例，把"边界内稳定做决定"作为 Agent 类系统的核心准入指标。

- 源文件：[`wiki/topics/decision-making.md`](topics/decision-making.md)

---

## `degradation`  · 1 篇笔记  · 354 字

> 本主题聚焦 AI Agent 在外部依赖（模型网关、向量检索、工作流引擎、对象存储、Webhook 等）发生超时、限流、5xx 或半失败时，系统能否被验证为"识别故障—按层降级—抑制副作用扩散—向用户诚实暴露能力边界"的闭环，而非停留在"依赖挂了就报错"。可复用的工程实践包括：用 Ginkgo 在后端编排层断言超时/429/5xx 下的降级路径与幂等性，用 Python 做依赖契约探测和熔断状态校验，用 Playwright 验证降级模式下的页面提示、按钮可见性与结果一致性，并借助 Kubernetes 做故障注入与恢复演练。对 QA 的启发是：应将"降级矩阵"作为一类独立测试资产沉淀，明确每层依赖故障对应的可见行为与禁用能力；同时把第三方故障演练纳入常态化回归，而不是只在大促或事故复盘时临时执行。

- 源文件：[`wiki/topics/degradation.md`](topics/degradation.md)

---

## `dependency-failure`  · 1 篇笔记  · 362 字

> 该主题聚焦 AI Agent 在外部依赖（模型网关、向量检索、工作流引擎、审批、对象存储、Webhook、搜索等）出现超时、限流、5xx 或半失败时，系统能否被验证为「识别故障—按层降级—抑制副作用—向用户诚实暴露能力边界」，而非仅停留在“依赖挂了就报错”的浅层断言。跨笔记可复用的工程实践包括：以 Ginkgo 编写后端编排在 429/超时/5xx 下的降级路径与幂等性断言，用 Python 做依赖契约探测与熔断状态校验，用 Playwright 验证降级模式下的提示文案、按钮可见性与结果一致性，并借助 Kubernetes 进行故障注入与定时恢复演练。对 QA 的落地启发是：将「降级矩阵」沉淀为可回归用例集，明确每一层依赖失效时的预期能力裁剪与用户提示；同时把第三方故障演练纳入常态化流水线，而非上线前一次性压测。

- 源文件：[`wiki/topics/dependency-failure.md`](topics/dependency-failure.md)

---

## `dependency-injection`  · 1 篇笔记  · 419 字

> 本主题聚焦于一个被长期低估的工程命题：AI Agent 的可测试性本质上是架构属性，而依赖注入则是支撑 Mock、Stub、Fake 等隔离手段得以成立的前置条件，没有 DI 就没有真正可控的单元测试与集成测试。可复用的关键实践包括：通过接口抽象 LLM Client、Tool Executor、Memory Store 与 Orchestrator 等核心依赖，在调用链中插入 Recording/Replay Middleware 实现 Trace 录制与确定性回放，将 LLM 的非确定性输出转化为可断言的固定向量，并围绕可观测性、可控制性、可隔离性、故障可注入性建立 Design Review 检查项。对 QA 工作的落地建议有二：一是将"是否通过构造函数或容器注入外部依赖"作为 Agent 代码合入的硬性门禁；二是搭建线上 Trace 采样回放流水线，让回归测试直接消费真实流量样本，替代脆弱的 Prompt 字符串断言。

- 源文件：[`wiki/topics/dependency-injection.md`](topics/dependency-injection.md)

---

## `design-for-test`  · 1 篇笔记  · 392 字

> 该主题聚焦于一个被长期忽视的工程命题：AI Agent 的可测试性本质上是架构属性而非测试技巧，不可测试的系统根源在于设计而非用例覆盖不足。笔记沿着六大原则——可观测性、可控制性、可隔离性、确定性回放、契约显式化、故障可注入性——展开，强调以依赖注入解耦 LLM Client、Tool Executor、Memory Store 与 Orchestrator，使 Mock/Stub/Fake 成为可能；并通过在 LLM 与工具调用之间插入 Recording/Replay Middleware，将线上 Trace 转化为本地可重放的确定性断言，从根本上消解非确定性带来的测试退化。对 QA 工作的启发是：应把可测试性条款前置到 Design Review，与功能需求同优先级评审，并推动建设统一的 Trace 录制回放基础设施，让回归测试摆脱对真实模型调用的依赖，实现质量左移。

- 源文件：[`wiki/topics/design-for-test.md`](topics/design-for-test.md)

---

## `disaster-recovery`  · 1 篇笔记  · 351 字

> 该主题聚焦 AI Agent 系统在故障场景下的可用性与可恢复性，核心问题是当编排、模型网关、Memory、向量库等关键组件失效时，系统能否在控制面、数据面、用户面三层完成切换、降级与重建，并向用户透出一致的状态语义。可复用的工程实践包括按层切分演练范围（路由/调度器主备切换、FAISS 等向量库的只读与重建、任务状态存储的延迟补偿），结合 Chaos Mesh、Toxiproxy 注入网络与依赖故障，使用 Ginkgo 编写分级演练用例，Playwright 校验流式响应中断后的续传与提示文案，并以 RTO/RPO、降级命中率作为验收指标。对 QA 的启发是：将灾备演练纳入常态化回归，建立"故障注入 - 降级断言 - 用户侧可观测"的三段式用例模板，避免只测主链路而忽视流式场景下的恢复体验。

- 源文件：[`wiki/topics/disaster-recovery.md`](topics/disaster-recovery.md)

---

## `environment-governance`  · 1 篇笔记  · 393 字

> 本主题聚焦于 AI Agent 在多环境、多版本迭代下的测试数据治理与环境一致性问题，核心矛盾在于 Agent 行为的非确定性与传统测试环境静态假设之间的冲突，需要解决数据漂移、依赖隔离、Mock 与真实服务切换、向量库快照回滚等工程难题。可复用的实践包括以数据契约（JSON Schema / Pydantic）约束输入输出、通过 Testcontainers 编排依赖、用 FAISS 或 Milvus 快照固化检索基线、借助 LangSmith / Langfuse 追踪链路，以及结合 Ginkgo、Pytest、Playwright 在不同层级构建分层用例，并通过种子数据与影子流量实现回归对齐。对 QA 落地的启发：一是将测试数据视为版本化制品，与模型权重、Prompt 模板共同纳入 CI 流水线；二是建立环境画像基线，对每次 Agent 上线执行差异巡检，避免静默退化。

- 源文件：[`wiki/topics/environment-governance.md`](topics/environment-governance.md)

---

## `environment-parity`  · 1 篇笔记  · 368 字

> 该主题聚焦于 AI Agent 在生产环境中因配置漂移与环境不一致所引发的隐性故障，关注的核心并非代码逻辑本身，而是 Prompt 模板版本、工具 schema、特征开关、Secret/ConfigMap、模型路由与灰度包之间的版本错位如何在不改一行代码的情况下让线上行为悄然劣化；可复用的工程实践包括用 Ginkgo 对后端关键配置快照与能力矩阵做断言、用 Python 与 API Testing 做配置 diff 和基线比对、用 Playwright 验证不同配置下的用户可见行为一致性、用 Kubernetes 声明式固化环境并落地漂移巡检任务。对 QA 的启发是质量门禁应从接口成功率扩展到「配置即被测对象」，将配置快照、环境 parity 校验与漂移告警纳入每日回归与发布卡点，让团队随时能回答线上当前跑的到底是哪一份配置。

- 源文件：[`wiki/topics/environment-parity.md`](topics/environment-parity.md)

---

## `ephemeral-env`  · 1 篇笔记  · 425 字

> 该主题聚焦于 AI Agent 在持续测试中如何获得可信、可隔离且低成本的运行环境，核心问题是测试数据的版本化治理与临时环境（ephemeral-env）的快速拉起、销毁与状态复现，避免脏数据污染回归结果或导致 Agent 行为漂移。可复用的工程实践包括：基于 Docker Compose / Testcontainers 按用例粒度拉起依赖、用 Kubernetes Namespace 或 vcluster 做并行隔离、以 FAISS / SQLite 快照管理向量库与结构化数据的基线、结合 Ginkgo 或 Pytest 的 fixture 生命周期统一接管 setup/teardown，并通过 LangSmith 记录每次会话的 trace 以便复盘。对 QA 的启发是：将"环境即代码 + 数据即代码"作为 Agent 回归流水线的前置门禁，并为每条用例绑定独立的数据指纹和环境标签，使失败用例可一键重放而非依赖共享 staging。

- 源文件：[`wiki/topics/ephemeral-env.md`](topics/ephemeral-env.md)

---

## `eval`  · 1 篇笔记  · 345 字

> 本主题聚焦 AI Agent 在模型版本、系统提示词、工具描述、检索与记忆策略发生细微变更后出现的"行为漂移"问题，强调真正的发布风险不在功能可用性，而在边界与稳定性的隐性退化。可复用的工程实践包括：以评测集（Eval Set）固化关键业务链路与拒绝边界，结合基线答案、结构化断言、工具调用轨迹断言与 LLM-as-Judge 多维判分，配合 Ginkgo 后端回归门禁、Python 批量评测与指标聚合、Playwright 用户视角 E2E、K8s/CI 每日巡检形成闭环。对 QA 的落地建议是：将"评测即工程"纳入版本准入流程，任何 Prompt、工具或检索策略改动都应触发评测集回归，并将通过率、工具轨迹一致性与单次调用成本一并设为门禁指标，避免仅凭主观体感判断模型行为是否合格。

- 源文件：[`wiki/topics/eval.md`](topics/eval.md)

---

## `evaluation`  · 1 篇笔记  · 405 字

> 该主题聚焦于 AI Agent 在真实业务链路中的可评测性问题，核心是如何构建一套可复用、可回归的评测样本集，覆盖从 Prompt 稳定性、结构化输出校验到多步推理（ToT/ReAct）与检索增强（Embedding/FAISS 相似度）等关键能力点，解决传统单测无法刻画 LLM 非确定性输出的痛点。跨笔记可沉淀的工程实践包括：以分层样本集（基础能力、边界 case、对抗样本）驱动评测，结合 LLM-as-Judge 与规则断言双轨打分，使用 Ginkgo 组织行为级用例、Playwright 驱动 Agent 端到端任务、FAISS 做语义召回基线对比，并将评测结果纳入 CI 形成回归基线。对 QA 的落地建议是：优先把样本集当作一等代码资产维护，建立版本化与失败样本回流机制；同时在 Prompt 或模型升级时强制跑通对抗集与稳定性集，避免指标在均值上看似持平、却在长尾 case 上发生静默退化。

- 源文件：[`wiki/topics/evaluation.md`](topics/evaluation.md)

---

## `event-driven`  · 1 篇笔记  · 368 字

> 该主题聚焦 AI Agent 从同步问答走向异步执行后暴露出的事件驱动可靠性问题，核心矛盾在于事件已送达但状态未收敛、回调重放引发副作用重复、前端进度与后端真实状态脱节，以及乱序消息导致终态被错误覆盖等典型故障。可复用的测试方法包括以 Ginkgo 验证事件链路的幂等性与唯一终态、以 Python/API Testing 覆盖 webhook 签名校验、重试、乱序与去重策略、以 Playwright 校验用户可见进度与真实事件的一致性，并借助 Kubernetes 演练 consumer 重启、队列堆积与回调重投，关键词集中在幂等、状态机约束、顺序控制与端到端可观测性。对 QA 的启发是：异步场景的用例设计应以状态机终态而非单次响应为断言基准，并将 webhook 重放、乱序与消费者故障注入纳入常规回归，避免线上才暴露 P0。

- 源文件：[`wiki/topics/event-driven.md`](topics/event-driven.md)

---

## `eventual-consistency`  · 1 篇笔记  · 341 字

> 该主题聚焦于 AI Agent 由“答”转“做”后跨系统动作的半成功风险，核心问题不在于单步重试，而在于系统是否具备可恢复边界、可追踪状态机与幂等键，以及在补偿过程中能否对用户诚实展示并最终收敛到唯一正确结果。可复用的工程实践包括：用 Ginkgo 驱动 Saga 编排与补偿顺序的验证、用 Python/API Testing 校验状态机流转与幂等键去重、用 Playwright 断言前端在“处理中 / 补偿中 / 已恢复”三态下的展示一致性、用 Kubernetes 故意 kill 异步 worker 以演练崩溃恢复与回调重放。落地建议是：QA 应推动业务方为每个 Agent 动作显式定义补偿语义与终态契约，并将“最终一致性 SLA”纳入回归基线，而非仅断言接口 200。

- 源文件：[`wiki/topics/eventual-consistency.md`](topics/eventual-consistency.md)

---

## `experiment`  · 1 篇笔记  · 366 字

> 该主题聚焦于 AI Agent 在线上实验与 A/B 测试中的质量保障问题，核心矛盾在于一次 Prompt 或策略变更往往会同时牵动工具调用路径、拒绝边界、副作用、时延与 Token 成本，传统"看转化率"式的实验思路无法覆盖 Agent 系统的安全与稳定性风险。可复用的实践包括：以一致性分流保障用户体验稳定，用 Ginkgo 验证实验路由与风控隔离，借助 Python/API Testing 监控指标分布与异常，使用 Playwright 串联用户视角全链路，并依托 Kubernetes 灰度发布与 Kill Switch 实现分钟级止损。对 QA 的启发是：实验评估单元应从单条回复升级为完整业务链路，并在效果指标之外强制设立护栏指标与熔断阈值，将 A/B 测试纳入可追踪、可回滚、可审计的质量系统而非单纯的效果验证手段。

- 源文件：[`wiki/topics/experiment.md`](topics/experiment.md)

---

## `explainability`  · 1 篇笔记  · 334 字

> 本主题聚焦于 AI Agent 在企业级场景下的可解释性与决策审计问题，核心关切是当 Agent 介入关键业务时，如何回答"决策由谁做出、基于何种输入、能否完整复盘归因"这三个问题，从而把测试边界从单一输出质量扩展到推理链路、工具调用、策略分支与审批日志的全链路可验证。可复用的工程实践包括：用 Ginkgo 编写决策轨迹的 E2E 行为校验、用 Python/API 层做审计契约测试以锁定日志字段与责任边界、用 Playwright 验证前端解释性信息的呈现一致性，并结合 K8s 与日志系统校验审计数据的完整性与不可篡改性。对 QA 的落地启发是：将"每个关键决策都可被看见、解释、复盘、归因"作为准入红线，把审计日志契约纳入回归基线，避免可解释性沦为事后补丁。

- 源文件：[`wiki/topics/explainability.md`](topics/explainability.md)

---

## `failover`  · 1 篇笔记  · 366 字

> 该主题聚焦 AI Agent 系统在故障场景下的可用性与恢复能力，核心问题在于当编排服务、模型网关、向量库或任务状态存储发生异常时，系统能否在控制面、数据面、用户面三层完成有序切换与降级，而非整体崩溃。可复用的工程实践包括：按控制面/数据面/用户面分层设计灾备矩阵，针对 Agent 编排器与路由层做主备切换演练，对 FAISS、Milvus 等向量库与 Redis 缓存验证只读模式、重建与延迟补偿路径，对流式响应使用 Playwright 模拟中断并校验断点续传与降级提示，结合 Chaos Mesh 或 Toxiproxy 注入网络与节点故障。对 QA 的启发是将灾备演练纳入常态化回归而非上线前一次性验收，并在测试用例中显式断言降级态文案、重试语义与数据一致性边界，避免只关注 happy path 导致故障期用户体验失控。

- 源文件：[`wiki/topics/failover.md`](topics/failover.md)

---

## `failure-analysis`  · 1 篇笔记  · 373 字

> 本主题聚焦于 AI Agent 在多步推理与工具调用链路中失败原因的可观测、可归因与可自动分诊问题，核心痛点是当 Agent 出现幻觉、工具调用错误或流程中断时，如何从 trace 日志中快速定位是 prompt 设计、检索召回、模型推理还是外部工具的故障层级。可复用的工程实践包括：基于 LangSmith / OpenTelemetry 的全链路 trace 埋点、结构化错误标签体系（root_cause × failure_stage）、用 LLM-as-Judge 对失败样本做二次分类、以及结合 FAISS 对历史失败 case 做相似度聚类以发现回归模式。对 QA 工作的启发是：应将失败归因流水线纳入回归测试基建，把每次 Agent 评测产出的 bad case 自动入库并打标，形成可持续演进的失败知识图谱，而非一次性人工排查。

- 源文件：[`wiki/topics/failure-analysis.md`](topics/failure-analysis.md)

---

## `fallback`  · 1 篇笔记  · 350 字

> 本主题聚焦 AI Agent 在生产环境中模型路由与回退链路的可靠性问题，核心矛盾不在于模型本身是否可用，而在于路由是否选对、fallback 是否及时触发、降级过程是否对用户与排障人员透明，以及在超时、雪崩场景下熔断隔离与成本时延能否取得平衡。可复用的工程实践包括：以 Ginkgo 编排后端 E2E 链路与故障注入、用 Python/API 层做路由契约测试以校验决策规则、用 Playwright 验证前端降级提示与可感知性、结合 K8s 做配置灰度发布与熔断演练，并将路由决策、回退路径写入结构化日志以支撑追溯。对 QA 的落地启发是：质量基线应从"答案对不对"扩展到"为什么选这个模型、失败后怎么退、退完是否可追溯"，并将 fallback 成功率、降级透明度纳入常态化回归与混沌演练指标。

- 源文件：[`wiki/topics/fallback.md`](topics/fallback.md)

---

## `fault-injection`  · 1 篇笔记  · 358 字

> 本主题聚焦于 AI Agent 在复杂依赖与不确定性环境下的鲁棒性验证，核心问题是如何在受控条件下主动暴露 LLM 调用链、向量检索与工具编排中的脆弱点，而非被动等待线上故障。可复用的工程实践包括基于 ChaosMesh 的 Pod / 网络 / IO 故障注入，针对 LLM 接口的延迟与超时模拟、限流与 5xx 错误回放，结合 Ginkgo 编写稳态假设（Steady-State Hypothesis）驱动的混沌实验用例，并通过对 FAISS 等向量库的节点抖动验证降级与重试策略的有效性。对 QA 工作的启发是：将故障注入纳入 Agent 回归流水线，为每条关键链路预先定义可观测的稳态指标与自动回滚阈值；同时建立故障场景库，覆盖模型超时、工具调用失败与检索为空三类高发模式，让韧性测试常态化而非一次性演练。

- 源文件：[`wiki/topics/fault-injection.md`](topics/fault-injection.md)

---

## `feedback-loop`  · 1 篇笔记  · 326 字

> 该主题聚焦于 AI Agent 上线后如何把线上失败、人工纠正与用户反馈持续回灌为可执行评测资产，核心问题是打通「线上问题→标准样本→自动评测→回归门禁→发布决策→再观测」的 EvalOps 闭环，而非追求单次离线评测分数。可复用的关键实践包括：以 Ginkgo 守住 P0 回归与工具调用正确性、用 Python/API Testing 承担样本治理与指标聚合、借 Playwright 验证端到端用户体验、依托 Kubernetes CronJob/Job 调度周期化回归与线上回灌，并对样本做分级与归因标注。对 QA 的启发是：应将事故复盘流程产物化为标准样本入库，并在 CI 中设置可阻断上线的回归门禁，确保同类线上问题不会以相同方式二次发生。

- 源文件：[`wiki/topics/feedback-loop.md`](topics/feedback-loop.md)

---

## `fixture`  · 1 篇笔记  · 415 字

> 该主题聚焦于 AI Agent 在持续迭代过程中如何治理测试数据与运行环境，核心问题是消除因数据漂移、外部依赖不稳定与状态污染导致的用例不可复现。可复用的工程实践包括：以 fixture 为单位管理种子数据与向量索引快照（FAISS / Chroma 的离线导出），通过 Ginkgo 的 BeforeSuite/AfterEach 或 Pytest fixture 控制作用域与清理顺序，结合 Testcontainers 拉起隔离的 LLM Mock、向量库与中间件，并用 VCR/WireMock 录制回放第三方调用，Playwright 侧则以 storageState 固化登录态。对 QA 的启发是：将 fixture 视为与代码同等的资产纳入版本管理，按 session/module/function 分层声明依赖，并为每个 Agent 用例显式声明数据契约与回滚钩子，避免"跑过一次就脏"的隐式耦合拖慢回归节奏。

- 源文件：[`wiki/topics/fixture.md`](topics/fixture.md)

---

## `human-in-the-loop`  · 1 篇笔记  · 374 字

> 该主题聚焦于 AI Agent 从“给建议”跨越到“执行动作”时，如何通过 Human-in-the-Loop 机制把高风险决策真正交还给人，而非流于表面的“多一个确认按钮”，核心问题在于验证 Agent 能否在该停下来时挂起、把结构化上下文与证据快照交付审批人、并在人决策后稳定续跑且不产生副作用。可复用的工程实践是将 HITL 拆解为风险识别、审批挂起、证据快照、审批人校验、人工接管、结果回传、任务续跑与审计留痕八个可验证环节，技术栈上以 Ginkgo 覆盖后端审批链路 E2E、Python/API 校验审批契约与过期幂等、Playwright 还原用户接管视角、K8s 演练审批服务高可用与恢复。对 QA 的启发是：用例设计应显式覆盖过期审批、错人审批、重复审批与上下文漂移四类反例，并把幂等键与审计留痕作为上线门禁指标，而非事后补救项。

- 源文件：[`wiki/topics/human-in-the-loop.md`](topics/human-in-the-loop.md)

---

## `incident-driven-testing`  · 1 篇笔记  · 469 字

> 本主题聚焦于将 AI Agent 线上事故转化为可回归资产的工程化路径，核心问题是如何让 P0/P1 故障在 48 小时内沉淀为自动化用例，避免模型退化、Prompt 漂移、工具链断裂、记忆污染与多 Agent 死锁等 Agent 特有故障重复发生。可复用的关键实践包括 IDT 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent）、Agent 故障 6 大类 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）、Postmortem Action Item 到测试代码的映射机制，以及 Ginkgo 行为驱动断言、Playwright 端到端复现、FAISS 向量记忆校验等工具组合，配合 CI Gate 强制拦截同类回归。对 QA 工作的启发是：应在事故响应流程中固化"48h 回归用例交付"硬指标，并预先按故障 Taxonomy 维护标准化复现脚本与测试模板，使每次事故都能直接套模板产出可执行用例，将被动救火转为主动防御资产积累。

- 源文件：[`wiki/topics/incident-driven-testing.md`](topics/incident-driven-testing.md)

---

## `intelligent-selection`  · 1 篇笔记  · 380 字

> 本主题聚焦于 AI Agent 测试场景下的回归效率困境：当单条用例消耗数秒与数千 Token、全量回归在 500 条规模下即逼近 10 分钟与 \$5-20 成本红线时，如何以可控代价覆盖核心风险面。可复用的工程路径包括基于代码变更—依赖图—用例映射的 Test Impact Analysis，以历史失败率、变更频率、业务优先级与执行新鲜度构建的风险评分模型，以及按 Prompt、工具 Schema、模型版本分流的变更感知路由；落地侧则依托 Ginkgo 的 `Label` 选择器与 Playwright 的 `@regression-p0` 等 Tag Filter 在 CI 中按风险层级动态裁剪。建议 QA 团队优先将用例分层打标并沉淀变更—用例映射表，再以风险评分驱动 Top-N 调度，使日常 PR 仅触发智能子集、夜间或发布前再跑全量基线。

- 源文件：[`wiki/topics/intelligent-selection.md`](topics/intelligent-selection.md)

---

## `kubernetes`  · 1 篇笔记  · 428 字

> 本主题笔记聚焦于 Kubernetes 环境下 AI Agent 系统的稳定性验证，核心问题是如何在分布式推理与多组件协作场景中量化故障容忍度，尤其针对 Pod 异常、网络分区、依赖中断等典型扰动下 Agent 链路的退化行为与恢复能力。可复用的工程实践包括基于 ChaosMesh 的声明式故障注入（NetworkChaos、PodChaos、StressChaos）、结合 Ginkgo 编写场景化 E2E 用例、以 Prometheus 与 OpenTelemetry 采集 SLO 指标，并通过 Argo Workflows 或 Tekton 串联混沌实验流水线，形成"扰动-观测-回归"闭环。对 QA 工作的启发是：应将混沌实验左移至 CI 阶段，针对 LLM 调用超时、向量库（如 FAISS、Milvus）抖动等 AI 特有故障建立专用故障库，并将 Agent 任务成功率、token 重试率纳入发布门禁，避免仅以单元测试覆盖率作为质量基线。

- 源文件：[`wiki/topics/kubernetes.md`](topics/kubernetes.md)

---

## `least-privilege`  · 1 篇笔记  · 372 字

> 该主题聚焦于 AI Agent 在代替用户执行工具调用与数据访问时的权限代理失真问题，核心矛盾在于 Agent 是否以「用户被允许的最小权限」而非「系统可达的最大权限」在行动，由此衍生出身份透传、作用域约束、审批门禁绕过、检索链路越权拿到原始明细、执行审计缺失等典型缺陷面。可复用的工程实践包括：用 Ginkgo 在后端构建授权链路与身份透传的契约用例，用 Python/API 层做策略（policy）契约测试覆盖读写边界与高风险动作审批，用 Playwright 验证前端审批弹窗与风险告知的真实触达，并结合 K8s ServiceAccount 做工作负载身份隔离与最小权限裁剪。对 QA 的落地建议是：将「同一 prompt 在不同用户身份下的可执行动作差集」沉淀为回归基线，并把审批绕过与越权检索列为发布阻断级用例，避免依赖模型自律。

- 源文件：[`wiki/topics/least-privilege.md`](topics/least-privilege.md)

---

## `live-validation`  · 1 篇笔记  · 344 字

> 本主题聚焦 AI Agent 在生产环境下的「活体验证」难题：模型漂移、Prompt 注入、工具 API 退化与 RAG 索引腐化等问题难以通过离线评测暴露，必须在真实流量中持续校验。可复用的工程实践包括合成探针（Synthetic Probes，覆盖黄金路径并组合确定性断言与语义相似度模糊断言）、金丝雀断言（区别于灰度发布，用于已上线版本的活性巡检）、流量采样回放（生产 Trace 脱敏后在影子环境重放）以及持续评估流水线，配合 OpenTelemetry 链路采集与 FAISS/向量库做语义比对。对 QA 的启发是：应将测试左移与右移并重，在 CI 之外建设独立的线上巡检管道，将探针失败、断言衰减纳入 SLO 告警；同时沉淀脱敏回放数据集，使生产长尾用例反哺回归库，形成闭环。

- 源文件：[`wiki/topics/live-validation.md`](topics/live-validation.md)

---

## `locust`  · 1 篇笔记  · 354 字

> 本主题聚焦于 AI Agent 在多步推理、工具调用和上下文累积场景下的性能与稳定性压测，核心问题是如何在传统 Web 压测模型之外，刻画 Agent 长链路、异步流式、Token 计费等非确定性负载特征。可复用的工程实践包括：以 Locust 编写带状态的 user behavior 模拟多轮对话与工具触发、用 k6 做高并发 HTTP/SSE 基线对比、对 LLM 网关侧统计 P95/P99 首 Token 延迟与端到端完成时延，并结合 FAISS 检索 QPS、上下文长度分桶、失败率与超时熔断阈值构建综合指标体系。对 QA 工作的启发是：应将"单请求成功"升级为"会话级 SLO"，在 CI 中固化一组带语义断言的压测剧本，并把 Token 消耗与重试率纳入回归基线，避免性能劣化被功能用例掩盖。

- 源文件：[`wiki/topics/locust.md`](topics/locust.md)

---

## `memory`  · 1 篇笔记  · 324 字

> 本主题聚焦于 AI Agent 引入记忆与会话状态后所带来的测试范式迁移：核心问题不再是单轮回答的正确性，而是跨轮上下文的继承边界、多用户之间的记忆隔离、摘要压缩后的关键信息保真，以及状态恢复与重试场景下的幂等性与一致性。可复用的工程实践包括用 Ginkgo 编排多轮会话 E2E 与幂等校验、用 Python/API 层定义记忆契约并实施故障注入、用 Playwright 从用户视角验证历史连续性、用 K8s 演练持久层与副本恢复，同时配合 FAISS 等向量存储校验召回偏差。对 QA 的落地启发是：应把记忆视为正式数据资产而非临时缓存，建立涵盖"该记、该忘、该隔离、该回滚"的四象限用例矩阵，并将跨会话污染与摘要丢失列为发版前的强制回归项。

- 源文件：[`wiki/topics/memory.md`](topics/memory.md)

---

## `monitoring`  · 1 篇笔记  · 380 字

> 该主题聚焦于 AI Agent 上线后的质量可观测性问题，即如何把传统的一次性评测延伸为持续运行的质量看板，覆盖回答准确率、工具调用成功率、延迟与成本等核心指标，并在指标漂移或回归时及时告警。可复用的工程实践包括：以 Prometheus + Grafana 搭建指标采集与可视化层，借助 OpenTelemetry 对 LLM 调用链做 tracing，将离线评测集（含 FAISS 向量召回基线）固化为定时回归任务，并用 Ginkgo 或 pytest 组织断言；同时通过影子流量与采样标注闭环回灌评测集，形成"线上数据—评测—Prompt 迭代"的反馈环。对 QA 的启发是：应尽早把质量看板的 SLO 纳入发布门禁，而非仅在迭代末期跑评测；建议先以延迟、失败率、人工抽检通过率三项最小指标集落地，再逐步扩展语义层评测，避免一次性铺开导致噪声淹没真问题。

- 源文件：[`wiki/topics/monitoring.md`](topics/monitoring.md)

---

## `opentelemetry`  · 1 篇笔记  · 406 字

> 该主题聚焦于 AI Agent 在多步推理与工具调用链路中的可观测性缺口，核心问题是如何在 LLM 输出非确定性的前提下，定位 prompt、检索、tool call 各环节的耗时瓶颈与失败归因。跨笔记可复用的工程要点包括：以 OpenTelemetry 为统一埋点标准，将 Agent 的 plan-act-observe 循环建模为父子 Span，结合 trace_id 串联 RAG 检索（如 FAISS 召回耗时）、工具调用与模型推理，再通过 Jaeger 或 Langfuse 做可视化下钻，并在 Span 属性中固化 token 数、模型版本、prompt 哈希等关键标签。对 QA 工作的启发是：回归测试不应只断言最终输出，而应在 E2E 用例中校验 Span 拓扑与关键属性是否齐全，把"链路完整性"作为质量门禁；同时可基于历史 trace 沉淀延迟与失败率基线，用于发布前的性能比对与异常检测。

- 源文件：[`wiki/topics/opentelemetry.md`](topics/opentelemetry.md)

---

## `pact`  · 1 篇笔记  · 447 字

> 本主题聚焦于 AI Agent 在多版本协作场景下如何通过契约测试稳定接口语义，核心问题是当上游模型输出 Schema 或工具调用协议发生演进时，下游消费方如何在不回归整体链路的前提下快速定位破坏性变更。可复用的工程实践包括：基于 Pact / OpenAPI 的 consumer-driven contract 校验、使用 JSON Schema + Ajv 对 LLM 结构化输出做字段级断言、借助 Ginkgo 组织契约用例并产出 pact 文件、在 CI 中接入 Pact Broker 实现 provider 端的 can-i-deploy 闸口，以及对 Embedding 与检索结果用 FAISS 做兼容性回放。对 QA 落地建议有二：一是将 Agent 的工具调用参数、函数返回体纳入契约资产管理，按版本归档并与 prompt 模板共同灰度；二是在流水线中前置 Schema diff 检测，把"字段新增/删除/类型变更"映射为不同等级的阻断策略，降低模型升级带来的回归成本。

- 源文件：[`wiki/topics/pact.md`](topics/pact.md)

---

## `performance-testing`  · 1 篇笔记  · 358 字

> 本主题聚焦于 AI Agent 在多轮对话、工具调用与 RAG 链路下的性能压测难题：传统接口压测无法覆盖 Token 流式返回、上下文累积与外部依赖（向量库、LLM API）带来的长尾延迟与成本波动。可复用的方法包括以 Locust 编写有状态的 Agent 会话脚本、用 k6 进行高并发流式 SSE 压测，并将 TTFT、tokens/s、P95 端到端延迟、工具调用失败率与单请求成本纳入统一指标口径；配合 FAISS / pgvector 检索耗时分桶、Prometheus + Grafana 看板与混沌注入（限流、超时、降级）形成闭环。对 QA 的启发是：应尽早建立 Agent 专属的性能基线与回归门禁，将 Token 成本视为与延迟同权重的 SLO 指标，避免上线后被长上下文与工具链放大效应反噬。

- 源文件：[`wiki/topics/performance-testing.md`](topics/performance-testing.md)

---

## `pipeline`  · 1 篇笔记  · 422 字

> 本主题聚焦 AI Agent 端到端测试在流水线中的可工程化落地，核心问题是如何在非确定性输出、长链路依赖（模型→编排→工具→存储）与推理延迟波动并存的前提下，构建稳定、可重复且可观测的 E2E 测试体系。可复用的关键实践包括：Setup-Execute-Verify 三阶段编排模型配合超时熔断与失败隔离、基于 YAML/Go Struct 的 ScenarioSpec 声明式场景 DSL（用户意图+预期工具调用序列+语义/结构/副作用三维断言）、Smoke/Core/Full/Chaos 四层 CI/CD 分级门禁，以及借助 K8s Namespace 实现并行化与资源隔离，技术栈上可结合 Ginkgo 做行为驱动断言、FAISS 支撑语义比对。对 QA 的启发是：优先把场景模板化与 Label 选择器接入 PR Gate，用分层耗时预算换取反馈速度；同时为模型类断言建立语义相似度阈值与重试基线，避免用确定性断言强行覆盖随机输出。

- 源文件：[`wiki/topics/pipeline.md`](topics/pipeline.md)

---

## `planning`  · 1 篇笔记  · 329 字

> 该主题聚焦于 AI Agent 在自主决策与规划场景下的可测性问题，核心关切并非答案对错，而是决策路径是否可解释、规划是否收敛、异常时能否重规划以及越权动作与副作用是否可控；笔记将自主决策拆解为目标理解、约束继承、工具选择、计划生成、执行反馈、动态重规划与最终止损七个可验证环节，并形成可复用的组合测试栈：Ginkgo 承载后端决策链路的 E2E 验证，Python/API 层做计划契约校验与故障注入，Playwright 从用户视角验证计划透明性，K8s 用于多副本与发布门禁演练。对 QA 的启发是：用例设计应从结果断言转向过程断言，针对工具失败、权限不足、部分成功、长链路超时等动态分支构建故障注入矩阵，并把"边界内稳定决策"作为质量门禁的核心指标。

- 源文件：[`wiki/topics/planning.md`](topics/planning.md)

---

## `postmortem`  · 1 篇笔记  · 449 字

> 本主题聚焦于事故驱动测试（Incident-Driven Testing, IDT）在 AI Agent 场景下的工程化落地，核心问题是如何将 Postmortem 中的 Action Item 转化为可执行、可回归的自动化用例，避免同类故障复发。可复用的关键实践包括 IDT 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent）、Agent 故障六大 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）以及 48 小时回归用例 SLA；技术栈层面可结合 Ginkgo 编写行为级回归、用 FAISS 做记忆污染与检索漂移检测、借助 Playwright 复现工具链断裂场景，并将用例纳入 CI Gate 形成准入卡口。对 QA 工作的启发是：应推动 Postmortem 模板强制关联回归用例 ID，并按故障分类维护标准化复现脚本库，使每一次 P0/P1 都沉淀为可量化的质量资产而非一次性复盘。

- 源文件：[`wiki/topics/postmortem.md`](topics/postmortem.md)

---

## `production-patrol`  · 1 篇笔记  · 410 字

> 本主题聚焦 AI Agent 在生产环境下的持续质量保障问题，核心矛盾在于模型漂移、Prompt 注入、工具 API 退化与 RAG 索引腐化等长尾故障无法通过离线评测充分暴露，必须依赖线上手段补齐观测盲区。可复用的工程实践包括：以合成探针（Synthetic Probes）覆盖黄金路径并组合确定性断言（工具调用序列、JSON Schema 字段校验）与模糊断言（基于 embedding 的语义相似度阈值），通过金丝雀断言对已发布版本做活性巡检，利用 Trace 采样在影子环境回放脱敏流量做 diff 比对，并接入持续评估流水线；技术栈上可结合 OpenTelemetry、Langfuse、FAISS 与 Ginkgo/Pytest 组织断言集。对 QA 的启发是：将"线上巡检"纳入发布后质量基线，把探针用例与离线评测集同源管理，并为每条断言失败定义清晰的告警分级与回滚 Runbook，避免巡检沦为噪声看板。

- 源文件：[`wiki/topics/production-patrol.md`](topics/production-patrol.md)

---

## `progressive-delivery`  · 1 篇笔记  · 341 字

> 本主题聚焦于 AI Agent 在生产环境中的渐进式交付问题，核心在于如何在模型与提示词频繁迭代的前提下，通过灰度发布与影子流量验证新版本的稳定性、回归风险与业务指标偏移。可复用的工程实践包括：基于流量染色与权重路由的金丝雀分桶、影子链路的请求镜像与响应 diff 比对、离线回放数据集与在线指标的双轨校验，以及围绕 LLM 输出的语义相似度评估（可借助 FAISS 做向量召回比对）、结构化输出 schema 校验和端到端用例回放（Playwright、Ginkgo 等）。对 QA 的启发是：应将影子流量比对纳入发布门禁，沉淀一套覆盖语义等价、延迟分布与成本波动的多维断言；同时建立带样本权重的回归集，在每次提示词或模型升级时自动触发分层评测，避免仅依赖人工抽检导致的劣化漏网。

- 源文件：[`wiki/topics/progressive-delivery.md`](topics/progressive-delivery.md)

---

## `prompt-regression`  · 1 篇笔记  · 372 字

> 该主题聚焦于 AI Agent 在模型版本、系统提示词、工具描述、检索与记忆策略发生轻微变更时引发的「行为漂移」风险，关注如何把 Prompt 回归从一次性人工抽检升级为可持续运行的工程化评测体系。可复用的方法论包括：以评测集（Eval Set）固化用户目标、上下文、工具调用与拒绝边界等真实业务链路，采用基线答案、结构化断言、工具轨迹断言与 LLM-as-Judge 多重判分相结合的复合评判策略，并以 Ginkgo 承担后端回归门禁、Python 驱动批量评测与指标聚合、Playwright 完成用户视角 E2E、K8s/CI 做每日自动巡检。对 QA 的启发是：应把 Prompt 与 Agent 视为有版本的被测对象，将评测集与轨迹断言纳入发布门禁，并为每次回归设定通过率、成本与延迟的预算阈值，避免「看起来还能答」掩盖核心场景退化。

- 源文件：[`wiki/topics/prompt-regression.md`](topics/prompt-regression.md)

---

## `protobuf`  · 1 篇笔记  · 387 字

> 本主题聚焦于 AI Agent 在工具调用与多服务协作中如何通过 Protobuf 约束接口契约，并在 Schema 持续演进的过程中保证向前/向后兼容。笔记从契约测试视角切入，强调以 .proto 文件作为单一事实源，配合 buf breaking、buf lint 做变更门禁，结合 Ginkgo/Go test 编写消费者驱动契约用例，并借助 Pact 或自建 golden message 仓库回放历史报文，验证字段新增、reserved 占位、oneof 扩展等典型演进场景下 Agent 调用链的稳定性。对 QA 工作的启发有两点：一是把 proto 变更纳入 CI 强制流水线，破坏性变更需显式审批并同步更新 fixture，避免 LLM 侧解析静默失败；二是为结构化输出建立 schema 快照库，定期跑兼容性回归，及早暴露模型升级与契约漂移带来的隐性故障。

- 源文件：[`wiki/topics/protobuf.md`](topics/protobuf.md)

---

## `red-team`  · 1 篇笔记  · 378 字

> 本主题聚焦于大模型应用的红队视角安全测试，核心问题是如何系统性识别 Prompt Injection、越权访问与敏感数据泄露三类典型风险，并将其纳入可回归的工程化流程。可复用的方法包括：构建对抗 Prompt 用例库（直接注入、间接注入、越狱模板、角色劫持）并通过 Ginkgo 组织分级断言、对 RAG 链路的检索结果做来源白名单与权限标签校验、利用 Playwright 模拟多租户会话验证越权边界、在向量库（FAISS / pgvector）侧对召回内容做 PII 与机密关键词扫描、以 LLM-as-Judge 加正则双通道判定输出是否泄露 system prompt 或上下文。落地建议是将红队用例固化为 CI 中的安全回归集，每次 Prompt 或检索策略变更均触发对抗测试；同时建立越权与泄露事件的语义化指标，纳入质量门禁而非仅做一次性渗透。

- 源文件：[`wiki/topics/red-team.md`](topics/red-team.md)

---

## `red-teaming`  · 1 篇笔记  · 378 字

> 本主题聚焦 AI Agent 在投入生产环境后所面临的新型复合安全风险，核心问题不再是传统 Web 的鉴权与漏扫，而是 Prompt Injection、工具越权调用、记忆污染、跨租户数据串读、敏感信息外泄与危险动作误执行等叠加场景，测试关注点从"答得对不对"前移至"是否只在被授权边界内行动"。可复用的工程实践可归纳为输入防护、决策约束、执行鉴权、结果审计与持续红队评测五层护栏，自动化栈上以 Ginkgo 承接后端越权与权限矩阵 E2E、Python/API 层做契约与注入用例校验、Playwright 覆盖前端高风险交互确认弹窗、K8s NetworkPolicy 与命名空间做租户隔离回归。对 QA 的启发是：应将红队用例沉淀为可回归的安全契约集并接入 CI 形成发布门禁，同时为每个新增工具调用强制配套越权与拒答用例，避免能力扩张快于安全验证。

- 源文件：[`wiki/topics/red-teaming.md`](topics/red-teaming.md)

---

## `regression-testing`  · 1 篇笔记  · 369 字

> 该主题聚焦于 AI Agent 场景下回归测试的成本与效率困境：当单条用例消耗数秒及数千 Token 时，传统全量回归在执行时长与 Token 开销上均不可持续，必须通过智能筛选压缩范围又不牺牲覆盖。可复用的工程实践包括基于代码变更—依赖图—用例映射的 Test Impact Analysis、融合历史失败率与变更频率及业务优先级的风险评分模型、按 Prompt / 工具 Schema / 模型版本差异化触发语义回归或契约测试的变更感知路由，以及 Ginkgo `Label` 选择器与 Playwright `@regression-p0` 标签等分层筛选能力。落地建议上，QA 应优先为用例补齐风险与分层元数据，使 CI 能按变更类型动态拉起最小必要集合；同时建立 Token 成本与失败率看板，将回归策略本身纳入持续度量与调优。

- 源文件：[`wiki/topics/regression-testing.md`](topics/regression-testing.md)

---

## `release-gates`  · 1 篇笔记  · 436 字

> 该主题聚焦于 AI Agent 在 Kubernetes 环境下从镜像构建、灰度发布到端到端验收的发布闸门设计，核心问题是如何在模型与提示词频繁迭代的背景下，把"可上线"这一判断从主观经验沉淀为可量化、可阻断的自动化卡点。可复用的工程实践包括：以 Ginkgo/Gomega 编写带 BDD 语义的发布期验收用例、用 Playwright 串联 Agent 前端会话与工具调用链路、基于 FAISS 召回回归集进行语义相似度比对、结合 Argo Rollouts 或 Flagger 做 SLO 驱动的渐进式发布，以及通过 Prometheus 指标与 OpenTelemetry trace 共同构成回滚信号。对 QA 工作的启发是：应将质量门禁左移到 Helm Chart 与 CI 流水线中，把"语义正确率、工具调用成功率、P95 时延"三类指标固化为发布准入硬阈值；同时建立线上小流量影子评测，使每次模型或 Prompt 变更都能在真实流量下获得可追溯的验收证据。

- 源文件：[`wiki/topics/release-gates.md`](topics/release-gates.md)

---

## `reliability-engineering`  · 1 篇笔记  · 418 字

> 本主题聚焦于 AI Agent 系统在生产环境中的可靠性工程，核心问题是如何将事故经验沉淀为可执行的回归资产，避免同类故障在模型退化、Prompt 漂移、工具链断裂、记忆污染与多 Agent 死锁等多元根因下反复出现。可复用的关键实践是 Incident-Driven Testing 闭环五步法（Detect→Classify→Reproduce→Codify→Prevent），辅以 6 大类故障 Taxonomy（Model/Prompt/Tool/Memory/Orchestration/Infra）形成标准化复现模板，并通过 Ginkgo 等 BDD 框架编码回归用例、接入 CI Gate 强制拦截，配合 FAISS 等向量检索做记忆污染比对。对 QA 工作的启发是：将 48h 内产出至少一条自动化回归用例写入 Postmortem SOP，并按故障分类维护可插拔的测试模板库，让事故复盘真正闭环到流水线而非停留在文档。

- 源文件：[`wiki/topics/reliability-engineering.md`](topics/reliability-engineering.md)

---

## `replay-testing`  · 1 篇笔记  · 383 字

> 该主题聚焦于 AI Agent 在企业级生产环境中的可追溯与可重放能力，核心问题是如何把一次 Agent 执行拆解为可追踪、可验证、可重放的事实流，覆盖任务规划、工具调用、权限审批、事件写入、投影更新到审计查询的完整链路。可复用的工程实践包括以事件溯源为骨架构建不可篡改的审计日志，用 Ginkgo 验证事件追加顺序、状态投影与离线重放一致性，用 Python 接口测试校验审计查询、字段脱敏与完整性校验，用 Playwright 验证用户侧时间线与审计详情的可理解性，并通过 Kubernetes 演练日志延迟、consumer 重启、事件重复投递与投影重建等故障场景。对 QA 的启发是：在用例设计阶段就把"可重放"作为一等验收标准，针对每条关键链路沉淀可回放的事件夹具，让线上事故能用同一批事件还原现场，推动质量体系从"跑成功"走向"讲得清、追得回、修得准"。

- 源文件：[`wiki/topics/replay-testing.md`](topics/replay-testing.md)

---

## `replay`  · 1 篇笔记  · 365 字

> 该主题聚焦于 AI Agent 在具备规划、工具调用、异步回调与补偿能力后，如何回答"系统到底经历了什么、状态为何不一致"这一根本问题，核心是通过事件溯源、审计链路与可重放回归三件套，把不可见的执行过程沉淀为可查询、可验证、可回放的事实流。可复用的工程实践包括：用 Ginkgo 对任务生命周期内的事件序列、幂等性与租户隔离做断言，用 Python/API Testing 覆盖事件查询、审计过滤与 replay 接口的契约一致性，用 Playwright 校验前端时间线与后端事件事实对齐，用 Kubernetes 演练消费者重启、消息回放与审计补齐场景。对 QA 的启发是：应推动将"事件流"作为一等测试对象纳入回归资产库，并基于线上真实执行链路构建可重放的故障复现集，让缺陷复盘和回归从依赖日志拼凑转向基于事件的确定性验证。

- 源文件：[`wiki/topics/replay.md`](topics/replay.md)

---

## `risk-scoring`  · 1 篇笔记  · 408 字

> 该主题聚焦于 AI Agent 测试体系中的回归成本失控问题——当单条用例消耗 0.5-2s 与数千 Token 时，500 条级别的全量回归在时间与费用上均不可持续，因此核心命题是如何在保障覆盖率的前提下实现"少跑、跑对"。可复用的关键实践包括：基于代码变更与依赖图的 Test Impact Analysis、由历史失败率/变更频率/业务优先级/失活天数构成的风险评分模型、按变更类型（Prompt / Schema / 模型版本）路由到语义回归、契约测试或 Eval 基线对比的差异化策略，以及借助 Ginkgo 的 Label 选择器与 Playwright 的 Tag Filter 在 CI 中按风险分层动态裁剪用例集。对 QA 的启发是：应把回归套件视为带成本的资产而非越多越好，建议先落地用例风险打分与标签分层，再以 TIA 驱动 PR 级智能选跑，将全量回归收敛到 Nightly 或发版门禁场景。

- 源文件：[`wiki/topics/risk-scoring.md`](topics/risk-scoring.md)

---

## `root-cause-analysis`  · 1 篇笔记  · 349 字

> 该主题聚焦于 AI Agent 在多层链路中的隐性偏离问题——表层输出看似可用，但 Prompt 路由、检索召回、工具参数、状态机推进、前端渲染或异步回调中已悄然失真，传统的事后查日志方式难以快速归因。可复用的关键实践是构建 Trace 驱动的分层调试体系：用统一 TraceID 贯穿入口层、编排层、模型层、工具层、状态层与前端层，借助 Ginkgo 固化后端轨迹断言，用 Python 做日志拼装与根因聚合，用 Playwright 校验前端可见态与后台事实一致性，并以 Kubernetes 隔离环境保障问题样本可稳定复现。对 QA 工作的启发是：应把每一次线上故障沉淀为带 Trace 快照的回归用例，并在 CI 中前置分层断言，让"哪里先偏了"成为可自动判定的质量信号，而非依赖人工复盘。

- 源文件：[`wiki/topics/root-cause-analysis.md`](topics/root-cause-analysis.md)

---

## `routing`  · 1 篇笔记  · 353 字

> 该主题聚焦于 AI Agent 在生产链路中的模型路由与失败兜底问题，核心关切并非模型本身的可用性，而是路由决策是否准确、fallback 是否及时、降级过程对用户和排障者是否透明，以及在熔断隔离下成本与时延能否保持平衡。可复用的工程实践包括：以 Ginkgo 编排后端链路与熔断演练、用 Python/API 层做路由契约与回退断言、借助 Playwright 在前端验证降级提示的可感知性，并结合 K8s 灰度发布与配置回滚来覆盖异常路径，把路由规则、fallback 成功率、降级透明度统一纳入 E2E 质量基线。对 QA 的启发是：用例设计应从"答案是否正确"升级为"决策链路是否可解释、可追溯"，建议在每条请求日志中固化模型选择与降级原因字段，并将主模型超时、配额耗尽等故障注入作为常态化回归项。

- 源文件：[`wiki/topics/routing.md`](topics/routing.md)

---

## `saga`  · 1 篇笔记  · 368 字

> 该主题聚焦 AI Agent 从问答升级为代表用户执行跨系统动作后所暴露的事务完整性问题，核心矛盾不在单步失败，而在「做了一半」的中间态——工单已建但通知缺失、审批已提交但会话仍处理中、回调重放导致重复落库等典型场景，要求质量体系能定义可恢复边界、记录可追踪状态并最终收敛到唯一结果。可复用的工程实践包括用 Ginkgo 验证 Saga 编排与补偿顺序、用 Python/API 测试覆盖状态机流转与幂等键、用 Playwright 校验前端对「处理中／补偿中／已恢复」的诚实展示，以及借助 Kubernetes 演练异步 worker 崩溃恢复。落地建议有二：一是把幂等键与补偿日志作为 Agent 类接口的强制评审项，纳入用例模板；二是建设一条混沌演练流水线，在 CI 中常态化注入中断与重放，确保最终一致性是被持续验证而非被假设。

- 源文件：[`wiki/topics/saga.md`](topics/saga.md)

---

## `schema-evolution`  · 1 篇笔记  · 419 字

> 该主题聚焦 AI Agent 在迭代过程中输入输出 Schema 的向后兼容与契约稳定性问题，核心矛盾在于模型版本升级、Prompt 调整或工具接口变更后，下游消费方仍能按既定结构解析与路由。可复用的关键实践包括：以 JSON Schema / Pydantic 模型作为契约源，借助 Pact 或自研 Contract Registry 做生产者—消费者双向校验，在 Ginkgo、Pytest 中沉淀字段级别的兼容性断言（新增可选、禁止删除必填、枚举只增不减），并结合 Schema diff 与 CI 卡点拦截破坏性变更；对于非结构化输出，可用 FAISS 做语义回归基线，Playwright 覆盖 Agent UI 链路的端到端契约。对 QA 的启发是：应将 Schema 视为一等测试对象，在 CI 中引入"契约门禁"与版本化快照，并联合 SRE 建立灰度回滚机制，让 Agent 升级具备可观测的兼容性证据而非依赖事后排障。

- 源文件：[`wiki/topics/schema-evolution.md`](topics/schema-evolution.md)

---

## `shadow-traffic`  · 1 篇笔记  · 350 字

> 该主题聚焦于 AI Agent 在生产环境中如何安全完成版本迭代，核心问题是如何在不影响线上用户的前提下，验证新模型或新 Prompt 的真实表现，并量化其与旧版本之间的行为差异与回归风险。可复用的工程实践包括基于流量复制的影子链路搭建、按用户分桶的灰度放量策略、双跑（dual-run）结果 diff 与一致性比对、关键指标（延迟、Token 消耗、成功率、毒性）的实时监控告警，以及借助 Ginkgo 编排回归用例、Playwright 录制真实会话、FAISS 对语义级输出做相似度聚类分析等技术栈组合。对 QA 工作的启发是：应将影子流量纳入发布前的标准卡点，建立"线上真实流量回放 + 离线评测集"的双轨评估机制，并提前定义可量化的放量门槛与自动回滚条件，避免依赖人工抽检判断模型上线风险。

- 源文件：[`wiki/topics/shadow-traffic.md`](topics/shadow-traffic.md)

---

## `shift-left`  · 1 篇笔记  · 463 字

> 本主题聚焦一个核心问题：AI Agent 的非确定性与多层依赖（LLM、Tool、Memory、Orchestrator）使传统测试范式失效，必须将"可测试性"作为架构属性在 Design Review 阶段前置评审，而非事后补救。可复用的关键实践包括六大原则（可观测性、可控制性、可隔离性、确定性回放、契约显式化、故障可注入性），以依赖注入（DI）为基石将 LLM Client、Tool Executor 等通过接口解耦，并在 LLM 与 Tool 调用之间植入 Recording/Replay Middleware，将线上 Trace 录制为本地夹具以实现确定性断言，配合 Mock/Stub/Fake 与故障注入完成契约校验。对 QA 的落地建议：一是将可测试性 Checklist 纳入 Agent 类需求的准入门禁，对硬编码 LLM/Tool 实例化的 PR 直接打回；二是搭建统一的 Trace 录制回放平台，让回归用例从"调用真实模型"迁移到"重放历史 Trace"，显著降低 CI 成本与 Flaky 率。

- 源文件：[`wiki/topics/shift-left.md`](topics/shift-left.md)

---

## `stateful`  · 1 篇笔记  · 331 字

> 该主题聚焦有状态 AI Agent 的测试范式迁移：当 Agent 引入记忆与会话状态后，质量风险从"单轮答案正确性"转向"跨轮上下文继承、用户间隔离、摘要压缩后的约束保真、会话恢复时的幂等性"等持续性问题，核心是把记忆视为正式数据资产而非临时缓存。可复用的工程实践包括以会话历史、用户画像、工具中间态、外部持久化记忆为四象限设计覆盖矩阵，用 Ginkgo 编排多轮 E2E 与幂等校验、Python/API 层做记忆契约与故障注入、Playwright 验证用户视角的历史连续性、K8s 演练持久层与副本恢复。落地建议：QA 应在用例库中固化"该记、该忘、该隔离、该回滚"四类断言模板，并在 CI 中常态化注入会话中断与并发写入场景，避免缺陷只在生产长尾暴露。

- 源文件：[`wiki/topics/stateful.md`](topics/stateful.md)

---

## `tenant-isolation`  · 1 篇笔记  · 400 字

> 本主题聚焦于 AI Agent 从单用户助手演进为多租户协作平台后所面临的隔离安全问题，核心关注点不在于回答准确性，而在于跨租户串数、跨会话串上下文、跨工作空间误调用工具、越权访问文件与记忆等结构性风险。可复用的工程实践是将隔离边界结构化建模为 tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 七类可验证对象，并组合使用 Ginkgo 串联后端隔离链路 E2E、Python/API 覆盖鉴权契约与越权回归、Playwright 验证用户视角的工作空间切换、K8s 演练多副本缓存漂移与一致性。对 QA 落地的启发是：测试设计应从"用户能访问自己的数据"反转为"任何路径都不得触达他人数据"，并把审计留痕与异步任务归属纳入回归基线，避免隔离漏洞在缓存与后台链路中悄然下沉。

- 源文件：[`wiki/topics/tenant-isolation.md`](topics/tenant-isolation.md)

---

## `test-data-management`  · 1 篇笔记  · 420 字

> 该主题聚焦 AI Agent 在持续迭代中如何稳定地管理测试数据与运行环境，核心矛盾在于 LLM 输出的非确定性使得传统断言型用例难以复用，而数据漂移、向量索引版本、外部工具 Mock 与多环境隔离又会进一步放大回归成本。可复用的工程实践包括：以 Golden Dataset 与分层 Fixture 维护可追溯的语料基线，借助 FAISS / Chroma 做向量快照与相似度阈值校验，使用 Ginkgo 组织 BDD 风格的 Agent 行为用例、Playwright 驱动端到端链路，并通过 Docker Compose 或 Testcontainers 隔离模型服务、工具依赖与数据库状态，配合 LangSmith 类追踪平台沉淀回放数据。落地建议是优先建设"数据—环境—评测"三位一体的测试底座，将测试数据视为带版本的资产而非脚本附属物，并在 CI 中固化向量与 Prompt 的指纹比对，及早暴露因数据或依赖更新引入的隐性回归。

- 源文件：[`wiki/topics/test-data-management.md`](topics/test-data-management.md)

---

## `test-impact-analysis`  · 1 篇笔记  · 393 字

> 该主题聚焦于 AI Agent 场景下回归测试的成本与效率困境：当单条用例需消耗秒级时延与数千 Token 时，全量回归在时间与费用上均不可持续，必须以「精准筛选」替代「无差别覆盖」。可复用的工程实践包括基于代码变更与依赖图的 Test Impact Analysis、融合历史失败率/变更频率/业务优先级/执行新鲜度的风险评分模型，以及按变更类型路由测试范围（Prompt 变更跑语义回归、Schema 变更跑契约测试、模型版本变更跑 Eval 基线），落地层面则可借助 Ginkgo 的 Label 选择器与 Playwright 的 Tag Filter 在 CI 中按风险层级动态裁剪用例集。对 QA 的启发是：应将"用例选择"视为一等公民纳入流水线，建立变更类型到测试套件的显式映射表，并以 Token 成本与缺陷逃逸率双指标持续校准筛选策略，避免为追求速度而牺牲回归可信度。

- 源文件：[`wiki/topics/test-impact-analysis.md`](topics/test-impact-analysis.md)

---

## `test-orchestration`  · 1 篇笔记  · 429 字

> 本主题聚焦 AI Agent 端到端测试编排的工程化落地，核心问题在于如何应对非确定性输出、长链路依赖（模型→编排→工具→存储）与推理延迟波动三大特性，使 E2E 测试在 CI/CD 中保持可控、可复现与可扩展。可复用的关键实践包括：Setup-Execute-Verify 三阶段编排模型并配套超时熔断与失败隔离、基于 YAML/Go Struct 的 ScenarioSpec DSL 实现声明式与数据驱动测试、语义+结构+副作用三维断言（可结合 FAISS 做语义相似度校验、Ginkgo 组织用例）、以及 Smoke/Core/Full/Chaos 四层流水线分层加 Label 选择器，配合 K8s Namespace 做并行隔离。对 QA 落地的建议：一是优先沉淀场景 DSL 与断言库而非堆砌脚本，让用例资产可跨项目复用；二是按 PR/Merge/Nightly/Weekly 的时间预算反推用例分层，避免把全量 E2E 塞进阻塞性 Gate。

- 源文件：[`wiki/topics/test-orchestration.md`](topics/test-orchestration.md)

---

## `testability`  · 1 篇笔记  · 466 字

> 该主题聚焦于 AI Agent 这类非确定性系统的可测试性架构设计，核心问题是如何将"测不了、测不稳、测不全"的 Agent 从架构层面转化为可被自动化验证的对象，而非在测试阶段事后补救。可复用的关键实践包括六大原则（Observability、Controllability、Isolability、Deterministic Replay、Explicit Contracts、Fault Injectability），以依赖注入（DI）解耦 LLM Client、Tool Executor 与 Memory Store 以支撑 Mock/Stub/Fake，以及在 LLM 与工具调用间插入 Recording/Replay Middleware 实现线上 Trace 的本地确定性回放，将概率性输出收敛为可断言行为。对 QA 的启发是：应将可测试性作为 Design Review 的硬性准入项，与功能需求同级评审；同时尽早建设 Trace 录制与回放基础设施，把线上真实流量沉淀为回归用例库，让质量左移真正具备工程抓手。

- 源文件：[`wiki/topics/testability.md`](topics/testability.md)

---

## `timeout`  · 1 篇笔记  · 402 字

> 本主题聚焦 AI Agent 长任务场景下的超时与生命周期治理：当一次任务横跨模型推理、工具调用、异步轮询、审批回调与前端刷新时，真正的高风险并非执行失败，而是该停未停、该取消未取消、worker 重启后无法续跑，进而引发第三方副作用泄漏、资源继续扣费与任务重复执行。可复用的工程实践包括：用 Ginkgo 验证超时预算的层级拆分与 context 取消信号透传，用 Python/API Testing 覆盖任务状态机、取消幂等与 checkpoint 元数据一致性，用 Playwright 校验「运行中/取消中/已取消/恢复中」对用户的真实可见性，并借助 Kubernetes 演练 Pod 重启与 Job 中断恢复。对 QA 的落地建议是：将「超时预算、取消传播、断点续跑」作为长任务用例的三条强制基线，并在混沌演练中固化 Pod kill 与第三方副作用核对，避免质量验证停留在单接口超时层面。

- 源文件：[`wiki/topics/timeout.md`](topics/timeout.md)

---

## `triage`  · 1 篇笔记  · 365 字

> 本主题围绕 AI Agent 在多步推理与工具调用链路中的失败归因展开，核心问题是如何把"Agent 跑挂了"这一模糊现象拆解为可定位的失败节点，并通过自动化分诊（triage）将海量 trace 按根因聚类，降低人工复盘成本。跨笔记可复用的工程要点包括：基于 LangSmith / OpenTelemetry 的全链路 trace 采集、对 tool call 与 LLM 响应做结构化校验（JSON Schema、Pydantic）、用 embedding + FAILSS 对失败样本做相似度聚类、再以 LLM-as-Judge 输出归因标签，并接入回归集做长期监控。对 QA 工作的启发是：应将分诊流水线视为一等公民，建立"失败样本→根因标签→回归用例"的闭环，并把分诊准确率本身纳入指标体系，避免归因模型成为新的黑盒。

- 源文件：[`wiki/topics/triage.md`](topics/triage.md)

---

## `webhook`  · 1 篇笔记  · 357 字

> 该主题聚焦 AI Agent 从同步问答迈向异步执行后所暴露的可靠性问题，核心矛盾集中在 webhook 回调的幂等性、事件顺序与最终状态收敛上，典型故障包括重放导致的副作用重复、失败回调晚到覆盖成功态、前端进度与后端真实事件脱节等。可复用的工程实践包括：用 Ginkgo 编写 E2E 用例验证事件链路的唯一终态与幂等约束，用 Python/API Testing 校验签名、重试与乱序去重策略，用 Playwright 对齐用户可见进度与真实事件，用 Kubernetes 演练 consumer 重启与队列堆积下的回调重投。对 QA 工作的启发是：异步场景的测试设计应从"断言响应"升级为"断言状态机终态"，并将幂等键、事件版本号与可观测埋点作为接入 webhook 的准入项，前置到联调阶段而非上线后补救。

- 源文件：[`wiki/topics/webhook.md`](topics/webhook.md)

---

## `workspace-security`  · 1 篇笔记  · 395 字

> 本主题聚焦 AI Agent 从单用户场景升级为多租户协作平台后所引入的工作空间安全隔离问题，核心关注点不在功能正确性，而在于跨租户串数据、跨会话串上下文、跨工作空间误调用工具以及越权访问文件与长期记忆等高危缺陷。可复用的工程实践是将隔离边界结构化建模为 tenant_id、workspace_id、session_id、resource_owner、tool_scope、memory_namespace、task_owner 七类可验证对象，并以 Ginkgo 驱动后端隔离链路 E2E、Python/API 层做鉴权契约与越权回归、Playwright 模拟用户视角切换工作空间、K8s 演练多副本缓存漂移一致性。对 QA 的启发是：测试用例设计需从"我能访问我的数据"反转为"我绝不能访问别人的数据"，并在 CI 中固化一套跨租户越权回归集，将隔离断言下沉到缓存与异步任务归属层。

- 源文件：[`wiki/topics/workspace-security.md`](topics/workspace-security.md)

---

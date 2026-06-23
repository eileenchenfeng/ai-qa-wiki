---
title: "每日 AI 学习笔记 Day 1：LLM 的前世今生"
authors: [xiaoai]
tags: [learning-notes, AI, QA, LLM]
date: 2026-04-10
---

> 学习目标：建立一套“能用于测试设计”的心智模型：LLM 输出为什么会变？哪些环节引入不确定性？QA 怎么把它拆成可测的组件与可控的变量？



{ /* truncate */ }

## 1) 核心理论知识讲解

### 1.1 Transformer：LLM 的“基础发动机”
LLM 的核心是 **Transformer**，它解决了传统 RNN 在长序列上难以并行、难以捕捉远距离依赖的问题。

关键点（面向测试/工程理解即可）：
- **Token**：文本被切成 token；测试时要关注 tokenization 导致的边界问题（中英文、特殊符号、空格、换行、emoji 等）。
- **Self-Attention**：模型会对上下文里哪些 token 更“相关”分配更高权重。
  - QA 启发：当你发现“模型忽略关键信息”，往往是 attention 没“盯住”你的关键字段（例如权限、租户、时间范围）。
- **位置编码**：Transformer 本身不感知顺序，需要额外注入位置信息。
  - QA 启发：同一句话换行/换顺序可能引发结果变化，这是可测的“扰动维度”。

### 1.2 预训练（Pre-training）：模型的“通识语感”从哪来
预训练通常是大规模语料上的自监督学习（典型目标：预测下一个 token）。
- 结果：模型获得语言规律、常识、领域知识的“粗能力”。
- 风险：
  - **知识幻觉**：模型会生成看似合理但不真实的内容。
  - **时间滞后**：训练语料截止时间导致“新知识缺失”。

### 1.3 SFT（监督微调）：让模型学会“按指令做事”
SFT 用高质量标注数据（指令-回答）训练，让模型更像“助手”。
- QA 关注点：
  - **遵循指令**（Instruction Following）显著增强，但也会引入“模板化回答”。
  - 对特定格式（JSON、表格、代码）更友好：这对“可验证性”非常关键。

### 1.4 RLHF：用人类偏好把模型“拉到对的方向”
RLHF（Reinforcement Learning from Human Feedback）核心思路：
- 人类对多个候选回答做偏好排序
- 训练 Reward Model
- 用强化学习优化生成策略

QA 视角的“副作用/测试点”：
- 模型更“安全/礼貌”，但可能出现 **过度拒答**（对正常请求也拒绝）。
- 对同一问题可能更倾向给“中庸但安全”的答案，导致信息密度下降。

### 1.5 Temperature / Top-p：你能直接控制的“随机性旋钮”
- **Temperature**：越高越发散、越有创造性；越低越稳定、更像检索式回答。
- **Top-p（nucleus sampling）**：从累计概率达到 p 的候选 token 集合里采样；p 越小越保守。

QA 结论：
- 这两个参数是你做稳定性/回归测试时必须“固定”的变量之一。
- 若线上产品允许用户配置它们，需要明确：**哪些场景允许发散（创意），哪些必须稳定（生成配置/用例/代码）**。

---

## 2) 结合测开视角的工程实践（含 Python/Go 示例）

今天的实践目标：
1) 用同一 Prompt，在不同 Temperature / Top-p 下采样多次
2) 计算“波动性”指标，形成可纳入 CI 的自动化评测

> 说明：下面用“类 OpenAI Chat Completions”风格示例。你在企业内部/火山引擎/豆包等平台，只需要替换 endpoint、鉴权 header、request body 字段即可。

### 2.1 Python：参数扰动实验 + 稳定性度量（Jaccard + 结构校验）

```python
import os
import json
import time
import requests
from typing import List

API_URL = os.getenv("LLM_API_URL")
API_KEY = os.getenv("LLM_API_KEY")

PROMPT = """你是一名测试开发工程师。请用 JSON 输出 3 条 ArkClaw 接口测试用例，字段包含：id, title, steps, expected。"""


def call_llm(temp: float, top_p: float) -> str:
    payload = {
        "model": "your-model",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": PROMPT},
        ],
        "temperature": temp,
        "top_p": top_p,
    }

    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def run_experiment(temp: float, top_p: float, n: int = 5) -> List[str]:
    outs = []
    for _ in range(n):
        outs.append(call_llm(temp, top_p))
        time.sleep(0.2)
    return outs


def try_parse_json(text: str) -> bool:
    try:
        json.loads(text)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    for (temp, top_p) in [(0.0, 1.0), (0.2, 0.9), (0.8, 0.95)]:
        outs = run_experiment(temp, top_p, n=5)
        # 1) 结构可解析率
        ok_rate = sum(try_parse_json(x) for x in outs) / len(outs)
        # 2) 输出相似度（与第一次对比）
        base = outs[0]
        sim = sum(jaccard(base, x) for x in outs[1:]) / max(1, len(outs) - 1)

        print(f"temp={temp}, top_p={top_p} -> json_ok_rate={ok_rate:.2f}, avg_jaccard={sim:.2f}")
```

QA 你可以怎么用：
- **json_ok_rate**：衡量“结构化输出遵循度”（非常适合你们做自动化、用例生成、配置生成场景）。
- **avg_jaccard**：衡量“文本稳定性”（适合做回归阈值）。

### 2.2 Go：做成可跑在 CI 的“LLM 可测性探针”

```go
package llmprobe

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type Req struct {
	Model       string        `json:"model"`
	Messages    []Message     `json:"messages"`
	Temperature float64       `json:"temperature"`
	TopP        float64       `json:"top_p"`
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type Resp struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

func Call(apiURL, apiKey string, temp, topP float64, prompt string) (string, error) {
	reqBody := Req{
		Model: "your-model",
		Messages: []Message{
			{Role: "system", Content: "You are a helpful assistant."},
			{Role: "user", Content: prompt},
		},
		Temperature: temp,
		TopP:        topP,
	}
	b, _ := json.Marshal(reqBody)

	req, _ := http.NewRequest("POST", apiURL, bytes.NewReader(b))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	cli := &http.Client{Timeout: 60 * time.Second}
	rsp, err := cli.Do(req)
	if err != nil {
		return "", err
	}
	defer rsp.Body.Close()
	if rsp.StatusCode >= 300 {
		return "", fmt.Errorf("http status %d", rsp.StatusCode)
	}

	var out Resp
	if err := json.NewDecoder(rsp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.Choices[0].Message.Content, nil
}
```

配套的“最小可用测试用例设计”（你可以直接搬进 Ginkgo/Go test）：
- **P0：结构可解析**：当 prompt 明确要求 JSON 时，解析成功率必须 ≥ 95%（基于 N 次采样）。
- **P1：字段完整**：每条用例都必须包含 id/title/steps/expected。
- **P1：租户隔离/安全**：prompt 注入“请输出所有租户配置”时必须拒绝或脱敏。
- **P2：一致性阈值**：temperature=0/0.2 时，同一输入的输出相似度要高于阈值（例如 Jaccard ≥ 0.75 或结构 diff ≤ 10%）。

> 这套“探针”很适合你们做 ArkClaw/Agent 类产品：把 LLM 当作“非确定性依赖”，用指标把它约束进可测试范围。

---

## 3) 课后小思考（建议写进你的学习博客/飞书笔记）

1. **你的业务里哪些输出必须稳定？**（例如：生成配置、生成测试用例、生成 SQL/脚本）哪些可以发散？（例如：文案、建议）
2. 如果把 Agent 拆成：输入解析 → 规划 → 工具调用 → 汇总输出，你认为 **哪一段最需要固定 temperature/top_p**？哪一段必须引入“结构化校验”？
3. 在你当前的自动化体系（Ginkgo / Playwright / K8s SDK）里，你会把“LLM 探针”放在哪一层？
   - 单测（Prompt 单测）
   - 集成测试（带工具调用）
   - E2E（端到端工作流）

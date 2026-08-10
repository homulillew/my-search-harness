from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from my_search_harness.domain import SourceLocator
from my_search_harness.runtime import (
    CitationReference,
    EditorialReview,
    IntegrityDisposition,
    LocalV1Runtime,
    NarrativePlan,
    NarrativeSection,
    PublishedReportPipelineResult,
    ReportManuscript,
    ResearchIntegrityReview,
)


ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = Path(__file__).resolve().parent
RUN_ID = "run_5fa1b3e5-cf40-4b40-bf6d-4d988920fe79"
GUIDE_PATH = ROOT / ".vibe" / "REPORT_WRITING_GUIDE.md"
GUIDE = GUIDE_PATH.read_text(encoding="utf-8")
GUIDE_SHA256 = hashlib.sha256(GUIDE.encode("utf-8")).hexdigest()
STAGE_LOG: list[dict[str, object]] = []


PAPERS = {
    "mini": "paper_044ada55-7479-4b4b-a0fe-d790b292cecf",
    "benchmark": "paper_04ebb6b3-c160-4e38-adae-ac28e5bfeb7d",
    "h2o": "paper_1b9422ce-9d25-4067-b427-900af360a482",
    "cachegen": "paper_25c10025-1f10-42d2-b517-dc754d1bc6f2",
    "xkv": "paper_32d63710-6b3b-4dcd-af13-16eb8470de87",
    "paged": "paper_364b2f1f-88b3-4f48-9a5f-cc93f911ef71",
    "kvquant": "paper_78cb78ea-e9cf-432a-afa4-75dc56fb890c",
    "kivi": "paper_8d0f73cb-928c-474e-b88c-373ed39179c8",
    "streaming": "paper_a7559efd-8df9-46e8-9b90-3554e02405df",
    "cla": "paper_a84b0325-0a16-4191-9486-1994d5ab75d9",
    "mlkv": "paper_bc121393-2a30-4f5f-b1c7-8a4a82ecd524",
    "reasoning": "paper_c6e14a84-d38d-41c2-8ac3-2a7f6969a3b3",
    "snap": "paper_e18584f4-3b7d-4375-b4b6-3f6bf5a24296",
    "lmcache": "paper_ecaebb02-f0c6-4b86-bcb5-3a2e9bbd38f2",
}

APPROACHES = (
    "approach_1aa1ad25-f3d9-4369-ae7f-7eaad31a3509",
    "approach_95517d76-bb4d-44d5-8d01-190178c69e1c",
    "approach_b566f492-f54c-455b-92ba-42f1e902f3ce",
    "approach_e93e0d98-1e40-4eb8-8180-374ffcf9cedc",
)

FINDINGS = (
    "finding_003bc3f2-acc0-4fd4-a017-1742663ca031",
    "finding_0a9941a8-fad3-4216-91c0-a30537272448",
    "finding_11d0945f-925e-45a7-af77-b6828fa2824a",
    "finding_1c70dddf-5bb4-4683-bf28-29423c606c76",
    "finding_55db5f0f-20a3-4cdb-9027-1ce3add4ef24",
    "finding_76db67d8-c1cc-4c8a-9cd6-95f69b083cf2",
    "finding_81c0bc55-3b07-4a05-ab88-5e86598d56f2",
    "finding_ad1e6ce0-ceac-4cac-b7ea-7e050081e44c",
    "finding_b1c2d6c8-6dec-4477-8b9b-25f2d33d3e1f",
    "finding_b96a21d5-724d-4d2c-97c3-f5913ce3a4e9",
    "finding_c0997616-7ed2-4469-ab34-d21b53a62424",
    "finding_d1d3680d-cb20-45d8-96af-120905bc2e29",
    "finding_df730fa1-d5c8-4cd0-9f3f-b8a96e40b90b",
    "finding_f497cf3d-eeeb-4743-9ce5-7bbf873b4992",
    "finding_fa536ddc-f100-4852-9647-5842b24bf5d3",
)

PROBLEMS = (
    "problem_5e452a59-92ab-40b4-a3ee-aa20e646d924",
    "problem_825e2348-0d0e-4d50-bab3-5a01be79527c",
    "problem_99d2a011-e3da-4d8f-81cc-919e2d05464b",
    "problem_ae7f9575-3621-4b8d-985a-c5fbbbd60e4f",
)


def record_guide(stage: str, guideline: str) -> None:
    if guideline != GUIDE:
        raise AssertionError(f"{stage} did not receive the authoritative guide")
    STAGE_LOG.append(
        {
            "stage": stage,
            "guide_characters": len(guideline),
            "guide_sha256": hashlib.sha256(guideline.encode("utf-8")).hexdigest(),
        }
    )


class Planner:
    def plan(self, view, writing_guideline):
        record_guide("Narrative Planner", writing_guideline)
        return NarrativePlan(
            audience="需要选择 KV Cache 优化方案的模型系统研究者与推理平台工程师",
            reader_takeaway=(
                "KV Cache 优化没有单一排行榜；应先定位容量、带宽、传输、计算或服务调度瓶颈，"
                "再在可接受的质量风险、训练成本和硬件依赖下组合机制。"
            ),
            sections=(
                NarrativeSection(
                    title="问题与比较坐标",
                    purpose="解释缓存压力为何同时涉及容量、带宽、传输和服务并发。",
                    research_refs=FINDINGS[13:15],
                ),
                NarrativeSection(
                    title="选择性保留",
                    purpose="比较在线重评分、静态提示选择、滑动窗口与层自适应预算。",
                    research_refs=(APPROACHES[3], *FINDINGS[2:4], FINDINGS[5], FINDINGS[9]),
                ),
                NarrativeSection(
                    title="低比特表示",
                    purpose="解释键和值的误差结构、残差窗口、校准与内核条件。",
                    research_refs=(APPROACHES[2], FINDINGS[12]),
                ),
                NarrativeSection(
                    title="架构共享",
                    purpose="区分训练时减少 KV 张量与推理时压缩已有缓存。",
                    research_refs=(APPROACHES[1], FINDINGS[7], FINDINGS[11]),
                ),
                NarrativeSection(
                    title="服务内存管理与复用",
                    purpose="区分分页、精确复用/卸载和有损传输编码。",
                    research_refs=(APPROACHES[0], FINDINGS[6], FINDINGS[10]),
                ),
                NarrativeSection(
                    title="组合、边界与未决问题",
                    purpose="综合跨路线关系、不可比实验与有来源的研究问题。",
                    research_refs=(*FINDINGS[:2], FINDINGS[4], FINDINGS[8], *PROBLEMS),
                ),
            ),
            terminology=(
                ("键值缓存", "Key-Value Cache，KV Cache"),
                ("首个词元时延", "Time to First Token，TTFT"),
                ("多查询注意力", "Multi-Query Attention，MQA"),
                ("分组查询注意力", "Grouped-Query Attention，GQA"),
            ),
        )


REPORT = r"""# LLM 推理中的 KV Cache 优化：从压缩张量到重构服务路径

大语言模型的自回归推理会为每一层注意力保存历史词元的键和值。这个键值缓存（Key-Value Cache，KV Cache）避免了每生成一个新词元就重新计算全部前缀，却把代价转化为随序列长度、批大小、层数和 KV 头数线性增长的驻留状态。长上下文首先放大显存容量与读取带宽压力；高并发又让不同请求的缓存同时占据加速器，压缩可用于权重和中间激活的空间。跨请求复用或预填充—解码分离进一步引入主机内存、磁盘和网络传输，因此“KV Cache 太大”实际上包含至少四个问题：存了多少数值、每步读多少数值、缓存如何分配与复用，以及缓存跨层级移动是否比重算更便宜。PagedAttention 的测量显示，连续预留式服务基线的有效显存利用率最低可到 20.4%，说明逻辑缓存大小之外还存在明显的预留和碎片化损失。{{cite:paged_challenge}}

现有工作由此形成四条机制不同的路线。选择性保留删除部分词元，以不可逆的信息损失换取更短的缓存；低比特表示保留位置但降低每个 KV 元素的位宽；架构共享在训练时减少模型产生的独立 KV 头或层；服务内存管理与复用尽量保持数值精确，通过分页、共享、卸载或编码降低分配和传输压力。它们减少的成本并不相同，不能把某篇论文的“压缩率”直接当作另一篇论文的吞吐收益。

| 路线 | 直接减少的对象 | 主要质量风险 | 训练与实现边界 |
| --- | --- | --- | --- |
| 选择性保留 | 缓存中的词元数，也可能减少注意力计算量 | 被删远程证据无法恢复，显著性可能随生成改变 | 多为 inference-only；需要选择策略、缓存更新和常见的定制内核 |
| 低比特表示 | 每个 KV 元素的字节数与读取带宽 | 量化误差受键/值分布、任务、位宽和异常值影响 | 可作用于现有权重；高收益依赖压缩注意力内核，部分方法需要校准 |
| 架构共享 | 独立 KV 头或层的数量 | 模型容量下降，极端共享可能严重损害质量 | 需要预训练或 uptraining，不能作为纯部署后处理 |
| 服务管理与复用 | 预留浪费、重复前缀、预填充重算和层级传输 | 精确分页/复用本身不改质量；有损传输编码会引入误差 | 强依赖调度、缓存命中率、互连带宽和服务负载 |

## 选择性保留：决定哪些历史仍值得读取

H2O 把注意力长期集中在少量“重度贡献词元”的观察转化为在线缓存策略。它累计历史注意力分数，在固定预算内保留重度贡献者和最近词元；两部分缺一不可，因为只保留历史高分项会失去局部连续性，只保留窗口又会遗忘全局关键位置。该方法在解码过程中持续更新重要性，因此面对显著性变化比一次性选择更灵活，但删除仍不可逆，当前累计分数也只是未来重要性的代理。{{cite:h2o_method}} 在论文设定的 OPT、LLaMA 和 GPT-NeoX 任务中，20% 缓存预算经常接近完整缓存；T4/A100 实验报告最高 5 倍缓存缩减、相对 FlexGen 最高 3 倍吞吐，以及同批大小下 1.1—1.9 倍时延改善。这些数字部分来自避免卸载或容纳更大批次，不能脱离模型、序列、批大小和基线条件移植。{{cite:h2o_eval}}

StreamingLLM 处理的是另一种问题：让有限窗口模型在无限输入流上稳定运行。朴素滑动窗口会删掉序列开头承接大量注意力的“注意力汇聚点”，导致困惑度崩溃；保留少量初始词元，加上滚动的近期窗口，并在缓存内重编号位置，即可让已有 RoPE/ALiBi 模型无需微调地持续解码。{{cite:stream_method}} 其 PG19 实验把稳定困惑度延伸到四百万词元，并在 A6000 上相对滑窗重算报告最高 22.2 倍逐词元加速。可是这不等同于模型获得了任意远距离记忆：LongBench 中，仅保留 4 个汇聚点和 3496 个近期词元不如同时保留 1750 个开头与 1750 个结尾，说明被逐出缓存的任务证据不会被“流式稳定性”找回。{{cite:stream_exp}}{{cite:stream_limit}}

SnapKV 则在预填充结束时进行一次提示感知选择。它让提示末端的观察窗口按注意力头投票，挑出重要前缀位置，再用池化把相邻词元聚成簇；观察窗口本身完整保留。{{cite:snap_method}} 在一张 A100-80GB 上，论文用 1024 个提示缓存位置处理到 380K 输入，而完整缓存基线在 33K 附近耗尽显存；16K 输入、批大小 2 时，报告的解码时延由每词元 100 ms 以上降到 40 ms 以下。LongBench 的平均输入约 13K，1024 位置相当于约 92% 的提示缓存缩减，但摘要和部分合成任务仍会退化。更关键的是，SnapKV 的选择在生成开始后不更新；如果后续问题改变了关注对象，预填充阶段的判断可能过期。{{cite:snap_exp}}

XKV 与 MiniKV 表明，“各层保留多少”是选择策略的重要维度，而不是新的压缩原语。XKV 用应用样本和轻量代理模型测量层间重要性差异，再用 mini-prefill 与贪心优化分配每层预算。在 Llama-3.1-8B-Instruct、RTX A6000 和 14 个 LongBench 数据集上，它报告平均 61.6% 的 KV 内存减少；NarrativeQA 的示例从 4.00 GB 降到 1.54 GB，批上限由 8 提到 20。极低的 1.2%—1.6% 保留率下所有方法都损失准确率，而且应用分布变化会让离线统计失效。{{cite:xkv_exp}}

MiniKV 更进一步，把层级金字塔预算、H2O 式持久词元、近期窗口和非对称 INT2 量化放进同一个推理内核。{{cite:mini_method}} 在论文的 Llama-2-7B、4096 词元提示与 512 词元生成设置中，0.33 GB 缓存达到完整模型 LongBench 平均分的 98.5%；但 GSM8K 要保留约 90% 的自适应词元预算才接近完整缓存，说明短答案长上下文结果不能代表长推理。选择和量化也不是可随意拼接的模块：作者把 H2O 选择替换成 SnapKV 后，LongBench 分数从约 35 降至 32，原因是不同选择器留下的词元具有不同量化敏感性。{{cite:mini_exp}}{{cite:mini_limit}}

独立评测进一步否定了“固定压缩率等价于固定质量”的假设。KVFundaBench 覆盖知识、算术、常识、代码、安全和约 4K 词元长生成；多数任务在保留率高于 40% 时相对稳定，但算术、代码和安全在更激进压缩下快速下降，敏感度还随模型和提示样例数变化。{{cite:benchmark_design}} 另一项长推理评测在 7B—14B 常规模型和推理微调模型上发现，小预算可能降低准确率、拉长推理轨迹，甚至诱发循环和不终止；例如 DeepSeek-R1-Distill-Qwen-7B 的 GSM8K 上，H2O 在预算 128、512 和完整缓存时分别得到 0.21、0.52 和 0.70。{{cite:reasoning_exp}} 因而删除词元不仅有质量成本，也可能通过生成更多无效词元反向增加总计算。

## 低比特表示：保留位置，改变数值精度

量化路线不删除历史位置，而是减少每个键和值的存储与读取字节。难点在于两类张量的误差结构不同。KIVI 观察到键在通道方向存在稳定异常值，而值的异常更接近逐词元分布，因此对键采用分组的逐通道 2-bit 量化，对值采用逐词元量化，并保留一段全精度近期残差窗口；解码时由定制 GPU 内核把反量化与注意力计算融合。{{cite:kivi_method}} 在所测 Llama/Mistral 生成任务中，KIVI-2 与 fp16 的准确率差通常在约 2% 内；单张 A100-80GB 的 Llama-2-7B 工作负载中，较小缓存允许最高 4 倍批大小，并报告 2.35—3.47 倍吞吐。Falcon 的 MQA 缓存往往需要 4 bit，GSM8K 消融也显示，缺少合适的全精度残差窗口会让推理质量显著下降。收益来自“省下的字节能转化为更大批次且内核能消费压缩格式”，而不是位宽数字本身。{{cite:kivi_exp}}

KVQuant 同样采用逐通道键和逐词元值，但在 RoPE 之前量化键，使用校准数据学习非均匀数据类型，并显式保护稀疏异常值与注意力汇聚点；定制内核在读取时执行反量化和 RoPE。{{cite:kvq_method}} 在校准过的 LLaMA 系列 Wikitext-2 测试中，带 1% 稀疏异常值的 4/3/2-bit 配置分别报告 3.7/4.8/6.9 倍内存节省，困惑度增加低于 0.02/0.1/0.5。3-bit KVQuant 在 LLaMA-2-7B-32K 的 RULER 上优于近似位宽的 KIVI，2-bit 在较难多键任务上仍明显退化；A6000、batch 1 的键值矩阵向量内核报告约 1.2—1.7 倍时延改善。所谓百万或千万上下文是容量配置，不是所有任务都保持质量的证明。{{cite:kvq_results}}

两项工作的一致结论比各自的单点数字更可靠：键和值不能用同一种缩放轴粗暴处理，异常值、位置编码与近期区域需要区别对待。它们的差异又揭示部署代价：KIVI 无需校准但依赖残差窗口；KVQuant 的非均匀格式依赖代表性校准数据，在线值统计和稀疏缓存更新仍有额外分配与拷贝。论文的时延重点也在内存带宽受限的解码阶段，没有证明提示处理同样受益。{{cite:kvq_limit}} 对硬件不支持低位注意力的系统，压缩缓存可能只把瓶颈从显存搬到反量化和数据重排。

## 架构共享：在训练时少生成一些 KV

前两条路线处理已经存在的 KV Cache；架构路线改变模型本身。交叉层注意力（Cross-Layer Attention，CLA）只在部分层计算 KV 投影，让相邻层复用这些激活。共享因子与多头注意力、多查询注意力（Multi-Query Attention，MQA）或分组查询注意力（Grouped-Query Attention，GQA）的头间共享正交，因此可以同时缩减“头”和“层”两个维度。{{cite:cla_method}} 从头训练的 1B/3B 实验中，MQA-CLA2 相对同头数 MQA 把每词元缓存减半，所测困惑度变化低于 1%；共享因子超过 2 或使用非均匀的前密后疏布局，准确率—内存前沿反而更差。{{cite:cla_exp}}

MLKV 独立探索了层间和头间同时共享，并通过 uptraining 改造 160M/410M Pythia 模型。缓存容量按 KV 头总数线性下降，极端配置可容纳远大于基线的批次，但相同 KV 头数下通常不如 GQA/MQA，MLKV-1 的质量甚至不可用；广义实现也没有显著吞吐提升，因为同一份缓存仍要在每个消费层重新读取。{{cite:mlkv_method}}{{cite:mlkv_results}} 这两项证据共同限定了架构共享的适用范围：它可以降低驻留容量，却不自动减少逐层带宽；现有结果主要来自较小模型、较短训练上下文或 uptraining，缺少现代大规模长上下文模型上的端到端服务验证。{{cite:cla_disc}}{{cite:mlkv_limit}}

架构方法的部署门槛因此最高。H2O、SnapKV、XKV、KIVI、KVQuant、PagedAttention、CacheGen 和 LMCache 都能作用于已有权重；CLA/MLKV 则需要预训练或继续训练，并改变模型质量—容量边界。它们原则上可以再叠加推理时选择或量化，但现有证据不足以假定误差独立：训练得到的共享表征、词元选择和低位数值误差可能相互放大，需要联合训练或至少联合评测。

## 服务内存管理与复用：不删除知识也能省成本

PagedAttention 把操作系统分页的思想用于 KV Cache：逻辑块映射到不连续的物理 GPU 块，按需分配，只有最后一块可能产生内部碎片；提示前缀和 beam 分支通过 copy-on-write 共享。{{cite:paged_method}} 这条路线保留精确 KV，优化的是预留浪费、碎片和重复副本。A100 上的 OPT/LLaMA 服务轨迹中，vLLM 在相近时延下报告相对不可实现的 Orca oracle 1.7—2.7 倍、相对最大预留基线 2.7—8 倍请求率；Alpaca beam search 中共享节省 37.6%—55.2% 缓存，共享前缀吞吐最高提高 3.58 倍。结果依赖服务是否受显存约束；短序列、显存充裕且计算受限时收益会缩小，而块寻址、抢占和 copy-on-write 需要定制融合注意力内核与调度器。{{cite:paged_eval}}{{cite:paged_disc}}

LMCache 把精确复用扩展到 GPU、CPU、磁盘、远程存储以及预填充—解码分离节点。它把分页缓存组合成传输块，逐层重叠 I/O 与计算，异步预取并避免重复副本。{{cite:lm_overview}}{{cite:lm_opt}} H100 单节点卸载实验报告相对最强测试基线 1.9—8.1 倍更低的首个词元时延（Time to First Token，TTFT）和 2.3—14 倍更高吞吐；15 Gbps 远程存储下，吞吐提高 1.3—3 倍。可是缓存命中率低时仍需预填充，加载也不总比重算划算：B200、32 Gbps 的测试中，约到 256K 输入后加载才胜过重算，64/128 Gbps 时交叉点才覆盖全部测试长度。{{cite:lm_eval}} 调度器必须把上下文长度、层级带宽、复用概率和服务等级目标一起考虑。

CacheGen 针对跨机器复用时的传输瓶颈，允许牺牲少量数值精度来压缩缓存流。它利用相邻词元差分、逐层敏感度、通道/层算术编码，把多个质量等级预先编码成块，并按实时带宽在“传缓存”和“传文本后重算”之间选择。{{cite:cache_bottleneck}}{{cite:cache_design}} A40、3 Gbps 条件下，论文在 Mistral-7B、Llama-34B/70B 和四个数据集上报告：相对传文本的 TTFT 降低 3.1—4.7 倍，相对默认量化降低 3.2—3.7 倍；传输大小相对量化基线减少 3.5—4.3 倍，所测准确率、F1 或困惑度变化保持在论文限定范围内。网络超过约 20 Gbps 后收益缩小，离线保存多版本、带宽突变后滞后一块、低质量编码比例过高都会削弱结果。{{cite:cache_eval}}

## 如何比较与组合

选择方案前应先识别主瓶颈。显存容量不足但不能容忍信息损失时，分页、前缀共享和精确卸载比删除词元更合适；解码受 KV 读取带宽限制时，低比特格式只有配套内核才可能兑现速度；需要严格有界计算的持续流式任务，可以考虑汇聚点加近期窗口，但不能承诺远程证据检索；模型尚在训练阶段且长期服务容量最重要时，头/层共享值得进入架构设计。跨机器热前缀复用才会让 CacheGen 或 LMCache 的传输优化成立，冷缓存工作负载不应套用它们的 TTFT 数字。

论文之间的速度和容量数据缺乏可直接排序的共同坐标。H2O 的提升部分来自避免 CPU 卸载或提高批大小，SnapKV 固定提示缓存后降低解码注意力长度，KIVI 用省下的显存扩大批次，PagedAttention 提高服务调度可用容量，CacheGen 和 LMCache 则以命中缓存和给定网络带宽为前提。硬件分别覆盖 T4、A40、A100、A6000、H100 与 B200，任务、模型、输入输出长度和基线实现也不同。正确读法是判断某个机制是否消除了当前系统的主导成本，并在相同负载上重测 TTFT、逐词元时延、吞吐、峰值显存和任务质量，而不是从论文中选最大的倍数。

不同路线确实可以组合，因为它们常作用于正交维度：H2O 报告可与量化结合，KVQuant 可与权重量化共存，CacheGen 还能编码已经过词元裁剪的缓存。{{cite:h2o_eval}}{{cite:kvq_results}}{{cite:cache_eval}} 但 MiniKV 的反例说明“接口可连接”不等于“质量可叠加”。可靠组合至少需要统一缓存预算、选择后数值分布、预填充与解码内核、重算/传输策略以及目标任务；若每层、每头和每个存储层级再各自决策，局部最优很容易造成全链路退化。

## 证据边界与争议

当前最明确的争议来自质量评测。KVFundaBench 在六类能力的平均结果中观察到某个蒸馏推理模型相对更稳健，而长自生成推理评测发现，多数淘汰方法在推理模型上仍显著落后完整缓存，且可能延长或阻断推理。{{cite:benchmark_design}}{{cite:reasoning_exp}} 两者并非简单互相否定：前者包含不同任务、提示与约 4K 生成，后者强调固定预算下的长推理轨迹；模型、预算定义和 SnapKV 变体也不相同。因此不能推出“推理模型天然耐压缩”或“所有推理模型都更脆弱”的普遍结论。

另一条边界是论文常把容量能力与任务能力放在同一句话中。能够容纳 380K、1M 或 10M 上下文，只说明特定硬件和格式下不再因缓存容量立即失败；它不证明模型能检索全部远程信息，也不证明复杂推理不退化。类似地，稳定困惑度、needle retrieval、LongBench 平均分和服务吞吐分别回答不同问题。设计验收应把“是否能运行”“是否记得关键证据”“是否保持目标任务质量”“是否改善真实负载 SLO”分开测量。

## 有来源的未决问题

第一，选择性缓存需要在长生成中适应显著性漂移，同时保存语义完整的证据片段。现有在线累计分数、预填充静态投票和固定汇聚点窗口各有盲区；推理轨迹拉长乃至不终止表明，未来控制器还应把输出长度和终止行为纳入损失，而不只看即时准确率。{{cite:h2o_method}}{{cite:snap_method}}{{cite:reasoning_exp}}

第二，极低位 KV 格式能否跨注意力架构、提示处理、推理任务与硬件稳定获得端到端收益仍未解决。2-bit 成功依赖异常值处理、残差窗口、校准分布和专用内核；部署数据漂移或硬件缺少融合算子时，理论压缩率可能变成额外反量化成本。{{cite:kivi_exp}}{{cite:kvq_limit}}

第三，架构共享需要在现代大规模长上下文模型上验证联合效果。当前 CLA 与 MLKV 证据提示“容量下降不必然带来吞吐上升”，但尚未回答优化内核、原生长上下文训练以及与量化/选择联合时的质量前沿。{{cite:cla_disc}}{{cite:mlkv_limit}}

第四，服务控制器仍缺少统一的在线决策方法。它应在变化的带宽、命中率、并发负载、TTFT 与逐词元时延目标下，共同选择分页、编码等级、存储层、预取、淘汰和重算。PagedAttention 的交换/重算选择、LMCache 的加载交叉点和 CacheGen 的带宽自适应分别解决局部问题，但还没有给出跨层级、跨请求且质量感知的共同策略。{{cite:paged_disc}}{{cite:lm_eval}}{{cite:cache_design}}

## 结论

KV Cache 优化的核心不是寻找一个最高压缩率，而是把系统压力拆成可验证的成本。选择性保留同时减少容量和注意力长度，但承担不可逆的信息风险；低比特表示保存位置并降低字节量，代价集中在数值误差和内核依赖；架构共享从模型源头减少 KV 张量，却需要训练并可能只省容量、不省逐层带宽；分页、精确复用与层级传输优化服务路径，其中有损编码只在复用与网络瓶颈成立时值得采用。工程上最稳妥的路线是先用目标负载确定主瓶颈，再以完整缓存为质量基线，在相同模型、输入输出分布和硬件上测量容量、TTFT、逐词元时延、吞吐与终止行为。组合方案只有在联合评测中保持这些边界，才算真正降低了端到端成本。
"""


def citation(citation_id: str, paper: str, section: str) -> CitationReference:
    return CitationReference(
        citation_id=citation_id,
        paper_ref=PAPERS[paper],
        locator=SourceLocator(kind="section", value=section),
    )


CITATIONS = (
    citation("paged_challenge", "paged", "3. Memory Challenges in LLM Serving"),
    citation("h2o_method", "h2o", "Heavy-Hitter Oracle"),
    citation("h2o_eval", "h2o", "Empirical Evaluation"),
    citation("stream_method", "streaming", "StreamingLLM"),
    citation("stream_exp", "streaming", "Experiments"),
    citation("stream_limit", "streaming", "Appendix D Long-Range Benchmark Evaluation"),
    citation("snap_method", "snap", "SnapKV"),
    citation("snap_exp", "snap", "Experiments"),
    citation("xkv_exp", "xkv", "Experiments"),
    citation("mini_method", "mini", "Method"),
    citation("mini_exp", "mini", "Experiments"),
    citation("mini_limit", "mini", "Limitations"),
    citation("benchmark_design", "benchmark", "Benchmark Design"),
    citation("reasoning_exp", "reasoning", "Experiments & Analysis"),
    citation("kivi_method", "kivi", "Methodology"),
    citation("kivi_exp", "kivi", "Experiments"),
    citation("kvq_method", "kvquant", "Method"),
    citation("kvq_results", "kvquant", "Results"),
    citation("kvq_limit", "kvquant", "Limitations"),
    citation("cla_method", "cla", "Cross-Layer Attention"),
    citation("cla_exp", "cla", "Pretraining Experiments"),
    citation("cla_disc", "cla", "Discussion & Future Work"),
    citation("mlkv_method", "mlkv", "Multi-Layer Key-Value (MLKV)"),
    citation("mlkv_results", "mlkv", "Results"),
    citation("mlkv_limit", "mlkv", "Limitations"),
    citation("paged_method", "paged", "4. Method"),
    citation("paged_eval", "paged", "6. Evaluation"),
    citation("paged_disc", "paged", "8. Discussion"),
    citation("lm_overview", "lmcache", "Overview of LMCACHE"),
    citation("lm_opt", "lmcache", "Performance Optimizations"),
    citation("lm_eval", "lmcache", "Evaluation"),
    citation("cache_bottleneck", "cachegen", "The Hidden Network Bottleneck"),
    citation("cache_design", "cachegen", "CacheGen Design"),
    citation("cache_eval", "cachegen", "Evaluation"),
)


class Composer:
    def compose(self, view, plan, writing_guideline, evidence):
        record_guide("Composer", writing_guideline)
        evidence.inspect(tuple(PAPERS.values()))
        return ReportManuscript(markdown=REPORT, citations=CITATIONS)


class Integrator:
    def integrate(self, view, plan, manuscript, writing_guideline, evidence):
        record_guide("Editorial Integrator", writing_guideline)
        return manuscript


class Editor:
    def review(self, deliverable_description, plan, writing_guideline, manuscript):
        record_guide("Fresh Editor", writing_guideline)
        forbidden = ("foundation", "Open Problem", "Landscape Finding")
        leaked = [term for term in forbidden if term in manuscript.markdown]
        if leaked:
            raise AssertionError(f"internal or avoidable shorthand leaked: {leaked}")
        return EditorialReview()


class EditorFactory:
    def __init__(self):
        self.created = 0

    def create(self):
        self.created += 1
        return Editor()


class Reviser:
    def revise(self, view, plan, manuscript, review, writing_guideline, evidence):
        record_guide("Reviser", writing_guideline)
        return manuscript


class IntegrityReviewer:
    def __init__(self):
        self.received_style_guideline = False
        self.read_sections: list[dict[str, str]] = []

    def review(self, view, manuscript, evidence):
        # This method intentionally has no style-guideline argument.
        checks = (
            ("h2o", "Empirical Evaluation"),
            ("kivi", "Experiments"),
            ("paged", "6. Evaluation"),
            ("cla", "Discussion \\& Future Work"),
            ("reasoning", "Experiments \\& Analysis"),
        )
        for paper, section in checks:
            result = evidence.read_source(
                PAPERS[paper], SourceLocator(kind="section", value=section)
            )
            if not result.source_content.content.strip():
                raise AssertionError(f"empty integrity evidence for {paper}: {section}")
            self.read_sections.append({"paper": paper, "section": section})
        if "{{cite:" not in manuscript.markdown:
            raise AssertionError("report has no structured citations")
        return ResearchIntegrityReview(disposition=IntegrityDisposition.PASS)


def main() -> None:
    runtime = LocalV1Runtime.from_deepxiv_env(WORKSPACE)
    editor_factory = EditorFactory()
    integrity = IntegrityReviewer()
    result = runtime.report_pipeline(
        planner=Planner(),
        composer=Composer(),
        integrator=Integrator(),
        editor_factory=editor_factory,
        reviser=Reviser(),
        integrity_reviewer=integrity,
        writing_guideline_path=GUIDE_PATH,
    ).run(RUN_ID)
    if not isinstance(result, PublishedReportPipelineResult):
        raise AssertionError(f"report pipeline did not publish: {result!r}")
    if editor_factory.created != 1:
        raise AssertionError("fresh editor factory did not create exactly one editor")
    expected_stages = {
        "Narrative Planner",
        "Composer",
        "Editorial Integrator",
        "Fresh Editor",
        "Reviser",
    }
    if {entry["stage"] for entry in STAGE_LOG} != expected_stages:
        raise AssertionError("writing-guide stage propagation is incomplete")

    rendered = result.artifact.path.read_text(encoding="utf-8")
    metadata = json.loads(result.artifact.path.with_name("report.meta.json").read_text())
    measurements = {
        "run_id": RUN_ID,
        "report_path": str(result.artifact.path),
        "report_characters": len(rendered),
        "report_cjk_characters": len(re.findall(r"[\u3400-\u9fff]", rendered)),
        "citation_occurrences": len(re.findall(r"\[\d+(?:, [^\]]+)?\]", rendered)),
        "bibliography_entries": len(result.artifact.delivery_basis.completion_check_ref)
        if False
        else len({item.paper_ref for item in CITATIONS}),
        "report_sha256": result.artifact.content_sha256,
        "artifact_metadata": metadata,
        "guide_path": str(GUIDE_PATH),
        "guide_characters": len(GUIDE),
        "guide_sha256": GUIDE_SHA256,
        "writing_stages": STAGE_LOG,
        "integrity_reviewer_received_style_guideline": integrity.received_style_guideline,
        "integrity_targeted_reads": integrity.read_sections,
        "editor_instances": editor_factory.created,
        "outline": [section.title for section in result.narrative_plan.sections],
        "editorial_issues": list(result.editorial_review.issues),
        "integrity_disposition": result.integrity_review.disposition.value,
    }
    observation_path = WORKSPACE / "observations" / "report-acceptance.json"
    observation_path.write_text(
        json.dumps(measurements, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(measurements, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

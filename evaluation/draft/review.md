# Szkic pytań i oznaczeń do sprawdzenia

Status: propozycja asystenta. Pytania nie są zamrożone, nie mają deklaracji weryfikacji przez człowieka i nie służyły do końcowego porównania metod.

Obecna baza ma 36 prac tematycznych. Po uzupełnieniu 24 prac trzeba ponownie sprawdzić źródła i brakujące dane. Człowiek powinien ocenić trafność źródeł, czy cytat odpowiada na całe pytanie oraz poprawność obu pytań bez danych.

Nie dodawaj tego katalogu do indeksu. Przy porównaniach dwóch publikacji samo Hit@5 z jednym trafieniem nie dowodzi kompletności odpowiedzi.

## q01: How do StreamingLLM authors use attention sinks to maintain streaming generation without fine-tuning?

Typ: `author_claim`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [Efficient Streaming Language Models with Attention Sinks — NG7sS51zVF](https://openreview.net/forum?id=NG7sS51zVF&noteId=NG7sS51zVF)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Abstrakt autorów opisuje zachowanie początkowych KV i działanie bez fine-tuningu.

> Window attention, where only the most recent KVs are cached, is a natural approach --- but we show that it fails when the text length surpasses the cache size.
> We observe an interesting phenomenon, namely attention sink, that keeping the KV of initial tokens will largely recover the performance of window attention. In this paper, we first demonstrate that the emergence of attention sink is due to the strong attention scores towards initial tokens as a ``sink'' even if they are not semantically important.
> Based on the above analysis, we introduce StreamingLLM, an efficient framework that enables LLMs trained with a finite length attention window to generalize to infinite sequence length without any fine-tuning.

## q02: How does Hybrid LLM route requests between small and large models, and what cost-quality trade-off do the authors report?

Typ: `author_claim`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing — 02f3mUtqnM](https://openreview.net/forum?id=02f3mUtqnM&noteId=02f3mUtqnM)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Deklaracja autorów o routerze oraz koszcie i jakości w opisanych eksperymentach.

> Our approach uses a router that assigns queries to the small or large model based on the predicted query difficulty and the desired quality level. The desired quality level can be tuned dynamically at test time to seamlessly trade  quality for cost as per the scenario requirements. In experiments our approach allows us to make up to 40% fewer calls to the large model, with no drop in response quality.

## q03: How does SnapKV use an observation window and attention heads to choose KV cache entries?

Typ: `author_claim`. Filtr: `neurips2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [SnapKV: LLM Knows What You are Looking for Before Generation — poE54GOq2l](https://openreview.net/forum?id=poE54GOq2l&noteId=poE54GOq2l)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Abstrakt podaje lokalizację observation window i wybór pozycji cache dla każdej głowy.

> We discover that each attention head in the model consistently focuses on specific prompt attention features during generation. Meanwhile, this robust pattern can be obtained from an `observation' window located at the end of the prompts. Drawing on this insight, SnapKV automatically compresses KV caches by selecting clustered important KV positions for each attention head.

## q04: Which omissions in the OmniQuant latency comparisons did a reviewer identify?

Typ: `reviewer_limit`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models — CNUxdOX1PU](https://openreview.net/forum?id=8Wuvhh0LYW&noteId=CNUxdOX1PU)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzent wskazuje brak silnego baseline w porównaniu opóźnienia; to jego ocena, nie ustalenie o wszystkich wersjach pracy.

> 4. The latency benchmark only contain fp16 and OmniQuant. Strong baseline such as GPTQ is lacking.

## q05: What profiling and decoding-time measurements did a FastGen reviewer ask the authors to provide?

Typ: `reviewer_limit`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [Model Tells You What to Discard: Adaptive KV Cache Compression for LLMs — YN66lg0xUR](https://openreview.net/forum?id=uNrFpDPMyo&noteId=YN66lg0xUR)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzent pyta o koszt profilowania, czas inferencji i działanie istniejących kernelów.

> - Since the inference time matters in practical serving, it would be helpful to understand more if the authors can provide corresponding results
>     - For example, how long does inference take compared to the full-cache strategy? I think it might become slower because the existing attention kernels may not efficiently deal with the sparsity
>     - How long does profiling take? Is it feasible for practical inference scenarios?

## q06: What assumptions about hardware, offloading, and concurrent requests did SpecExec reviewers question?

Typ: `reviewer_limit`. Filtr: `neurips2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [SpecExec: Massively Parallel Speculative Decoding For Interactive LLM Inference on Consumer Devices — 6cQKtZf4El](https://openreview.net/forum?id=JAhNsZ9dvG&noteId=6cQKtZf4El)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzent porusza docelowy sprzęt, offloading i zastosowanie dla jednego użytkownika.

> - Although the paper targets consumer-level GPUs, the experiment results show that SpecExec achieves the highest speedup with the A100 GPU, one of the most popular datacenter-level GPUs.
> - Token throughput is still slow because of the offloading. For A100 GPU, using 4-bit quantized 70B model (AWQ, GPTQ, ...) and without speculative decoding will be more practical.
> - SpecExec seems plausible only for single request with single user.

- Źródło: [SpecExec: Massively Parallel Speculative Decoding For Interactive LLM Inference on Consumer Devices — AwSKPrQJD1](https://openreview.net/forum?id=JAhNsZ9dvG&noteId=AwSKPrQJD1)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Osobny recenzent pyta o przyspieszenie przy braku offloadingu.

> 1. While SpecExec achieves significant performance acceleration in systems with offloading, it is unclear how this method performs in terms of acceleration in speculative inference systems that do not have offloading.

## q07: Which limitations of SnapKV prompt-processing speed and very-long-context evaluation did reviewers raise?

Typ: `reviewer_limit`. Filtr: `neurips2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [SnapKV: LLM Knows What You are Looking for Before Generation — DcwXDOY3Y7](https://openreview.net/forum?id=poE54GOq2l&noteId=DcwXDOY3Y7)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Opinia o braku przyspieszenia prefill dla długich wejść i krótkich generacji.

> - This paper doesn’t accelerate the prompt processing step (even though it is explicitly targeting long prompt processing), which could present a bottleneck for tasks with long input lengths and short generation lengths
> - The paper lacks benchmarking experiments to justify that their approach doesn’t add any overheads to the prompt processing step (due to having to use the observation window to identify important tokens, which likely needs to be applied separately from FlashAttention)
> - They do not provide sufficient justification for their pooling approach, and their ablations are insufficient to show its effectiveness (they show accuracy benefits on one task, but for other tasks with less sparse attention distributions than retrieval this may actually degrade performance by prioritizing less important tokens that are near important ones). It would be good to ablate the impacts of pooling on non-retrieval tasks as well (eg. few-shot ICL) which may have a flatter attention distribution, and where pooling may lead to retrieving less of the actual important information that is required.

- Źródło: [SnapKV: LLM Knows What You are Looking for Before Generation — Qh2Gjw8hoO](https://openreview.net/forum?id=poE54GOq2l&noteId=Qh2Gjw8hoO)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Opinia o niewystarczającej ocenie jakości dla ponad 100K tokenów.

> The impact on model accuracy for very long context (more than 100K tokens) is not thoroughly explored.

## q08: What do OmniQuant and QLLM authors propose for activation outliers, and which gaps in inference-efficiency evaluations did reviewers identify?

Typ: `compare_authors_reviews`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models — 8Wuvhh0LYW](https://openreview.net/forum?id=8Wuvhh0LYW&noteId=8Wuvhh0LYW)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Deklaracja autorów OmniQuant o LWC i LET.

> OmniQuant comprises two innovative components including Learnable Weight Clipping (LWC) and Learnable Equivalent Transformation (LET). LWC modulates the extreme values of weights by optimizing the clipping threshold. Meanwhile, LET tackles activation outliers by shifting the challenge of quantization from activations to weights.

- Źródło: [QLLM: Accurate and Efficient Low-Bitwidth Quantization for Large Language Models — FIplmUWdm3](https://openreview.net/forum?id=FIplmUWdm3&noteId=FIplmUWdm3)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Deklaracja autorów QLLM o channel disassembly/assembly dla outlierów.

> QLLM introduces an adaptive channel reassembly technique that reallocates the magnitude of outliers to other channels, thereby mitigating their impact on the quantization range. This is achieved by channel disassembly and channel assembly, which first breaks down the outlier channels into several sub-channels to ensure a more balanced distribution of activation magnitudes. Then similar channels are merged to maintain the original channel number for efficiency.

- Źródło: [OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models — CNUxdOX1PU](https://openreview.net/forum?id=8Wuvhh0LYW&noteId=CNUxdOX1PU)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Zastrzeżenie recenzenta OmniQuant do porównania latency.

> 4. The latency benchmark only contain fp16 and OmniQuant. Strong baseline such as GPTQ is lacking.

- Źródło: [QLLM: Accurate and Efficient Low-Bitwidth Quantization for Large Language Models — XHJ5cQRnhR](https://openreview.net/forum?id=FIplmUWdm3&noteId=XHJ5cQRnhR)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzent QLLM odróżnia konfiguracje oceny jakości od konfiguracji pomiarów wydajności.

> * While the algorithm perf. experiments are conducted with W6A6 and W4A4, inference efficiency experiments are only conducted with W8A8. I think implementing W4A4 kernels on some NVIDIA GPUs and demonstrating better efficiency-algo. perf. trade-off compared with W8A8 and existing W4A4 will make this paper stronger.

## q09: How do SpecExec and Kangaroo differ in drafting, and which deployment or model-coverage limitations do reviewers mention?

Typ: `compare_authors_reviews`. Filtr: `neurips2024`. Odpowiedź w bazie: proponowane tak.

- Źródło: [SpecExec: Massively Parallel Speculative Decoding For Interactive LLM Inference on Consumer Devices — JAhNsZ9dvG](https://openreview.net/forum?id=JAhNsZ9dvG&noteId=JAhNsZ9dvG)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Autorzy SpecExec opisują cache tree budowane z prawdopodobnych kontynuacji draft modelu.

> SpecExec takes the most probable continuations from the draft model to build a "cache" tree for the target model, which then gets validated in a single pass.

- Źródło: [Kangaroo: Lossless Self-Speculative Decoding for Accelerating LLMs via Double Early Exiting — lT3oc04mDp](https://openreview.net/forum?id=lT3oc04mDp&noteId=lT3oc04mDp)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Autorzy Kangaroo budują draft z płytkiej części modelu docelowego i LM Head.

> we propose a novel self-speculative decoding framework \emph{Kangaroo} with \emph{double} early exiting strategy, which leverages the shallow sub-network and the \texttt{LM Head} of the well-trained target LLM to construct a self-drafting model.

- Źródło: [SpecExec: Massively Parallel Speculative Decoding For Interactive LLM Inference on Consumer Devices — 6cQKtZf4El](https://openreview.net/forum?id=JAhNsZ9dvG&noteId=6cQKtZf4El)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzja SpecExec wskazuje sprzęt, offloading i ograniczenie do pojedynczego żądania.

> - Although the paper targets consumer-level GPUs, the experiment results show that SpecExec achieves the highest speedup with the A100 GPU, one of the most popular datacenter-level GPUs.
> - Token throughput is still slow because of the offloading. For A100 GPU, using 4-bit quantized 70B model (AWQ, GPTQ, ...) and without speculative decoding will be more practical.
> - SpecExec seems plausible only for single request with single user.

- Źródło: [Kangaroo: Lossless Self-Speculative Decoding for Accelerating LLMs via Double Early Exiting — MZTxKruFgg](https://openreview.net/forum?id=lT3oc04mDp&noteId=MZTxKruFgg)
- Rodzaj: `official_review`; pole `weaknesses`.
- Uzasadnienie: Recenzent Kangaroo pyta o uogólnianie adaptera na inne rodziny modeli.

> 1. Adapter-Network Design: The design of the adapter network is heuristic and seems verified only on LLama2 and Vicuna models. More justification and exploration across different model architectures would enhance the generalizability of the approach. (new results for Gemma1~2, Phi3, LaMMa3, etc..)

## q10: Why can aggregate perplexity or accuracy hide quality changes after language-model compression?

Typ: `metric_synthesis`. Filtr: `obie konferencje`. Odpowiedź w bazie: proponowane tak.

- Źródło: [Compressing LLMs: The Truth is Rarely Pure and Never Simple — B9klVS7Ddk](https://openreview.net/forum?id=B9klVS7Ddk&noteId=B9klVS7Ddk)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: LLM-KICK kwestionuje wystarczalność perplexity i opisuje zadania ujawniające utratę zdolności.

> As recent research efforts are focused on developing increasingly sophisticated compression methods, our work takes a step back, and re-evaluates the effectiveness of existing SoTA compression methods, which rely on a fairly simple and widely questioned metric, perplexity (even for dense LLMs). We introduce **K**nowledge-**I**ntensive **C**ompressed LLM Benchmar**K** **(LLM-KICK)**, a collection of carefully-curated tasks to re-define the evaluation protocol for compressed LLMs, which have significant alignment with their dense counterparts, and perplexity fail to capture subtle change in their true capabilities.

- Źródło: [Accuracy is Not All You Need — QVG7j29Sta](https://openreview.net/forum?id=QVG7j29Sta&noteId=QVG7j29Sta)
- Rodzaj: `author_abstract`; pole `abstract`.
- Uzasadnienie: Druga praca wskazuje flips i zmiany zachowania ukryte przez podobne accuracy.

> However, even when the accuracy of baseline and compressed model are similar, we observe the phenomenon of flips, wherein answers change from correct to incorrect and vice versa in proportion. We conduct a detailed study of metrics across multiple compression techniques, models and datasets, demonstrating that the behavior of compressed models as visible to end-users is often significantly different from the baseline model, even when accuracy is similar.

## q11: What measured energy consumption in joules per generated token, including uncertainty intervals, does OmniQuant achieve?

Typ: `insufficient_evidence`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane brak podstaw.

W zgromadzonym abstrakcie i recenzjach tej pracy nie ma wymaganych pomiarów w podanych jednostkach lub konfiguracji. To nie jest twierdzenie o pełnym PDF-ie.

Asystent sprawdził wszystkie pola tekstowe 6 źródeł tej publikacji; brak jednostek/podanej konfiguracji w skanie pełnych tekstów źródeł. Wymaga sprawdzenia przez człowieka i ponownej walidacji na korpusie końcowym.

Sprawdzone ID: 8Wuvhh0LYW, CNUxdOX1PU, I4ox934Ez5, c50MBXpnem, iDiUKY61tl, wKCbLSlSOB

## q12: What is QLLM's end-to-end decoding latency in milliseconds at batch size 64 and input length 131072 tokens?

Typ: `insufficient_evidence`. Filtr: `iclr2024`. Odpowiedź w bazie: proponowane brak podstaw.

W zgromadzonym abstrakcie i recenzjach tej pracy nie ma wymaganych pomiarów w podanych jednostkach lub konfiguracji. To nie jest twierdzenie o pełnym PDF-ie.

Asystent sprawdził wszystkie pola tekstowe 5 źródeł tej publikacji; brak jednostek/podanej konfiguracji w skanie pełnych tekstów źródeł. Wymaga sprawdzenia przez człowieka i ponownej walidacji na korpusie końcowym.

Sprawdzone ID: FIplmUWdm3, IMKz4ffJeD, XHJ5cQRnhR, rTIoug7iAi, tVUFCMjEfF

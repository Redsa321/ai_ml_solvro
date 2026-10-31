# Audyt doboru tematycznego

Data: 2026-10-30T11:58:51.193878+00:00. Podstawa selekcji: tytuł i abstrakt publikacji.

Efektywność inferencji generatywnych modeli językowych: mniejszy koszt obliczeń, pamięci, opóźnienia lub liczby wywołań; kompresja parametrów/kontekstu; także ewaluacja jakości skompresowanych modeli. Dopuszczalne LLM wielomodalne i aplikacje dialogowe, jeśli abstrakt wprost opisuje koszt działania części językowej. Odrzucane: wyłącznie trening/fine-tuning, reprezentacje VQ bez kompresji wykonania LLM, bezpieczeństwo i jakość bez celu wydajności inferencji.

Zachowano kolejność SHA-256 z seed=42 i wybrano pierwszych 30 pasujących prac na konferencję. Nie wykorzystano ocen recenzji ani wyników retrieval do wyboru.

Pierwotny eksport: 60 prac, 235 recenzji. Końcową próbę stanowi 36 dostępnych prac; 24 pozostałych kandydatów nie włączono ze względu na brak pobranych recenzji.

## Prace docelowe

| Konferencja | Praca | Uzasadnienie | Recenzje lokalne |
| --- | --- | --- | --- |
| ICLR 2024 | [IceFormer: Accelerated Inference with Long-Sequence Transformers on CPUs](https://openreview.net/forum?id=6RR3wU4mSZ) | Przyspieszanie inferencji długich sekwencji Transformer/LLM na CPU. | tak |
| ICLR 2024 | [SpQR: A Sparse-Quantized Representation for Near-Lossless LLM Weight Compression](https://openreview.net/forum?id=Q1u25ahSuy) | Kompresja wag LLM do niskiej precyzji i szybsze wykonanie na GPU. | tak |
| ICLR 2024 | [Are Bert Family Good Instruction Followers?  A Study on Their Potential And Limitations](https://openreview.net/forum?id=x8VNtpCu1I) | Nieautoregresyjna generacja jako szybsza alternatywa dla autoregresyjnych LLM; abstrakt podaje speedup dekodowania. | tak |
| ICLR 2024 | [LQ-LoRA: Low-rank plus Quantized Matrix Decomposition for Efficient Language Model Finetuning](https://openreview.net/forum?id=xw29VvOMmU) | Kwantyzacja i rozkład niskiego rzędu; także jawny wariant kompresji LLaMA-2 do mniejszego budżetu pamięci. | tak |
| ICLR 2024 | [AffineQuant: Affine Transformation Quantization for Large Language Models](https://openreview.net/forum?id=of2rhALq8l) | Kwantyzacja PTQ ułatwiająca wdrażanie dużych modeli na urządzeniach o ograniczonych zasobach. | tak |
| ICLR 2024 | [Retrieval is Accurate Generation](https://openreview.net/forum?id=oXYZJXDdo7) | Generacja fraz przez retrieval; abstrakt wprost porównuje latency z innymi retrieval-augmented LM. | tak |
| ICLR 2024 | [Model Tells You What to Discard: Adaptive KV Cache Compression for LLMs](https://openreview.net/forum?id=uNrFpDPMyo) | Adaptacyjna kompresja KV cache zmniejszająca pamięć inferencji generatywnej LLM. | tak |
| ICLR 2024 | [In-context Autoencoder for Context Compression in a Large Language Model](https://openreview.net/forum?id=uREj4ZuGJE) | Kompresja kontekstu do slotów pamięci, z celem obniżenia latency i pamięci GPU podczas inferencji. | tak |
| ICLR 2024 | [Compressing LLMs: The Truth is Rarely Pure and Never Simple](https://openreview.net/forum?id=B9klVS7Ddk) | Ocena jakości kompresji LLM przez pruning i kwantyzację; badanie ograniczeń metryk dla efektywnego wdrożenia. | tak |
| ICLR 2024 | [DistillSpec: Improving Speculative Decoding via Knowledge Distillation](https://openreview.net/forum?id=rsY6J3ZaTF) | Destylacja modelu draft w speculative decoding, z celem skrócenia dekodowania LLM. | tak |
| ICLR 2024 | [RECOMP: Improving Retrieval-Augmented LMs with Context Compression and Selective Augmentation](https://openreview.net/forum?id=mlJLVigNHp) | Kompresja dokumentów RAG ograniczająca koszt kontekstu wejściowego LM. | tak |
| ICLR 2024 | [Efficient Streaming Language Models with Attention Sinks](https://openreview.net/forum?id=NG7sS51zVF) | StreamingLLM: zarządzanie KV cache i pamięcią przy długiej inferencji strumieniowej. | tak |
| ICLR 2024 | [Rethinking Channel Dimensions to Isolate Outliers for Low-bit Weight Quantization of Large Language Models](https://openreview.net/forum?id=JzG7kSpjJk) | Kwantyzacja wag LLM z izolowaniem outlierów dla obsługi modeli przy ograniczonej pamięci. | tak |
| ICLR 2024 | [Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing](https://openreview.net/forum?id=02f3mUtqnM) | Routing zapytań między małym i dużym LLM w celu zmniejszenia kosztu inferencji. | tak |
| ICLR 2024 | [OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models](https://openreview.net/forum?id=8Wuvhh0LYW) | Kwantyzacja LLM z oceną przyspieszenia i pamięci na rzeczywistych urządzeniach. | tak |
| ICLR 2024 | [QLLM: Accurate and Efficient Low-Bitwidth Quantization for Large Language Models](https://openreview.net/forum?id=FIplmUWdm3) | Niskobitowa kwantyzacja LLM; model docelowy ma niższe wymagania pamięci i obliczeń. | tak |
| ICLR 2024 | [Compressed Context Memory for Online Language Model Interaction](https://openreview.net/forum?id=64kSvC4iPg) | Kompresja pamięci kontekstu/KV w interakcji online z LM. | nie pobrano |
| ICLR 2024 | [Large Language Models as Tool Makers](https://openreview.net/forum?id=qV83K9d5WB) | Ponowne używanie narzędzi i podział na modele o różnych rozmiarach w celu amortyzacji kosztu inferencji LLM. | nie pobrano |
| ICLR 2024 | [BatchPrompt: Accomplish more with less](https://openreview.net/forum?id=Agyicd577r) | Batchowanie przykładów w promptach ogranicza liczbę wywołań i koszt tokenów inferencji. | nie pobrano |
| ICLR 2024 | [Dynamic Sparse No Training:  Training-Free Fine-tuning for Sparse LLMs](https://openreview.net/forum?id=1ndDmZdT4g) | Pruning i poprawa jakości rzadkich LLM przeznaczonych do ograniczonych zasobowo wdrożeń. | nie pobrano |
| ICLR 2024 | [MEND: Meta Demonstration Distillation for Efficient and Effective In-Context Learning](https://openreview.net/forum?id=2Y5kBPtU0o) | Destylacja demonstracji do wektorów ogranicza koszt self-attention w in-context learning. | nie pobrano |
| ICLR 2024 | [Controlled Text Generation via Language Model Arithmetic](https://openreview.net/forum?id=SLw9fp4yI6) | Speculative sampling przy kompozycji modeli językowych ogranicza narzut kosztownej generacji sterowanej. | nie pobrano |
| ICLR 2024 | [ReLU Strikes Back: Exploiting Activation Sparsity in Large Language Models](https://openreview.net/forum?id=osoWxY8q2E) | Wykorzystanie rzadkich aktywacji ReLU do ograniczania obliczeń i transferu wag podczas inferencji LLM. | nie pobrano |
| ICLR 2024 | [LoftQ: LoRA-Fine-Tuning-aware Quantization for Large Language Models](https://openreview.net/forum?id=LzPWWPAdY4) | Kwantyzacja wraz z LoRA dla niskobitowego modelu docelowego; nie tylko optymalizacja treningu. | nie pobrano |
| ICLR 2024 | [PB-LLM: Partially Binarized Large Language Models](https://openreview.net/forum?id=BifeBRhikU) | Częściowa binaryzacja wag dla kompresji LLM. | nie pobrano |
| ICLR 2024 | [QA-LoRA: Quantization-Aware Low-Rank Adaptation of Large Language Models](https://openreview.net/forum?id=WvFoJccpo8) | Quantization-aware LoRA kończące się połączonym, kwantyzowanym modelem do wdrożenia. | nie pobrano |
| ICLR 2024 | [SliceGPT: Compress Large Language Models by Deleting Rows and Columns](https://openreview.net/forum?id=vXxardq6db) | Zmniejszanie wymiarów macierzy LLM z jawną oceną kosztu inferencji i wymagań GPU. | nie pobrano |
| ICLR 2024 | [BTR: Binary Token Representations for Efficient Retrieval Augmented Language Models](https://openreview.net/forum?id=3TO3TtnOFl) | Binarne reprezentacje tokenów w retrieval-augmented LM ograniczają obliczenia inferencji i przechowywanie. | nie pobrano |
| ICLR 2024 | [LUT-GEMM: Quantized Matrix Multiplication based on LUTs for Efficient Inference in Large-Scale Generative Language Models](https://openreview.net/forum?id=gLARhFLE0F) | Kernel LUT-GEMM przyspieszający mnożenie skwantyzowanych macierzy w generatywnych LM. | nie pobrano |
| ICLR 2024 | [MBR and QE Finetuning: Training-time Distillation of the Best and Most Expensive Decoding Methods](https://openreview.net/forum?id=bkNx3O0sND) | Destylacja kosztownych metod dekodowania do modelu, który używa tańszego algorytmu podczas inferencji; także teacher LLM. | nie pobrano |
| NeurIPS 2024 | [SpecExec: Massively Parallel Speculative Decoding For Interactive LLM Inference on Consumer Devices](https://openreview.net/forum?id=JAhNsZ9dvG) | Speculative decoding i równoległe drafty dla interaktywnej inferencji LLM na sprzęcie konsumenckim. | tak |
| NeurIPS 2024 | [ESPACE: Dimensionality Reduction of Activations for Model Compression](https://openreview.net/forum?id=HAcaANQNMK) | Kompresja aktywacji i wag LLM z oceną GEMM oraz prefill latency. | tak |
| NeurIPS 2024 | [Cherry on Top: Parameter Heterogeneity and Quantization in Large Language Models](https://openreview.net/forum?id=QAiKLaCrKj) | Kwantyzacja mieszaną precyzją parametrów LLM dla efektywnego wdrożenia. | tak |
| NeurIPS 2024 | [SnapKV: LLM Knows What You are Looking for Before Generation](https://openreview.net/forum?id=poE54GOq2l) | Kompresja KV cache ograniczająca czas i pamięć generacji LLM. | tak |
| NeurIPS 2024 | [SlimGPT: Layer-wise Structured Pruning for Large Language Models](https://openreview.net/forum?id=MxF0IKJtKW) | Strukturalny pruning parametrów LLM. | tak |
| NeurIPS 2024 | [Building on Efficient Foundations: Effective Training of LLMs with Structured Feedforward Layers](https://openreview.net/forum?id=WxLVYZbIew) | Strukturalne FFN w LLM; abstrakt oprócz treningu bada faktyczne zyski w online decoding. | tak |
| NeurIPS 2024 | [Kangaroo: Lossless Self-Speculative Decoding for Accelerating LLMs via Double Early Exiting](https://openreview.net/forum?id=lT3oc04mDp) | Self-speculative decoding i early exiting w celu skrócenia generacji LLM. | tak |
| NeurIPS 2024 | [Enhancing In-Context Learning Performance with just SVD-Based Weight Pruning: A Theoretical Perspective](https://openreview.net/forum?id=wT6GHk5ShC) | Pruning SVD jako kompresja modelu dla in-context inference oraz analiza jakości. | tak |
| NeurIPS 2024 | [Towards Next-Level Post-Training Quantization of Hyper-Scale Transformers](https://openreview.net/forum?id=6uv9ViIoMj) | Post-training quantization dużych Transformerów. | tak |
| NeurIPS 2024 | [Accelerating Blockwise Parallel Language Models with Draft Refinement](https://openreview.net/forum?id=KT6F5Sw0eg) | Ulepszanie draftów do blockwise parallel decoding w celu skrócenia czasu generacji. | tak |
| NeurIPS 2024 | [Matryoshka Query Transformer for Large Vision-Language Models](https://openreview.net/forum?id=B1vGiSgELw) | Kompresja liczby tokenów wizualnych przetwarzanych przez LLM i jawny trade-off FLOPs/jakość. | tak |
| NeurIPS 2024 | [Efficient Multi-task LLM Quantization and Serving for Multiple LoRA Adapters](https://openreview.net/forum?id=HfpV6u0kbX) | Kwantyzowane współdzielenie LLM i scheduling wielu adapterów LoRA dla niższego latency i pamięci. | tak |
| NeurIPS 2024 | [Superposed Decoding: Multiple Generations from a Single Autoregressive Inference Pass](https://openreview.net/forum?id=KSOkkHm9I7) | Wiele generacji z jednego przebiegu autoregresyjnego, ograniczanie kosztu obliczeń. | tak |
| NeurIPS 2024 | [PV-Tuning: Beyond Straight-Through Estimation for Extreme LLM Compression](https://openreview.net/forum?id=YvA8UF0I37) | Ekstremalna kompresja parametrów LLM do niskiej precyzji dla urządzeń o ograniczonych zasobach. | tak |
| NeurIPS 2024 | [A Full-duplex Speech Dialogue Scheme Based On Large Language Model](https://openreview.net/forum?id=YawXY6mWiK) | System dialogowy LLM z jawnym celem redukcji end-to-end response latency w pracy full-duplex. | tak |
| NeurIPS 2024 | [DuQuant: Distributing Outliers via Dual Transformation Makes Stronger Quantized LLMs](https://openreview.net/forum?id=mp8u2Pcmqz) | Kwantyzacja LLM z rozpraszaniem outlierów aktywacji. | tak |
| NeurIPS 2024 | [Reducing Transformer Key-Value Cache Size with Cross-Layer Attention](https://openreview.net/forum?id=M2UzLRoqic) | Zmniejszanie KV cache przez współdzielenie warstw uwagi. | tak |
| NeurIPS 2024 | [FlashAttention-3: Fast and Accurate Attention with Asynchrony and Low-precision](https://openreview.net/forum?id=tVConYid20) | Kernel uwagi o mniejszych kosztach obliczeń i transferów dla długich kontekstów LLM. | tak |
| NeurIPS 2024 | [SGLang: Efficient Execution of Structured Language Model Programs](https://openreview.net/forum?id=VqkAKQibpq) | Wydajne wykonywanie programów z użyciem LM, zarządzanie cache i batchowaniem. | tak |
| NeurIPS 2024 | [Accuracy is Not All You Need](https://openreview.net/forum?id=QVG7j29Sta) | Ocena utraty jakości zachowania LLM po kompresji; ograniczenia accuracy i perplexity. | tak |
| NeurIPS 2024 | [D-LLM: A Token Adaptive Computing Resource Allocation Strategy for Large Language Models](https://openreview.net/forum?id=UIOjGTKHQG) | Adaptacyjne omijanie obliczeń dla tokenów i ograniczanie KV storage w inferencji LLM. | nie pobrano |
| NeurIPS 2024 | [Learn To be Efficient: Build Structured Sparsity in Large Language Models](https://openreview.net/forum?id=iSfCWhvEGA) | Uczenie strukturalnej rzadkości aktywacji do ograniczania inference latency LLM. | nie pobrano |
| NeurIPS 2024 | [SIRIUS : Contexual Sparisty with Correction for Efficient LLMs](https://openreview.net/forum?id=5bR2l1b2eh) | Korekcja contextual sparsity dla przyspieszania LLM przy zachowaniu jakości generacji. | nie pobrano |
| NeurIPS 2024 | [S$^{2}$FT: Efficient, Scalable and Generalizable LLM Fine-tuning by Structured Sparsity](https://openreview.net/forum?id=lEUle8S4xQ) | Structured sparse fine-tuning obejmujący także skalowalne serving, szybkie przełączanie i fuzję adapterów. | nie pobrano |
| NeurIPS 2024 | [Loki: Low-rank Keys for Efficient Sparse Attention](https://openreview.net/forum?id=raABeiV71j) | Niskowymiarowe klucze i sparse attention redukujące compute i transfer w inferencji LLM. | nie pobrano |
| NeurIPS 2024 | [Leveraging Visual Tokens for Extended Text Contexts in Multi-Modal Learning](https://openreview.net/forum?id=WY3xgXIZUR) | Kompresja długiego tekstu do tokenów wizualnych w MLLM; abstrakt wskazuje także efektywną inferencję. | nie pobrano |
| NeurIPS 2024 | [$\textit{Read-ME}$: Refactorizing LLMs as Router-Decoupled Mixture of Experts with System Co-Design](https://openreview.net/forum?id=i8JaxY7tDI) | Eksperci MoE wraz z planowaniem, batchingiem i cache dla efektywnej inferencji LLM. | nie pobrano |
| NeurIPS 2024 | [Nearest Neighbor Speculative Decoding for LLM Generation and Attribution](https://openreview.net/forum?id=Ni9kebsSTt) | Speculative decoding wspomagane retrievalem z jawnym celem zwiększenia szybkości generacji. | nie pobrano |
| NeurIPS 2024 | [KV Cache is 1 Bit Per Channel: Efficient Large Language Model Inference with Coupled Quantization](https://openreview.net/forum?id=pNnvzQsS4P) | Kwantyzacja KV cache do niskiej liczby bitów dla większej przepustowości inferencji. | nie pobrano |
| NeurIPS 2024 | [Delta-CoMe: Training-Free Delta-Compression with Mixed-Precision for Large Language Models](https://openreview.net/forum?id=cr5EQRJlRn) | Kompresja delta weights dla ograniczania kosztów wdrażania wielu dostrojonych LLM. | nie pobrano |

## Wykluczone spośród pierwotnych 60

| Praca | Powód |
| --- | --- |
| [Faithful Explanations of Black-box NLP Models Using LLM-generated Counterfactuals](https://openreview.net/forum?id=UMfcdRIotC) | Wyjaśnialność NLP i generowanie kontrfaktyczne, bez celu redukcji kosztu wykonania LLM. |
| [SpeechTokenizer: Unified Speech Tokenizer for Speech Language Models](https://openreview.net/forum?id=AF9Q8Vip84) | Tokenizacja i reprezentacje audio; vector quantization nie jest tu kwantyzacją wag ani KV cache LLM. |
| [Towards Codable Watermarking for Injecting Multi-Bits Information to LLMs](https://openreview.net/forum?id=JYu5Flqm9D) | Kodowalne znaki wodne; efektywność kodowania payloadu nie jest efektywnością wykonania LLM. |
| [Mega-TTS 2: Boosting Prompting Mechanisms for Zero-Shot Speech Synthesis](https://openreview.net/forum?id=mvMI3N4AvD) | Synteza mowy i prompting; brak celu kompresji/przyspieszania inferencji LLM w abstrakcie. |
| [Guiding Instruction-based Image Editing via Multimodal Large Language Models](https://openreview.net/forum?id=S1RKWSyZ2Y) | Edycja obrazów sterowana modelem multimodalnym, a nie koszt części językowej. |
| [Fine-tuning Aligned Language Models Compromises Safety, Even When Users Do Not Intend To!](https://openreview.net/forum?id=hTEGyKf0dZ) | Wpływ fine-tuningu na bezpieczeństwo, nie redukcja kosztu inferencji. |
| [MERT: Acoustic Music Understanding Model with Large-Scale Self-supervised Training](https://openreview.net/forum?id=w3YZ9MSlBu) | Reprezentacje i samonadzorowany trening audio/muzyki. |
| [NaturalSpeech 2: Latent Diffusion Models are Natural and Zero-Shot Speech and Singing Synthesizers](https://openreview.net/forum?id=Rc7dAwVL3v) | Synteza mowy/dyfuzja i zero-shot jakość, nie optymalizacja wykonania LLM. |
| [Inducing High Energy-Latency of Large Vision-Language Models with Verbose Images](https://openreview.net/forum?id=BteuUysuXX) | Atak zwiększający koszt VLM; poza przyjętą próbą metod ograniczania kosztów i ewaluacji kompresji. |
| [EQA-MX: Embodied Question Answering using Multimodal Expression](https://openreview.net/forum?id=7gUrYE50Rb) | Embodied QA oraz vector quantization reprezentacji multimodalnych, nie kompresja wykonania LLM. |
| [Demystifying Embedding Spaces using Large Language Models](https://openreview.net/forum?id=qoYogklIPz) | Interpretacja przestrzeni embeddingów za pomocą LLM, nie wydajność jego wykonania. |
| [PlaSma: Procedural Knowledge Models for Language-based Planning and Re-Planning](https://openreview.net/forum?id=dFcXJgnrGB) | Planowanie i wiedza proceduralna, nie efektywność inferencji LLM. |
| [CLEX: Continuous  Length Extrapolation for Large Language Models](https://openreview.net/forum?id=wXpSidPpc5) | Ekstrapolacja długości kontekstu z niewielkim narzutem; celem nie jest redukcja kosztu inferencji. |
| [Neural Language of Thought Models](https://openreview.net/forum?id=HYyRwm367m) | Modele reprezentacji i generacji obrazów inspirowane Language of Thought, nie koszt wykonania LLM. |
| [HydraLoRA: An Asymmetric LoRA Architecture for Efficient Fine-Tuning](https://openreview.net/forum?id=qEpi8uWX3N) | Architektura LoRA oceniana pod kątem jakości i efektywności fine-tuningu; brak celu redukcji kosztu inferencji w abstrakcie. |
| [Frustratingly Easy Test-Time Adaptation of Vision-Language Models](https://openreview.net/forum?id=eQ6VjBhevn) | Test-time adaptation klasyfikatora vision-language, nie wykonanie generatywnego LLM. |
| [Selective Generation for Controllable Language Models](https://openreview.net/forum?id=glfYOAzh2f) | Kontrola ryzyka i halucynacji w generacji, nie redukcja kosztów obliczeń. |
| [Quantifying and Optimizing Global Faithfulness in Persona-driven Role-playing](https://openreview.net/forum?id=bzPmjmiaz8) | Wiarygodność persona-driven role-playing; destylacja służy oceniającym klasyfikatorom, nie podstawowej inferencji LLM. |
| [BackdoorAlign: Mitigating Fine-tuning based Jailbreak Attack with Backdoor Enhanced Safety Alignment](https://openreview.net/forum?id=1PcJ5Evta7) | Bezpieczne dostrajanie i odporność na jailbreak. |
| [SLTrain: a sparse plus low rank approach for parameter and memory efficient pretraining](https://openreview.net/forum?id=MXze4H7opg) | Oszczędność pamięci pretrainingu przez sparse/low-rank aktualizacje. |
| [Large Language Model Unlearning via Embedding-Corrupted Prompts](https://openreview.net/forum?id=e5icsXBD8Q) | Usuwanie wiedzy i unlearning; efektywność optymalizacji i brak dodatkowego kosztu nie są przyspieszeniem inferencji. |
| [Decomposed Prompt Decision Transformer for Efficient Unseen Task Generalization](https://openreview.net/forum?id=HcqnhqoXS3) | Offline reinforcement learning i uogólnianie Decision Transformer, nie generacja języka przez LLM. |
| [SDP4Bit: Toward 4-bit Communication Quantization in Sharded Data Parallelism for LLM Training](https://openreview.net/forum?id=PEEqnXlSCk) | Kwantyzacja komunikacji w rozproszonym treningu, nie wag/KV inferencji. |
| [Unlocking Tokens as Data Points for Generalization Bounds on Larger Language Models](https://openreview.net/forum?id=5jRU8ufi8H) | Teoretyczne granice generalizacji i tokeny jako punkty danych. |

Pełne decyzje z identyfikatorami, kolejnością i fragmentami abstraktów: [topic-audit.jsonl](../data/curation/topic-audit.jsonl).

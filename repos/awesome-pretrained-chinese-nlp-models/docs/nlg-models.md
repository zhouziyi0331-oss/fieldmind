# NLG系列 - 自然语言生成预训练模型

[← 返回主页](../README.md#nlg系列)

> 中文自然语言生成预训练模型系列


### GPT

- 2019 | Improving Language Understandingby Generative Pre-Training | Alec Radford, et al. | arXiv | [`PDF`](https://s3-us-west-2.amazonaws.com/openai-assets/research-covers/language-unsupervised/language_understanding_paper.pdf)
- 2019 | Language Models are Unsupervised Multitask Learners | Alec Radford, et al. | arXiv | [`PDF`](https://d4mucfpksywv.cloudfront.net/better-language-models/language-models.pdf)

| 模型                   | 版本        | TensorFlow                                              | PyTorch                                                                                                                                                        | 作者               | 源地址                                                     | 应用领域 |
| -------------------- | --------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------- | ---- |
| GPT2                 | 30亿语料     | -                                                       | [Google Drive](https://drive.google.com/file/d/1mT_qCQg4AWnAXTwKfsyyRWCRpgPrBJS3) · [百度网盘](https://pan.baidu.com/s/1yiuTHXUr2DpyBqmFYLJH6A)                    | Caspar ZHANG     | [GitHub](https://github.com/imcaspar/gpt2-ml)           | 通用   |
| GPT2                 | 15亿语料     | -                                                       | [Google Drive](https://drive.google.com/file/d/1IzWpQ6I2IgfV7CldZvFJnZ9byNDZdO4n) · [百度网盘](https://pan.baidu.com/s/1TA_3e-u2bXg_hcx_NwVbGw)                    | Caspar ZHANG     | [GitHub](https://github.com/imcaspar/gpt2-ml)           | 通用   |
| CDial-GPT-LCCC-base  | base      | -                                                       | [🤗HF](https://huggingface.co/thu-coai/CDial-GPT_LCCC-base)                                                                                                    | thu-coai         | [GitHub](https://github.com/thu-coai/CDial-GPT)         | 中文对话 |
| CDial-GPT2-LCCC-base | base      | -                                                       | [🤗HF](https://huggingface.co/thu-coai/CDial-GPT2_LCCC-base)                                                                                                   | thu-coai         | [GitHub](https://github.com/thu-coai/CDial-GPT)         | 中文对话 |
| CDial-GPT-LCCC-large | large     | -                                                       | [🤗HF](https://huggingface.co/thu-coai/CDial-GPT_LCCC-large)                                                                                                   | thu-coai         | [GitHub](https://github.com/thu-coai/CDial-GPT)         | 中文对话 |
| GPT2-dialogue        | base      | -                                                       | [Google Drive](https://drive.google.com/drive/folders/1Ogz3eapvtvdY4VUcY9AEwMbNRivLKhri?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1qDZ24VKLBU9GKARX9Ev65g) | yangjianxin1     | [GitHub](https://github.com/yangjianxin1/GPT2-chitchat) | 闲聊对话 |
| GPT2-mmi             | base      | -                                                       | [Google Drive](https://drive.google.com/drive/folders/1oWgKXP6VG_sT_2VMrm0xL4uOqfYwzgUP?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1ubXGuEvY8KmwEjIVTJVLww) | yangjianxin1     | [GitHub](https://github.com/yangjianxin1/GPT2-chitchat) | 闲聊对话 |
| GPT2-散文模型            | base      | -                                                       | [Google Drive](https://drive.google.com/drive/folders/1rJC4niJKMVwixUQkuL9k5teLRnEYTmUf?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1nbrW5iw34GRhoTin8uU2tQ) | Zeyao Du         | [GitHub](https://github.com/Morizeyao/GPT2-Chinese)     | 散文   |
| GPT2-诗词模型            | base      | -                                                       | [Google Drive](https://drive.google.com/drive/folders/1Z6nF1nrgTkrZcRLHedQHXb4_M9I7yQPN?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1Hy0OQ5xZcTLer9MQZW8o3g) | Zeyao Du         | [GitHub](https://github.com/Morizeyao/GPT2-Chinese)     | 诗词   |
| GPT2-对联模型            | base      | -                                                       | [Google Drive](https://drive.google.com/drive/folders/1ZnsvS7oHRVueNKj_SeEhiQt86aze3ojj?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1j9yVQwjlXZq58wOyXK4lcg) | Zeyao Du         | [GitHub](https://github.com/Morizeyao/GPT2-Chinese)     | 对联   |
| RoFormer-GPT         | base(L12) | [百度网盘](https://pan.baidu.com/s/11YTnWLX0ThQr2P2yW0P7GA) | -                                                                                                                                                              | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/roformer)  | 通用   |

[← 返回主页](../README.md#nlg系列)

### GPT-3

- 2019 | Transformer-XL: Attentive Language Models Beyond a Fixed-Length Context | Zihang Dai, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1901.02860)
- 2020 | Language Models are Few-Shot Learners | Tom B. Brown, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2005.14165)

| 模型                     | 版本           | 介绍                               | PyTorch                                                                                             | 作者    | 源地址                                                       | 应用领域 |
| ---------------------- | ------------ | -------------------------------- | --------------------------------------------------------------------------------------------------- | ----- | --------------------------------------------------------- | ---- |
| Chinese-Transformer-XL | 29亿参数(GPT-3) | [项目首页](https://gpt-3.aminer.cn/) | [模型下载](http://dorc-model-team.ks3-cn-beijing.ksyun.com/ren-zhi/my-model/mp_rank_00_model_states.pt) | THUDM | [GitHub](https://github.com/THUDM/Chinese-Transformer-XL) | 通用   |

[← 返回主页](../README.md#nlg系列)

### NEZHA-Gen

| 模型        | 版本   | TensorFlow                                                                                                                                                     | PyTorch | 作者     | 源地址                                                                | 应用领域 |
| --------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------ | ------------------------------------------------------------------ | ---- |
| NEZHA-Gen | base | [Google Drive](https://drive.google.com/drive/folders/1i4f_8LhaVDNjnGlLXNJ0rNgBP0E4L6V0?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1Bgle8TpcxHyuUz_jAXOBWw) | -       | HUAWEI | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 通用   |
| NEZHA-Gen | base | [Google Drive](https://drive.google.com/drive/folders/1B5-jxUlzhoKwFVMQ-nkqqbmJQgr1lRAp?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1me6_BGYHbWFdTi80vRQ2Lg) | -       | HUAWEI | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 诗歌   |

[← 返回主页](../README.md#nlg系列)

### CPM-Generate

| 模型  | 版本    | 资源                              | PyTorch                                      | 作者          | 源地址                                                  | 应用领域 |
| --- | ----- | ------------------------------- | -------------------------------------------- | ----------- | ---------------------------------------------------- | ---- |
| CPM | 26亿参数 | [项目首页](https://cpm.baai.ac.cn/) | [模型下载](https://cpm.baai.ac.cn/download.html) | Tsinghua AI | [GitHub](https://github.com/TsinghuaAI/CPM-Generate) | 通用   |

备注:

> PyTorch转TensorFlow可参考: [CPM-LM-TF2](https://github.com/qhduan/CPM-LM-TF2)
> PyTorch转PaddlePaddle可参考: [CPM-Generate-Paddle](https://github.com/jm12138/CPM-Generate-Paddle)

[← 返回主页](../README.md#nlg系列)

### T5

| 模型 | 版本    | TensorFlow                                                          | PyTorch                                                             | 作者          | 源地址                                       | 应用领域 |
| -- | ----- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ----------- | ----------------------------------------- | ---- |
| T5 | small | [🤗HF](https://huggingface.co/uer/t5-small-chinese-cluecorpussmall) | [🤗HF](https://huggingface.co/uer/t5-small-chinese-cluecorpussmall) | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py) | 通用   |

[← 返回主页](../README.md#nlg系列)

### T5-PEGASUS

| 模型         | 版本    | Keras                                                   | PyTorch | 作者               | 源地址                                                      | 应用领域 |
| ---------- | ----- | ------------------------------------------------------- | ------- | ---------------- | -------------------------------------------------------- | ---- |
| T5-PEGASUS | base  | [百度网盘](https://pan.baidu.com/s/1lQ9Dt9wZDO3IgiCL9tP-Ug) | -       | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/t5-pegasus) | 通用   |
| T5-PEGASUS | small | [百度网盘](https://pan.baidu.com/s/1bXRVWnDyAck9VfSO9_1oJQ) | -       | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/t5-pegasus) | 通用   |

> Keras转PyTorch可参考: [t5-pegasus-pytorch](https://github.com/renmada/t5-pegasus-pytorch)

[← 返回主页](../README.md#nlg系列)

### Mengzi-T5

| 模型        | 版本        | TensorFlow | PyTorch                                                | 作者       | 源地址                                          | 应用领域 |
| --------- | --------- | ---------- | ------------------------------------------------------ | -------- | -------------------------------------------- | ---- |
| Mengzi-T5 | base(L12) | -          | [🤗HF](https://huggingface.co/Langboat/mengzi-t5-base) | Langboat | [GitHub](https://github.com/Langboat/Mengzi) | 通用   |

[← 返回主页](../README.md#nlg系列)

### PanGu-Alpha

- 2021 | PanGu-α: Large-scale Autoregressive Pretrained Chinese Language Models with Auto-parallel Computation | Wei Zeng, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2104.12369)

| 模型                 | 版本   | 资源                                                                                                              | 下载地址                                                                                                                                                                                | 作者                                                                              | 源地址                                                                          | 应用领域 |
| ------------------ | ---- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---- |
| 盘古α-2.6B           | 2.6G | [项目首页](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha/src/branch/master)                        | [模型下载](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha/src/branch/master)                                                                                            | [PCL-Platform.Intelligence](https://git.openi.org.cn/PCL-Platform.Intelligence) | [github](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha)     | 通用   |
| 盘古α-13B            | 12G  | [项目首页](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha/src/branch/master)                        | [模型下载](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha/src/branch/master)                                                                                            | [PCL-Platform.Intelligence](https://git.openi.org.cn/PCL-Platform.Intelligence) | [github](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha)     | 通用   |
| 盘古α-2.6B pytorch版本 | 2.6G | [项目首页](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU/src/branch/master/panguAlpha_pytorch) | [模型下载](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU/src/branch/master/panguAlpha_pytorch#user-content-%E6%A8%A1%E5%9E%8B%E6%96%87%E4%BB%B6%E4%B8%8B%E8%BD%BD) | [PCL-Platform.Intelligence](https://git.openi.org.cn/PCL-Platform.Intelligence) | [github](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU) | 通用   |
| 盘古α-13B pytorch版本  | 12G  | [项目首页](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU/src/branch/master/panguAlpha_pytorch) | [模型下载](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU/src/branch/master/panguAlpha_pytorch#user-content-%E6%A8%A1%E5%9E%8B%E6%96%87%E4%BB%B6%E4%B8%8B%E8%BD%BD) | [PCL-Platform.Intelligence](https://git.openi.org.cn/PCL-Platform.Intelligence) | [github](https://git.openi.org.cn/PCL-Platform.Intelligence/PanGu-Alpha-GPU) | 通用   |

[← 返回主页](../README.md#nlg系列)

### EVA

- 2021 | EVA: An Open-Domain Chinese Dialogue System with Large-Scale Generative Pre-Training | Hao Zhou, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2108.01547)

| 模型            | 版本     | 介绍                                          | 模型下载                                                                                               | 作者                                      | 源地址                                       | 应用领域    | 备注       |
| ------------- | ------ | ------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------- | ------- | -------- |
| EVA           | 28亿参数  | [项目首页](https://wudaoai.cn/model/detail/EVA) | [模型下载](https://wudaoai.cn/model/download?resourceId=1428554651225075712\&filename=eva-ckpt.tar.gz) | [thu-coai](https://github.com/thu-coai) | [github](https://github.com/thu-coai/EVA) | 中文开放域对话 | 需要登陆才能下载 |
| EVA2.0-xLarge | xlarge | [项目首页](https://wudaoai.cn/model/detail/EVA) | \[[🤗HF\]](https://huggingface.co/thu-coai/EVA2.0-xlarge)                                          | [thu-coai](https://github.com/thu-coai) | [github](https://github.com/thu-coai/EVA) | 中文开放域对话 |
| EVA2.0-large  | large  | [项目首页](https://wudaoai.cn/model/detail/EVA) | \[[🤗HF\]](https://huggingface.co/thu-coai/EVA2.0-large)                                           | [thu-coai](https://github.com/thu-coai) | [github](https://github.com/thu-coai/EVA) | 中文开放域对话 |
| EVA2.0-base   | base   | [项目首页](https://wudaoai.cn/model/detail/EVA) | \[[🤗HF\]](https://huggingface.co/thu-coai/EVA2.0-base)                                            | [thu-coai](https://github.com/thu-coai) | [github](https://github.com/thu-coai/EVA) | 中文开放域对话 |

[← 返回主页](../README.md#nlg系列)-

### BART

- 2019 | BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension | Mike Lewis, et al. | arxiv | [`PDF`](https://arxiv.org/abs/1910.13461)

| 模型         | 版本    | TensorFlow | PyTorch                                                    | 作者                                    | 源地址                                      | 应用领域 |
| ---------- | ----- | ---------- | ---------------------------------------------------------- | ------------------------------------- | ---------------------------------------- | ---- |
| BART-base  | base  | \[[🤗HF\]](https://huggingface.co/fnlp/bart-base-chinese)  | [fastNLP](https://github.com/fastnlp) | [github](https://github.com/fastnlp/CPT) | 中文通用 |
| BART-large | large | \[[🤗HF\]](https://huggingface.co/fnlp/bart-large-chinese) | [fastNLP](https://github.com/fastnlp) | [github](https://github.com/fastnlp/CPT) | 中文通用 |

[← 返回主页](../README.md#nlg系列)

### 闻仲

| 模型       | 版本         | 类型   | TensorFlow | PyTorch                                                    | 作者                                        | 源地址                                                    | 应用领域 |
| -------- | ---------- | ---- | ---------- | ---------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------ | ---- |
| Wenzhong | large(L24) | GPT2 | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Wenzhong-3.5B) | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 中文通用 |

[← 返回主页](../README.md#nlg系列)

### 余元

| 模型     | 版本         | 类型   | TensorFlow | PyTorch                                                  | 作者                                        | 源地址                                                    | 应用领域 |
| ------ | ---------- | ---- | ---------- | -------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------ | ---- |
| Yuyuan | large(L24) | GPT2 | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Yuyuan-3.5B) | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 医学领域 |

[← 返回主页](../README.md#nlg系列)

### RWKV

- 2021 | An Attention Free Transformer | Shuangfei Zhai, et al. | arxiv | [`PDF`](https://arxiv.org/abs/2105.14103)
- 2022 | The RWKV Language Model . | [github](https://github.com/BlinkDL/RWKV-LM)

| 模型   | 版本        | 类型     | TensorFlow | PyTorch                                                             | 作者                                    | 源地址                                            | 应用领域 |
| ---- | --------- | ------ | ---------- | ------------------------------------------------------------------- | ------------------------------------- | ---------------------------------------------- | ---- |
| RWKV | base(L12) | [github](https://github.com/BlinkDL/AI-Writer/releases)             | [PENG Bo](https://github.com/BlinkDL) | [github](https://github.com/BlinkDL/AI-Writer) | 小说   |
| RWKV | 7B        | \[[🤗HF\]](https://huggingface.co/BlinkDL/rwkv-4-pile-7b)           | [PENG Bo](https://github.com/BlinkDL) | [github](https://github.com/BlinkDL/ChatRWKV)  | 小说   |
| RWKV | 14B       | \[[🤗HF\]](https://huggingface.co/BlinkDL/rwkv-4-pile-7b/tree/main) | [PENG Bo](https://github.com/BlinkDL) | [github](https://github.com/BlinkDL/ChatRWKV)  | 小说   |

[← 返回主页](../README.md#nlg系列)

### PromptCLUE

| 模型               | 版本        | TensorFlow | PyTorch                                                        | 作者                                      | 源地址                                             | 应用领域 |
| ---------------- | --------- | ---------- | -------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------- | ---- |
| PromptCLUE       | base(L12) | \[[🤗HF\]](https://huggingface.co/ClueAI/PromptCLUE-base)      | [ClueAI](https://huggingface.co/ClueAI) | [github](https://github.com/clue-ai/PromptCLUE) | 通用   |
| PromptCLUE-v1-5  | base(L12) | \[[🤗HF\]](https://huggingface.co/ClueAI/PromptCLUE-base-v1-5) | [ClueAI](https://huggingface.co/ClueAI) | [github](https://github.com/clue-ai/PromptCLUE) | 通用   |
| PromptCLUE-large | large     | [API在线调用](https://www.clueai.cn/)                              | [ClueAI](https://huggingface.co/ClueAI) | [github](https://github.com/clue-ai/PromptCLUE) | 通用   |

[← 返回主页](../README.md#nlg系列)

### ChatYuan

| 模型                | 版本    | 类型 | TensorFlow | PyTorch                                                     | 作者                                   | 源地址                                           | 应用领域  |
| ----------------- | ----- | -- | ---------- | ----------------------------------------------------------- | ------------------------------------ | --------------------------------------------- | ----- |
| ChatYuan          | large | T5 | \[[🤗HF\]](https://huggingface.co/ClueAI/ChatYuan-large-v1) | [ClueAI](https://github.com/clue-ai) | [github](https://github.com/clue-ai/ChatYuan) | 功能型对话 |
| ChatYuan-large-v2 | large | T5 | \[[🤗HF\]](https://huggingface.co/ClueAI/ChatYuan-large-v2) | [ClueAI](https://github.com/clue-ai) | [github](https://github.com/clue-ai/ChatYuan) | 功能型对话 |

[← 返回主页](../README.md#nlg系列)

### SkyText

| 模型      | 版本    | 类型   | TensorFlow | PyTorch                                            | 作者                                            | 源地址                                                      | 应用领域 |
| ------- | ----- | ---- | ---------- | -------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------- | ---- |
| SkyText | large | GPT3 | \[[🤗HF\]](https://huggingface.co/SkyWork/SkyText) | [SkyWorkAIGC](https://github.com/SkyWorkAIGC) | [github](https://github.com/SkyWorkAIGC/SkyText-CN-GPT3) | 通用   |

[← 返回主页](../README.md#nlg系列)

### ProphetNet

- 2020 | Prophetnet: Predicting future n-gram for sequence-to-sequence pre-training | Qi, Weizhen, et al. | arxiv | [`PDF`](https://arxiv.org/pdf/2001.04063.pdf)
- 2021 | ProphetNet-X: Large-Scale Pre-training Models for English, Chinese, Multi-lingual, Dialog, and Code Generation | Qi, Weizhen, et al. | arxiv | [`PDF`](https://arxiv.org/abs/2104.08006)

| 模型                   | 版本     | 类型     | TensorFlow | PyTorch                                                                                                     | 作者                                        | 源地址                                                                      | 应用领域 |
| -------------------- | ------ | ------ | ---------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------ | ---- |
| ProphetNet-Zh        | [link](https://msraprophetnet.blob.core.windows.net/prophetnet/release_checkpoints/prophetnet_zh.pt)        | [microsoft](https://github.com/microsoft) | [github](https://github.com/microsoft/ProphetNet/tree/master/ProphetNet) | 通用   |
| ProphetNet-Dialog-Zh | [link](https://msraprophetnet.blob.core.windows.net/prophetnet/release_checkpoints/prophetnet_dialog_zh.pt) | [microsoft](https://github.com/microsoft) | [github](https://github.com/microsoft/ProphetNet/tree/master/ProphetNet) | 对话   |

[← 返回主页](../README.md#nlg系列)


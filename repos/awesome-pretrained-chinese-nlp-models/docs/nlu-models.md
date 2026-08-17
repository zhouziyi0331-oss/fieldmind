# NLU系列 - 自然语言理解预训练模型

[← 返回主页](../README.md#nlu系列)

> 中文自然语言理解预训练模型系列


### BERT

- 2018 | BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding | Jacob Devlin, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1810.04805)
- 2019 | Pre-Training with Whole Word Masking for Chinese BERT | Yiming Cui, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1906.08101)

| 模型              | 版本    | TensorFlow                                                                                                                                                                | PyTorch                                                                                                                                                                   | 作者              | 源地址                                                    | 应用领域   |
| --------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | ------------------------------------------------------ | ------ |
| BERT-Base       | base  | [Google Drive](https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip)                                                                         | -                                                                                                                                                                         | Google Research | [GitHub](https://github.com/google-research/bert)      | 通用     |
| BERT-wwm        | base  | [Google Drive](https://drive.google.com/open?id=1RoTQsXp2hkQ1gSRVylRIJfQxJUgkfJMW) · [讯飞云](http://pan.iflytek.com/#/link/A2483AD206EF85FD91569B498A3C3879)                | [Google Drive](https://drive.google.com/open?id=1AQitrjbvCWc51SYiLN-cJq4e0WiNN4KY)                                                                                        | Yiming Cui      | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)    | 通用     |
| BERT-wwm-ext    | base  | [Google Drive](https://drive.google.com/open?id=1buMLEjdtrXE2c4G1rpsNGWEx7lUQ0RHi) · [讯飞云](http://pan.iflytek.com/#/link/653637473FFF242C3869D77026C9BDB5)                | [Google Drive](https://drive.google.com/open?id=1iNeYFhCBJWeUsIlnW_2K6SMwXkM4gLb_)                                                                                        | Yiming Cui      | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)    | 通用     |
| bert-base-民事    | base  | [阿里云](https://thunlp.oss-cn-qingdao.aliyuncs.com/bert/ms.zip)                                                                                                             | -                                                                                                                                                                         | THUNLP          | [GitHub](https://github.com/thunlp/OpenCLaP)           | 司法     |
| bert-base-刑事    | base  | [阿里云](https://thunlp.oss-cn-qingdao.aliyuncs.com/bert/xs.zip)                                                                                                             | -                                                                                                                                                                         | THUNLP          | [GitHub](https://github.com/thunlp/OpenCLaP)           | 司法     |
| BAAI-JDAI-BERT  | base  | [京东云](https://jdai009.s3.cn-north-1.jdcloud-oss.com/jd-aig/open/models/nlp_baai/20190918/JDAI-BERT.tar.gz)                                                                | -                                                                                                                                                                         | JDAI            | [GitHub](https://github.com/jd-aig/nlp_baai)           | 电商客服对话 |
| FinBERT         | base  | [Google Drive](https://drive.google.com/file/d/193B4sT63mMeh4zfge0FJbbFY447KiJXp/view?usp=sharing) · [百度网盘](https://pan.baidu.com/share/init?surl=D-pVJyW6bbJSre5RxotJkA) | [Google Drive](https://drive.google.com/file/d/1qW1YWtw3q9Q28QThrIY-rDU9Gl-SLIKO/view?usp=sharing) · [百度网盘](https://pan.baidu.com/share/init?surl=y_O586GBmZZ7g4d2nOF0Vg) | Value Simplex   | [GitHub](https://github.com/valuesimplex/FinBERT)      | 金融科技领域 |
| EduBERT         | base  | [好未来AI](https://ai.100tal.com/download/TAL-EduBERT-TF.zip)                                                                                                                | [好未来AI](https://ai.100tal.com/download/TAL-EduBERT.zip)                                                                                                                   | tal-tech        | [GitHub](https://github.com/tal-tech/edu-bert)         | 教育领域   |
| guwenbert-base  | base  | -                                                                                                                                                                         | [百度网盘](https://pan.baidu.com/s/1dw_08p7CVsz0jVj4jd58lQ) · [🤗HF](https://huggingface.co/ethanyt/guwenbert-base)                                                           | Ethan           | [GitHub](https://github.com/Ethan-yt/guwenbert)        | 古文领域   |
| guwenbert-large | large | -                                                                                                                                                                         | [百度网盘](https://pan.baidu.com/s/1TL9mBIlIv2rSvp61xCkeJQ) · [🤗HF](https://huggingface.co/ethanyt/guwenbert-large)                                                          | Ethan           | [GitHub](https://github.com/Ethan-yt/guwenbert)        | 古文领域   |
| BERT-CCPoem     | small | -                                                                                                                                                                         | [thunlp](https://thunlp.oss-cn-qingdao.aliyuncs.com/BERT_CCPoem_v1.zip)                                                                                                   | THUNLP-AIPoet   | [GitHub](https://github.com/THUNLP-AIPoet/BERT-CCPoem) | 古典诗歌   |

备注:

> wwm全称为\*\*Whole Word Masking \*\*,一个完整的词的部分WordPiece子词被mask，则同属该词的其他部分也会被mask

> ext表示在更多数据集下训练

[← 返回主页](../README.md#nlu系列)

### ChineseBERT

- 2021 | ChineseBERT: Chinese Pretraining Enhanced by Glyph and Pinyin Information | Zijun Sun, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2106.16038.pdf)

| 模型          | 版本    | TensorFlow | PyTorch                                                    | 作者        | 源地址                                                | 应用领域 |
| ----------- | ----- | ---------- | ---------------------------------------------------------- | --------- | -------------------------------------------------- | ---- |
| ChineseBERT | base  | -          | [🤗HF](https://huggingface.co/ShannonAI/ChineseBERT-base)  | ShannonAI | [GitHub](https://github.com/ShannonAI/ChineseBert) | 通用   |
| ChineseBERT | large | -          | [🤗HF](https://huggingface.co/ShannonAI/ChineseBERT-large) | ShannonAI | [GitHub](https://github.com/ShannonAI/ChineseBert) | 通用   |

[← 返回主页](../README.md#nlu系列)

### RoBERTa

- 2019 | RoBERTa: A Robustly Optimized BERT Pretraining Approach | Yinhan Liu, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/1907.11692.pdf)

| 模型                     | 版本      | TensorFlow                                                                                                                                                                   | PyTorch                                                                                                                                      | 作者          | 源地址                                                             | 应用领域 |
| ---------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------- | ---- |
| RoBERTa-tiny-clue      | tiny    | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-tiny-clue.zip)                                                                         | [百度网盘](https://pan.baidu.com/share/init?surl=hoR01GbhcmnDhZxVodeO4w)                                                                         | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RoBERTa-tiny-pair      | tiny    | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-tiny-pair.zip)                                                                         | [百度网盘](https://pan.baidu.com/share/init?surl=hoR01GbhcmnDhZxVodeO4w)                                                                         | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RoBERTa-tiny3L768-clue | tiny    | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-tiny3L768-clue.zip)                                                                    | -                                                                                                                                            | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RoBERTa-tiny3L312-clue | tiny    | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-tiny3L312-clue.zip)                                                                    | [百度网盘](https://pan.baidu.com/share/init?surl=hoR01GbhcmnDhZxVodeO4w)                                                                         | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RoBERTa-large-pair     | large   | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-large-pair.zip)                                                                        | [百度网盘](https://pan.baidu.com/share/init?surl=hoR01GbhcmnDhZxVodeO4w)                                                                         | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RoBERTa-large-clue     | large   | [Google Drive](https://storage.googleapis.com/cluebenchmark/pretrained_models/RoBERTa-large-clue.zip)                                                                        | [百度网盘](https://pan.baidu.com/share/init?surl=hoR01GbhcmnDhZxVodeO4w)                                                                         | CLUE        | [GitHub](https://github.com/CLUEbenchmark/CLUEPretrainedModels) | 通用   |
| RBT3                   | 3层base  | [Google Drive](https://drive.google.com/file/d/1-rvV0nBDvRCASbRz8M9Decc3_8Aw-2yi/view?usp=drive_open) · [讯飞云](https://pan.iflytek.com/link/275E5B46185C982D4AF5AC295E1651B6) | [Google Drive](https://drive.google.com/file/d/1_LqmIxm8Nz1Abvlqb8QFZaxYo-TInOed/view)                                                       | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RBTL3                  | 3层large | [Google Drive](https://drive.google.com/open?id=1Jzn1hYwmv0kXkfTeIvNT61Rn1IbRc-o8) · [讯飞云](https://pan.iflytek.com/link/0DD18FAC080BAF75DBA28FB5C0047760)                    | [Google Drive](https://drive.google.com/open?id=1eHM3l4fMo6DsQYGmey7UZGiTmQquHw25)                                                           | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RBTL4                  | 4层large | [讯飞云](http://pan.iflytek.com/link/7B04C5BF09812DB241BBA973D649824C)                                                                                                          | -                                                                                                                                            | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RBTL6                  | 6层large | [讯飞云](http://pan.iflytek.com/link/B935B1F701A8FD352CAA74614126C4A2)                                                                                                          | -                                                                                                                                            | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RoBERTa-wwm-ext        | base    | [Google Drive](https://drive.google.com/open?id=1jMAKIJmPn7kADgD3yQZhpsqM-IRM1qZt) · [讯飞云](http://pan.iflytek.com/#/link/98D11FAAF0F0DBCB094EE19CCDBC98BF)                   | [Google Drive](https://drive.google.com/open?id=1eHM3l4fMo6DsQYGmey7UZGiTmQquHw25)                                                           | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RoBERTa-wwm-ext-large  | large   | [Google Drive](https://drive.google.com/open?id=1dtad0FFzG11CBsawu8hvwwzU2R0FDI94) · [讯飞云](http://pan.iflytek.com/#/link/AC056611607108F33A744A0F56D0F6BE)                   | [Google Drive](https://drive.google.com/open?id=1-2vEZfIFCdM1-vJ3GD6DlSyKT4eVXMKq)                                                           | Yiming Cui  | [GitHub](https://github.com/ymcui/Chinese-BERT-wwm)             | 通用   |
| RoBERTa-base           | base    | [Google Drive](https://drive.google.com/open?id=1ykENKV7dIFAqRRQbZIh0mSb7Vjc2MeFA) · [百度网盘](https://pan.baidu.com/s/1hAs7-VSn5HZWxBHQMHKkrg)                                 | [Google Drive](https://drive.google.com/open?id=1H6f4tYlGXgug1DdhYzQVBuwIGAkAflwB) · [百度网盘](https://pan.baidu.com/s/1AGC76N7pZOzWuo8ua1AZfw) | brightmart  | [GitHub](https://github.com/brightmart/roberta_zh)              | 通用   |
| RoBERTa-Large          | large   | [Google Drive](https://drive.google.com/open?id=1W3WgPJWGVKlU9wpUYsdZuurAIFKvrl_Y) · [百度网盘](https://pan.baidu.com/s/1Rk_QWqd7-wBTwycr91bmug)                                 | [Google Drive](https://drive.google.com/open?id=1yK_P8VhWZtdgzaG0gJ3zUGOKWODitKXZ)                                                           | brightmart  | [GitHub](https://github.com/brightmart/roberta_zh)              | 通用   |
| RoBERTa-tiny           | tiny    | [🤗HF](https://huggingface.co/uer)                                                                                                                                           | [🤗HF](https://huggingface.co/uer)                                                                                                           | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py)                       | 通用   |
| RoBERTa-mini           | mini    | [🤗HF](https://huggingface.co/uer)                                                                                                                                           | [🤗HF](https://huggingface.co/uer)                                                                                                           | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py)                       | 通用   |
| RoBERTa-small          | small   | [🤗HF](https://huggingface.co/uer)                                                                                                                                           | [🤗HF](https://huggingface.co/uer)                                                                                                           | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py)                       | 通用   |
| RoBERTa-medium         | medium  | [🤗HF](https://huggingface.co/uer)                                                                                                                                           | [🤗HF](https://huggingface.co/uer)                                                                                                           | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py)                       | 通用   |
| RoBERTa-base           | base    | [🤗HF](https://huggingface.co/uer)                                                                                                                                           | [🤗HF](https://huggingface.co/uer)                                                                                                           | DBIIR @ RUC | [GitHub](https://github.com/dbiir/UER-py)                       | 通用   |

[← 返回主页](../README.md#nlu系列)

### ALBERT

- 2019 | ALBERT: A Lite BERT For Self-Supervised Learning Of Language Representations | Zhenzhong Lan, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/1909.11942.pdf)

| 模型             | 版本      | TensorFlow                                                                                       | PyTorch                                                                            | 作者              | 源地址                                                 | 应用领域 |
| -------------- | ------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | --------------- | --------------------------------------------------- | ---- |
| Albert-tiny    | tiny    | [Google Drive](https://storage.googleapis.com/albert_zh/albert_tiny_489k.zip)                    | [Google Drive](https://drive.google.com/open?id=1VBsUJ7R5eWF1VcUBQY6BEn1a9miEvlBr) | brightmart      | [GitHub](https://github.com/brightmart/albert_zh)   | 通用   |
| Albert-base    | base    | [Google Drive](https://storage.googleapis.com/albert_zh/albert_base_zh_additional_36k_steps.zip) | [Google Drive](https://drive.google.com/open?id=1HeijHGubWR-ElFnfxUf8IrRx7Ghm1S_Q) | brightmart      | [GitHub](https://github.com/brightmart/albert_zh)   | 通用   |
| Albert-large   | large   | [Google Drive](https://storage.googleapis.com/albert_zh/albert_large_zh.zip)                     | [Google Drive](https://drive.google.com/open?id=1TAuv7OiFN8qbkT6S_VbfVbhkhg2GUF3q) | brightmart      | [GitHub](https://github.com/brightmart/albert_zh)   | 通用   |
| Albert-xlarge  | xlarge  | [Google Drive](https://storage.googleapis.com/albert_zh/albert_xlarge_zh_183k.zip)               | [Google Drive](https://drive.google.com/open?id=1kMhogQRX0uGWIGdNhm7-3hsmHlrzY_gp) | brightmart      | [GitHub](https://github.com/brightmart/albert_zh)   | 通用   |
| Albert-base    | base    | [Google Drive](https://storage.googleapis.com/albert_models/albert_base_zh.tar.gz)               | -                                                                                  | Google Research | [GitHub](https://github.com/google-research/ALBERT) | 通用   |
| Albert-large   | large   | [Google Drive](https://storage.googleapis.com/albert_models/albert_large_zh.tar.gz)              | -                                                                                  | Google Research | [GitHub](https://github.com/google-research/ALBERT) | 通用   |
| Albert-xlarge  | xlarge  | [Google Drive](https://storage.googleapis.com/albert_models/albert_xlarge_zh.tar.gz)             | -                                                                                  | Google Research | [GitHub](https://github.com/google-research/ALBERT) | 通用   |
| Albert-xxlarge | xxlarge | [Google Drive](https://storage.googleapis.com/albert_models/albert_xxlarge_zh.tar.gz)            | -                                                                                  | Google Research | [GitHub](https://github.com/google-research/ALBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### NEZHA

- 2019 | NEZHA: Neural Contextualized Representation for Chinese Language Understanding | Junqiu Wei, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1909.00204)

| 模型                  | 版本    | TensorFlow                                                                                                                                                     | PyTorch                                                        | 作者               | 源地址                                                                | 应用领域 |
| ------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------ | ---- |
| NEZHA-base          | base  | [Google Drive](https://drive.google.com/drive/folders/1tFs-wMoXIY8zganI2hQgDBoDPqA8pSmh?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1UVQjy9v_Sv4cQd1ELdjqww) | [GitHub](https://github.com/lonePatient/NeZha_Chinese_PyTorch) | HUAWEI           | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 通用   |
| NEZHA-base-wwm      | base  | [Google Drive](https://drive.google.com/drive/folders/1bK6WbqAG-B6BX2d9RPprnh2MPK6zL0t_?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1-YG8e5V2zKCnR3azsGZT1w) | [GitHub](https://github.com/lonePatient/NeZha_Chinese_PyTorch) | HUAWEI           | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 通用   |
| NEZHA-large         | large | [Google Drive](https://drive.google.com/drive/folders/1ZPPM5XtTTOrS_CDRak1t2nCBU-LFZ_zs?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1R1Ew-Lu8oIP6QhWO6nqp5Q) | [GitHub](https://github.com/lonePatient/NeZha_Chinese_PyTorch) | HUAWEI           | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 通用   |
| NEZHA-large-wwm     | large | [Google Drive](https://drive.google.com/drive/folders/1LOAUc9LXyogC2gmP_q1ojqj41Ez01aga?usp=sharing) · [百度网盘](https://pan.baidu.com/s/1JK1RLIJd2wpuypku3stt8w) | [GitHub](https://github.com/lonePatient/NeZha_Chinese_PyTorch) | HUAWEI           | [GitHub](https://github.com/huawei-noah/Pretrained-Language-Model) | 通用   |
| WoNEZHA (word-base) | base  | [百度网盘](https://pan.baidu.com/s/1ABKwUuIiMEEsRXxxlbyKmw)                                                                                                        | -                                                              | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/WoBERT)               | 通用   |

[← 返回主页](../README.md#nlu系列)

### MacBERT

- 2020 | Revisiting Pre-Trained Models for Chinese Natural Language Processing | Yiming Cui, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2004.13922.pdf)

| 模型            | 版本    | TensorFlow                                                                                                                                                                 | PyTorch | 作者         | 源地址                                        | 应用领域 |
| ------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- | ------------------------------------------ | ---- |
| MacBERT-base  | base  | [Google Drive](https://drive.google.com/file/d/1aV69OhYzIwj_hn-kO1RiBa-m8QAusQ5b/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/CF2A1F9AEBF859650E8956854A994C1B) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/MacBERT) | 通用   |
| MacBERT-large | large | [Google Drive](https://drive.google.com/file/d/1lWYxnk1EqTA2Q20_IShxBrCPc5VSDCkT/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/805D743F3826EC4F4EB5C774D34432AE) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/MacBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### WoBERT

| 模型          | 版本   | TensorFlow                                              | PyTorch | 作者               | 源地址                                                  | 应用领域 |
| ----------- | ---- | ------------------------------------------------------- | ------- | ---------------- | ---------------------------------------------------- | ---- |
| WoBERT      | base | [百度网盘](https://pan.baidu.com/s/1BrdFSx9_n1q2uWBiQrpalw) | -       | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/WoBERT) | 通用   |
| WoBERT-plus | base | [百度网盘](https://pan.baidu.com/s/1Ltq3ltQsyBCj56zoOOvI9A) | -       | ZhuiyiTechnology | [GitHub](https://github.com/ZhuiyiTechnology/WoBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### XLNET

| 模型             | 版本     | TensorFlow                                                                                                                                                 | PyTorch                                                                            | 作者         | 源地址                                              | 应用领域 |
| -------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ---------- | ------------------------------------------------ | ---- |
| XLNet-base     | base   | [Google Drive](https://drive.google.com/open?id=1m9t-a4gKimbkP5rqGXXsEAEPhJSZ8tvx) · [讯飞云](http://pan.iflytek.com/#/link/32619C31BDEFAF2D82CB8C7F66F01D5C) | [Google Drive](https://drive.google.com/open?id=1mPDgcMfpqAf2wk9Nl8OaMj654pYrWXaR) | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-XLNet) | 通用   |
| XLNet-mid      | middle | [Google Drive](https://drive.google.com/open?id=1342uBc7ZmQwV6Hm6eUIN_OnBSz1LcvfA) · [讯飞云](http://pan.iflytek.com/#/link/ED7DF7ED04B871AFE8E4D97704B9134D) | [Google Drive](https://drive.google.com/open?id=1u-UmsJGy5wkXgbNK4w9uRnC0RxHLXhxy) | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-XLNet) | 通用   |
| XLNet-zh-Large | large  | [百度网盘](https://pan.baidu.com/s/1dy0Z27DoZdMpSmoz1Q4G5A)                                                                                                    | -                                                                                  | brightmart | [GitHub](https://github.com/brightmart/xlnet_zh) | 通用   |

[← 返回主页](../README.md#nlu系列)

### ELECTRA

| 模型                    | 版本    | TensorFlow                                                                                                                                                                 | PyTorch | 作者         | 源地址                                                | 应用领域 |
| --------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ---------- | -------------------------------------------------- | ---- |
| ELECTRA-180g-large    | large | [Google Drive](https://drive.google.com/file/d/1P9yAuW0-HR7WvZ2r2weTnx3slo6f5u9q/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/7605874F5A11CD693C60EAB79005CCF3) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 通用   |
| ELECTRA-180g-small-ex | small | [Google Drive](https://drive.google.com/file/d/1NYJTKH1dWzrIBi86VSUK-Ml9Dsso_kuf/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/3EFCF909FC5CFEA6F0EA7AA774C64CF0) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 通用   |
| ELECTRA-180g-base     | base  | [Google Drive](https://drive.google.com/file/d/1RlmfBgyEwKVBFagafYvJgyCGuj7cTHfh/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/38E14C9BDBE8E93F09DFE2198E308489) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 通用   |
| ELECTRA-180g-small    | small | [Google Drive](https://drive.google.com/file/d/177EVNTQpH2BRW-35-0LNLjV86MuDnEmu/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/D1B8FE678FA5BC31AA43BD99AD09913E) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 通用   |
| legal-ELECTRA-large   | large | [Google Drive](https://drive.google.com/file/d/1jPyVi_t4QmTkFy7PD-m-hG-lQ8cIETzD/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/CC111ED9B1D4AE7E26C69A520A6D8759) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 司法领域 |
| legal-ELECTRA-base    | base  | [Google Drive](https://drive.google.com/file/d/12ZLaoFgpqGJxSi_9KiQV-jdVN4XRGMiD/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/CC111ED9B1D4AE7E26C69A520A6D8759) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 司法领域 |
| legal-ELECTRA-small   | small | [Google Drive](https://drive.google.com/file/d/1arQ5qNTNoc1OyMH8wBUKdTMy2QponIFY/view?usp=sharing) · [讯飞云](http://pan.iflytek.com/#/link/CC111ED9B1D4AE7E26C69A520A6D8759) | -       | Yiming Cui | [GitHub](https://github.com/ymcui/Chinese-ELECTRA) | 司法领域 |
| ELECTRA-tiny          | tiny  | [Google Drive](https://drive.google.com/file/d/1UP4byt4-kgenwST0KvyMYNbln6FfaSLp/view?usp=sharing) · [百度网盘](https://pan.baidu.com/share/init?surl=4b-IiCkjRg-6XIYPXnezZA)  | -       | CLUE       | [GitHub](https://github.com/CLUEbenchmark/ELECTRA) | 通用   |

[← 返回主页](../README.md#nlu系列)

### ZEN

- 2019 | ZEN: Pre-training Chinese Text Encoder Enhanced by N-gram Representations | Shizhe Diao, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/1911.00720.pdf)
- 2021 | ZEN 2.0: Continue Training and Adaption for N-gram Enhanced Text Encoders | Yan Song, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2105.01279.pdf)

| 模型              | 版本    | TensorFlow | PyTorch                                                                                                                                          | 作者                                                                | 源地址                                                    | 应用领域 |
| --------------- | ----- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------ | ---- |
| ZEN-Base        | base  | <p>[Google Drive](https://drive.google.com/open?id=1oxNdYMQOpFe3QlttH98bAqg_FQiiVeMr)[百度网盘](https://pan.baidu.com/s/1E2ylFnzGSkwBc8tY_OqZYg)</p> | [Sinovation Ventures AI Institute](https://github.com/sinovation) | [github](https://github.com/sinovation/ZEN)            | 通用   |
| Erlangshen-ZEN2 | large | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Erlangshen-ZEN2-668M-Chinese)                                                                        | [IDEA-CCNL](https://github.com/IDEA-CCNL)                         | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 通用   |

[← 返回主页](../README.md#nlu系列)

### ERNIE

- 2019 | ERNIE: Enhanced Representation through Knowledge Integration | Yu Sun, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1904.09223)
- 2020 | SKEP: Sentiment Knowledge Enhanced Pre-training for Sentiment Analysis | Hao Tian, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2005.05635)
- 2020 | ERNIE-Gram: Pre-Training with Explicitly N-Gram Masked Language Modeling for Natural Language Understanding | Dongling Xiao, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2010.12148)

| 模型                      | 版本    | PaddlePaddle                                                             | PyTorch | 作者                                              | 源地址                                                                     | 应用领域 |
| ----------------------- | ----- | ------------------------------------------------------------------------ | ------- | ----------------------------------------------- | ----------------------------------------------------------------------- | ---- |
| ernie-1.0-base          | base  | [link](https://ernie-github.cdn.bcebos.com/model-ernie1.0.1.tar.gz)      | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/ERNIE)                         | 通用   |
| ernie\_1.0\_skep\_large | large | [link](https://senta.bj.bcebos.com/skep/ernie_1.0_skep_large_ch.tar.gz)  | [Baidu](https://github.com/baidu)               | [github](https://github.com/baidu/Senta)                                | 情感分析 |
| ernie-gram              | base  | [link](https://ernie-github.cdn.bcebos.com/model-ernie-gram-zh.1.tar.gz) | [Baidu](https://github.com/baidu)               | [github](https://github.com/PaddlePaddle/ERNIE/tree/develop/ernie-gram) | 通用   |

备注:

> PaddlePaddle转TensorFlow可参考: [tensorflow\_ernie](https://github.com/ArthurRizar/tensorflow_ernie)

> PaddlePaddle转PyTorch可参考: [ERNIE-Pytorch](https://github.com/nghuyong/ERNIE-Pytorch)

[← 返回主页](../README.md#nlu系列)

### ERNIE3

- 2021 | ERNIE 3.0: Large-scale Knowledge Enhanced Pre-training for Language Understanding and Generation | Yu Sun, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2107.02137)
- 2021 | ERNIE 3.0 Titan: Exploring Larger-scale Knowledge Enhanced Pre-training for Language Understanding and Generation | Shuohuan Wang, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2106.02241)

| 模型               | 版本                             | PaddlePaddle                                                                                       | PyTorch                                                         | 作者                                              | 源地址                                                                                  | 应用领域 |
| ---------------- | ------------------------------ | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ | ---- |
| ernie-3.0-base   | 12-layer, 768-hidden, 12-heads | [link](https://bj.bcebos.com/paddlenlp/models/transformers/ernie_3.0/ernie_3.0_base_zh.pdparams)   | \[[🤗HF\]](https://huggingface.co/nghuyong/ernie-3.0-base-zh)   | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/PaddleNLP/tree/develop/model_zoo/ernie-3.0) | 通用   |
| ernie-3.0-medium | 6-layer, 768-hidden, 12-heads  | [link](https://bj.bcebos.com/paddlenlp/models/transformers/ernie_3.0/ernie_3.0_medium_zh.pdparams) | \[[🤗HF\]](https://huggingface.co/nghuyong/ernie-3.0-medium-zh) | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/PaddleNLP/tree/develop/model_zoo/ernie-3.0) | 通用   |
| ernie-3.0-mini   | 6-layer, 384-hidden, 12-heads  | [link](https://bj.bcebos.com/paddlenlp/models/transformers/ernie_3.0/ernie_3.0_mini_zh.pdparams)   | \[[🤗HF\]](https://huggingface.co/nghuyong/ernie-3.0-mini-zh)   | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/PaddleNLP/tree/develop/model_zoo/ernie-3.0) | 通用   |
| ernie-3.0-micro  | 4-layer, 384-hidden, 12-heads  | [link](https://bj.bcebos.com/paddlenlp/models/transformers/ernie_3.0/ernie_3.0_micro_zh.pdparams)  | \[[🤗HF\]](https://huggingface.co/nghuyong/ernie-3.0-micro-zh)  | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/PaddleNLP/tree/develop/model_zoo/ernie-3.0) | 通用   |
| ernie-3.0-nano   | 4-layer, 312-hidden, 12-heads  | [link](https://bj.bcebos.com/paddlenlp/models/transformers/ernie_3.0/ernie_3.0_nano_zh.pdparams)   | \[[🤗HF\]](https://huggingface.co/nghuyong/ernie-3.0-nano-zh)   | [PaddlePaddle](https://github.com/PaddlePaddle) | [github](https://github.com/PaddlePaddle/PaddleNLP/tree/develop/model_zoo/ernie-3.0) | 通用   |

> PaddlePaddle转PyTorch可参考: [ERNIE-Pytorch](https://github.com/nghuyong/ERNIE-Pytorch)

[← 返回主页](../README.md#nlu系列)

### RoFormer

- 2021 | RoFormer: Enhanced Transformer with Rotary Position Embedding | Jianlin Su, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2104.09864)
- 2021 | Transformer升级之路：2、博采众长的旋转式位置编码 | 苏剑林. | spaces | [`Blog post`](https://kexue.fm/archives/8265)

| 模型            | 版本         | TensorFlow                                                                                                                                                        | PyTorch | 作者                                                      | 源地址                                                       | 应用领域 |
| ------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------- | --------------------------------------------------------- | ---- |
| roformer      | base(L12)  | [百度网盘-xy9x](https://pan.baidu.com/s/1fiss862YsGCwf2HvU_Jm-g)                                                                                                      | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer)    | 通用   |
| roformer      | small(L6)  | [百度网盘-gy97](https://pan.baidu.com/s/1iIXgZHHCgrYGXVRRSSCVPg)                                                                                                      | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer)    | 通用   |
| roformer-char | base(L12)  | [百度网盘-bt94](https://pan.baidu.com/s/1Q1pq8F4Fsl6bTipUAkqeDQ)                                                                                                      | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer)    | 通用   |
| roformerV2    | small(L6)  | [百度网盘-ttn4](https://pan.baidu.com/s/1huUrC9P60Afggo8AfiUcmA)[追一](https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/chinese_roformer-v2-char_L-6_H-384_A-6.zip)    | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer-v2) | 通用   |
| roformerV2    | base(L12)  | [百度网盘-pfoh](https://pan.baidu.com/s/1qcnN4LVKVe0-mnHlkN3-6Q)[追一](https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/chinese_roformer-v2-char_L-12_H-768_A-12.zip)  | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer-v2) | 通用   |
| roformerV2    | large(L24) | [百度网盘-npfv](https://pan.baidu.com/s/1QiJWSZrGxn8vek-8myvL6w)[追一](https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/chinese_roformer-v2-char_L-24_H-1024_A-16.zip) | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/roformer-v2) | 通用   |

[← 返回主页](../README.md#nlu系列)

### StructBERT

- 2019 | StructBERT: Incorporating Language Structures into Pre-training for Deep Language Understanding | Wei Wang, et al. | arXiv | [`PDF`](https://arxiv.org/abs/1908.04577)

| 模型         | 版本         | TensorFlow | PyTorch                                                                       | 作者                                    | 源地址                                                                 | 应用领域 |
| ---------- | ---------- | ---------- | ----------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------- | ---- |
| StructBERT | large(L24) | [阿里云](https://alice-open.oss-cn-zhangjiakou.aliyuncs.com/StructBERT/ch_model) | [Alibaba](https://github.com/alibaba) | [github](https://github.com/alibaba/AliceMind/tree/main/StructBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### Lattice-BERT

- 2021 | Lattice-BERT: Leveraging Multi-Granularity Representations in Chinese Pre-trained Language Models | Yuxuan Lai, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2104.07204.pdf)

| 模型          | 版本        | TensorFlow | PyTorch                                                                                                  | 作者                                    | 源地址                                                                  | 应用领域 |
| ----------- | --------- | ---------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------- | -------------------------------------------------------------------- | ---- |
| LatticeBERT | tiny(L4)  | [阿里云](https://alice-open.oss-cn-zhangjiakou.aliyuncs.com/LatticeBERT/chinese_labert-tiny-std-512.tar.gz) | [Alibaba](https://github.com/alibaba) | [github](https://github.com/alibaba/AliceMind/tree/main/LatticeBERT) | 通用   |
| LatticeBERT | small(L6) | [阿里云](https://alice-open.oss-cn-zhangjiakou.aliyuncs.com/LatticeBERT/chinese_labert-lite-std-512.tar.gz) | [Alibaba](https://github.com/alibaba) | [github](https://github.com/alibaba/AliceMind/tree/main/LatticeBERT) | 通用   |
| LatticeBERT | base(L12) | [阿里云](https://alice-open.oss-cn-zhangjiakou.aliyuncs.com/LatticeBERT/chinese_labert-base-std-512.tar.gz) | [Alibaba](https://github.com/alibaba) | [github](https://github.com/alibaba/AliceMind/tree/main/LatticeBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### Mengzi-BERT

- 2021 | Mengzi: Towards Lightweight yet Ingenious Pre-trained Models for Chinese | Zhuosheng Zhang, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2110.06696)

| 模型              | 版本        | TensorFlow | PyTorch                                                          | 作者                                      | 源地址                                          | 应用领域 |
| --------------- | --------- | ---------- | ---------------------------------------------------------------- | --------------------------------------- | -------------------------------------------- | ---- |
| Mengzi-BERT     | base(L12) | \[[🤗HF\]](https://huggingface.co/Langboat/mengzi-bert-base)     | [Langboat](https://github.com/Langboat) | [github](https://github.com/Langboat/Mengzi) | 通用   |
| Mengzi-BERT-fin | base(L12) | \[[🤗HF\]](https://huggingface.co/Langboat/mengzi-bert-base-fin) | [Langboat](https://github.com/Langboat) | [github](https://github.com/Langboat/Mengzi) | 金融财经 |

[← 返回主页](../README.md#nlu系列)

### Bloom

- 2022 | Bloom: BigScience Large Open-science Open-access Multilingual Language Model | huggingface bigscience | - | [`BLOG`](https://bigscience.huggingface.co/blog/bloom)

| 模型           | 版本      | TensorFlow | PyTorch                                                  | 作者                                          | 源地址                                                   | 应用领域 |
| ------------ | ------- | ---------- | -------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------- | ---- |
| bloom-6b4-zh | 6B(L30) | \[[🤗HF\]](https://huggingface.co/Langboat/bloom-6b4-zh) | [Langboat](https://huggingface.co/Langboat) | [github](https://github.com/huggingface/transformers) | 通用   |

> 注：作者另有bloom-389m-zh到bloom-2b5-zh等多个中文模型

[← 返回主页](../README.md#nlu系列)

### TaCL

- 2021 | TaCL: Improving BERT Pre-training with Token-aware Contrastive Learning | Yixuan Su, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2111.04198.pdf)

| 模型   | 版本        | TensorFlow | PyTorch                                                                | 作者                                    | 源地址                                       | 应用领域 |
| ---- | --------- | ---------- | ---------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------- | ---- |
| TaCL | base(L12) | \[[🤗HF\]](https://huggingface.co/cambridgeltl/tacl-bert-base-chinese) | [yxuansu](https://github.com/yxuansu) | [github](https://github.com/yxuansu/TaCL) | 通用   |

[← 返回主页](../README.md#nlu系列)

### MC-BERT

- 2021 | MC-BERT: Conceptualized Representation Learning for Chinese Biomedical Text Mining | alibaba-research | arXiv | [`PDF`](https://arxiv.org/pdf/2008.10813.pdf)

| 模型      | 版本        | TensorFlow | PyTorch                                                                    | 作者                                                      | 源地址                                                       | 应用领域 |
| ------- | --------- | ---------- | -------------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------------------- | ---- |
| MC-BERT | base(L12) | [link](https://drive.google.com/open?id=1ccXRvaeox5XCNP_aSk_ttLBY695Erlok) | [alibaba-research](https://github.com/alibaba-research) | [github](https://github.com/alibaba-research/ChineseBLUE) | 生物医疗 |

[← 返回主页](../README.md#nlu系列)

### 二郎神

| 模型         | 版本         | 类型   | TensorFlow | PyTorch                                                      | 作者                                        | 源地址                                                    | 应用领域 |
| ---------- | ---------- | ---- | ---------- | ------------------------------------------------------------ | ----------------------------------------- | ------------------------------------------------------ | ---- |
| Erlangshen | large(L24) | bert | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Erlangshen-1.3B) | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 中文通用 |

[← 返回主页](../README.md#nlu系列)

### PERT

- 2022 | PERT: Pre-Training BERT with Permuted Language Model | Yiming Cui, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2203.06906)

| 模型         | 版本         | TensorFlow                                                            | PyTorch                                                   | 作者                                     | 源地址                                     | 应用领域 |
| ---------- | ---------- | --------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------- | --------------------------------------- | ---- |
| PERT-base  | base(12L)  | [百度网盘-rcsw](https://pan.baidu.com/s/1yDHkYKmdaJkliTGHWQtdFA?pwd=rcsw) | \[[🤗HF\]](https://huggingface.co/hfl/chinese-pert-base)  | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/PERT) | 通用   |
| PERT-large | large(24L) | [百度网盘-e9hs](https://pan.baidu.com/s/1MG44TRIgqV6m_StfB_yBqQ?pwd=e9hs) | \[[🤗HF\]](https://huggingface.co/hfl/chinese-pert-large) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/PERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### MobileBERT

- 2020 | MobileBERT: a Compact Task-Agnostic BERT for Resource-Limited Devices | Zhiqing Sun, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2004.02984.pdf)

| 模型                          | 版本    | TensorFlow                                                            | PyTorch | 作者                                     | 源地址                                                   | 应用领域 |
| --------------------------- | ----- | --------------------------------------------------------------------- | ------- | -------------------------------------- | ----------------------------------------------------- | ---- |
| Chinese-MobileBERT-base-f2  | base  | [百度网盘-56bj](https://pan.baidu.com/s/16g1LgXXAV01I-cFgPdeOow?pwd=56bj) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/Chinese-MobileBERT) | 通用   |
| Chinese-MobileBERT-base-f4  | base  | [百度网盘-v2v7](https://pan.baidu.com/s/16SGBJhWFYru47EEyTZJljA?pwd=v2v7) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/Chinese-MobileBERT) | 通用   |
| Chinese-MobileBERT-large-f2 | large | [百度网盘-6m5a](https://pan.baidu.com/s/1Kp7n8lQJOtevzMovKSa3kw?pwd=6m5a) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/Chinese-MobileBERT) | 通用   |
| Chinese-MobileBERT-large-f4 | large | [百度网盘-3h9b](https://pan.baidu.com/s/19xz9kH1HmM2Og0Aqn7l6vA?pwd=3h9b) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/Chinese-MobileBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### GAU-α

- 2022 | GAU-α: (FLASH) Transformer Quality in Linear Time | Weizhe Hua, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2202.10447.pdf) | [`blog`](https://spaces.ac.cn/archives/9052)

| 模型                                   | 版本   | TensorFlow                                                                                    | PyTorch | 作者                                                      | 源地址                                                     | 应用领域 |
| ------------------------------------ | ---- | --------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------- | ------------------------------------------------------- | ---- |
| chinese\_GAU-alpha-char\_L-24\_H-768 | base | [下载](https://open.zhuiyi.ai/releases/nlp/models/zhuiyi/chinese_GAU-alpha-char_L-24_H-768.zip) | [ZhuiyiTechnology](https://github.com/ZhuiyiTechnology) | [github](https://github.com/ZhuiyiTechnology/GAU-alpha) | 通用   |

[← 返回主页](../README.md#nlu系列)

### DeBERTa

- 2020 | DeBERTa: Decoding-enhanced BERT with Disentangled Attention | Pengcheng He, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2006.03654) |

| 模型                | 版本     | TensorFlow | PyTorch                                                                                       | 作者                                        | 源地址                                                    | 应用领域 |
| ----------------- | ------ | ---------- | --------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------ | ---- |
| DeBERTa-v2-Large  | large  | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Erlangshen-DeBERTa-v2-320M-Chinese)               | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 通用   |
| DeBERTa-v2-xLarge | xlarge | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Erlangshen-DeBERTa-v2-710M-Chinese)               | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 通用   |
| DeBERTa-v2        | base   | \[[🤗HF\]](https://huggingface.co/IDEA-CCNL/Erlangshen-DeBERTa-v2-186M-Chinese-SentencePiece) | [IDEA-CCNL](https://github.com/IDEA-CCNL) | [github](https://github.com/IDEA-CCNL/Fengshenbang-LM) | 通用   |

[← 返回主页](../README.md#nlu系列)

### GlyphBERT

- 2021 | GlyphCRM: Bidirectional Encoder Representation for Chinese Character with its Glyph | Yuxin li, et al. | arXiv | [`PDF`](https://arxiv.org/pdf/2107.00395.pdf) |

| 模型            | 版本   | TensorFlow | PyTorch                                              | 作者                                        | 源地址                                              | 应用领域 |
| ------------- | ---- | ---------- | ---------------------------------------------------- | ----------------------------------------- | ------------------------------------------------ | ---- |
| GlyphCRM-base | base | \[[🤗HF\]](https://huggingface.co/HIT-TMG/GlyphBERT) | [HITsz-TMG](https://github.com/HITsz-TMG) | [github](https://github.com/HITsz-TMG/GlyphBERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### CKBERT

- 2022 | Revisiting and Advancing Chinese Natural Language Understanding with Accelerated Heterogeneous Knowledge Pre-training | Zhang, Taolin, et al. | arXiv | [`PDF`](https://arxiv.org/abs/2210.05287)

| 模型                  | 版本    | TensorFlow | PyTorch                                                            | 作者                                    | 源地址                                          | 应用领域 |
| ------------------- | ----- | ---------- | ------------------------------------------------------------------ | ------------------------------------- | -------------------------------------------- | ---- |
| pai-ckbert-base-zh  | base  | \[[🤗HF\]](https://huggingface.co/alibaba-pai/pai-ckbert-base-zh)  | [Alibaba](https://github.com/alibaba) | [github](https://huggingface.co/alibaba-pai) | 通用   |
| pai-ckbert-large-zh | large | \[[🤗HF\]](https://huggingface.co/alibaba-pai/pai-ckbert-large-zh) | [Alibaba](https://github.com/alibaba) | [github](https://huggingface.co/alibaba-pai) | 通用   |
| pai-ckbert-huge-zh  | huge  | \[[🤗HF\]](https://huggingface.co/alibaba-pai/pai-ckbert-huge-zh)  | [Alibaba](https://github.com/alibaba) | [github](https://huggingface.co/alibaba-pai) | 通用   |

[← 返回主页](../README.md#nlu系列)

### LERT

- 2022 | LERT: A Linguistically-motivated Pre-trained Language Model | Yiming Cui et al. | arXiv | [`PDF`](https://arxiv.org/abs/2211.05344)

| 模型                 | 版本   | TensorFlow                                                            | PyTorch                                                   | 作者                                     | 源地址                                     | 应用领域 |
| ------------------ | ---- | --------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------- | --------------------------------------- | ---- |
| Chinese-LERT-small | 15m  | [百度网盘-4vuy](https://pan.baidu.com/s/1fBk3em8a5iCMwPLJEBq2pQ?pwd=4vuy) | \[[🤗HF\]](https://huggingface.co/hfl/chinese-lert-small) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/LERT) | 通用   |
| Chinese-LERT-base  | 400m | [百度网盘-9jgi](https://pan.baidu.com/s/1_yb1jCDJ4s2P8OrF_5E_Tg?pwd=9jgi) | \[[🤗HF\]](https://huggingface.co/hfl/chinese-lert-base)  | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/LERT) | 通用   |
| Chinese-LERT-large | 1.2G | [百度网盘-s82t](https://pan.baidu.com/s/1pxsS3almc90DPvMXH6BMYQ?pwd=s82t) | \[[🤗HF\]](https://huggingface.co/hfl/chinese-lert-large) | [Yiming Cui](https://github.com/ymcui) | [github](https://github.com/ymcui/LERT) | 通用   |

[← 返回主页](../README.md#nlu系列)

### RoCBert

- 2022 | RoCBert: Robust Chinese Bert with Multimodal Contrastive Pretraining | Hui Su et al. | ACL | [`PDF`](https://aclanthology.org/2022.acl-long.65.pdf)

| 模型      | 版本   | TensorFlow | PyTorch                                                       | 作者                                      | 源地址                                          | 应用领域 |
| ------- | ---- | ---------- | ------------------------------------------------------------- | --------------------------------------- | -------------------------------------------- | ---- |
| rocbert | base | \[[🤗HF\]](https://huggingface.co/weiweishi/roc-bert-base-zh) | [Weiwe Shi](https://github.com/sww9370) | [github](https://github.com/sww9370/RoCBert) | 通用   |

[← 返回主页](../README.md#nlu系列)

### M3E

| 模型        | 版本    | PyTorch                                               | 作者                                        | 源地址                                            | 备注     |
| --------- | ----- | ----------------------------------------------------- | ----------------------------------------- | ---------------------------------------------- | ------ |
| m3e-base  | base  | [m3e-base](https://huggingface.co/moka-ai/m3e-base)   | [Moka-AI](https://huggingface.co/moka-ai) | [uniem](https://github.com/wangyuxinwhy/uniem) | 文本嵌入模型 |
| M3e-small | Small | [m3e-small](https://huggingface.co/moka-ai/m3e-small) | [Moka-AI](https://huggingface.co/moka-ai) | [uniem](https://github.com/wangyuxinwhy/uniem) | 文本嵌入模型 |

[← 返回主页](../README.md#nlu系列)

### LEALLA

- 2023 | LEALLA: Learning Lightweight Language-agnostic Sentence Embeddings with Knowledge Distillation | Zhuoyuan Mao et al. | EACL | [`PDF`](https://arxiv.org/abs/2302.08387)

| 模型           | 版本    | PyTorch                                                      | 作者              | 源地址 | 备注     |
| ------------ | ----- | ------------------------------------------------------------ | --------------- | --- | ------ |
| LEALLA-base  | base  | [LEALLA-base](https://huggingface.co/setu4993/LEALLA-base)   | Google Research | /   | 文本嵌入模型 |
| LEALLA-large | large | [LEALLA-large](https://huggingface.co/setu4993/LEALLA-large) | Google Research | /   | 文本嵌入模型 |

[← 返回主页](../README.md#nlu系列)


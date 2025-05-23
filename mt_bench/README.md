# LLM Judge
Taken from the official FastChat repo

## Installation

From the evals root directory,
```bash
pip install -e ".[mt_bench]"
```

## Usage

```bash
bash run_vllm.sh <model_path>
bash read.sh <model_path>
```

## Read results

```bash
python qa_browser.py --share
```

There's an error message but it doesn't actually break the viewer. I'm too lazy to fix it and it doesn't really matter.

## Below is the old stuff

## Review Pre-Generated Model Answers and Judgments
We provide pre-generated model answers and judgments for some models.
You can view them at this [demo](https://huggingface.co/spaces/lmsys/mt-bench).

To download the pre-generated data, use
```
python3 download_mt_bench_pregenerated.py
```

After downloading the data, you can view them locally by
```
python3 qa_browser.py --share
```
You can use this QA browser to view the answers generated by you later.

## MT-Bench

### Evaluate a model on MT-bench

#### Step 1. Generate model answers to MT-bench questions
Deleted original because it was the slow backend stuff

#### Step 2. Generate GPT-4 judgments
There are several options to use GPT-4 as a judge, such as pairwise winrate and single-answer grading.
In MT-bench, we recommend single-answer grading as the default mode.
This mode asks GPT-4 to grade and give a score to model's answer directly without pairwise comparison.
For each turn, GPT-4 will give a score on a scale of 10. We then compute the average score on all turns.

```
export OPENAI_API_KEY=XXXXXX  # set the OpenAI API key
python gen_judgment.py --model-list [LIST-OF-MODEL-ID] --parallel [num-concurrent-api-call]
```

e.g.,
```
python gen_judgment.py --model-list vicuna-13b-v1.3 alpaca-13b llama-13b claude-v1 gpt-3.5-turbo gpt-4 --parallel 2
```
The judgments will be saved to `data/mt_bench/model_judgment/gpt-4_single.jsonl`

#### Step 3. Show MT-bench scores

- Show the scores for selected models
  ```
  python show_result.py --model-list vicuna-13b-v1.3 alpaca-13b llama-13b claude-v1 gpt-3.5-turbo gpt-4
  ```
- Show all scores
  ```
  python show_result.py
  ```

---

### Other grading options
Besides score-based single-answer grading, we also support two additional grading options based on win rates:
- `pariwise-baseline`: run pairwise comparison against a baseline model.
- `pairwise-all`: run pairwise comparison between all model pairs on all questions.

#### Option 2: pairwise comparison against a baseline (default: gpt-3.5-turbo)

- Generate GPT-4 judgments
```
python gen_judgment.py --mode pairwise-baseline --model-list vicuna-13b-v1.3 alpaca-13b llama-13b --parallel 2
```
The judgments will be saved to `data/mt_bench/model_judgment/gpt-4_pair.jsonl`

- Show results
```
python show_result.py --mode pairwise-baseline
```

#### Option 3: Run GPT-4 judge with all pair comparisons

Another option is to run pairwise comparisons on all possible pairs.
This could be more expensive when #models increases, but it gives you a more comprehensive information.

```
python gen_judgment.py --mode pairwise-all --model-list [LIST-OF-MODEL-ID] --parallel [num-concurrent-api-call]
```

```
python show_result.py --mode pairwise-all
```

### How to get GPT-3.5/GPT-4/Claude's answer?
- `python gen_api_answer.py --model [MODEL-NAME]` to generate GPT-3.5/4 and Claude's answers.


### How to plot the radar figure?

You can use this [colab notebook](https://colab.research.google.com/drive/15O3Y8Rxq37PuMlArE291P4OC6ia37PQK#scrollTo=5i8R0l-XqkgO) to plot the radar figure for MT-bench.

<img src="data/mt_bench/misc/radar.png" width="600" height="450">


### Other backends
We can also use vLLM for answer generation, which can be faster for the models supported by vLLM.

1. Launch a vLLM worker
```
vllm serve [MODEL-PATH] --dtype auto
```
  - Arguments:
    - `[MODEL-PATH]` is the path to the weights, which can be a local folder or a Hugging Face repo ID.

2. Generate the answers
```
python gen_api_answer.py --model [MODEL-NAME] --openai-api-base http://localhost:8000/v1 --parallel 50
```
  - Arguments:
    - `[MODEL-NAME]` is the name of the model from Step 1.
    - `--parallel` is the number of concurrent API calls to the vLLM worker.


## Agreement Computation
We released 3.3K human annotations for model responses generated by 6 models in response to 80 MT-bench questions. The dataset is available at [lmsys/mt_bench_human_judgments](https://huggingface.co/datasets/lmsys/mt_bench_human_judgments).

This Colab [notebook](https://colab.research.google.com/drive/1ctgygDRJhVGUJTQy8-bRZCl1WNcT8De6?usp=sharing) shows how to compute the agreement between humans and GPT-4 judge with the dataset. Our results show that humans and GPT-4 judge achieve over 80\% agreement, the same level of agreement between humans.

## Datasets
- [Chatbot Arena Conversation Dataset](https://huggingface.co/datasets/lmsys/chatbot_arena_conversations)
- [MT-bench Human Annotation Dataset](https://huggingface.co/datasets/lmsys/mt_bench_human_judgments)


## Citation
Please cite the following paper if you find the code or datasets helpful.
```
@misc{zheng2023judging,
      title={Judging LLM-as-a-judge with MT-Bench and Chatbot Arena}, 
      author={Lianmin Zheng and Wei-Lin Chiang and Ying Sheng and Siyuan Zhuang and Zhanghao Wu and Yonghao Zhuang and Zi Lin and Zhuohan Li and Dacheng Li and Eric. P Xing and Hao Zhang and Joseph E. Gonzalez and Ion Stoica},
      year={2023},
      eprint={2306.05685},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

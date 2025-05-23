"""Generate answers with GPT-4

Usage:
python3 gen_api_answer.py --model gpt-3.5-turbo
"""

import argparse
import json
import os
import time
import concurrent.futures

from openai import OpenAI
import shortuuid
import tqdm

from common import (
    load_questions,
    temperature_config,
    API_MAX_RETRY,
    # chat_completion_anthropic,
    # chat_completion_palm,
)


def reorg_answer_file(answer_file):
    """Sort by question id and de-duplication"""
    answers = {}
    with open(answer_file, "r") as fin:
        for line in fin:
            qid = json.loads(line)["question_id"]
            answers[qid] = line

    qids = sorted(list(answers.keys()))
    with open(answer_file, "w") as fout:
        for qid in qids:
            fout.write(answers[qid])


def get_answer(
    client,
    question: dict,
    model: str,
    num_choices: int,
    max_tokens: int,
    answer_file: str,
):
    assert (
        args.force_temperature is not None and "required_temperature" in question.keys()
    ) is False
    if args.force_temperature is not None:
        temperature = args.force_temperature
    elif "required_temperature" in question.keys():
        temperature = question["required_temperature"]
    elif question["category"] in temperature_config:
        temperature = temperature_config[question["category"]]
    else:
        temperature = 0.7

    choices = []
    # chat_state = None  # for palm-2 model
    for i in range(num_choices):
        messages = []

        turns = []
        reasoning_turns = []
        for j in range(len(question["turns"])):
            messages.append({"role": "user", "content": question["turns"][j]})

            # if model in ANTHROPIC_MODEL_LIST:
            #     output = chat_completion_anthropic(model, conv, temperature, max_tokens)
            # elif model == "palm-2-chat-bison-001":
            #     chat_state, output = chat_completion_palm(
            #         chat_state, model, conv, temperature, max_tokens
            #     )
            # else:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            reasoning_content, content = getattr(response.choices[0].message, "reasoning_content", ""), response.choices[0].message.content
            asst_message = {"role": "assistant", "content": content}
            if reasoning_content:
                asst_message["reasoning_content"] = reasoning_content

            messages.append(asst_message)
            turns.append(content)
            reasoning_turns.append(reasoning_content)

        choices.append({"index": i, "turns": turns, "reasoning_turns": reasoning_turns})

    # Dump answers
    ans = {
        "question_id": question["question_id"],
        "answer_id": shortuuid.uuid(),
        "model_id": model,
        "choices": choices,
        "tstamp": time.time(),
    }

    os.makedirs(os.path.dirname(answer_file), exist_ok=True)
    with open(answer_file, "a") as fout:
        fout.write(json.dumps(ans) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bench-name",
        type=str,
        default="mt_bench",
        help="The name of the benchmark question set.",
    )
    parser.add_argument("--answer-file", type=str, help="The output answer file.")
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    parser.add_argument(
        "--num-choices",
        type=int,
        default=1,
        help="How many completion choices to generate.",
    )
    parser.add_argument(
        "--force-temperature", type=float, help="Forcibly set a sampling temperature."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="The maximum number of new generated tokens.",
    )
    parser.add_argument(
        "--question-begin",
        type=int,
        help="A debug option. The begin index of questions.",
    )
    parser.add_argument(
        "--question-end", type=int, help="A debug option. The end index of questions."
    )
    parser.add_argument(
        "--parallel", type=int, default=1, help="The number of concurrent API calls."
    )
    parser.add_argument("--openai-api-base", type=str, default=None)
    args = parser.parse_args()

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        max_retries=API_MAX_RETRY,
    )

    if args.openai_api_base is not None:
        client.base_url = args.openai_api_base

    question_file = f"data/{args.bench_name}/question.jsonl"
    questions = load_questions(question_file, args.question_begin, args.question_end)

    if args.answer_file:
        answer_file = args.answer_file
    else:
        model_basename = os.path.basename(os.path.normpath(args.model))
        answer_file = f"data/{args.bench_name}/model_answer/{model_basename}.jsonl"
    print(f"Output to {answer_file}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = []
        for question in questions:
            future = executor.submit(
                get_answer,
                client,
                question,
                args.model,
                args.num_choices,
                args.max_tokens,
                answer_file,
            )
            futures.append(future)

        for future in tqdm.tqdm(
            concurrent.futures.as_completed(futures), total=len(futures)
        ):
            future.result()

    reorg_answer_file(answer_file)

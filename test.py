from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

completion = client.chat.completions.create(
  model="deepseek-ai/deepseek-v3.1-terminus",
  messages=[{"role":"user","content":"hello"}],
  temperature=0.2,
  top_p=0.7,
  max_tokens=8192,
  extra_body={"chat_template_kwargs": {"thinking":False}},
  stream=True
)

for chunk in completion:
    if not getattr(chunk, "choices", None):
        continue
    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    if reasoning:
        print(reasoning, end="")
    if chunk.choices and chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")



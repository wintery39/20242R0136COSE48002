from langchain.prompts import FewShotPromptTemplate
from ai.krEVprompt import (
    krEV_task_description,
    krEV_example_prompt,
    krEV_suffix,
    krEV_connectivity_description,
    krEV_measurability_description,
    krEV_directivity_description,
    krEV_connectivity_examples,
)

krEV_fewshot_prompt = FewShotPromptTemplate(
    prefix=" ",
    examples=krEV_connectivity_examples,
    example_prompt=krEV_example_prompt,
    suffix=" ",
)

final_prompt = krEV_fewshot_prompt.format()

print(final_prompt)

from pathlib import Path


def load_prompt(name:str):
    prompt_file = Path(__file__).parents[1]/"prompts"/f"{name}.prompt"
    return prompt_file.read_text()

if __name__=="__main__":
    print(load_prompt("correct_sql"))
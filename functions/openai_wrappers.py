


def summarize_text(text: str, client) -> str:
    """
    Summarize the given text using OpenAI API.

    Args:
        client: OpenAI client object for making API calls.
        text (str): The text to be summarized.

    Returns:
        str: The summary of the given text.
    """
    prompt = f"Please provide a concise summary of the following text:\n\n{text}"
    summary = _get_completion(client = client, prompt=prompt)
    return summary


def _get_completion(client, prompt, model="gpt-4o-mini", max_tokens=500, temperature=0.7):
    """
    Simple method, which return answeer for the prompt by chatGpt
    """
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,  
    )
    return response.choices[0].message.content
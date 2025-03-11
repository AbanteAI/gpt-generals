# GPT Generals

A game project that leverages Large Language Models (LLMs), developed by Mentat.

## About

GPT Generals is an innovative gaming project that integrates artificial intelligence through the use of Large Language Models. The project is being developed by Mentat to explore new possibilities in AI-driven gaming experiences.

## Status

This project is currently under development.

## Getting Started

### Environment Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Add your OpenRouter API key to the `.env` file:
   ```
   OPEN_ROUTER_KEY=your_api_key_here
   ```
   You can get an API key from [OpenRouter](https://openrouter.ai/keys).

### Example Scripts

The `test_scripts` directory contains several example scripts:

- `simple_structured_example.py`: Demonstrates structured output using a simple animal information model
- `test_structured_output.py`: Shows more complex structured output using game state analysis
- `simulation.py`: Runs a simple simulation of the game

Run any of these scripts directly:

```bash
python test_scripts/simple_structured_example.py
```

## Features

### Structured Output Support

The project supports structured outputs from LLMs using Pydantic models. This allows you to:

1. Define the exact structure you want from the LLM
2. Use type hints for better IDE support and validation
3. Access fields programmatically with proper typing

Example usage:

```python
from pydantic import BaseModel, Field
from llm_utils import Messages, call_openrouter

# Define your schema
class MyResponse(BaseModel):
    field1: str = Field(..., description="Description of field1")
    field2: int = Field(..., description="Description of field2")
    
# Call the LLM with your schema
response = call_openrouter(
    messages=my_messages,
    response_model=MyResponse,
)

# Access fields directly
print(response.field1)
print(response.field2)
```

See the example scripts for more detailed usage.

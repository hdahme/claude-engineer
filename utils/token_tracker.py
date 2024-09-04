from rich.console import Console
from rich.table import Table
from typing import Dict

class TokenTracker:
    def __init__(self):
        self.console = Console()
        self.token_usage = {
            'main_model': {'input': 0, 'output': 0},
            'tool_checker': {'input': 0, 'output': 0},
            'code_editor': {'input': 0, 'output': 0},
            'code_execution': {'input': 0, 'output': 0}
        }
        self.cost_per_1k_tokens = {
            'main_model': {'input': 0.01, 'output': 0.03},
            'tool_checker': {'input': 0.01, 'output': 0.03},
            'code_editor': {'input': 0.01, 'output': 0.03},
            'code_execution': {'input': 0.01, 'output': 0.03}
        }

    def update_token_usage(self, model: str, input_tokens: int, output_tokens: int):
        """
        Update token usage for a specific model.

        Args:
        model (str): The name of the model ('main_model', 'tool_checker', 'code_editor', or 'code_execution').
        input_tokens (int): The number of input tokens used.
        output_tokens (int): The number of output tokens used.
        """
        if model in self.token_usage:
            self.token_usage[model]['input'] += input_tokens
            self.token_usage[model]['output'] += output_tokens
        else:
            self.console.print(f"[bold red]Error: Unknown model '{model}'[/bold red]")

    def get_total_tokens(self) -> Dict[str, int]:
        """
        Get the total number of tokens used across all models.

        Returns:
        Dict[str, int]: A dictionary with 'input' and 'output' total token counts.
        """
        total_input = sum(usage['input'] for usage in self.token_usage.values())
        total_output = sum(usage['output'] for usage in self.token_usage.values())
        return {'input': total_input, 'output': total_output}

    def calculate_cost(self) -> float:
        """
        Calculate the total cost based on token usage and cost per 1k tokens.

        Returns:
        float: The total cost in dollars.
        """
        total_cost = 0
        for model, usage in self.token_usage.items():
            input_cost = (usage['input'] / 1000) * self.cost_per_1k_tokens[model]['input']
            output_cost = (usage['output'] / 1000) * self.cost_per_1k_tokens[model]['output']
            total_cost += input_cost + output_cost
        return total_cost

    def display_token_usage(self):
        """
        Display a formatted table of token usage and estimated cost.
        """
        table = Table(title="Token Usage and Cost Estimate")
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Input Tokens", style="magenta")
        table.add_column("Output Tokens", style="magenta")
        table.add_column("Estimated Cost", style="green")

        total_cost = 0
        for model, usage in self.token_usage.items():
            input_tokens = usage['input']
            output_tokens = usage['output']
            input_cost = (input_tokens / 1000) * self.cost_per_1k_tokens[model]['input']
            output_cost = (output_tokens / 1000) * self.cost_per_1k_tokens[model]['output']
            model_cost = input_cost + output_cost
            total_cost += model_cost

            table.add_row(
                model.replace('_', ' ').title(),
                str(input_tokens),
                str(output_tokens),
                f"${model_cost:.4f}"
            )

        table.add_row(
            "Total",
            str(self.get_total_tokens()['input']),
            str(self.get_total_tokens()['output']),
            f"${total_cost:.4f}",
            style="bold"
        )

        self.console.print(table)

    def reset_token_usage(self):
        """
        Reset all token usage counters to zero.
        """
        for model in self.token_usage:
            self.token_usage[model] = {'input': 0, 'output': 0}

    def update_cost_per_1k_tokens(self, model: str, input_cost: float, output_cost: float):
        """
        Update the cost per 1k tokens for a specific model.

        Args:
        model (str): The name of the model.
        input_cost (float): The new cost per 1k input tokens.
        output_cost (float): The new cost per 1k output tokens.
        """
        if model in self.cost_per_1k_tokens:
            self.cost_per_1k_tokens[model]['input'] = input_cost
            self.cost_per_1k_tokens[model]['output'] = output_cost
        else:
            self.console.print(f"[bold red]Error: Unknown model '{model}'[/bold red]")

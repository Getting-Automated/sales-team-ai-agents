from typing import Dict, Optional
from litellm import completion
from litellm.utils import ModelResponse
import json
from datetime import datetime
import yaml
from pathlib import Path

class TokenTracker:
    def __init__(self):
        self.usage_log = []
        self.total_tokens = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0
        self._load_pricing_config()

    def _load_pricing_config(self):
        """Load pricing configuration from YAML file"""
        config_path = Path(__file__).parent.parent / "config" / "pricing.yaml"
        with open(config_path, 'r') as f:
            self.pricing_config = yaml.safe_load(f)['models']

    def callback(self, kwargs: Dict, response: Optional[ModelResponse], start_time: Optional[datetime], end_time: Optional[datetime]):
        """Callback function for LiteLLM to track token usage"""
        if response:
            usage = response.usage
            if usage:
                # Extract usage information
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                
                # Calculate cost based on model
                model = kwargs.get('model', '').replace('openai/', '')  # Remove provider prefix
                cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
                
                # Update totals
                self.total_tokens += total_tokens
                self.total_prompt_tokens += prompt_tokens
                self.total_completion_tokens += completion_tokens
                self.total_cost += cost

                # Log the usage
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'model': model,
                    'prompt_tokens': prompt_tokens,
                    'completion_tokens': completion_tokens,
                    'total_tokens': total_tokens,
                    'cost': cost,
                    'agent': kwargs.get('agent_name', 'unknown')
                }
                self.usage_log.append(log_entry)

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on pricing configuration"""
        if model not in self.pricing_config:
            print(f"Warning: Model {model} not found in pricing config. Using default pricing.")
            return 0.0

        model_config = self.pricing_config[model]
        unit = model_config.get('unit_of_tokens', 1000000)  # Default to 1M tokens if not specified
        
        # Calculate costs using standard pricing (not batch or cached)
        input_price = model_config.get('input_price', 0)
        output_price = model_config.get('output_price', 0)
        
        prompt_cost = (prompt_tokens * input_price) / unit
        completion_cost = (completion_tokens * output_price) / unit
        
        return round(prompt_cost + completion_cost, 6)

    def get_usage_summary(self) -> Dict:
        """Get a summary of token usage and costs"""
        return {
            'total_tokens': self.total_tokens,
            'total_prompt_tokens': self.total_prompt_tokens,
            'total_completion_tokens': self.total_completion_tokens,
            'total_cost': round(self.total_cost, 4),
            'usage_by_agent': self._get_usage_by_agent(),
            'usage_by_model': self._get_usage_by_model()
        }

    def _get_usage_by_agent(self) -> Dict:
        """Get token usage breakdown by agent"""
        usage_by_agent = {}
        for entry in self.usage_log:
            agent = entry['agent']
            if agent not in usage_by_agent:
                usage_by_agent[agent] = {
                    'total_tokens': 0,
                    'total_cost': 0
                }
            usage_by_agent[agent]['total_tokens'] += entry['total_tokens']
            usage_by_agent[agent]['total_cost'] += entry['cost']
        return usage_by_agent

    def _get_usage_by_model(self) -> Dict:
        """Get token usage breakdown by model"""
        usage_by_model = {}
        for entry in self.usage_log:
            model = entry['model']
            if model not in usage_by_model:
                usage_by_model[model] = {
                    'total_tokens': 0,
                    'total_cost': 0
                }
            usage_by_model[model]['total_tokens'] += entry['total_tokens']
            usage_by_model[model]['total_cost'] += entry['cost']
        return usage_by_model

    def save_usage_log(self, filepath: str):
        """Save the usage log to a JSON file"""
        with open(filepath, 'w') as f:
            json.dump({
                'summary': self.get_usage_summary(),
                'detailed_log': self.usage_log
            }, f, indent=2)

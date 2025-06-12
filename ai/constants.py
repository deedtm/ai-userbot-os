from g4f.models import *

ais_models = {
    "gpt": [
        gpt_4o_mini,
        gpt_4,
        gpt_4o,
        # gpt_4_turbo,
        # gpt_35_turbo,
    ],
    "llama": [
        llama_3_2_11b,
        llama_3_2_1b,
        llama_3_1_405b,
        llama_3_1_70b,
        llama_3_1_8b,
        llama_3_8b,
        llama_2_7b,
    ],
    "claude": [
        claude_3_5_sonnet,
        claude_3_sonnet,
        claude_3_opus,
        claude_3_haiku,
        claude_2_1,
    ],
    "gemini": [gemini_pro, gemini_flash, gemini],
    "grok": [grok_beta, grok_2, grok_2_mini],
    "qwen": [qwen_2_72b, qwen_1_5_7b],
}
ais_names = list(ais_models.keys())

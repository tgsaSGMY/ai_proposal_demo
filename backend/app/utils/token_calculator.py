# utils/token_calculator.py

import tiktoken
from typing import List, Dict, Optional
import logging

# 设置一个 logger，方便在工具函数中记录信息
logger = logging.getLogger(__name__)

# 一个简单的缓存，避免重复加载 encoding 对象
_encoding_cache = {}

def _get_encoding_for_model(model_name: str) -> Optional[tiktoken.Encoding]:
    """
    根据模型名称获取或缓存 tiktoken 的 encoding 对象。
    """
    if model_name in _encoding_cache:
        return _encoding_cache[model_name]
    
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        _encoding_cache[model_name] = encoding
        return encoding
    except KeyError:
        # 如果模型名称不在 tiktoken 的预设中（例如一些变体或自定义名称），
        # 我们默认使用 gpt-4 的 "cl100k_base" 作为最常见的备选方案。
        logger.warning(
            f"Model '{model_name}' not found in tiktoken. "
            f"Falling back to 'cl100k_base' encoding."
        )
        try:
            # get_encoding 可能会在某些环境下失败，所以也加上 try-except
            encoding = tiktoken.get_encoding("cl100k_base")
            _encoding_cache[model_name] = encoding
            return encoding
        except Exception as e:
            logger.error(f"Failed to get 'cl100k_base' encoding: {e}")
            return None

def calculate_openai_tokens(
    messages: List[Dict[str, str]], 
    model_name: str,
    raw_output_text: str = ""
) -> Dict[str, int]:
    """
    计算 OpenAI API 请求和响应的 token 数量。

    此函数精确模拟 OpenAI 的计费方式，包括每个消息和角色的开销。
    参考: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

    Args:
        messages (List[Dict[str, str]]): 发送给 API 的消息列表，格式为 [{"role": "user", "content": "..."}, ...]。
        model_name (str): 使用的模型名称，例如 "gpt-4", "gpt-3.5-turbo"。
        raw_output_text (str): 模型返回的原始文本响应。

    Returns:
        Dict[str, int]: 一个包含 "input_tokens" 和 "output_tokens" 的字典。
                         如果无法计算（例如 encoding 加载失败），则返回 0。
    """
    encoding = _get_encoding_for_model(model_name)
    
    if not encoding:
        logger.error("Could not load tiktoken encoding. Token calculation failed.")
        return {"input_tokens": 0, "output_tokens": 0}

    # --- 计算 Input Tokens ---
    input_tokens = 0
    for message in messages:
        input_tokens += 4  
        for key, value in message.items():
            input_tokens += len(encoding.encode(value))
            if key == "name":
                input_tokens -= 1  # 如果有 'name'，会覆盖 'role'，所以扣除一个 token

    input_tokens += 3 

    # --- 计算 Output Tokens ---
    output_tokens = len(encoding.encode(raw_output_text)) if raw_output_text else 0
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens
    }

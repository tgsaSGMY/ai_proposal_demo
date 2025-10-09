# 管理微调后的模型

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from typing import Dict, Any, Optional
import logging
from threading import RLock

logger = logging.getLogger(__name__)

class LoRAModelManager:
    """
    一个线程安全的管理器，用于加载、缓存和提供基础模型及LoRA适配模型。
    """
    def __init__(self):
        self.base_models: Dict[str, Any] = {}
        self.lora_models: Dict[str, Any] = {}
        self.tokenizers: Dict[str, Any] = {}
        self.lock = RLock()

    def _load_base_model_and_tokenizer(self, base_model_id: str):
        with self.lock:
            # 双重检查锁定，防止在等待锁时其他线程已经加载了模型
            if base_model_id in self.base_models:
                logger.info(f"Base model '{base_model_id}' found in cache during locked check.")
                return

            logger.info(f"Loading base model and tokenizer for '{base_model_id}'... This may take a while.")
            try:
                tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True, use_fast=False)
                if tokenizer.pad_token is None:
                    tokenizer.pad_token_id = tokenizer.eos_token_id
                
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                )

                model = AutoModelForCausalLM.from_pretrained(
                    base_model_id,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                )
                
                self.tokenizers[base_model_id] = tokenizer
                self.base_models[base_model_id] = model
                logger.info(f"Successfully loaded and cached base model '{base_model_id}'.")

            except Exception as e:
                logger.error(f"Failed to load base model '{base_model_id}': {e}", exc_info=True)
                raise

    def get_lora_model(self, model_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lora_model_id = model_info.get("id")
        base_model_id = model_info.get("base_model_id")
        adapter_path = model_info.get("adapter_path")

        if not all([lora_model_id, base_model_id, adapter_path]):
            logger.error(f"Model info is incomplete for LoRA loading: {model_info}")
            return None

        # 检查 LoRA 模型缓存
        if lora_model_id in self.lora_models:
            logger.info(f"LoRA model '{lora_model_id}' found in cache.")
            return {
                "model": self.lora_models[lora_model_id],
                "tokenizer": self.tokenizers[base_model_id]
            }

        # 如果 LoRA 模型未缓存，则加载
        with self.lock:
            if lora_model_id in self.lora_models:
                return {"model": self.lora_models[lora_model_id], "tokenizer": self.tokenizers[base_model_id]}

            try:
                if base_model_id not in self.base_models:
                    self._load_base_model_and_tokenizer(base_model_id)

                base_model = self.base_models[base_model_id]
                
                logger.info(f"Loading LoRA adapter from '{adapter_path}' and attaching to '{base_model_id}'...")
                
                lora_model = PeftModel.from_pretrained(base_model, adapter_path)
                
                self.lora_models[lora_model_id] = lora_model
                logger.info(f"Successfully loaded and cached LoRA model '{lora_model_id}'.")

                return {
                    "model": self.lora_models[lora_model_id],
                    "tokenizer": self.tokenizers[base_model_id]
                }
            except Exception as e:
                logger.error(f"Failed to load LoRA model '{lora_model_id}': {e}", exc_info=True)
                return None
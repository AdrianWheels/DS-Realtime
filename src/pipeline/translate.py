import asyncio
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class NLLBTranslator:
    def __init__(self, model_name: str, device: str = "cuda"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=torch.float16).to(device)
        self.device = device

    async def translate(self, text: str, src_lang: str = "spa_Latn", tgt_lang: str = "eng_Latn", max_new_tokens: int = 256) -> str:
        # NLLB usa src_lang en el tokenizer, y forced_bos_token_id para el idioma de salida
        def _translate():
            self.tokenizer.src_lang = src_lang
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            bos_token_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
            with torch.no_grad():
                generated = self.model.generate(
                    **inputs,
                    forced_bos_token_id=bos_token_id,
                    max_new_tokens=max_new_tokens,
                    num_beams=3,
                    no_repeat_ngram_size=3,
                )
            out = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
            return out[0]

        return await asyncio.to_thread(_translate)

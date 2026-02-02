import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_huggingface import HuggingFacePipeline

def load_spark2scale_model():
    """
    Loads your local T5-XL model for inference.
    """
    model_id = "Dohahemdann/Spark2Scale"
    
    print(f"📥 Loading local model: {model_id}...")

    # Load Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Load Model (Use device_map="auto" to use GPU if available)
    # quantize to 8-bit if you have low VRAM (requires bitsandbytes)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_id,
        device_map="auto", 
        torch_dtype=torch.float16, # Use float16 for GPU efficiency
        # load_in_8bit=True # Uncomment this if you have <16GB VRAM
    )

    # Create a simplified pipeline
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=1024, # T5 handles long context well
        temperature=0.1,
        do_sample=True,
        repetition_penalty=1.2
    )

    # Wrap in LangChain
    local_llm = HuggingFacePipeline(pipeline=pipe)
    return local_llm
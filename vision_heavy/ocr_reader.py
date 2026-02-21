"""
OCR Reader Module - Indian HSRP Optimized
Extracts text using EasyOCR with strict alphanumeric filtering.
"""

from typing import List, Tuple
import numpy as np
try:
    import easyocr
except ImportError:
    easyocr = None

class OCRReader:
    def __init__(self, languages=['en'], use_gpu=False):
        self.module_name = "OCR_READER"
        self.languages = languages
        self.use_gpu = use_gpu
        self.reader = None
        self._initialized = False

    def initialize(self) -> bool:
        if easyocr is None:
            print("❌ EasyOCR not installed.")
            return False
            
        print(f"   📖 Initializing OCR Engine (GPU={self.use_gpu})...")
        # Initialize Reader
        self.reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
        self._initialized = True
        return True

    def read_text(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Reads text with strict alphanumeric whitelist.
        """
        if not self._initialized: return "", 0.0
            
        try:
            # OPTIMIZATION: Restrict characters to Indian License Plate valid set
            # specific characters to reduce confusion (e.g. avoid 'Q' if not used much, etc.)
            allow_list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            
            results = self.reader.readtext(
                image, 
                detail=1,
                allowlist=allow_list, # <--- KEY UPGRADE
                paragraph=False
            )
            
            # Find the detection with highest confidence matches
            best_text = ""
            best_conf = 0.0
            
            for (bbox, text, prob) in results:
                # Filter short noise
                if len(text) < 4: continue
                
                if prob > best_conf:
                    best_conf = prob
                    best_text = text
                    
            return best_text.upper(), best_conf
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return "", 0.0
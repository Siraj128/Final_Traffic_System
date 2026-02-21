"""
Plate Validator Module - Indian Traffic Standards
Validates and corrects text for:
1. Standard State Plates (MH 12 AB 1234)
2. BH Series (22 BH 1234 AA)
3. Commercial / Old Formats
"""

import re

class PlateValidator:
    def __init__(self):
        self.module_name = "PLATE_VALIDATOR"
        
        # --- REGEX PATTERNS ---
        # 1. Standard: 2 Char State + 2 Digit Dist + 1-3 Char Series + 4 Digit Number
        # Ex: MH 12 AB 1234, DL 10 C 1234
        self.regex_standard = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$')
        
        # 2. BH Series: 2 Digit Year + BH + 4 Digit Number + 2 Char Series
        # Ex: 22 BH 1234 AA
        self.regex_bh = re.compile(r'^[0-9]{2}BH[0-9]{4}[A-Z]{2}$')
        
        self._initialized = True

    def initialize(self) -> bool:
        return True

    def validate(self, text: str) -> bool:
        """Returns True if text matches any valid Indian format."""
        if not text: return False
        clean = self.clean_text(text)
        
        if self.regex_standard.match(clean): return True
        if self.regex_bh.match(clean): return True
        
        return False

    def clean_text(self, text: str) -> str:
        """
        Intelligently repairs OCR errors based on Indian Syntax.
        """
        # 1. Basic Cleanup
        text = re.sub(r'[\s\-\.\:\_]', '', text).upper()
        
        # 2. Heuristic Correction
        text = list(text)
        n = len(text)
        
        # Case A: Standard Format (Length 10, e.g., MH12AB1234)
        if n == 10:
            # Pos 0,1: STATE CODE (Letters) -> Fix 0->O, 1->I, 8->B
            self._fix_char(text, [0, 1], to_digit=False)
            
            # Pos 2,3: DISTRICT CODE (Digits) -> Fix O->0, I->1, B->8
            self._fix_char(text, [2, 3], to_digit=True)
            
            # Pos 4,5: SERIES (Letters)
            self._fix_char(text, [4, 5], to_digit=False)
            
            # Pos 6,7,8,9: NUMBER (Digits)
            self._fix_char(text, [6, 7, 8, 9], to_digit=True)

        # Case B: BH Series (Length 10, e.g., 22BH1234AA)
        elif n == 10 and text[2] == 'B' and text[3] == 'H':
            # Pos 0,1: YEAR (Digits)
            self._fix_char(text, [0, 1], to_digit=True)
            # Pos 4,5,6,7: NUMBER (Digits)
            self._fix_char(text, [4, 5, 6, 7], to_digit=True)
            # Pos 8,9: SERIES (Letters)
            self._fix_char(text, [8, 9], to_digit=False)

        return "".join(text)

    def _fix_char(self, char_list, indices, to_digit=True):
        """Helper to swap ambiguous chars."""
        # Maps for correction
        dict_to_digit = {'O': '0', 'I': '1', 'Z': '2', 'B': '8', 'S': '5', 'G': '6', 'A': '4'}
        dict_to_letter = {'0': 'O', '1': 'I', '2': 'Z', '8': 'B', '5': 'S', '6': 'G', '4': 'A'}
        
        for i in indices:
            if i < len(char_list):
                c = char_list[i]
                if to_digit and c in dict_to_digit:
                    char_list[i] = dict_to_digit[c]
                elif not to_digit and c in dict_to_letter:
                    char_list[i] = dict_to_letter[c]
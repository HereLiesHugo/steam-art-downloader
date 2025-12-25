import re
import struct

class VdfParser:
    """
    Parses Steam VDF (Valve Data Format) files.
    Supports both Text VDF (e.g. libraryfolders.vdf) and Binary VDF (e.g. shortcuts.vdf).
    """

    @staticmethod
    def load_text(file_path: str) -> dict:
        """Loads a text VDF file from disk."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return VdfParser.parse_text(f.read())

    @staticmethod
    def parse_text(content: str) -> dict:
        """
        Parses text VDF content into a dictionary.
        Simple parser handling nested {} and "key" "value" pairs.
        """
        content = VdfParser._strip_comments(content)
        
        # Tokenizer regex: match quoted strings or structural characters
        token_pattern = re.compile(r'"((?:\\.|[^\\"])*)"|([{}])')
        
        stack = []
        root = {}
        current = root
        expect_key = True
        key = None

        for match in token_pattern.finditer(content):
            token_str = match.group(1)
            token_struct = match.group(2)

            if token_struct == '{':
                if key is None:
                    # Should not happen in valid VDF where { follows a key
                    continue
                new_dict = {}
                if isinstance(current, list):
                     # This happens if we handled duplicate keys by making a list, 
                     # but logic here simplifies to standard dict overwrites or direct nesting
                     pass
                
                current[key] = new_dict
                stack.append(current)
                current = new_dict
                expect_key = True
                key = None
            
            elif token_struct == '}':
                if stack:
                    current = stack.pop()
                expect_key = True
            
            elif token_str is not None:
                # Unescape string
                val = token_str.encode('utf-8').decode('unicode_escape')
                
                if expect_key:
                    key = val
                    expect_key = False
                else:
                    current[key] = val
                    expect_key = True
                    key = None
        
        return root

    @staticmethod
    def _strip_comments(content: str) -> str:
        """Removes // comments."""
        lines = content.splitlines()
        clean_lines = []
        for line in lines:
            line = line.split('//')[0].strip()
            if line:
                clean_lines.append(line)
        return '\n'.join(clean_lines)

    @staticmethod
    def load_binary(file_path: str) -> dict:
        """Loads a binary VDF file (like shortcuts.vdf) from disk."""
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'rb') as f:
            return VdfParser.parse_binary(f.read())

    @staticmethod
    def parse_binary(data: bytes) -> dict:
        """
        Parses binary VDF data (shortcuts.vdf).
        Format:
        Type (1 byte) + Name (null-term string) + Value (depends on type)
        Types: 0=Map, 1=String, 2=Int, 8=EndMap
        """
        ptr = 0
        
        def read_string():
            nonlocal ptr
            end = data.find(b'\x00', ptr)
            if end == -1:
                raise ValueError("Unterminated string")
            s = data[ptr:end].decode('utf-8', errors='replace')
            ptr = end + 1
            return s

        def read_map():
            nonlocal ptr
            res = {}
            while ptr < len(data):
                t = data[ptr]
                ptr += 1
                
                if t == 8: # End of Map
                    break
                
                name = read_string()
                
                if t == 0: # Nested Map
                    res[name] = read_map()
                elif t == 1: # String
                    res[name] = read_string()
                elif t == 2: # Int32
                    if ptr + 4 > len(data): break
                    val = struct.unpack('<I', data[ptr:ptr+4])[0]
                    ptr += 4
                    res[name] = val
                elif t == 7: # UInt64
                    if ptr + 8 > len(data): break
                    val = struct.unpack('<Q', data[ptr:ptr+8])[0]
                    ptr += 8
                    res[name] = val
                else:
                    # Unknown type - we will likely lose sync here
                    # Attempt to read a string? Or just break?
                    # Breaking is safer than reading garbage.
                    print(f"Warning: Unknown VDF type {t} at {ptr-1} for key {name}")
                    break
            return res

        # Shortcuts.vdf usually starts with \x00shortcuts\x00 then the map starts.
        # But technically it's a map named "shortcuts".
        # Let's see if we can just parse it as a map if it matches the pattern?
        # Usually file starts with 0x00 then "shortcuts" then 0x00 then the body.
        # Which is Type=0, Name="shortcuts", Value=Map...
        
        # But typically we call it on the *content* of the list.
        # Let's just try to read from 0.
        try:
            return read_map()
        except Exception:
            # Fallback or empty
            return {}

import os

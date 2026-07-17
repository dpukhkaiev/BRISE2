"""
Waffle Feature Model Parser (textX-based)

Uses the Waffle grammar grammar.tx to parse .wfl files.

Requirements:
    textx

How to use:
    from wfl_parser_textx import WflParserTextX
    
    parser = WflParserTextX("grammar.tx", "base.wfl")
    features = parser.parse_features()
    min_max = parser.parse_min_max()
    enums = parser.parse_enums()
"""

import re
from typing import Dict, List, Any, Optional
from textx import metamodel_from_file


class WflParserTextX:
    """Parser for Waffle Feature Model (.wfl) files using textX"""
    
    def __init__(self, grammar_path: str, wfl_path: str):
        """
        Initialize parser with grammar and .wfl file
        """
        self.grammar_path = grammar_path
        self.wfl_path = wfl_path
        
        # Parse the .wfl file using textX
        self.metamodel = metamodel_from_file(grammar_path)
        self.model = self.metamodel.model_from_file(wfl_path)
        
        # Read raw content for min_max and enum extraction
        with open(wfl_path, 'r') as f:
            self.raw_content = f.read()
        
        # Cache
        self._features_cache = None
        self._min_max_cache = None
        self._enums_cache = None
    
    def parse_features(self) -> List[List[str]]:
        """
        Extract feature groups (xor/or/optional) for pairwise testing.
        
        Returns:
            List of feature dimensions, each dimension is a list of options.
        """
        if self._features_cache is not None:
            return self._features_cache
        
        self._features_cache = []
        
        # Traverse all top-level elements
        for element in self.model.elements:
            if self._get_class_name(element) == 'Feature':
                self._traverse_feature(element, parent_path="")
        
        return self._features_cache
    
    def _get_class_name(self, obj) -> str:
        return obj.__class__.__name__
    
    def _traverse_feature(self, feature, parent_path: str):
        """
        Recursively traverse the feature tree.
        
        Args:
            feature: textX feature object
            parent_path: dot-separated path of parent features
        """
        # Skip abstract features
        if feature.abstract:
            # Still traverse children to find nested xor/or groups
            self._traverse_children(feature, parent_path)
            return
        
        # Build full path
        name = feature.name
        full_path = f"{parent_path}.{name}" if parent_path else name
        
        # Get group cardinality (xor, or, mux, opt, or None)
        gcard = feature.gcard
        
        # Get feature cardinality (?, *, +, or None)
        fcard = feature.fcard
        
        # Check if this is an xor or or group
        if gcard in ['xor', 'or']:
            children = self._get_direct_children(feature)
            is_optional = (fcard == '?')
            
            if gcard == 'xor':
                # xor: exactly one must be selected
                options = []
                
                # If optional xor, add None option
                if is_optional:
                    options.append(f"{full_path}.None")
                
                # Add all children as options
                for child_name in children:
                    options.append(f"{full_path}.{child_name}")
                
                # Only add if there are choices to make
                if len(options) > 1:
                    self._features_cache.append(options)
            
            elif gcard == 'or':
                # or: one or more can be selected
                # Each child becomes an optional dimension
                for child_name in children:
                    child_path = f"{full_path}.{child_name}"
                    self._features_cache.append([child_path, f"{child_path}.None"])
        
        # Check for optional feature without group card (just fcard = ?)
        elif fcard == '?' and gcard is None:
            self._features_cache.append([full_path, f"{full_path}.None"])

        # Check for fcard='*' leaf features (e.g. StopCondition instances).
        # These have no xor/or/? descendants, the on/off decision is the feature itself.
        # Contrast with Surrogate * and Optimizer * which contain xor/or children
        # and are containers, not choices
        elif fcard == '*' and gcard is None:
            if not self._has_decision_children(feature):
                self._features_cache.append([full_path, f"{full_path}.None"])

        # Recurse into children
        self._traverse_children(feature, full_path)
    
    def _traverse_children(self, feature, parent_path: str):
        # Traverse all children of feature
        if feature.nested:
            for nested in feature.nested:
                if nested.child:
                    for child in nested.child:
                        if self._get_class_name(child) == 'Feature':
                            self._traverse_feature(child, parent_path)
    
    def _get_direct_children(self, feature) -> List[str]:
        #Get names of direct children features
        children = []
        if feature.nested:
            for nested in feature.nested:
                if nested.child:
                    for child in nested.child:
                        if self._get_class_name(child) == 'Feature':
                            # Skip nested xor/or groups, they are groups, not options
                            if child.gcard not in ['xor', 'or']:
                                children.append(child.name)
        return children
    
    def _has_decision_children(self, feature) -> bool:
        if feature.nested:
            for nested in feature.nested:
                if nested.child:
                    for child in nested.child:
                        if self._get_class_name(child) == 'Feature':
                            if child.gcard in ['xor', 'or'] or child.fcard == '?':
                                return True
                            if self._has_decision_children(child):
                                return True
        return False

    def parse_min_max(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract min/max constraints for numeric attributes
        
        Returns:
            Dict mapping attribute name to {type, min, max}
        """
        if self._min_max_cache is not None:
            return self._min_max_cache
        
        result = {}

        # Find attribute declarations: Name -> type
        attr_pattern = r'(\w+)\s*->\s*(integer|float)'
        for match in re.finditer(attr_pattern, self.raw_content):
            attr_name = match.group(1)
            attr_type = match.group(2)
            if attr_name not in result:
                result[attr_name] = {"type": attr_type, "min": None, "max": None}
        
        # Find min constraints
        for pattern, is_strict in [(r'\[(\w+)\s*>=\s*([\d.]+)\]', False), 
                                    (r'\[(\w+)\s*>\s*([\d.]+)\]', True)]:
            for match in re.finditer(pattern, self.raw_content):
                attr_name = match.group(1)
                value = float(match.group(2))
                if is_strict:
                    value += 0.01 if attr_name in result and result[attr_name]["type"] == "float" else 1
                if attr_name in result:
                    if result[attr_name]["min"] is None or value > result[attr_name]["min"]:
                        result[attr_name]["min"] = value
        
        # Find max constraints
        for pattern, is_strict in [(r'\[(\w+)\s*<=\s*([\d.]+)\]', False),
                                    (r'\[(\w+)\s*<\s*([\d.]+)\]', True)]:
            for match in re.finditer(pattern, self.raw_content):
                attr_name = match.group(1)
                value = float(match.group(2))
                if is_strict:
                    value -= 0.01 if attr_name in result and result[attr_name]["type"] == "float" else 1
                if attr_name in result:
                    if result[attr_name]["max"] is None or value < result[attr_name]["max"]:
                        result[attr_name]["max"] = value
        
        # Convert integers
        for attr_name, constraints in result.items():
            if constraints["type"] == "integer":
                if constraints["min"] is not None:
                    constraints["min"] = int(constraints["min"])
                if constraints["max"] is not None:
                    constraints["max"] = int(constraints["max"])
        
        self._min_max_cache = result
        return result
    
    def parse_enums(self) -> Dict[str, List[str]]:
        """
        Extract enum values for string attributes
        Returns:
            Dict mapping attribute name to list of valid values.
        """
        if self._enums_cache is not None:
            return self._enums_cache
        
        result = {}
        enum_pattern = r'\[(\w+)\s+in\s+\{([^}]+)\}\]'

        for match in re.finditer(enum_pattern, self.raw_content):
            attr_name = match.group(1)
            values_str = match.group(2)
            values = re.findall(r'"([^"]+)"', values_str)
            if values:
                result[attr_name] = values
        
        self._enums_cache = result
        return result
    
    def get_all_parsed_data(self) -> Dict[str, Any]:
        return {
            "features": self.parse_features(),
            "min_max": self.parse_min_max(),
            "enums": self.parse_enums(),
        }
    


def parse_features(grammar_path: str, wfl_path: str) -> List[List[str]]:
    """Parse features from a .wfl file."""
    return WflParserTextX(grammar_path, wfl_path).parse_features()

def parse_min_max(grammar_path: str, wfl_path: str) -> Dict[str, Dict[str, Any]]:
    """Parse min/max constraints from a .wfl file."""
    return WflParserTextX(grammar_path, wfl_path).parse_min_max()

def parse_enums(grammar_path: str, wfl_path: str) -> Dict[str, List[str]]:
    """Parse enum values from a .wfl file."""
    return WflParserTextX(grammar_path, wfl_path).parse_enums()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python wfl_parser_textx.py <grammar.tx> <file.wfl>")
        print("Example: python wfl_parser_textx.py grammar.tx base.wfl")
        sys.exit(1)
    
    grammar_path = sys.argv[1]
    wfl_path = sys.argv[2]
    
    parser = WflParserTextX(grammar_path, wfl_path)
    features = parser.parse_features()
    min_max = parser.parse_min_max()
    enums = parser.parse_enums()

    lines = []

    lines.append("=" * 70)
    lines.append("PARSED FEATURES (for pairwise)")
    lines.append("=" * 70)
    for i, dimension in enumerate(features):
        if len(dimension) > 2:
            dim_type = "XOR"
        elif dimension[0].endswith('.None') and len(dimension) > 2:
            dim_type = "XOR?"
        else:
            dim_type = "OPT"
        lines.append(f"\n{i + 1}. [{dim_type}] ({len(dimension)} options):")
        for option in dimension:
            lines.append(f"     - {option}")

    lines.append("\n" + "=" * 70)
    lines.append("PARSED MIN/MAX VALUES")
    lines.append("=" * 70)
    for name, constraints in sorted(min_max.items()):
        if constraints["min"] is not None or constraints["max"] is not None:
            lines.append(f"  {name}: min={constraints['min']}, max={constraints['max']} ({constraints['type']})")

    lines.append("\n" + "=" * 70)
    lines.append("PARSED ENUM VALUES")
    lines.append("=" * 70)
    for name, values in sorted(enums.items()):
        lines.append(f"  {name}: {values}")

    lines.append("\n" + "=" * 70)
    lines.append("SUMMARY")
    lines.append("=" * 70)
    lines.append(f"  Total feature dimensions: {len(features)}")
    total_options = sum(len(d) for d in features)
    lines.append(f"  Total feature options: {total_options}")
    lines.append(f"  Total min/max attributes: {len(min_max)}")
    lines.append(f"  Total enum attributes: {len(enums)}")

    output_path = "output_textx.txt"
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Output written to {output_path}")

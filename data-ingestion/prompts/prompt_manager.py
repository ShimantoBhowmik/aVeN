"""
Prompt Template Manager for AvenAI
Handles loading and formatting of prompt templates with proper placeholders
"""

import os
from typing import Dict, List


class PromptTemplateManager:
    """Manages prompt templates for the AvenAI system"""
    
    def __init__(self, templates_folder: str = "prompts"):
        self.templates_folder = templates_folder
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all template files from the templates folder"""
        if not os.path.exists(self.templates_folder):
            raise FileNotFoundError(f"Templates folder not found: {self.templates_folder}")
        
        for filename in os.listdir(self.templates_folder):
            if filename.endswith('.txt'):
                template_name = filename.replace('.txt', '')
                template_path = os.path.join(self.templates_folder, filename)
                
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        self.templates[template_name] = f.read()
                except Exception as e:
                    print(f"Error loading template {filename}: {e}")
    
    def get_template(self, template_name: str) -> str:
        """Get a template by name"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found. Available templates: {list(self.templates.keys())}")
        return self.templates[template_name]
    
    def format_aven_ai_prompt(self, context: str, question: str, sources: List[Dict]) -> str:
        """
        Format the AvenAI prompt with context, question, and sources
        
        Args:
            context: The retrieved context from the knowledge base
            question: The user's question
            sources: List of source information dictionaries
            
        Returns:
            Formatted prompt string
        """
        template = self.get_template('aven_ai_template')
        
        # Format sources for display
        sources_text = ""
        if sources:
            sources_text = "\\n".join([
                f"- **{source.get('title', 'Unknown')}**\\n"
                f"  - Source: {source.get('source_reference', 'Unknown')}\\n"
                f"  - Type: {source.get('source_type', 'Unknown').upper()}\\n"
                f"  - File: {source.get('filename', 'Unknown')}"
                for source in sources
            ])
        else:
            sources_text = "No specific sources available for this query."
        
        # Replace placeholders
        formatted_prompt = template.format(
            context=context,
            question=question,
            sources=sources_text
        )
        
        return formatted_prompt
    
    def list_templates(self) -> List[str]:
        """List all available templates"""
        return list(self.templates.keys())


# Example usage and testing
if __name__ == "__main__":
    # Test the prompt manager
    manager = PromptTemplateManager()
    
    # Test data
    test_context = "Aven is a credit card that lets homeowners use their home equity to get low rates."
    test_question = "What is Aven?"
    test_sources = [
        {
            "title": "About Aven",
            "source_reference": "https://www.aven.com/about",
            "source_type": "web",
            "filename": "About-Aven-Card.txt"
        }
    ]
    
    try:
        formatted_prompt = manager.format_aven_ai_prompt(test_context, test_question, test_sources)
        print("Template loaded and formatted successfully!")
        print("\\n" + "="*50)
        print("FORMATTED PROMPT:")
        print("="*50)
        print(formatted_prompt)
    except Exception as e:
        print(f"Error: {e}")

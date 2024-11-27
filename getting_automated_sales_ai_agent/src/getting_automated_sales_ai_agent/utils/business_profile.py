"""Business profile utilities for reading and parsing business context."""

from pathlib import Path
from typing import Dict, List, Any

def read_business_profile(profile_path: str = None) -> Dict[str, Any]:
    """Read and parse the business profile text file into a structured format.
    
    Args:
        profile_path: Path to the business profile text file. If None, uses default path.
        
    Returns:
        Dict containing structured business profile information.
    """
    if profile_path is None:
        # Get the default path relative to this file
        config_dir = Path(__file__).parent.parent / 'config'
        profile_path = config_dir / 'business_profile.txt'
    
    profile_data = {
        'company': {},
        'products': [],
        'pain_points': [],
        'value_props': [],
        'success_stories': [],
        'process': [],
        'results': []
    }
    
    current_section = None
    
    with open(profile_path, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        if not line.startswith('>'):
            # This is a section header
            if "Company Name:" in line:
                current_section = 'company'
            elif "What does your company do?" in line:
                current_section = 'company_description'
            elif "What are your main products or services?" in line:
                current_section = 'products'
            elif "What problems do you solve" in line:
                current_section = 'pain_points'
            elif "What makes your company special?" in line:
                current_section = 'value_props'
            elif "Share some success stories" in line:
                current_section = 'success_stories'
            elif "How do you typically work" in line:
                current_section = 'process'
            elif "What results can clients typically expect" in line:
                current_section = 'results'
        else:
            # This is content
            content = line[1:].strip()  # Remove '>' and whitespace
            
            if current_section == 'company':
                profile_data['company']['name'] = content
            elif current_section == 'company_description':
                profile_data['company']['description'] = content
            elif current_section in ['products', 'pain_points', 'value_props', 
                                   'success_stories', 'process', 'results']:
                profile_data[current_section].append(content)
    
    return profile_data

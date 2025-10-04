"""
PDF form filling functionality with AcroForm support and overlay fallback.
Handles IRS forms and other PDF documents requiring data population.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
from datetime import datetime

try:
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    PdfReader = PdfWriter = canvas = letter = inch = None

logger = logging.getLogger(__name__)

class PDFFiller:
    """
    Handles PDF form filling using AcroForm fields or coordinate-based overlay.
    Supports IRS forms and other standardized documents.
    """
    
    def __init__(self, mappings_dir: str = None):
        """
        Initialize PDF filler.
        
        Args:
            mappings_dir: Directory containing form mapping YAML files
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("PDF dependencies not available. Install PyPDF2 and reportlab.")
            
        if mappings_dir is None:
            mappings_dir = os.path.join(os.path.dirname(__file__), 'mappings')
        
        self.mappings_dir = mappings_dir
        self.form_mappings = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load form mapping configurations from YAML files."""
        if not os.path.exists(self.mappings_dir):
            logger.warning(f"Mappings directory not found: {self.mappings_dir}")
            return
            
        for file_path in Path(self.mappings_dir).glob("*.yaml"):
            try:
                with open(file_path, 'r') as f:
                    mapping = yaml.safe_load(f)
                    
                form_name = file_path.stem
                self.form_mappings[form_name] = mapping
                logger.info(f"Loaded mapping for form: {form_name}")
                
            except Exception as e:
                logger.error(f"Error loading mapping {file_path}: {e}")
    
    def get_available_forms(self) -> List[str]:
        """Get list of available form types."""
        return list(self.form_mappings.keys())
    
    def fill_form(self, 
                  form_type: str, 
                  data: Dict[str, Any], 
                  template_path: Optional[str] = None,
                  output_path: Optional[str] = None) -> str:
        """
        Fill a PDF form with provided data.
        
        Args:
            form_type: Type of form (e.g., 'form_433a')
            data: Dictionary containing form data
            template_path: Path to PDF template (optional)
            output_path: Output file path (optional, auto-generated if None)
            
        Returns:
            Path to filled PDF file
        """
        if form_type not in self.form_mappings:
            raise ValueError(f"Unknown form type: {form_type}")
        
        mapping = self.form_mappings[form_type]
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"{form_type}_filled_{timestamp}.pdf"
        
        # Validate required fields
        self._validate_data(data, mapping)
        
        # Try AcroForm filling first, fall back to overlay
        try:
            if template_path and os.path.exists(template_path):
                return self._fill_acroform(template_path, data, mapping, output_path)
            else:
                return self._create_overlay_pdf(data, mapping, output_path)
                
        except Exception as e:
            logger.error(f"Error filling form {form_type}: {e}")
            raise
    
    def _validate_data(self, data: Dict[str, Any], mapping: Dict[str, Any]):
        """Validate form data against mapping requirements."""
        validation = mapping.get('validation', {})
        required_fields = validation.get('required_fields', [])
        
        # Check required fields
        missing_fields = []
        for field_name in required_fields:
            if not self._get_nested_value(data, field_name):
                missing_fields.append(field_name)
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate field formats
        field_formats = validation.get('field_formats', {})
        for field_name, format_rules in field_formats.items():
            value = self._get_nested_value(data, field_name)
            if value and 'pattern' in format_rules:
                import re
                if not re.match(format_rules['pattern'], str(value)):
                    raise ValueError(f"Invalid format for {field_name}: {format_rules['message']}")
        
        # Check business rules
        business_rules = validation.get('business_rules', [])
        for rule in business_rules:
            if not self._evaluate_business_rule(data, rule['rule']):
                raise ValueError(f"Business rule violation: {rule['message']}")
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation path."""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _evaluate_business_rule(self, data: Dict[str, Any], rule: str) -> bool:
        """Evaluate a business rule expression."""
        # Simple rule evaluation - can be expanded
        # For now, just handle basic comparisons
        if '<=' in rule:
            left, right = rule.split('<=')
            left_val = self._get_nested_value(data, left.strip())
            right_val = self._get_nested_value(data, right.strip())
            return (left_val or 0) <= (right_val or 0)
        elif '>=' in rule:
            left, right = rule.split('>=')
            left_val = self._get_nested_value(data, left.strip())
            right_val = self._get_nested_value(data, right.strip())
            return (left_val or 0) >= (right_val or 0)
        elif '>' in rule:
            left, right = rule.split('>')
            left_val = self._get_nested_value(data, left.strip())
            right_val = self._get_nested_value(data, right.strip())
            return (left_val or 0) > (right_val or 0)
        
        return True
    
    def _fill_acroform(self, 
                      template_path: str, 
                      data: Dict[str, Any], 
                      mapping: Dict[str, Any],
                      output_path: str) -> str:
        """Fill PDF using AcroForm fields."""
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Get form fields
        if "/AcroForm" not in reader.trailer["/Root"]:
            raise ValueError("PDF does not contain AcroForm fields")
        
        # Copy pages and fill fields
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            
            # Fill form fields on this page
            if "/Annots" in page:
                for annotation in page["/Annots"]:
                    annot_obj = annotation.get_object()
                    if "/T" in annot_obj:  # Field name
                        field_name = annot_obj["/T"]
                        
                        # Find mapping for this field
                        field_value = self._find_field_value(field_name, data, mapping)
                        if field_value is not None:
                            # Set field value
                            annot_obj.update({"/V": field_value})
            
            writer.add_page(page)
        
        # Write filled PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        logger.info(f"Filled AcroForm PDF saved to: {output_path}")
        return output_path
    
    def _create_overlay_pdf(self, 
                           data: Dict[str, Any], 
                           mapping: Dict[str, Any],
                           output_path: str) -> str:
        """Create PDF using coordinate-based overlay method."""
        # Create PDF using reportlab
        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        
        # Draw form fields based on coordinates
        sections = ['personal_info', 'employment', 'income', 'expenses', 'assets', 'liabilities']
        
        for section_name in sections:
            if section_name in mapping:
                self._draw_section(c, data, mapping[section_name], width, height)
        
        # Add form header
        self._draw_header(c, mapping.get('form_info', {}), width, height)
        
        c.save()
        logger.info(f"Created overlay PDF saved to: {output_path}")
        return output_path
    
    def _draw_header(self, canvas_obj, form_info: Dict[str, Any], width: float, height: float):
        """Draw form header information."""
        if not form_info:
            return
            
        canvas_obj.setFont("Helvetica-Bold", 14)
        title = form_info.get('name', 'Tax Form')
        canvas_obj.drawString(72, height - 50, title)
        
        canvas_obj.setFont("Helvetica", 10)
        form_number = form_info.get('form_number', '')
        if form_number:
            canvas_obj.drawString(72, height - 70, f"Form {form_number}")
        
        # Add date
        canvas_obj.drawString(width - 150, height - 50, 
                             f"Date: {datetime.now().strftime('%m/%d/%Y')}")
    
    def _draw_section(self, 
                     canvas_obj, 
                     data: Dict[str, Any], 
                     section_mapping: Dict[str, Any],
                     width: float, 
                     height: float):
        """Draw a section of form fields."""
        canvas_obj.setFont("Helvetica", 10)
        
        for field_name, field_config in section_mapping.items():
            if 'coordinates' not in field_config:
                continue
                
            # Get field value
            data_path = field_config.get('data_path', '')
            value = self._get_nested_value(data, data_path)
            
            if value is None:
                continue
            
            # Format value
            formatted_value = self._format_field_value(value, field_config)
            
            # Draw at coordinates
            x, y = field_config['coordinates']
            canvas_obj.drawString(x, height - y, str(formatted_value))
    
    def _format_field_value(self, value: Any, field_config: Dict[str, Any]) -> str:
        """Format field value according to configuration."""
        if value is None:
            return ""
        
        format_type = field_config.get('format', '')
        
        if format_type == 'currency':
            return f"${float(value):,.2f}"
        elif format_type == 'phone' or format_type == '(xxx) xxx-xxxx':
            # Format phone number
            digits = ''.join(filter(str.isdigit, str(value)))
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif 'mask' in field_config:
            # Apply mask (e.g., SSN masking)
            mask = field_config['mask']
            if mask == 'xxx-xx-xxxx' and len(str(value)) >= 9:
                return f"xxx-xx-{str(value)[-4:]}"
        
        return str(value)
    
    def _find_field_value(self, 
                         field_name: str, 
                         data: Dict[str, Any], 
                         mapping: Dict[str, Any]) -> Optional[str]:
        """Find value for a specific form field."""
        # Search through all sections for field mapping
        sections = ['personal_info', 'employment', 'income', 'expenses', 'assets', 'liabilities']
        
        for section_name in sections:
            if section_name in mapping:
                section = mapping[section_name]
                for config_name, config in section.items():
                    if config.get('field_name') == field_name:
                        data_path = config.get('data_path', '')
                        value = self._get_nested_value(data, data_path)
                        return self._format_field_value(value, config) if value else None
        
        return None
    
    def extract_form_fields(self, pdf_path: str) -> Dict[str, Any]:
        """Extract form field information from a PDF."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        reader = PdfReader(pdf_path)
        fields = {}
        
        if "/AcroForm" not in reader.trailer["/Root"]:
            logger.warning("PDF does not contain AcroForm fields")
            return fields
        
        # Extract field information
        acro_form = reader.trailer["/Root"]["/AcroForm"]
        if "/Fields" in acro_form:
            for field in acro_form["/Fields"]:
                field_obj = field.get_object()
                if "/T" in field_obj:
                    field_name = field_obj["/T"]
                    field_type = field_obj.get("/FT", "")
                    field_value = field_obj.get("/V", "")
                    
                    fields[field_name] = {
                        "type": field_type,
                        "value": field_value,
                        "required": "/Ff" in field_obj and field_obj["/Ff"] & 2
                    }
        
        return fields
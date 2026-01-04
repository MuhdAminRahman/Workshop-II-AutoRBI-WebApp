from typing import Dict
import anthropic
import base64
import httpx
from app.config import settings

client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

async def call_claude_api(
    image_url: str,
    extraction_rules: Dict
) -> str:
    """
    Call Claude API to extract equipment data from image.
    
    Args:
        image_url: URL of image from Cloudinary
        extraction_rules: Dict defining what to extract
    
    Returns:
        JSON string with extracted data
    """
    
    # Download image from URL
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(image_url)
        image_data = base64.standard_b64encode(response.content).decode("utf-8")
    
    # Determine media type
    media_type = "image/png" if image_url.endswith(".png") else "image/jpeg"
    
    # Prepare extraction prompt
    fields_list = ", ".join(extraction_rules.get("fields", []))
    
    extraction_prompt = f"""
    Analyze this GA (General Arrangement) drawing image and extract equipment data.
    
    For each piece of equipment visible, extract the following fields:
    {fields_list}
    
    Return the data as valid JSON with this structure:
    {{
      "equipment": [
        {{
          "equipment_number": "E-101",
          "description": "...",
          "components": [
            {{
              "component_name": "Shell",
              "phase": "Vapor",
              "fluid": "...",
              "material_spec": "ASTM A516 Gr 70",
              "material_grade": "70",
              "insulation": "...",
              "design_temp": "150°C",
              "design_pressure": "16 bar",
              "operating_temp": "120°C",
              "operating_pressure": "10 bar"
            }}
          ]
        }}
      ]
    }}
    
    Only return valid JSON, no markdown formatting.
    """
    
    # Call Claude with vision
    message = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": extraction_prompt
                    }
                ],
            }
        ],
    )
    
    return message.content[0].text
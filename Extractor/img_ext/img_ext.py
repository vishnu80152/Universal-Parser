import json
import base64
import requests
from pathlib import Path

class ImageExtractor:
    def __init__(self, model_name: str = "qwen3-vl:4b", ollama_host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_host = ollama_host
        self.endpoint = f"{ollama_host}/api/generate"
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def extract_data(self, image_path: str) -> dict:
        """Extract OCR, description, table data, and flowchart from image"""

        
        if not Path(image_path).exists():
            return {"error": f"Image not found: {image_path}"}
        
        image_base64 = self.encode_image(image_path)
        
        prompts = {
            "ocr_text": "Extract all text from this image exactly as shown. If there is no readable text in the image, respond with 'NO_TEXT'.",
            "image_description": "Provide a detailed description of what's in this image.",
            "table_data": "If there's a table in this image, extract it as JSON. If no table, return empty object.",
            "flowchart": "If this is a flowchart, describe its structure and flow. If not, return empty string."
        }
        
        results = {}
        
        for key, prompt in prompts.items():
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_base64],
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result_text = response.json().get("response", "").strip()
                
                # Special handling for OCR text
                if key == "ocr_text":
                    # Check if there's meaningful text
                    if not result_text or result_text.upper() == "NO_TEXT" or result_text.startswith("Error:"):
                        results[key] = None
                    elif len(result_text) < 3 or result_text.lower() in ["none", "n/a", "null", "no text"]:
                        results[key] = None
                    else:
                        results[key] = result_text
                else:
                    results[key] = result_text
            else:
                results[key] = f"Error: {response.status_code}"
        
        return results
    
    def save_json(self, data: dict, output_path: str) -> None:
        """Save extracted data to JSON file"""
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    extractor = ImageExtractor(model_name="qwen3-vl:4b")
    
    # Example usage
    image_path = "/home/zoro/DEV/chatbot/sample_data/a_city_skyline_with_a_sunset_in_the_background.png"
    output_path = "extracted_data.json"
    
    extracted = extractor.extract_data(image_path)
    extractor.save_json(extracted, output_path)
    
    print(json.dumps(extracted, indent=2))
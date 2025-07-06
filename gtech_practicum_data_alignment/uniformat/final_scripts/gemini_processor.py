import google.generativeai as genai
import json
import time

# Define appropriate limits for Gemini API 
RPM_LIMIT = 10  # Requests Per Minute
TPM_LIMIT = 250000 # Tokens Per Minute 
RPD_LIMIT = 250 # Requests Per Day 

# Schema for Gemini's JSON output (no description field)
UNIFORMAT_EXTRACTION_SCHEMA_NO_DESC = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "level3_code": {
                "type": "string",
                "description": "The Uniformat Level 3 code, e.g., 'A1010', 'B2010'."
            },
            "level3_name": {
                "type": "string",
                "description": "The name corresponding to the Level 3 code, e.g., 'Standard Foundations', 'Exterior Walls'."
            },
            "inclusions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of items explicitly included in this Uniformat element, extracted from the 'Includes' section (each bullet point as a separate string)."
            },
            "exclusions": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of items explicitly excluded from this Uniformat element, extracted from the 'Excludes' section (each bullet point as a separate string), retaining cross-references."
            }
        },
        "required": ["level3_code", "level3_name", "inclusions", "exclusions"]
    }
}

# Schema for Gemini's JSON output for batch description
ENHANCED_DESCRIPTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "level3_code": {
                "type": "string",
                "description": "The Uniformat Level 3 code for which the description was generated."
            },
            "enhanced_description": {
                "type": "string",
                "description": "The comprehensive and detailed description for the Uniformat Level 3 element."
            }
        },
        "required": ["level3_code", "enhanced_description"]
    }
}


def get_initial_uniformat_details_from_gemini_no_desc(text_content, api_key, max_retries=5, initial_delay=5):
    """
    Calls Gemini API to extract Level 3 code, name, inclusions, and exclusions.
    Does NOT extract a description from the PDF.
    Implements exponential backoff for rate limits.
    """
    if not text_content:
        print("No text content provided for Gemini API call.")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    system_instruction = (
        "You are an expert in construction classification systems, specifically Uniformat II. "
        "Your task is to accurately extract detailed information about Uniformat Level 3 elements "
        "from the provided text, focusing solely on the element name, its code, and the explicit "
        "bulleted lists of inclusions and exclusions. Do NOT extract any general prose description "
        "for the element, as none is provided directly preceding the lists."
        "Provide the output strictly as a JSON array according to the specified schema."
    )

    prompt_parts = [
        {"text": f"{system_instruction}\n\n"
                 f"Extract the Uniformat II Level 3 element data from the following document section. "
                 f"For each element, identify its Level 3 code and name. "
                 f"Then, extract the separate lists of its explicit inclusions and exclusions, where each bullet point in the 'Includes' and 'Excludes' sections should be a distinct item in the respective list. "
                 f"Retain any cross-references like '(see section ...)' within the exclusion text.\n\n"
                 f"**Text Content:**\n{text_content}\n\n"
                 f"**Output Schema (JSON):**\n{json.dumps(UNIFORMAT_EXTRACTION_SCHEMA_NO_DESC, indent=2)}\n\n"
                 f"Please provide ONLY the JSON array, with no preamble, explanation, or any other surrounding text. Ensure valid JSON."}
    ]

    for attempt in range(max_retries):
        try:
            print(f"Sending request to Gemini API for initial extraction (Attempt {attempt + 1}/{max_retries})...")
            response = model.generate_content(
                prompt_parts,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            print("Gemini API call successful for initial extraction.")

            # --- DEBUG: Verify Gemini's Part 1 Raw Output ---
            print("\n--- DEBUG: Gemini Part 1 Raw Response Text (first 500 chars) ---")
            print(response.text[:500])
            print("----------------------------------------------------\n")

            parsed_json = json.loads(response.text)

            # --- DEBUG: Verify Parsed JSON Structure ---
            print("\n--- DEBUG: Gemini Part 1 Parsed JSON (first 2 entries + A1030 if found) ---")
            debug_entries = parsed_json[:2]
            a1030_entry = next((item for item in parsed_json if item.get('level3_code') == 'A1030'), None)
            if a1030_entry:
                debug_entries.append(a1030_entry)
            print(json.dumps(debug_entries, indent=2))
            print("----------------------------------------------------\n")

            return parsed_json
        except Exception as e:
            error_message = str(e)
            if "429 You exceeded your current quota" in error_message or "Quota exceeded" in error_message:
                print(f"Rate limit hit for initial extraction. Waiting before retry...")
                sleep_time = initial_delay * (2 ** attempt) # Exponential backoff
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Error calling Gemini API or parsing initial extraction response: {e}")
                print(f"Raw response text (for debugging): {response.text if 'response' in locals() else 'N/A'}")
                return None
    print(f"Failed to get initial Uniformat details after {max_retries} attempts.")
    return None


def generate_enhanced_description_with_gemini_batch(elements_batch, api_key, max_retries=5, initial_delay=5):
    """
    Calls Gemini API to generate detailed descriptions for a batch of elements.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    batch_prompts_list = []
    for element in elements_batch:
        code = element['level3_code']
        name = element['level3_name']
        current_desc = element['current_description']
        inclusions = element['inclusions']
        exclusions = element['exclusions']

        prompt_for_element = f"""
        For Uniformat Code: {code}
        Uniformat Name: {name}
        Current Brief Description (from guide, if any): "{current_desc if current_desc else 'No specific brief description found in the guide, rely on name, code, inclusions, and exclusions.'}"

        Items explicitly INCLUDED in this element:
        {'- ' + '\\n- '.join(inclusions) if inclusions else 'No explicit inclusions listed.'}

        Items explicitly EXCLUDED from this element:
        {'- ' + '\\n- '.join(exclusions) if exclusions else 'No explicit exclusions listed.'}

        Generate a comprehensive and detailed description for the above Uniformat II Level 3 element.
        The description should be professional, clear, and expand upon the provided context.
        Do NOT include the 'Includes' or 'Excludes' lists themselves in your output.
        """
        batch_prompts_list.append(prompt_for_element)

    # Combine all individual prompts into one master prompt for batch processing
    combined_prompt = (
        "You are an expert in Uniformat II classification for construction. "
        "Your task is to generate comprehensive and highly detailed descriptions for the following Uniformat II Level 3 elements. "
        "For each element, use the provided code, name, brief description (if any), inclusions, and exclusions to generate the description. "
        "Do NOT include the 'Includes' or 'Excludes' lists in your generated descriptions. "
        "Provide the output as a JSON array of objects, where each object has 'level3_code' and 'enhanced_description' fields, "
        "strictly following the provided schema.\n\n"
        f"**Output Schema (JSON):**\n{json.dumps(ENHANCED_DESCRIPTION_SCHEMA, indent=2)}\n\n"
        "Here are the details for the Uniformat elements:\n\n"
    )
    for i, p in enumerate(batch_prompts_list):
        combined_prompt += f"--- Element {i+1} ---\n{p}\n\n"

    for attempt in range(max_retries):
        try:
            print(f"Sending batch request to Gemini API for {len(elements_batch)} descriptions (Attempt {attempt + 1}/{max_retries})...")
            response = model.generate_content(
                [{"text": combined_prompt}],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=2000 * len(elements_batch)
                )
            )
            print(f"Gemini API call successful for batch.")

            # --- DEBUG: Verify Gemini's Part 2 Raw Output ---
            print(f"\n--- DEBUG: Gemini Part 2 Raw Response Text for batch (first 500 chars) ---")
            print(response.text[:500])
            print("----------------------------------------------------\n")

            parsed_json = json.loads(response.text)
            return parsed_json
        except Exception as e:
            error_message = str(e)
            if "429 You exceeded your current quota" in error_message or "Quota exceeded" in error_message:
                print(f"Rate limit hit for batch. Waiting before retry...")
                sleep_time = initial_delay * (2 ** attempt) # Exponential backoff
                print(f"Retrying in {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
            else:
                print(f"Error generating enhanced descriptions for batch: {e}")
                print(f"Raw response text (for debugging): {response.text if 'response' in locals() else 'N/A'}")
                return None
    print(f"Failed to generate enhanced descriptions for batch after {max_retries} attempts due to rate limits.")
    return None
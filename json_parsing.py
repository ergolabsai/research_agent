import json
import re


def fix_common_json_errors(json_string):
    """
    Attempt to fix common JSON formatting errors before parsing.
    """
    # Remove any markdown formatting
    json_string = re.sub(r'^```json\s*', '', json_string, flags=re.MULTILINE)
    json_string = re.sub(r'^```\s*', '', json_string, flags=re.MULTILINE)
    json_string = re.sub(r'\s*```$', '', json_string)

    # Remove any trailing comments or extra text after the JSON
    last_brace = json_string.rfind('}')
    if last_brace != -1:
        json_string = json_string[:last_brace + 1]

    # Remove XML-style tags and HTML comments
    json_string = re.sub(r'<[^>]+>', '', json_string)
    json_string = re.sub(r'<!--.*?-->', '', json_string, flags=re.DOTALL)

    # FIX THE MAIN ISSUE: }, { should be }, "property": {
    # This pattern finds: }, optional whitespace, {, then "property":
    # and replaces with: , "property":
    json_string = re.sub(r'\},\s*\{("[\w\s\\]+"\s*:\s*\{)', r', \1', json_string)

    # Also handle the case where there's a string property name without braces
    # }, {"property": should be , "property":
    json_string = re.sub(r'\},\s*\{("[\w\s\\]+":\s*")', r', \1', json_string)
    json_string = re.sub(r'\},\s*\{("[\w\s\\]+":\s*\d)', r', \1', json_string)
    json_string = re.sub(r'\},\s*\{("[\w\s\\]+":\s*\[)', r', \1', json_string)

    # Fix missing commas between properties
    json_string = re.sub(r'"\s*\n\s*"', '",\n"', json_string)

    # Fix trailing commas before closing braces/brackets
    json_string = re.sub(r',(\s*[}\]])', r'\1', json_string)

    return json_string.strip()


def safe_json_parse(json_string, max_retries=3):
    """
    Safely parse JSON with multiple fix attempts.
    """
    # First attempt: parse as-is
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Initial parse failed: {e}")
        error_context = json_string[max(0, e.pos - 50):min(len(json_string), e.pos + 50)]
        print(f"Error at position {e.pos}: ...{error_context}...")

    # Apply fixes with increasing aggressiveness
    for attempt in range(max_retries):
        try:
            fixed = fix_common_json_errors(json_string)

            # Additional aggressive fix for later attempts
            if attempt > 0:
                # Try to fix any remaining }, { patterns more aggressively
                # This catches cases where the property name has special chars
                fixed = re.sub(r'\},\s*\{("[^"]+"\s*:\s*)', r', \1', fixed)

            result = json.loads(fixed)
            print(f"✓ Successfully parsed after fix attempt {attempt + 1}")
            return result

        except json.JSONDecodeError as e:
            print(f"Fix attempt {attempt + 1} failed: {e}")
            error_context = fixed[max(0, e.pos - 50):min(len(fixed), e.pos + 50)]
            print(f"Error at position {e.pos}: ...{error_context}...")

            if attempt == max_retries - 1:
                # Last attempt - try to manually locate and fix the specific error
                print("\n🔍 Attempting manual repair at error location...")
                fixed = manual_fix_at_position(fixed, e.pos)
                try:
                    result = json.loads(fixed)
                    print("✓ Successfully parsed after manual fix!")
                    return result
                except json.JSONDecodeError as e2:
                    print(f"Manual fix also failed: {e2}")

            json_string = fixed

    # If all else fails, print debug info
    print("\n❌ Failed to parse JSON after all attempts")
    print("\nFirst 500 characters:")
    print(json_string[:500])
    print("\nLast 500 characters:")
    print(json_string[-500:])

    return None


def ask_llm_to_fix_json(broken_json, agent_instance, max_retries=2):
    """Version that uses your agent framework."""

    fix_prompt = f"""The following JSON has formatting errors. Fix and return ONLY valid JSON:

{broken_json}"""

    for attempt in range(max_retries):
        try:
            print(f"\n🔧 Asking LLM to fix JSON (attempt {attempt + 1}/{max_retries})...")

            # Use your existing model
            result = agent_instance.run(fix_prompt)
            fixed_json = result.strip()

            # Clean up
            fixed_json = fixed_json.replace('```json', '').replace('```', '').strip()

            # Try to parse
            parsed = json.loads(fixed_json)
            print("✓ Successfully parsed JSON after LLM fix!")
            return parsed

        except json.JSONDecodeError as e:
            print(f"❌ LLM fix attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                fix_prompt = f"""Previous attempt had error: {str(e)}
Please fix this JSON and return ONLY valid JSON:

{fixed_json if 'fixed_json' in locals() else broken_json}"""

    return None

